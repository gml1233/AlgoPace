import logging
import os
import time
import re
import json
import tempfile
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

from agents.base import BaseAgent
from agents.concept_interpreter import ConceptAnalysis, SubConcept
from agents.manim_models import (
    ScenePlan, SceneAction, ManimSceneCode, RenderResult,
    AnimationResult, AnimationConfig, AnimationMetadata
)
from rendering.manim_renderer import ManimRenderer
from tools.manim_linter import lint_manim_code
from config import settings


_FAST_AAC_ENCODER: Optional[str] = None


def _fast_aac_encoder() -> str:
    """Return the fastest available AAC encoder, probed once per process.

    On the single-scene concat fast path the AAC re-encode is the dominant
    cost once the video stream is copied (measured: 6.4s with the built-in
    ``aac`` encoder vs 1.4s with Windows MediaFoundation's ``aac_mf`` on the
    same 260s file). Falls back to ``settings.audio_codec`` wherever the
    faster encoder is not compiled in, so this is a no-op on other platforms.
    """
    global _FAST_AAC_ENCODER
    if _FAST_AAC_ENCODER is not None:
        return _FAST_AAC_ENCODER

    _FAST_AAC_ENCODER = settings.audio_codec
    try:
        probe = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=20,
        )
        if probe.returncode == 0 and " aac_mf " in probe.stdout:
            _FAST_AAC_ENCODER = "aac_mf"
    except (OSError, subprocess.SubprocessError):
        pass  # keep the configured default

    return _FAST_AAC_ENCODER


class ManimAgent(BaseAgent):
    """
    Manim Agent: Transforms structured concept analysis into visual animations
    using scene planning and Manim code generation with <manim> tag extraction.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        output_dir: Path,
        config: Optional[AnimationConfig] = None,
        reasoning_tokens: Optional[float] = None,
        reasoning_effort: Optional[str] = None
    ):
        super().__init__(api_key=api_key, base_url=base_url, model=model, reasoning_tokens=reasoning_tokens, reasoning_effort=reasoning_effort)
        self.output_dir = Path(output_dir)
        self.config = config or AnimationConfig()
        # Default target_language; overwritten by execute() per run.
        self.target_language = "English"

        # Initialize renderer
        self.renderer = ManimRenderer(
            output_dir=self.output_dir / "scenes",
            quality=self.config.quality,
            background_color=self.config.background_color,
            timeout=self.config.render_timeout,
            max_retries=self.config.max_retries_per_scene,
            preview_fps=self.config.preview_fps
        )

        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "scene_codes").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "animations").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "scenes").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "scene_plans").mkdir(parents=True, exist_ok=True)

        # ========== SKILL 模板系统（多家族：sorting / tree / graph ...） ==========
        # self.skill_registry = {family: {"templates": {name: code}, "base_code": str, "base_class_name": str}}
        # self.skill_templates / self.skill_base_code 保留为"排序家族"的别名，向后兼容。
        self.skill_registry: Dict[str, Dict[str, Any]] = {}
        self.skill_templates: Dict[str, str] = {}
        self.skill_base_code: Optional[str] = None
        self._load_skill_templates()

        # Cache for the latest Visual Contract built during code generation;
        # consumed by Tier 2 (regenerate-from-plan) so we don't rebuild it
        # for every failed scene at render time.
        self._cached_visual_contract: Optional[Dict[str, Any]] = None
        self._latest_planning_response_json: Optional[Dict[str, Any]] = None
        self._continuous_scene_plan: Optional[ScenePlan] = None

    # ========== 语言强制指令模板（运行时按 target_language 渲染） ==========
    # 注意：prepend 方式注入，避免改动下方海量 {{..}}-escaped JSON 模板。
    _PLANNING_LANGUAGE_DIRECTIVE = (
        "LANGUAGE DIRECTIVE (HARD - OVERRIDES EVERYTHING ELSE)\n"
        "- target_language = {target_language}\n"
        "- Scene `title`, `description`, every `parameters.text`,\n"
        "  `parameters.label`, and any other human-readable string field\n"
        "  MUST be written in {target_language}.\n"
        "- `id`, `target`, `action_type`, `element_type`, `sub_concept_id`,\n"
        "  `scene_dependencies` stay in snake_case English (internal IDs).\n"
        "- `parameters.equation` stays in standard LaTeX math.\n"
        "- When {target_language} is Chinese, do NOT include bilingual\n"
        "  parentheticals (e.g. write `\"\u5192\u6ce1\u6392\u5e8f\"`, NOT\n"
        "  `\"\u5192\u6ce1\u6392\u5e8f (Bubble Sort)\"`). No English tail in Chinese titles.\n"
        "- Examples below may be in English for structural illustration only;\n"
        "  your output MUST follow this directive.\n"
        "\n"
    )

    _CODEGEN_LANGUAGE_DIRECTIVE = (
        "LANGUAGE DIRECTIVE (HARD - OVERRIDES EVERYTHING ELSE)\n"
        "- target_language = {target_language}\n"
        "- Every on-screen string you put in `Text(...)`, `Tex(...)`,\n"
        "  scene titles, step text, annotation text, footer text, labels on\n"
        "  `SurroundingRectangle` / `Arrow` / `Brace`, and every\n"
        "  `self.voiceover(text=\"...\")` narration MUST be written in\n"
        "  {target_language}.\n"
        "- `MathTex(...)` stays as standard LaTeX math (do NOT translate\n"
        "  operators, variables, or function names).\n"
        "- `Code(code_string=...)` code stays in its original programming\n"
        "  language; do NOT translate identifiers, keywords, or comments\n"
        "  inside code snippets.\n"
        "- Do NOT reproduce bilingual titles like `\"\u5192\u6ce1\u6392\u5e8f (Bubble Sort)\"`.\n"
        "  Use pure {target_language}, e.g. `\"\u5192\u6ce1\u6392\u5e8f\"`. If the skill\n"
        "  template contains a bilingual title, rewrite it in {target_language}\n"
        "  only.\n"
        "- When {target_language} is Chinese: no English letters are allowed\n"
        "  inside Text/Tex/voiceover strings (numbers, math symbols and\n"
        "  punctuation are fine).\n"
        "\n"
    )

    def _build_planning_system_prompt(self) -> str:
        directive = self._PLANNING_LANGUAGE_DIRECTIVE.format(
            target_language=self.target_language
        )
        return directive + self.SCENE_PLANNING_PROMPT

    def _build_codegen_system_prompt(self, formatted_prompt: str) -> str:
        directive = self._CODEGEN_LANGUAGE_DIRECTIVE.format(
            target_language=self.target_language
        )
        return directive + formatted_prompt

    SCENE_PLANNING_PROMPT = """You are a Manim Scene Planning Agent for an educational STEM animation system.

**TASK**: Create detailed scene plans for animating STEM concepts using Manim (Mathematical Animation Engine).

**INPUT CONCEPT ANALYSIS**:
{concept_analysis}

**ANIMATION GUIDELINES**:

0. **SINGLE-SCENE MODE (MANDATORY — READ BEFORE PLANNING)**:
   - `scene_plans` MUST contain **EXACTLY ONE** plan. Do NOT split the video into
     multiple scenes. The whole algorithm walk-through (opening + initialization +
     main loop + completion + complexity) is ONE continuous Manim `construct(self)`
     so that ALL data-structure mobjects (tree nodes, array boxes, list cells,
     pointers, recursion stack, output sequence …) are CREATED ONCE and remain
     LIVE THROUGHOUT, giving exact, continuous visual tracking with zero
     state re-construction.
   - The single plan MUST have:
     - `id` = `"algorithm_full"`
     - `title` = the algorithm name (use `concept_analysis.main_concept` verbatim)
     - `description` = a one-line summary of the whole walk-through
     - `sub_concept_id` = `""`
     - `scene_dependencies` = `[]`
   - The plan's `actions` list is the entire ordered timeline of the video and
     SHOULD be organised into the following five PHASES (use ordinary `actions`
     for each phase — do NOT introduce new top-level keys):

     PHASE A — Opening (8-14s):
       a1. ONE action with `action_type: "show_overview_instant"`,
           `element_type: "diagram"`, `target: "algorithm_overview"`,
           `duration` = total narration duration (≈ 0.25s per Chinese char or
           0.4s per English word), and
           `parameters` = `{{"title": "<the algorithm title>",
                            "sentences": ["<sent 1>", "<sent 2>", ...]}}`.
           Contract: the title text AND the COMPLETE data structure must be
           DRAWN IN FRAME 0 instantly via `self.add(...)`, NO `Write` / `Create`
           / `FadeIn` / `LaggedStart` reveal — so the video's first frame is a
           complete thumbnail. The sentences are voiced one-by-one (each is its
           own SRT subtitle entry, so subtitles appear sentence-by-sentence).
       a2. ONE action with `action_type: "fade_out_title"`, `element_type: "none"`,
           `target: "intro_title_cleanup"`, `duration: 0.6`.
           Contract: fade out the TITLE TEXT ONLY. The data structure (tree /
           array / list / sequence list) MUST REMAIN ON SCREEN — it will be
           reused as-is throughout phases B-E. DO NOT call `FadeOut` on the
           structure mobjects.

     PHASE B — Initialization (10-25s):
       Bring in the algorithm's auxiliary state on top of the SAME data
       structure: code panel (if any), step-text region, pointer(s) starting
       position, recursion stack panel, output-sequence row, etc. Use
       `fade_in` / `create` / `write` actions. NEVER recreate the data
       structure itself.

     PHASE C — Main Trace (60-180s):
       The actual algorithm execution, step by step, against the live data
       structure from phase A. Highlight nodes/elements, move pointers,
       push/pop stack, append to output, swap/relax/visit, etc. The data
       structure mobjects from phase A are MUTATED IN PLACE — same VGroups,
       same coordinates.

     PHASE D — Completion (10-20s):
       Show the final state: result text, full output sequence, "done"
       indicator. Keep the data structure visible.

     PHASE E — Complexity (10-20s):
       Show time / space complexity info (corner panel via base-class helper
       when available). Final voiceover summarising the algorithm.

   - Total scene duration: ≈ 120-260 seconds (2-4 min). It is OK and expected.
   - Between phases, do NOT clear the entire screen. The only allowed cleanup
     is the `fade_out_title` at the end of phase A, plus targeted `fade_out`
     of obsolete auxiliary elements (step-text being replaced, etc.).
   - DO NOT use `Write` / `Create` / `LaggedStart` / `FadeIn` anywhere inside
     the `show_overview_instant` action — that action's contract is INSTANT
     draw only.

1. **Scene Structure**:
   - You MUST emit exactly ONE entry in `scene_plans` (see rule 0).
   - That single entry holds the full algorithm walk-through (~120-260s total).
   - Build the `actions` list in the ordered phases A-E from rule 0.
   - For algorithm code tracing: dedicate consecutive blocks of actions to
     initialization, each major loop iteration / recursive call, and final
     results — all inside the SAME `actions` list, with the SAME data-structure
     mobjects mutated in place.

2. **Visual Design**:
   - Use clear, educational visual style (dark background, bright elements)
   - Include mathematical notation, equations, diagrams
   - Show relationships and transformations visually
   - Use color coding consistently:
     - Blue (#3B82F6) for known/assumed quantities
     - Green (#22C55E) for newly introduced concepts
     - Red (#EF4444) for key/important results or warnings

3. **Consistency & Continuity (VERY IMPORTANT)**:
   - If an illustrative example is used to demonstrate the concept (e.g., a specific array for a sorting algorithm, a fixed probability scenario, a single graph), **use the exact same example and values across all scenes** unless a scene explicitly explores a variant. 
   - Keep element IDs and targets stable across scenes (e.g., "example_array", "disease_prevalence_box") to preserve continuity.
   - Reuse and transform existing elements instead of recreating them where possible.
   - For linked-list algorithms, define one top-level `canonical_example` and reuse it in every scene.
     For deletion, it MUST include the initial node values, the delete position, the deleted value,
     and pointer names (usually `L`, `p`, `q`). Every scene action that references the linked list
     should repeat these values in `parameters` or explicitly reference the canonical example.
   - For linked-list deletion specifically, never change the node values, delete index, delete value,
     head-node convention, or pointer naming between scenes. A scene showing the final state must
     derive it from the same initial list and delete index.

4. **Animation Types**:
   - write / create: introduce text, equations, axes, or diagrams
   - transform / replace: mathematical transformations, substitutions, rearrangements
   - fade_in / fade_out: introduce or remove elements
   - move / highlight: focus attention
   - grow / shrink: emphasize scale or importance
   - **wait**: insert a timed pause with nothing changing on screen (used for narration beats)

5. **Pacing & Narration Cues**:
   - Animations should be **slow and deliberate**. After each significant action (write, transform, highlight, etc.), insert a **wait** action of 1.5–3.0 seconds for narration.
   - Typical durations (guideline, adjust as needed):
     - write/create (short text/equation): 4–5s
     - transform/replace (equation/diagram): 8-19s
     - move/highlight: 3-5s
     - fade_in/out: 2-5s
     - wait (narration): 2-4s
   - Prefer easing that reads smoothly (ease-in-out). Include `"parameters": {"easing": "ease_in_out"}` when relevant.

6. **Educational Flow**:
   - Start with context/overview
   - Introduce new elements step-by-step
   - Show relationships and connections visually
   - End with key takeaways or summaries, keeping the same example visible to reinforce learning

7. **Screen Layout Planning (IMPORTANT)**:
   - For each scene, plan which **screen zone** each element occupies:
     - TITLE ZONE (top): scene title only
     - MAIN ZONE (center): primary visualization (array, diagram, equation)
     - ANNOTATION ZONE (below center): step descriptions, explanatory text
     - FOOTER ZONE (just above the subtitle safe band): complexity info, small labels
     - **SUBTITLE SAFE ZONE (bottom, y ≈ -4.0 to -3.33)**: RESERVED for burned-in subtitles.
       NEVER place any visible element here. All mobjects must have `get_bottom()[1] >= -3.3`.
   - In the action descriptions, mention the intended zone when ambiguous.
   - **MAX on-screen elements**: ~5–7 at any moment. If adding more, specify which old elements to remove.
   - When a new action introduces text/labels near existing content, describe relative positioning (e.g., "below the array", "to the right of the equation").

8. **Element Naming**:
   - Use descriptive, stable targets (e.g., "bayes_equation", "likelihood_label", "frequency_grid") reused across scenes.
   - When transforming, specify `"parameters": {"from": "<old_target>", "to": "<new_target>"}` where helpful.

**OUTPUT FORMAT**:
Return ONLY valid JSON matching this exact structure. `canonical_example` is mandatory when an
algorithm is demonstrated with concrete data. `scene_plans` MUST contain EXACTLY ONE element
(see rule 0 — single-scene mode).
{{
    "canonical_example": {{
        "data": [10, 20, 30, 40, 50],
        "delete_index": 3,
        "delete_value": 30,
        "pointer_names": ["L", "p", "q"],
        "invariant": "The single scene uses this exact example end-to-end; later states are mutated in place from the initial mobjects."
    }},
    "scene_plans": [
        {{
            "id": "algorithm_full",
            "title": "<algorithm name verbatim>",
            "description": "Single continuous scene: opening overview → initialization → main trace → completion → complexity. The data-structure mobjects from the opening persist throughout.",
            "sub_concept_id": "",
            "actions": [
                {{
                    "action_type": "show_overview_instant",
                    "element_type": "diagram",
                    "description": "PHASE A. Draw title + COMPLETE data structure in frame 0 (no animation). Voice each sentence of the algorithm description one at a time.",
                    "target": "algorithm_overview",
                    "duration": 10.0,
                    "parameters": {{"title": "<algorithm name>", "sentences": ["<sentence 1 ending with 。/.>", "<sentence 2 ending with 。/.>", "<sentence 3 ending with 。/.>"]}}
                }},
                {{
                    "action_type": "fade_out_title",
                    "element_type": "none",
                    "description": "PHASE A end. Fade out ONLY the title text; the data structure stays on screen and is reused for phases B-E.",
                    "target": "intro_title_cleanup",
                    "duration": 0.6,
                    "parameters": {{}}
                }},
                {{
                    "action_type": "<phase B action>",
                    "element_type": "...",
                    "description": "PHASE B: bring in auxiliary state (code panel, pointers, stack, output row) — DO NOT recreate the data structure.",
                    "target": "...",
                    "duration": 0,
                    "parameters": {{}}
                }},
                {{
                    "action_type": "<phase C action>",
                    "element_type": "...",
                    "description": "PHASE C: highlight nodes, move pointers, push/pop stack, append output, etc. The data-structure mobjects are MUTATED IN PLACE.",
                    "target": "...",
                    "duration": 0,
                    "parameters": {{}}
                }}
            ],
            "scene_dependencies": []
        }}
    ]
}}

**LEGACY EXAMPLE** for Bayes' Theorem — kept ONLY as an illustration of the action-level
JSON syntax (`action_type`, `parameters`, etc.). The multi-scene shape shown here is
OBSOLETE: under SINGLE-SCENE MODE (rule 0) you MUST emit exactly ONE entry in
`scene_plans`, and treat the scene boundaries shown below as PHASE BOUNDARIES inside that
single scene's `actions` list. Do NOT copy the multi-scene layout.
{{
    "canonical_example": {{
        "scenario": "medical test",
        "prevalence": 0.01,
        "sensitivity": 0.90,
        "specificity": 0.95,
        "invariant": "All scenes reuse this exact scenario and these exact numbers."
    }},
    "scene_plans": [
        {{
            "id": "intro_context",
            "title": "Bayes' Theorem: Context & Setup",
            "description": "Introduce the medical testing example and define prior, sensitivity, and specificity.",
            "sub_concept_id": "context_prior",
            "actions": [
                {{
                    "action_type": "fade_in",
                    "element_type": "text",
                    "description": "Display title 'Bayes' Theorem'",
                    "target": "title_text",
                    "duration": 2.0,
                    "parameters": {{"text": "Bayes' Theorem", "color": "#FFFFFF"}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Narration pause after title",
                    "target": "narration_pause_1",
                    "duration": 2.0,
                    "parameters": {{}}
                }},
                {{
                    "action_type": "write",
                    "element_type": "text",
                    "description": "Present consistent example scenario",
                    "target": "scenario_text",
                    "duration": 5.0,
                    "parameters": {{"text": "Medical test scenario: Disease prevalence 1%, Sensitivity 90%, Specificity 95%", "color": "#FFFFFF", "easing": "ease_in_out"}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Pause for narrator to explain prevalence and test properties",
                    "target": "narration_pause_2",
                    "duration": 2.0,
                    "parameters": {{}}
                }},
                {{
                    "action_type": "write",
                    "element_type": "math_equation",
                    "description": "Define prior and test properties with color coding",
                    "target": "definitions",
                    "duration": 6.0,
                    "parameters": {{"equation": "P(D)=0.01,\\ \\text{{sensitivity}}=0.90,\\ \\text{{specificity}}=0.95", "color": "#3B82F6", "easing": "ease_in_out"}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Hold before moving on",
                    "target": "narration_pause_3",
                    "duration": 2.0,
                    "parameters": {{}}
                }},
                {{
                    "action_type": "write",
                    "element_type": "diagram",
                    "description": "Draw a population box to anchor the example that persists across scenes",
                    "target": "population_box",
                    "duration": 6.0,
                    "parameters": {{"style": "outlined", "color": "#3B82F6", "label": "Population"}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Pause to reinforce the setup",
                    "target": "narration_pause_4",
                    "duration": 3.0,
                    "parameters": {{}}
                }}
            ],
            "scene_dependencies": []
        }},
        {{
            "id": "equation_intro",
            "title": "Bayes' Formula",
            "description": "Introduce Bayes' theorem and map terms to the example.",
            "sub_concept_id": "bayes_equation",
            "actions": [
                {{
                    "action_type": "write",
                    "element_type": "math_equation",
                    "description": "Write Bayes' theorem",
                    "target": "bayes_equation",
                    "duration": 4.0,
                    "parameters": {{"equation": "P(D\\mid +)=\\frac{{P(+\\mid D)P(D)}}{{P(+)}}", "color": "#22C55E", "easing": "ease_in_out"}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Pause to read equation",
                    "target": "narration_pause_5",
                    "duration": 2.0,
                    "parameters": {{}}
                }},
                {{
                    "action_type": "write",
                    "element_type": "text",
                    "description": "Label terms: prior, likelihood, evidence, posterior",
                    "target": "term_labels",
                    "duration": 5.0,
                    "parameters": {{"text": "prior: P(D) (blue), likelihood: P(+|D) (green), evidence: P(+) (white), posterior: P(D|+) (red)", "color": "#FFFFFF"}}
                }},
                {{
                    "action_type": "highlight",
                    "element_type": "math_equation",
                    "description": "Color-code terms on the formula",
                    "target": "bayes_equation",
                    "duration": 3.0,
                    "parameters": {{"spans": [{{"term": "P(D)", "color": "#3B82F6"}}, {{"term": "P(+\\mid D)", "color": "#22C55E"}}, {{"term": "P(+)", "color": "#FFFFFF"}}, {{"term": "P(D\\mid +)", "color": "#EF4444"}}]}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Narration pause after mapping",
                    "target": "narration_pause_6",
                    "duration": 2.0,
                    "parameters": {{}}
                }}
            ],
            "scene_dependencies": ["intro_context"]
        }},
        {{
            "id": "tree_diagram",
            "title": "Likelihood Paths via Tree",
            "description": "Show a probability tree aligned with the same example numbers.",
            "sub_concept_id": "likelihood_evidence",
            "actions": [
                {{
                    "action_type": "write",
                    "element_type": "diagram",
                    "description": "Draw tree branches for D and ¬D from population",
                    "target": "probability_tree",
                    "duration": 6.0,
                    "parameters": {{"from": "population_box", "branches": [{{"label": "D (1%)", "color": "#3B82F6"}}, {{"label": "¬D (99%)", "color": "#3B82F6"}}]}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Pause for narrator to explain branches",
                    "target": "narration_pause_7",
                    "duration": 2.0,
                    "parameters": {{}}
                }},
                {{
                    "action_type": "write",
                    "element_type": "diagram",
                    "description": "Add test outcome branches with sensitivity/specificity",
                    "target": "probability_tree_outcomes",
                    "duration": 6.0,
                    "parameters": {{"branches": [{{"from": "D", "label": "+ (90%)", "color": "#22C55E"}}, {{"from": "D", "label": "− (10%)", "color": "#22C55E"}}, {{"from": "¬D", "label": "+ (5%)", "color": "#22C55E"}}, {{"from": "¬D", "label": "− (95%)", "color": "#22C55E"}}]}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Pause after outcomes",
                    "target": "narration_pause_8",
                    "duration": 2.0,
                    "parameters": {{}}
                }},
                {{
                    "action_type": "highlight",
                    "element_type": "diagram",
                    "description": "Highlight the evidence paths that lead to '+'",
                    "target": "probability_tree_outcomes",
                    "duration": 3.0,
                    "parameters": {{"paths": ["D→+", "¬D→+"], "color": "#EF4444"}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Hold to emphasize 'evidence' P(+)",
                    "target": "narration_pause_9",
                    "duration": 2.0,
                    "parameters": {{}}
                }}
            ],
            "scene_dependencies": ["intro_context", "equation_intro"]
        }},
        {{
            "id": "frequency_view",
            "title": "Frequency Grid Intuition",
            "description": "Use a 10,000-dot grid to make P(+) and P(D|+) concrete with the same numbers.",
            "sub_concept_id": "evidence_frequency",
            "actions": [
                {{
                    "action_type": "write",
                    "element_type": "diagram",
                    "description": "Create 10,000-dot grid inside population box (persists across scenes)",
                    "target": "frequency_grid",
                    "duration": 6.0,
                    "parameters": {{"rows": 100, "cols": 100, "color": "#555555", "parent": "population_box"}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Pause for narrator to explain frequency framing",
                    "target": "narration_pause_10",
                    "duration": 2.0,
                    "parameters": {{}}
                }},
                {{
                    "action_type": "highlight",
                    "element_type": "diagram",
                    "description": "Color 100 diseased dots (1%) in blue",
                    "target": "frequency_grid_D",
                    "duration": 4.0,
                    "parameters": {{"count": 100, "color": "#3B82F6"}}
                }},
                {{
                    "action_type": "highlight",
                    "element_type": "diagram",
                    "description": "Among D, highlight 90 true positives in green",
                    "target": "frequency_grid_TP",
                    "duration": 4.0,
                    "parameters": {{"count": 90, "color": "#22C55E"}}
                }},
                {{
                    "action_type": "highlight",
                    "element_type": "diagram",
                    "description": "Among ¬D, highlight 495 false positives (5% of 9,900) in green outline",
                    "target": "frequency_grid_FP",
                    "duration": 5.0,
                    "parameters": {{"count": 495, "style": "outline", "color": "#22C55E"}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Hold to let counts sink in",
                    "target": "narration_pause_11",
                    "duration": 3.0,
                    "parameters": {{}}
                }}
            ],
            "scene_dependencies": ["intro_context", "equation_intro", "tree_diagram"]
        }},
        {{
            "id": "posterior_compute",
            "title": "Compute P(D|+)",
            "description": "Compute the posterior step-by-step using the same counts and Bayes' formula.",
            "sub_concept_id": "posterior_computation",
            "actions": [
                {{
                    "action_type": "write",
                    "element_type": "math_equation",
                    "description": "Substitute numeric values into Bayes' formula",
                    "target": "substitution",
                    "duration": 5.0,
                    "parameters": {{"equation": "P(D\\mid +)=\\frac{{0.90\\times 0.01}}{{0.90\\times 0.01 + 0.05\\times 0.99}}", "color": "#FFFFFF"}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Pause for narrator before simplifying",
                    "target": "narration_pause_12",
                    "duration": 2.0,
                    "parameters": {{}}
                }},
                {{
                    "action_type": "transform",
                    "element_type": "math_equation",
                    "description": "Simplify numerators and denominators",
                    "target": "substitution",
                    "duration": 4.0,
                    "parameters": {{"to_equation": "P(D\\mid +)=\\frac{{0.009}}{{0.009+0.0495}}", "color": "#FFFFFF", "easing": "ease_in_out"}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Pause before final result",
                    "target": "narration_pause_13",
                    "duration": 2.0,
                    "parameters": {{}}
                }},
                {{
                    "action_type": "transform",
                    "element_type": "math_equation",
                    "description": "Compute final posterior and highlight",
                    "target": "substitution",
                    "duration": 4.0,
                    "parameters": {{"to_equation": "P(D\\mid +)\\approx 0.1538\\ (15.38\\%)", "color": "#EF4444", "easing": "ease_in_out"}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Hold on final posterior",
                    "target": "narration_pause_14",
                    "duration": 3.0,
                    "parameters": {{}}
                }}
            ],
            "scene_dependencies": ["equation_intro", "frequency_view"]
        }},
        {{
            "id": "interpretation_pitfalls",
            "title": "Interpretation & Common Pitfall",
            "description": "Explain why a positive test doesn't mean near-certainty; connect to base rates.",
            "sub_concept_id": "interpretation",
            "actions": [
                {{
                    "action_type": "write",
                    "element_type": "text",
                    "description": "State the common mistake: confusing P(+|D) with P(D|+)",
                    "target": "pitfall_text",
                    "duration": 4.0,
                    "parameters": {{"text": "Pitfall: P(+|D) \\neq P(D|+)", "color": "#EF4444"}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Pause for narrator",
                    "target": "narration_pause_15",
                    "duration": 2.0,
                    "parameters": {{}}
                }},
                {{
                    "action_type": "highlight",
                    "element_type": "diagram",
                    "description": "Re-highlight 90 TP vs 495 FP on the same grid to show contrast",
                    "target": "frequency_grid_contrast",
                    "duration": 4.0,
                    "parameters": {{"groups": [{{"label": "TP=90", "color": "#22C55E"}}, {{"label": "FP=495", "color": "#EF4444"}}]}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Hold to let the contrast register",
                    "target": "narration_pause_16",
                    "duration": 3.0,
                    "parameters": {{}}
                }}
            ],
            "scene_dependencies": ["posterior_compute"]
        }},
        {{
            "id": "summary_takeaways",
            "title": "Summary & Takeaways",
            "description": "Summarize Bayes' theorem using the same scenario and numbers.",
            "sub_concept_id": "summary",
            "actions": [
                {{
                    "action_type": "write",
                    "element_type": "text",
                    "description": "List key takeaways linked to the same example",
                    "target": "summary_points",
                    "duration": 6.0,
                    "parameters": {{"text": "1) Base rates matter. 2) Evidence combines with prior via likelihood. 3) Posterior here ≈ 15.38%.", "color": "#FFFFFF"}}
                }},
                {{
                    "action_type": "wait",
                    "element_type": "none",
                    "description": "Final narration pause",
                    "target": "narration_pause_17",
                    "duration": 3.0,
                    "parameters": {{}}
                }},
                {{
                    "action_type": "fade_out",
                    "element_type": "group",
                    "description": "Fade out all elements to close",
                    "target": "all_elements",
                    "duration": 2.0,
                    "parameters": {{}}
                }}
            ],
            "scene_dependencies": ["interpretation_pitfalls"]
        }}
    ]
}}

Generate scene plans that will create clear, educational animations for the given concept, using a single consistent example across scenes, with slow pacing and explicit narration pauses after each major action."""

    CODE_GENERATION_PROMPT = """You are a Manim Code Generation Agent for creating **very simple, 2D educational STEM animations with integrated voiceover**.

**TASK**: From the single **SCENE PLAN** below (one scene at a time), generate complete, executable Manim code for the **currently installed Manim Community Edition** in the runtime environment. Use only APIs that are valid for that install; the output will be checked by `manim-lint` against that exact Manim version.

**SCENE PLAN (SINGLE SCENE ONLY)**:
{scene_plan}

**CLASS NAME**: {class_name}
**TARGET DURATION (approx.)**: {target_duration} seconds

============================================================
SIMPLE 2D-ONLY MODE (STRICT)
============================================================

0) **Hard Limits (Do Not Violate)**
   - **2D only**: No 3D classes/cameras/surfaces/axes3D; do not import/use `ThreeDScene`.
   - **Exactly one scene class** named **{class_name}**, inheriting from `VoiceoverScene`.
   - **One file**, **one class**, **one `construct(self)`** method.
   - **No updaters** (no `add_updater`, no `always_redraw`).
   - **No ValueTracker / DecimalNumber**; keep logic static and stepwise.
   - **No config edits**, no camera/frame changes, no run_time tweaks (use `self.wait()` only).

0.5) **SINGLE-SCENE MODE + OPENING PHASE (READ FIRST)**

   This pipeline now produces **ONE Manim class** that runs the ENTIRE algorithm
   walk-through end-to-end (the scene plan's `id` is `"algorithm_full"`). Data-
   structure mobjects are CREATED ONCE in the opening phase and remain LIVE
   across the rest of the scene — every later `self.play(...)` call MUTATES
   them in place instead of recreating them. NEVER tear down and re-build the
   tree / array / list during this scene.

   The first two actions in the plan form the OPENING PHASE and have a strict
   contract that OVERRIDES the generic `action_type` mapping in section 3:

     • Action `show_overview_instant` (`parameters` has `title` + `sentences`)
     • Action `fade_out_title` (clears ONLY the title; structure stays)

   The remaining actions (PHASE B-E in the plan) follow the normal `action_type`
   mapping in section 3, using the SAME mobjects that were `self.add(...)`-ed
   in phase A.

   Required `construct(self)` skeleton (phases A → E in one method):
   ```python
   def construct(self):
       self.set_speech_service(...)  # follow the voiceover setup snippet

       # ===== PHASE A — OPENING (instant draw + sentence-by-sentence narration) =====
       # 1) Title mobject, positioned at top. Keep a reference — it is faded
       #    out at the end of phase A. Do NOT name it `title_mob` if the skill
       #    base class already owns that attribute; use `algo_title` instead.
       algo_title = Text("<title verbatim from parameters['title']>",
                         font_size=48, weight=BOLD).to_edge(UP, buff=0.6)
       # 2) COMPLETE data structure, drawn in frame 0 with NO animation.
       #    When a SHARED VISUAL CONTRACT / skill base class is provided below,
       #    call its `*_instant` helper:
       #      - sorting / array  → `self.show_array_instant(SHARED_DATA, title=None, show_indices=True)`
       #      - tree             → `self.setup_default_tree_instant(SHARED_DATA)`
       #      - linked list      → `self.setup_list_data_instant(SHARED_DATA)`
       #      - sequential list  → `self.setup_list_data_instant(SHARED_DATA)`
       #    These helpers use `self.add(...)` internally — NO `self.play(...)`.
       #    Keep the returned root / VGroup as a class-local variable; it WILL
       #    be reused across phases B-E.
       self.add(algo_title)
       root = self.setup_default_tree_instant(SHARED_DATA)   # or equivalent helper
       # 3) Voice the description SENTENCE-BY-SENTENCE. Each sentence in
       #    parameters['sentences'] becomes its OWN voiceover block (and SRT
       #    subtitle entry). The screen stays COMPLETELY STATIC — NO
       #    `self.play(...)` calls between sentences, only `self.wait(tracker.duration)`.
       for sentence in [
           "<sentence 1 verbatim from parameters['sentences'][0]>",
           "<sentence 2 verbatim from parameters['sentences'][1]>",
           "<sentence 3 verbatim from parameters['sentences'][2]>",
       ]:
           with self.voiceover(text=sentence) as tracker:
               self.wait(tracker.duration)
       # 4) END of phase A — fade out the TITLE ONLY (action `fade_out_title`).
       #    DO NOT FadeOut the data structure — it MUST stay visible.
       self.play(FadeOut(algo_title), run_time=0.6)

       # ===== PHASES B-E — INITIALIZATION → MAIN TRACE → COMPLETION → COMPLEXITY =====
       # The data structure created in phase A is still on screen. From here on,
       # follow the generic action mapping (section 3) and use base-class helpers
       # (`self.highlight_node`, `self.move_pointer`, `self.swap_elements`, etc.)
       # to MUTATE the existing mobjects. NEVER call `*_instant` again, NEVER
       # rebuild `SHARED_DATA` from scratch — the same mobjects must be reused.
       # ... (the rest of the actions from the plan, generated normally) ...
   ```

   Hard rules:
   - Phase A actions (`show_overview_instant` + `fade_out_title`) are NOT
     mapped via section 3 — follow the contract above exactly.
   - In `show_overview_instant`: NO `Write` / `Create` / `LaggedStart` / `FadeIn` /
     `GrowArrow` / `GrowFromCenter`. The title and the data structure MUST
     exist via `self.add(...)` (or an instant-helper that uses `self.add(...)`)
     BEFORE any `self.play(...)` call in the scene. The first rendered frame
     must contain both, suitable as a thumbnail.
   - The sentences inside each `self.voiceover(text=...)` MUST come from
     `parameters['sentences']` verbatim, ONE LIST ITEM PER VOICEOVER BLOCK.
     Do NOT join them into one long string (that would produce a single SRT
     entry showing all lines at once). Do NOT split them further. Do NOT
     paraphrase. Emit EXACTLY `len(sentences)` voiceover blocks, in order.
   - Between consecutive sentence voiceover blocks in phase A, do NOT call
     `self.play(...)`, `FadeIn`, `Write`, `Create`, or `self.wait()` with a
     literal number. The only allowed call inside each `with` block is
     `self.wait(tracker.duration)`.
   - For `fade_out_title`: the ONLY mobject faded out is `algo_title`. NEVER
     do `self.play(*[FadeOut(m) for m in self.mobjects], ...)` — that would
     destroy the data structure and break visual continuity.
   - During phases B-E: do NOT call any `*_instant` helper a second time, do
     NOT call `self.show_tree` / `self.show_array` / `self.setup_list_data`
     after phase A (the structure is already on screen). Use the base-class
     mutation helpers only.
   - Backward-compatibility fallback: if `parameters` has a legacy
     `narration` string instead of `sentences`, split that string on terminal
     punctuation `[。！？.!?]` (keeping the punctuation with the preceding
     sentence) into 2-4 sentences and apply the same per-sentence voiceover
     pattern.

1) **Imports**
   - Always start with: `from manim import *`
   - Must include: `from manim_voiceover import VoiceoverScene`
   - Include service-specific import exactly as follows:
{voiceover_imports}
   - Optionally: `import numpy as np` **only if actually used**.
   - Import nothing else.

2) **Element Types & Mapping**
   - Use **`Text`** for plain text, **`MathTex`** for math, **`Tex`** for LaTeX (non-math).
   - **Code**: For snippet strings use `Code(code_string=code_str, language="cpp")` (or `"python"` etc.); for files use `code_file=path`. Valid kwargs ONLY: `code_string`, `code_file`, `language`, `formatter_style`, `tab_width`, `add_line_numbers`, `background`, `background_config`, `paragraph_config`. **Never** use `code=`, `font=`, or `font_size=` — they are invalid for typical Manim CE installs and `manim-lint` will flag misuse. To access individual lines, use `code_obj.code_lines[i]` (portable); avoid `code_obj.code[i]` — if unsure, follow linter diagnostics for your environment.
   - Allowed 2D mobjects: `Dot, Line, Arrow, Vector, Circle, Square, Rectangle, Triangle, NumberPlane, Axes, Brace, SurroundingRectangle, Text, MathTex, Tex, Code, VGroup`.
   - Unsupported elements in the plan (e.g., complex “diagram” types) must be **downgraded** to simple shapes + labels (e.g., boxes, lines, arrows, small groups of dots).

3) **Action → Code Mapping (Use Only These)**
   - `"write"` → `self.play(Write(obj))`
   - `"create"` → `self.play(Create(obj))`
   - `"fade_in"` / `"fade_out"` → `FadeIn(obj)` / `FadeOut(obj)`
   - `"transform"` → `Transform(old, new)` (both must exist/added)
   - `"replacement_transform"` → `ReplacementTransform(old, new)`
   - `"move"` → `obj.animate.shift(DIR * amount)`
   - `"highlight"` → Prefer `Indicate(obj)`; or show a `SurroundingRectangle(obj)` with `FadeIn`/`FadeOut`
   - `"wait"` → `self.wait(duration)`
   - Any other `action_type` not listed → use nearest allowed mapping or **skip with a short comment** (still respect pacing).

4) **Using `target` as Variable Names (Continuity)**
   - For each action, **use the plan’s `"target"` as the Python variable name** (sanitize to snake_case, alphanumerics + underscores).
   - Reuse the same variable to transform/indicate; do **not** recreate after `FadeOut` unless the plan explicitly reintroduces it.
   - If the SCENE PLAN references elements created in earlier scenes, **stub a minimal placeholder** (e.g., a labeled `Rectangle` or `Text`) consistent with the example, so this scene remains executable without cross-scene state.

5) **Parameters Handling**
   - Map common fields directly:
     - `{{"text": "..."}}` → Text(...) or Tex(...)
     - `{{"equation": "..."}}` → MathTex(r"...")
     - `{{"color": BUILTIN_COLOR}}`
   - **Colors (Built-ins Only)**: `WHITE, BLACK, RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, PINK`. **Never use CYAN.**
   - If plan provides hex colors (e.g., `#3B82F6`), **replace with the closest built-in** (e.g., `BLUE`, `GREEN`, `RED`, `WHITE`).
   - Ignore unsupported params silently; keep code minimal.

6) **Pacing & Narration (Derived from Plan)**
   - Set speech service as the first step in `construct(self)`:
{tts_setup_snippet}
   - Every major action must be driven by voiceover:
     `with self.voiceover(text="...") as tracker:`
     `    self.play(..., run_time=tracker.duration)`
   - Narration text should be concise and educational.
   - Prefer voiceover-driven timing instead of `self.wait()`.

7) **Layout & Anti-overlap (CRITICAL — READ CAREFULLY)**

   Manim default frame: 14.2 units wide × 8 units tall. Center is ORIGIN (0,0).
   X range: roughly −7.1 to +7.1.  Y range: roughly −4 to +4.

   **⚠ SUBTITLE SAFE ZONE (HARD CONSTRAINT)**
   The bottom band `y ∈ [−4.0, −3.33]` is **RESERVED for burned-in subtitles**.
   - NO visible mobject (text, shape, arrow, label, etc.) may overlap this band.
   - After every positioning call, the element must satisfy `mobj.get_bottom()[1] >= -3.3`.
   - Do NOT use bare `to_edge(DOWN)` (which lands near y ≈ −3.6). Always pass a buff
     so the element stays above the safe band, e.g. `to_edge(DOWN, buff=0.9)`.
   - Do NOT use `.move_to(DOWN * 2.8)` or lower. Maximum downward shift is `DOWN * 2.2`.
   - Do NOT use `.to_corner(DL)` / `.to_corner(DR)` bare — prefer `.to_corner(UR)` /
     `.to_corner(UL)`, or add `buff=1.0` if a bottom corner is truly needed.

   **A) Screen Zone Map** — assign every element to ONE zone:
   ```
   ┌──────────────────────────────────────┐  y ≈ +4.0
   │  TITLE ZONE   (to_edge(UP))         │  y ≈ +3.0 to +4.0
   ├──────────────────────────────────────┤
   │  SUBTITLE ZONE (UP * 2.5)           │  y ≈ +2.0 to +3.0
   ├──────────────────────────────────────┤
   │                                      │
   │   MAIN CONTENT ZONE                 │  y ≈ −1.0 to +2.0
   │   (ORIGIN or slight shift)          │
   │                                      │
   ├──────────────────────────────────────┤
   │  ANNOTATION ZONE                    │  y ≈ −1.5 to −2.4
   │  (step text, secondary labels)      │
   ├──────────────────────────────────────┤
   │  FOOTER ZONE                        │  y ≈ −2.5 to −3.3
   │  (to_edge(DOWN, buff=0.9))          │
   ├──────────────────────────────────────┤  y ≈ −3.33
   │  SUBTITLE SAFE ZONE (FORBIDDEN)     │  y ≈ −3.33 to −4.0
   └──────────────────────────────────────┘
   ```

   **B) Concrete positioning rules**:
   - Title: `title.to_edge(UP)` → stays near y ≈ +3.5. Max font_size=48.
   - Subtitle / secondary heading: `.move_to(UP * 2.5)` or `.next_to(title, DOWN, buff=0.5)`. Max font_size=36.
   - Main visualization (arrays, diagrams, equations): keep centered, ideally between y = −1.0 and y = +1.5.
     Use `.move_to(ORIGIN)` or `.move_to(UP * 0.5)` to leave room for annotations below.
   - Annotation / step text: `.move_to(DOWN * 2.0)` or `.next_to(main_content, DOWN, buff=0.6)`. Max font_size=28.
     After positioning, ensure `get_bottom()[1] >= -3.3`; if lower, `.shift(UP * (-3.3 - mobj.get_bottom()[1]))`.
   - Footer / complexity info: `.to_edge(DOWN, buff=0.9)` or `.to_corner(UR)`. Max font_size=22.
     (Bare `.to_edge(DOWN)` / `.to_corner(DR)` is FORBIDDEN — it enters the subtitle safe zone.)

   **C) Overlap-prevention rules**:
   - **NEVER place two independent elements in the same zone** without using `next_to()` or `arrange()`.
   - Before adding a NEW element to a zone already occupied, **FadeOut the old element first**, OR
     use `ReplacementTransform(old, new)` to swap them in place.
   - Use `buff=0.5` minimum between vertically stacked elements (default is 0.25, too tight).
   - When multiple text/equation blocks appear, group them: `VGroup(a, b, c).arrange(DOWN, buff=0.5)`.
   - **MAX on-screen elements at any moment**: ~5–7 mobjects. If you need more, FadeOut older ones first.
   - Side-by-side layouts: use `LEFT * 3.5` and `RIGHT * 3.5` to split screen into two halves.

   **D) Font size limits** (strict, by zone):
   - Title: 40–48
   - Main content Text: 30–40 ; MathTex: 36–44
   - Annotation / step text: 24–30
   - Labels / captions: 18–24
   - **Never exceed font_size=48** for any element.

   **E) Element lifecycle management**:
   - Track what is visible. Before adding element N+1, ask: "Is there room?"
   - If the scene has accumulated ≥ 6 visible elements, FadeOut the least-important ones.
   - At scene transitions or topic shifts, clear old content:
     `self.play(*[FadeOut(mob) for mob in self.mobjects])`
   - Pointer arrows / SurroundingRectangles are TEMPORARY: always FadeOut after 2–3s.

   **F) Common anti-patterns to AVOID**:
   - ❌ Placing explanation text at ORIGIN when a diagram is already there.
   - ❌ Stacking > 3 text lines without using VGroup + arrange.
   - ❌ Using `self.add()` instead of `self.play(FadeIn())` — self.add skips layout awareness.
   - ❌ Forgetting to FadeOut highlight rectangles or pointer arrows.
   - ❌ Using font_size > 48 or very long single-line Text (> 50 chars). Break into multiple lines or reduce font.
   - ❌ Entering the SUBTITLE SAFE ZONE (y < −3.3): bare `to_edge(DOWN)`, `to_corner(DR)`, `to_corner(DL)`, `.move_to(DOWN * 2.8)` or lower, or any `.next_to(..., DOWN, buff=...)` whose result ends up below y = −3.3.
   - ❌ Using `Code(code=...)`, `Code(..., font=...)`, or `Code(..., font_size=...)` — all **invalid**. Only use: `Code(code_string=..., language=..., tab_width=..., background=...)`.
   - ❌ Using `code_obj.code[i]` to access lines — **invalid** (`code` attribute does not exist). Use `code_obj.code_lines[i]` instead.
   - ❌ Using `CENTER` as a constant — **it does not exist in Manim**. Use `ORIGIN` for the center point. To overlay text on a shape, do NOT use `.arrange(CENTER)`; instead create them separately and call `text.move_to(shape.get_center())`.

8) **Flow (Minimal & Clear)**
   - Brief title (2–3s), then step-by-step reveal matching the order of `actions`.
   - Insert `self.wait(1)` **at minimum** between logical steps if the plan’s duration is missing.
   - End with `self.wait(2)` holding the final state.
   - **CLEANUP RULE**: When transitioning between major logical sections within a scene,
     FadeOut elements that are no longer relevant before introducing new ones.
     Example: after finishing a derivation, FadeOut intermediate steps before showing the final result.

9) **Graceful Downgrades for Heavy Visuals**
   - Large “grids” or thousands of dots: substitute a labeled `Rectangle` or a **small** `VGroup` (≤ 20 dots) plus a label like `"10,000 cases (schematic)"`.
   - Complex “tree diagrams”: approximate with `Line` + `Text` labels; keep branches ≤ 4 elements.

10) **Robustness**
   - Ensure each mobject is **created/added** before transforming/indicating it.
   - Do not reference objects after `FadeOut` unless re-created.
   - Only allowed animations/mobjects; **no** camera moves, seeds, randomness, external assets, or experimental APIs.
   - Make sure that your code match with the concept we are tring to visualize.
   - The visualization must be correct and reflect the topic being shown since this will affect the learning outcome.
   - Avoid using uncommon parameters and methods in your code.

11) **Consistency with the Planner’s Example**
   - **Do not change** numeric values or scenario details present in this scene plan (this preserves cross-scene example consistency).
   - Keep variable names identical to `"target"` (post-sanitization) across all actions in this scene.

12) **DO NOT INCLUDE BACKTICKS (``) IN YOUR CODE, EVER!**

13) **Voiceover hard constraints**
   - `class {class_name}(VoiceoverScene):`
   - `construct` must call `self.set_speech_service(...)` before first `self.voiceover(...)`.
   - At least one `with self.voiceover(...) as tracker:` block is required.
   - Narration length target: <= 25 Chinese chars or <= 18 English words per segment.
   - **Pronunciation-friendly narration** — the string passed to `self.voiceover(text=...)`
     goes straight to a neural TTS engine. Write it as you would SPEAK it, never as
     rendered math. Concretely:
     * Do NOT put LaTeX/ASCII formulas into the narration string. Keep formulas in
       `MathTex(...)` on screen; describe them in prose in the narration.
     * Forbidden in narration text (use the spoken form instead):
       `^`, `_`, `O(...)`, `Θ(...)`, `Ω(...)`, `>=`, `<=`, `!=`, `==`,
       `->`, `=>`, `√`, `∑`, `∏`, `∞`, `×`, `÷`, raw greek letters (α β γ …).
     * Examples (Chinese):
       - BAD : `text="时间复杂度是 O(N^2)，空间 O(1)"`
       - GOOD: `text="时间复杂度是N平方级别，空间是常数级别"`
       - BAD : `text="当 i >= n/2 时停止"`
       - GOOD: `text="当i大于等于n的一半时停止"`
       - BAD : `text="a_i 与 a_{{i+1}} 比较"`
       - GOOD: `text="比较第i个元素与第i加1个元素"`
     * Examples (English):
       - BAD : `text="Time complexity is O(N^2)"`
       - GOOD: `text="Time complexity is N squared"`
     * The on-screen `Text(...)` / `MathTex(...)` may still use the formal notation;
       this rule only applies to the narration string given to `voiceover`.
     * HARD RULE (Chinese narration): NEVER insert a space between Chinese characters
       and adjacent ASCII letters/digits/symbols (including variables like `i`, `n`, `N`,
       labels like `A`/`B`/`D`, and numbers like `2`/`10`). Example: write
       "移动到节点D的左子树" NOT "移动到节点 D 的左子树"; write "空间复杂度是N" NOT
       "空间复杂度是 N". SRT subtitles will otherwise render with jarring gaps.

14) **Linter Annotations (use sparingly)**
   The generated code will be statically checked by `manim-lint`. You MAY insert comment
   annotations to silence KNOWN-INTENTIONAL diagnostics. Never use these to hide real bugs.

   Supported syntax:
     `# manim-lint: ignore` — ignore all diagnostics on this line
     `# manim-lint: ignore[ML101]` — ignore a specific rule
     `# manim-lint: ignore[ML101,ML301]` — multiple rules
     `# manim-lint: ignore-overlap(obj_a, obj_b)` — suppress overlap between two mobjects
     `# manim-lint: ignore-next-line` — apply to the next line
     `# manim-lint: ignore-next-line[ML301]` — next-line + specific rule

   **When to use (allowed)**:
   - You INTENTIONALLY overlay a label on a shape:
       `label.move_to(box.get_center())  # manim-lint: ignore-overlap(label, box)`
   - You wrap a group inside a bounding rectangle for emphasis:
       `self.play(Create(frame))  # manim-lint: ignore-overlap(frame, dots_group)`
   - A deliberate SurroundingRectangle highlight on another mobject.

   **When NOT to use (forbidden)**:
   - Do NOT silence ML1xx (invalid kwarg) diagnostics — fix the call site instead.
   - Do NOT blanket-ignore a whole scene with repeated `# manim-lint: ignore`.
   - Do NOT add annotations for overlaps you did not explicitly intend — leave them; the pipeline may ask for a layout fix.

**GUIDELINE**:
- Skim through the scence and think of a draft version.
- Make sure to iterate through the code to make sure all the codes are correct.
- You have to make sure that all elements are created and placed correctly on the scene.

============================================================
OUTPUT FORMAT (MANDATORY)
============================================================
<manim>
from manim import *
import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
{voiceover_imports}
# Simple 2D Scene (compatible with whichever Manim CE version is installed)

class {class_name}(VoiceoverScene):
    def construct(self):
        {tts_setup_snippet}
        # Example:
        # title = Text("Your Title", font_size=48).to_edge(UP)
        # with self.voiceover(text="Introduce the key idea clearly.") as tracker:
        #     self.play(Write(title), run_time=tracker.duration)
</manim>
"""

    RENDER_FIX_PROMPT = """You are fixing a Manim scene that CRASHED at render time.
The Manim subprocess executed the scene and exited with an error; your job is to
repair ONLY what the stack trace identifies, keeping the scene's behavior intact.

ORIGINAL SCENE PLAN (for context):
{scene_plan}

FAILING CODE (class name MUST stay {class_name}):
<manim>
{current_code}
</manim>

RUNTIME ERROR (stderr + stdout tail from the Manim subprocess):
```
{error_output}
```

RULES:
- Return the FULL corrected file inside <manim>...</manim> tags. No commentary.
- Preserve the class name ({class_name}) and the VoiceoverScene structure:
  * must inherit from VoiceoverScene
  * must keep `self.set_speech_service(...)` call before any voiceover usage
  * keep the existing `with self.voiceover(...) as tracker:` blocks
  * keep all `from manim_voiceover ...` / `from manim ...` imports
- Fix ONLY what the traceback points to; do not redesign the animation.
- Common runtime bugs and how to repair them:
  * `TypeError: Cannot compare ManimColor with str` → never compare `mobject.color == "RED"`;
    compare against a Manim color constant (e.g. `ManimColor(RED) == mobject.color`) or,
    preferably, track state yourself with a plain Python variable/list instead of
    reading back `.color` / `.fill_color`.
  * `AttributeError: 'XYZ' object has no attribute 'foo'` → replace with the real
    attribute/method for the current Manim version (e.g. use `.animate.set_fill(...)`
    instead of a non-existent setter).
  * `TypeError: got an unexpected keyword argument 'xxx'` → drop or rename the kwarg.
  * `ValueError: ...` from color / coordinate args → pass a proper Manim color
    constant or `np.array([x, y, 0])`.
  * `IndexError` / `KeyError` on arrays → guard index arithmetic inside loops.
  * `KeyError` on `edge_mobjs[(u, v)]` in tree scenes → never index `edge_mobjs`
    directly. Use base helper `self.get_edge_mobj(u, v)` and guard `None` before
    animating the edge.
  * `TypeError: Code.__init__() got an unexpected keyword argument 'code'` →
    Manim CE v0.19 does NOT accept `code=`; replace every `Code(code=...)`
    with `Code(code_string=...)`. Also rewrite any read like `obj.code[i]`
    to `obj.code_lines[i]` (`code` attribute does not exist). The only valid
    kwargs are `code_string` / `code_file` / `language` / `tab_width` /
    `background` / `formatter_style` / `add_line_numbers`.
- Do NOT introduce new external libraries. Do NOT remove voiceover blocks.
- Keep the code runnable as a single self-contained file.
"""

    LINT_FIX_PROMPT = """You are fixing a Manim scene that failed static checks from `manim-lint`.
The lint runs against whichever Manim version is installed in the current environment,
so trust the diagnostics over any prior knowledge about a specific Manim release.

ORIGINAL SCENE PLAN:
{scene_plan}

CURRENT CODE (CLASS NAME MUST STAY {class_name}):
<manim>
{current_code}
</manim>

LINT DIAGNOSTICS (errors that MUST be resolved):
{diagnostics}

RULES:
- Fix ONLY the reported issues; do not redesign the scene.
- Preserve class name, overall structure, and existing variable names used as `target`s.
- Keep VoiceoverScene structure valid:
  * class must inherit from VoiceoverScene
  * must keep self.set_speech_service(...) in construct before voiceover calls
  * keep with self.voiceover(... ) as tracker blocks executable
- Common fixes:
  * ML1xx (invalid kwarg / bad signature) → remove or rename the argument to match the
    API reported by the linter. Never silence ML1xx with an ignore comment.
  * ML3xx (overlap / occlusion):
      - If the overlap is a BUG: reposition with `.next_to(..., buff>=0.5)`, shift, or
        FadeOut the earlier element before introducing the new one.
      - If the overlap is DELIBERATE (e.g. text centered on a shape), add a narrow
        suppression comment on that specific line:
            # manim-lint: ignore-overlap(<obj_a>, <obj_b>)
        Use this only for the exact mobject pair involved.
- Output the full corrected file inside <manim>...</manim> tags. No commentary.
"""

    # ==================== SKILL 模板系统方法 ====================

    # ---------- 多家族配置表 ----------
    # 每个家族独立描述：skill 目录、基类、模板文件名、关键词、shared_data 形态与默认值
    SKILL_FAMILIES: Dict[str, Dict[str, Any]] = {
        "sorting": {
            "skill_dir": ".agent/skills/sorting_algorithms/examples",
            "base_file": "sorting_base.py",
            "base_class_name": "SortingBase",
            "template_files": [
                "insertion_sort", "binary_insertion_sort", "shell_sort",
                "bubble_sort", "quick_sort", "selection_sort",
                "heap_sort", "merge_sort", "radix_sort",
            ],
            "shared_data_kind": "array",
            "shared_var_name": "SHARED_DATA",
            "default_shared_data": [5, 3, 8, 1, 4],
            "first_call_example": "self.show_array({var}, title=...)",
            "keywords": {
                # 直接插入排序
                "insertion sort": "insertion_sort",
                "insertion_sort": "insertion_sort",
                "插入排序": "insertion_sort",
                "直接插入排序": "insertion_sort",
                "直接插入": "insertion_sort",
                # 折半插入排序
                "binary insertion sort": "binary_insertion_sort",
                "binary_insertion_sort": "binary_insertion_sort",
                "折半插入排序": "binary_insertion_sort",
                "折半插入": "binary_insertion_sort",
                "二分插入排序": "binary_insertion_sort",
                # 希尔排序
                "shell sort": "shell_sort",
                "shell_sort": "shell_sort",
                "希尔排序": "shell_sort",
                "缩小增量排序": "shell_sort",
                # 冒泡排序
                "bubble sort": "bubble_sort",
                "bubble_sort": "bubble_sort",
                "冒泡排序": "bubble_sort",
                "冒泡": "bubble_sort",
                # 快速排序
                "quick sort": "quick_sort",
                "quick_sort": "quick_sort",
                "快速排序": "quick_sort",
                "快排": "quick_sort",
                # 简单选择排序
                "selection sort": "selection_sort",
                "selection_sort": "selection_sort",
                "选择排序": "selection_sort",
                "简单选择排序": "selection_sort",
                # 堆排序
                "heap sort": "heap_sort",
                "heap_sort": "heap_sort",
                "堆排序": "heap_sort",
                # 归并排序
                "merge sort": "merge_sort",
                "merge_sort": "merge_sort",
                "归并排序": "merge_sort",
                "合并排序": "merge_sort",
                # 基数排序
                "radix sort": "radix_sort",
                "radix_sort": "radix_sort",
                "基数排序": "radix_sort",
            },
        },
        "linked_list": {
            "skill_dir": ".agent/skills/linked_list_algorithms/examples",
            "base_file": "linked_list_base.py",
            "base_class_name": "LinkedListBase",
            "template_files": [
                "init_linked_list", "insert_node", "delete_node", "get_value", "find_value"
            ],
            "shared_data_kind": "array",
            "shared_var_name": "SHARED_DATA",
            "default_shared_data": [10, 20, 30, 40],
            "first_call_example": "self.setup_list_data({var})",
            "keywords": {
                "init linked list": "init_linked_list",
                "init_linked_list": "init_linked_list",
                "初始化单链表": "init_linked_list",
                "单链表初始化": "init_linked_list",
                "insert node": "insert_node",
                "insert_node": "insert_node",
                "单链表插入": "insert_node",
                "插入节点": "insert_node",
                "单链表插入操作": "insert_node",
                "delete node": "delete_node",
                "delete_node": "delete_node",
                "单链表删除": "delete_node",
                "删除节点": "delete_node",
                "单链表删除操作": "delete_node",
                "get value": "get_value",
                "get_value": "get_value",
                "单链表按位查找": "get_value",
                "按位查找": "get_value",
                "find value": "find_value",
                "find_value": "find_value",
                "单链表按值查找": "find_value",
                "按值查找": "find_value",
            },
        },
        "seq_list": {
            "skill_dir": ".agent/skills/seq_list_algorithms/examples",
            "base_file": "seq_list_base.py",
            "base_class_name": "SeqListBase",
            "template_files": [
                "init_seq_list", "get_value", "find_value", "insert_element", "delete_element"
            ],
            "shared_data_kind": "array",
            "shared_var_name": "SHARED_DATA",
            "default_shared_data": [10, 20, 30, 40],
            "first_call_example": "self.setup_list_data({var})",
            "keywords": {
                "init seq list": "init_seq_list",
                "init_seq_list": "init_seq_list",
                "初始化顺序表": "init_seq_list",
                "顺序表初始化": "init_seq_list",
                "get value seq": "get_value",
                "get_value_seq": "get_value",
                "顺序表取值": "get_value",
                "顺序表按位查找": "get_value",
                "find value seq": "find_value",
                "find_value_seq": "find_value",
                "顺序表查找": "find_value",
                "顺序表按值查找": "find_value",
                "insert element seq": "insert_element",
                "insert_element_seq": "insert_element",
                "顺序表插入": "insert_element",
                "顺序表插入操作": "insert_element",
                "delete element seq": "delete_element",
                "delete_element_seq": "delete_element",
                "顺序表删除": "delete_element",
                "顺序表删除操作": "delete_element",
            },
        },
        "stack": {
            "skill_dir": ".agent/skills/stack_algorithms/examples",
            "base_file": "stack_base.py",
            "base_class_name": "StackBase",
            "template_files": [
                "init_stack", "push_stack", "pop_stack", "get_top"
            ],
            "shared_data_kind": "array",
            "shared_var_name": "SHARED_DATA",
            "default_shared_data": [10, 20, 30],
            "first_call_example": "self.setup_stack_data({var}, maxsize=max(len({var})+2, 6))",
            "keywords": {
                "init stack": "init_stack",
                "init_stack": "init_stack",
                "初始化栈": "init_stack",
                "栈初始化": "init_stack",
                "顺序栈初始化": "init_stack",
                "构造空栈": "init_stack",
                "push stack": "push_stack",
                "push_stack": "push_stack",
                "栈的入栈": "push_stack",
                "入栈操作": "push_stack",
                "入栈": "push_stack",
                "压栈": "push_stack",
                "顺序栈入栈": "push_stack",
                "pop stack": "pop_stack",
                "pop_stack": "pop_stack",
                "栈的出栈": "pop_stack",
                "出栈操作": "pop_stack",
                "出栈": "pop_stack",
                "弹栈": "pop_stack",
                "顺序栈出栈": "pop_stack",
                "get top": "get_top",
                "get_top": "get_top",
                "gettop": "get_top",
                "取栈顶元素": "get_top",
                "取栈顶": "get_top",
                "栈顶元素": "get_top",
                "读栈顶": "get_top",
                "peek stack": "get_top",
                "peek_stack": "get_top",
            },
        },
        "tree": {
            "skill_dir": ".agent/skills/tree_algorithms/examples",
            "base_file": "tree_base.py",
            "base_class_name": "TreeBase",
            "template_files": [
                "inorder_recursive", "inorder_non_recursive", "preorder_build_tree",
                "copy_tree", "calculate_depth", "count_nodes", "inorder_threading"
            ],
            "shared_data_kind": "dict",
            "shared_var_name": "SHARED_DATA",
            "default_shared_data": {
                'v': 'A',
                'l': {'v': 'B', 'l': {'v': 'D'}, 'r': {'v': 'E'}},
                'r': {'v': 'C', 'r': {'v': 'F'}}
            },
            "first_call_example": "self.setup_default_tree({var})",
            "keywords": {
                "inorder recursive": "inorder_recursive",
                "中序遍历递归": "inorder_recursive",
                "中序遍历的递归算法": "inorder_recursive",
                "inorder non recursive": "inorder_non_recursive",
                "中序遍历非递归": "inorder_non_recursive",
                "中序遍历的非递归算法": "inorder_non_recursive",
                "preorder build tree": "preorder_build_tree",
                "先序建树": "preorder_build_tree",
                "先序遍历序列建立二叉链表": "preorder_build_tree",
                "copy tree": "copy_tree",
                "复制二叉树": "copy_tree",
                "calculate depth": "calculate_depth",
                "计算二叉树的深度": "calculate_depth",
                "count nodes": "count_nodes",
                "统计二叉树结点个数": "count_nodes",
                "统计二叉树结点": "count_nodes",
                "inorder threading": "inorder_threading",
                "二叉树线索化": "inorder_threading",
                "中序线索化": "inorder_threading",
            },
        },
    }

    # 排序算法关键词映射表：{关键词: 模板文件名（不含.py后缀）}
    # 保留为类属性以兼容外部引用，内容与 SKILL_FAMILIES['sorting']['keywords'] 等价。
    SORTING_KEYWORDS = {
        # 直接插入排序
        "insertion sort": "insertion_sort",      # 英文（空格）
        "insertion_sort": "insertion_sort",
        "插入排序": "insertion_sort",
        "直接插入排序": "insertion_sort",
        "直接插入": "insertion_sort",
        # 折半插入排序
        "binary insertion sort": "binary_insertion_sort",  # 英文（空格）
        "binary_insertion_sort": "binary_insertion_sort",
        "折半插入排序": "binary_insertion_sort",
        "折半插入": "binary_insertion_sort",
        "二分插入排序": "binary_insertion_sort",
        # 希尔排序
        "shell sort": "shell_sort",              # 英文（空格）
        "shell_sort": "shell_sort",
        "希尔排序": "shell_sort",
        "缩小增量排序": "shell_sort",
        # 冒泡排序
        "bubble sort": "bubble_sort",            # 英文（空格）
        "bubble_sort": "bubble_sort",
        "冒泡排序": "bubble_sort",
        "冒泡": "bubble_sort",
        # 快速排序
        "quick sort": "quick_sort",              # 英文（空格）
        "quick_sort": "quick_sort",
        "快速排序": "quick_sort",
        "快排": "quick_sort",
        # 简单选择排序
        "selection sort": "selection_sort",      # 英文（空格）
        "selection_sort": "selection_sort",
        "选择排序": "selection_sort",
        "简单选择排序": "selection_sort",
        # 堆排序
        "heap sort": "heap_sort",                # 英文（空格）
        "heap_sort": "heap_sort",
        "堆排序": "heap_sort",
        # 归并排序
        "merge sort": "merge_sort",              # 英文（空格）
        "merge_sort": "merge_sort",
        "归并排序": "merge_sort",
        "合并排序": "merge_sort",
        # 基数排序
        "radix sort": "radix_sort",              # 英文（空格）
        "radix_sort": "radix_sort",
        "基数排序": "radix_sort",
    }

    def _load_skill_templates(self):
        """加载所有 SKILL 家族（sorting / tree / graph ...）的模板文件。"""
        project_root = Path(__file__).parent.parent

        for family, meta in self.SKILL_FAMILIES.items():
            skill_dir = project_root / meta["skill_dir"]
            entry: Dict[str, Any] = {
                "templates": {},
                "base_code": None,
                "base_class_name": meta["base_class_name"],
            }
            if not skill_dir.exists():
                self.logger.info(f"未找到 {family} SKILL 目录：{skill_dir}，跳过")
                self.skill_registry[family] = entry
                continue

            base_file = skill_dir / meta["base_file"]
            if base_file.exists():
                entry["base_code"] = base_file.read_text(encoding="utf-8")
                self.logger.info(f"已加载 {family} 公共基类 {meta['base_file']}")

            for name in meta["template_files"]:
                filepath = skill_dir / f"{name}.py"
                if filepath.exists():
                    entry["templates"][name] = filepath.read_text(encoding="utf-8")
                    self.logger.debug(f"已加载 {family} 模板: {name}.py")

            self.skill_registry[family] = entry
            self.logger.info(
                f"{family} SKILL 模板加载完成：共 {len(entry['templates'])} 个模板"
            )

        # 排序家族别名，保持向后兼容
        sorting_entry = self.skill_registry.get("sorting", {})
        self.skill_templates = sorting_entry.get("templates", {}) or {}
        self.skill_base_code = sorting_entry.get("base_code")

    # ------------------------------------------------------------------
    # 高特异性关键词 → 指定 (family, template) 的硬性短路规则。
    # 放在 _match_any_skill_template 的最前，避免像 "复制二叉树" 这种
    # 复合概念被子串 "二叉树" 误导到遍历模板。
    # ------------------------------------------------------------------
    _SKILL_PRIORITY_OVERRIDES: List[tuple] = [
        # 复制/拷贝/克隆二叉树 → copy_binary_tree
        (
            (
                "复制二叉树", "拷贝二叉树", "复制树", "拷贝树",
                "copy binary tree", "copy tree",
                "clone tree", "clone binary tree",
                "duplicate tree", "duplicate binary tree",
            ),
            ("tree", "copy_binary_tree"),
        ),
    ]

    def _match_any_skill_template(self, concept_text: str) -> tuple:
        """跨所有家族匹配 SKILL 模板。

        Returns:
            (family, template_code, template_name) 或 (None, None, None)
        """
        if not concept_text:
            return None, None, None
        concept_lower = concept_text.lower()

        # 优先级 0：高特异性关键词一票通过（如 "复制二叉树" 必须贴 copy_binary_tree，
        # 不能被子串 "二叉树" 误路由到 preorder/inorder 遍历模板）
        for kw_list, (family, tmpl) in self._SKILL_PRIORITY_OVERRIDES:
            for kw in kw_list:
                if kw.lower() in concept_lower:
                    entry = self.skill_registry.get(family, {})
                    code = (entry.get("templates") or {}).get(tmpl)
                    if code:
                        self.logger.info(
                            f"SKILL 优先级短路：关键词'{kw}' → {family}/{tmpl}"
                        )
                        return family, code, tmpl

        for family, meta in self.SKILL_FAMILIES.items():
            entry = self.skill_registry.get(family, {})
            templates = entry.get("templates") or {}
            if not templates:
                continue
            for keyword, template_name in meta["keywords"].items():
                if keyword.lower() in concept_lower:
                    template_code = templates.get(template_name)
                    if template_code:
                        self.logger.info(
                            f"SKILL 匹配成功：family={family} 关键词'{keyword}' → 模板'{template_name}'"
                        )
                        return family, template_code, template_name
        return None, None, None

    def _match_sorting_template(self, concept_text: str) -> tuple:
        """兼容旧调用：仅在 sorting 家族匹配，返回 (template_code, template_name)。"""
        concept_lower = (concept_text or "").lower()
        sorting_meta = self.SKILL_FAMILIES.get("sorting", {})
        sorting_entry = self.skill_registry.get("sorting", {})
        templates = sorting_entry.get("templates") or {}
        for keyword, template_name in sorting_meta.get("keywords", {}).items():
            if keyword.lower() in concept_lower:
                template_code = templates.get(template_name)
                if template_code:
                    self.logger.info(
                        f"SKILL 匹配成功：关键词'{keyword}' → 模板'{template_name}'"
                    )
                    return template_code, template_name
        return None, None

    # -------- Visual Contract helpers (用于跨场景风格统一) --------

    def _extract_template_default_array(self, template_code: str) -> Optional[List[int]]:
        """从 SKILL 模板代码中提取默认数据数组（如 `data = [5, 3, 8, 1, 4]`）。"""
        if not template_code:
            return None
        match = re.search(r'\bdata\s*=\s*\[([\d,\s\-]+)\]', template_code)
        if not match:
            return None
        try:
            items = [int(x.strip()) for x in match.group(1).split(',') if x.strip()]
            return items or None
        except ValueError:
            return None

    def _extract_template_default_tree(self, template_code: str) -> Optional[str]:
        """从 tree SKILL 模板中提取默认先序字符串（`SHARED_TREE_PREORDER = "..."`）。

        与 sorting 的 `_extract_template_default_array` 对齐，提供第二层兜底；
        当 scene plan 未给出 tree 参数时，优先使用模板自身声明的字面量，再回退到
        SKILL_FAMILIES 里的硬编码默认值，避免模板改串后契约漂移。
        """
        if not template_code:
            return None
        pattern = re.compile(
            r'SHARED_TREE_PREORDER\s*=\s*([\'"])([^\'"\r\n]+)\1'
        )
        match = pattern.search(template_code)
        if not match:
            return None
        value = match.group(2).strip()
        return value or None

    def _extract_template_default_graph(self, template_code: str) -> Optional[Dict[str, Any]]:
        """从 graph SKILL 模板中提取默认邻接表（`SHARED_GRAPH = {...}`）。

        采用 `ast.literal_eval` 解析以保证安全；若模板未声明或声明不可字面求值，
        返回 None 让调用方回退到 `SKILL_FAMILIES["graph"]["default_shared_data"]`。
        """
        if not template_code:
            return None
        import ast as _ast
        try:
            tree = _ast.parse(template_code)
        except SyntaxError:
            return None
        for node in _ast.walk(tree):
            if isinstance(node, _ast.Assign):
                for target in node.targets:
                    if isinstance(target, _ast.Name) and target.id == "SHARED_GRAPH":
                        try:
                            value = _ast.literal_eval(node.value)
                        except (ValueError, SyntaxError):
                            return None
                        if (
                            isinstance(value, dict)
                            and isinstance(value.get("vertices"), list)
                            and isinstance(value.get("edges"), list)
                        ):
                            return value
        return None

    def _extract_shared_data_from_plans(self, scene_plans: List[ScenePlan]) -> Optional[List[int]]:
        """尝试从场景计划的参数中提取数据数组（若 planner 指定了具体数组）。

        寻找形如 parameters = {"array": [...], "data": [...], "values": [...]} 的字段。
        """
        candidate_keys = (
            "array", "data", "values", "initial_array", "initial_data",
            "linked_list", "linked_list_data", "list_values", "node_values",
        )
        candidates: List[List[int]] = []
        for plan in scene_plans:
            for action in plan.actions:
                params = action.parameters or {}
                for key in candidate_keys:
                    val = params.get(key)
                    parsed = self._coerce_numeric_list(val)
                    if parsed:
                        candidates.append(parsed)
        return self._choose_consistent_numeric_list(candidates, source_name="scene plans")

    @staticmethod
    def _coerce_numeric_list(value: Any) -> Optional[List[int]]:
        """Return a simple int list for planner/template payloads, otherwise None."""
        if not isinstance(value, list) or not value:
            return None
        if not all(isinstance(x, (int, float)) for x in value):
            return None
        try:
            return [int(x) for x in value]
        except (TypeError, ValueError):
            return None

    def _choose_consistent_numeric_list(
        self,
        candidates: List[List[int]],
        source_name: str,
    ) -> Optional[List[int]]:
        """Pick one numeric list, warning when planner supplied conflicting lists."""
        if not candidates:
            return None
        first = candidates[0]
        conflicts = [c for c in candidates[1:] if c != first]
        if conflicts:
            self.logger.warning(
                "Visual Contract: conflicting data arrays found in %s; using first %s, ignored %s",
                source_name,
                first,
                conflicts[:3],
            )
        return first

    def _latest_canonical_example(self) -> Dict[str, Any]:
        """Return the latest top-level planner canonical example, if present."""
        response = self._latest_planning_response_json or {}
        canonical = response.get("canonical_example") or response.get("visual_contract") or {}
        return canonical if isinstance(canonical, dict) else {}

    def _extract_canonical_data(self) -> Optional[List[int]]:
        """Extract globally declared example data from planner response."""
        canonical = self._latest_canonical_example()
        candidate_keys = (
            "data", "array", "values", "initial_data", "initial_array",
            "linked_list", "linked_list_data", "list_values", "node_values",
        )
        for key in candidate_keys:
            parsed = self._coerce_numeric_list(canonical.get(key))
            if parsed:
                return parsed
        return None

    def _extract_int_from_payloads(self, keys: tuple[str, ...], scene_plans: List[ScenePlan]) -> Optional[int]:
        """Extract a shared integer from canonical_example first, then scene action params."""
        canonical = self._latest_canonical_example()
        for key in keys:
            val = canonical.get(key)
            if isinstance(val, (int, float)):
                return int(val)
            if isinstance(val, str) and val.strip().isdigit():
                return int(val.strip())
        for plan in scene_plans:
            for action in plan.actions:
                params = action.parameters or {}
                for key in keys:
                    val = params.get(key)
                    if isinstance(val, (int, float)):
                        return int(val)
                    if isinstance(val, str) and val.strip().isdigit():
                        return int(val.strip())
        return None

    def _build_linked_list_shared_constants(
        self,
        shared_data: Any,
        scene_plans: List[ScenePlan],
    ) -> Dict[str, Any]:
        """Build extra constants that keep linked-list deletion scenes aligned."""
        constants: Dict[str, Any] = {}
        delete_index = self._extract_int_from_payloads(
            ("delete_index", "deletion_index", "delete_position", "position", "target_index", "i"),
            scene_plans,
        )
        delete_value = self._extract_int_from_payloads(
            ("delete_value", "deleted_value", "target_value", "value"),
            scene_plans,
        )
        if delete_index is not None:
            constants["SHARED_DELETE_INDEX"] = delete_index
        if delete_value is None and isinstance(shared_data, list) and delete_index is not None:
            # Linked-list templates use 1-based data-node positions because nodes[0] is the head node.
            data_pos = delete_index - 1
            if 0 <= data_pos < len(shared_data):
                delete_value = shared_data[data_pos]
        if delete_value is not None:
            constants["SHARED_DELETE_VALUE"] = delete_value
        canonical = self._latest_canonical_example()
        pointer_names = canonical.get("pointer_names")
        if isinstance(pointer_names, list) and pointer_names:
            constants["SHARED_POINTER_NAMES"] = [str(x) for x in pointer_names]
        else:
            constants["SHARED_POINTER_NAMES"] = ["L", "p", "q"]
        return constants

    def _extract_shared_tree_from_plans(self, scene_plans: List[ScenePlan]) -> Optional[str]:
        """从场景计划参数里寻找树的先序字符串（如 `tree`/`preorder`）。"""
        candidate_keys = ("tree", "preorder", "preorder_string", "tree_preorder")
        for plan in scene_plans:
            for action in plan.actions:
                params = action.parameters or {}
                for key in candidate_keys:
                    val = params.get(key)
                    if isinstance(val, str) and val.strip():
                        return val.strip()
        return None

    # 匹配 "先序[:：] A B # # C # #" 这种人类书写形式：
    #   1) 先锚定关键字（先序/前序/preorder，可带"序列 / 遍历序列 / sequence / string"后缀）
    #   2) 允许至多 8 个非字母/数字/# 的"分隔噪声"（括号、冒号、空格、"为/是/的"等）
    #   3) 贪心抓一段由 [A-Za-z0-9#] 与空白/逗号/顿号组成的连续先序片段
    _TREE_PREORDER_TEXT_RE = re.compile(
        r'(?:先序(?:序列|遍历序列)?|前序(?:序列|遍历序列)?|preorder(?:\s+(?:sequence|string))?)'
        r'[^A-Za-z0-9#\n]{0,8}?'
        r'([A-Za-z0-9#](?:[\s,;，、]*[A-Za-z0-9#]){2,})',
        re.IGNORECASE,
    )

    def _extract_shared_tree_from_text(self, *texts: str) -> Optional[str]:
        """从自由文本里抓形如 "先序: A B # # C # #" 的显式输入串。

        匹配到后把空白/逗号/分号全部压缩掉，并裁掉末尾多余字符；
        返回紧凑先序串（例："A B # # C # #" → "AB##C##"）。
        若没有任何文本命中，返回 None 供调用者走下一层兜底。
        """
        for txt in texts:
            if not txt:
                continue
            m = self._TREE_PREORDER_TEXT_RE.search(txt)
            if not m:
                continue
            raw = m.group(1)
            compact = re.sub(r'[\s,;，、:：]+', '', raw)
            # 至少含一个 '#' 或长度 ≥ 3 才算有效（避免误伤 "preorder A" 这类噪声）
            if not compact or len(compact) < 3:
                continue
            if not all(c.isalnum() or c == '#' for c in compact):
                continue
            return compact
        return None

    def _extract_shared_graph_from_plans(self, scene_plans: List[ScenePlan]) -> Optional[Dict[str, Any]]:
        """从场景计划参数里寻找图（邻接表）描述。"""
        candidate_keys = ("graph", "graph_adjlist", "adjlist", "weighted_graph")
        for plan in scene_plans:
            for action in plan.actions:
                params = action.parameters or {}
                for key in candidate_keys:
                    val = params.get(key)
                    if (
                        isinstance(val, dict)
                        and isinstance(val.get("vertices"), list)
                        and isinstance(val.get("edges"), list)
                    ):
                        return val
        return None

    def _transform_base_class_for_voiceover(
        self,
        base_code: str,
        base_class_name: str = "SortingBase",
    ) -> str:
        """把 `class <Base>(Scene)` 改写为 `class <Base>(VoiceoverScene)`，并确保 import 存在。

        参数化 base_class_name 以支持多家族（SortingBase / BinaryTreeBase / GraphBase）。
        """
        if not base_code:
            return base_code

        transformed = re.sub(
            rf'class\s+{re.escape(base_class_name)}\s*\(\s*Scene\s*\)\s*:',
            f'class {base_class_name}(VoiceoverScene):',
            base_code,
        )
        if 'from manim_voiceover import VoiceoverScene' not in transformed:
            lines = transformed.splitlines()
            insert_at = 0
            for idx, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('from manim') or stripped == 'from manim import *':
                    insert_at = idx + 1
            lines.insert(insert_at, 'from manim_voiceover import VoiceoverScene')
            transformed = "\n".join(lines)
        return transformed

    def _build_global_visual_contract(
        self,
        scene_plans: List[ScenePlan],
        concept_analysis: Optional[ConceptAnalysis] = None,
    ) -> Optional[Dict[str, Any]]:
        """为一整组场景计划构建共享的视觉契约（Visual Contract）。

        - 全局在所有家族（sorting / tree / graph）里匹配一次 SKILL 模板
        - 锁定唯一的共享数据（数组 / 先序字符串 / 邻接表）
        - 将对应基类改写为 VoiceoverScene 子类

        Returns:
            dict（含 family / base_class_name / shared_data_kind 等），或 None（未匹配）。
        """
        if not self.skill_registry:
            return None

        match_parts: List[str] = []
        if concept_analysis is not None:
            match_parts.append(concept_analysis.main_concept)
            for sc in concept_analysis.sub_concepts:
                match_parts.append(sc.title)
                match_parts.append(sc.description)
        for plan in scene_plans:
            match_parts.append(plan.title)
            match_parts.append(plan.description)
        aggregated_text = " ".join(p for p in match_parts if p)

        family, template_code, template_name = self._match_any_skill_template(aggregated_text)
        if not template_code or not family:
            return None

        meta = self.SKILL_FAMILIES[family]
        entry = self.skill_registry[family]
        base_code = entry.get("base_code") or ""
        if not base_code:
            self.logger.warning(
                f"匹配到家族 {family} 的模板 {template_name}，但基类代码缺失，跳过 Visual Contract"
            )
            return None

        kind = meta["shared_data_kind"]
        shared_data: Any
        shared_source: str = "default"
        if kind == "array":
            from_canonical = self._extract_canonical_data()
            if from_canonical:
                shared_data, shared_source = from_canonical, "canonical_example"
            else:
                from_plan = self._extract_shared_data_from_plans(scene_plans)
                if from_plan:
                    shared_data, shared_source = from_plan, "plan"
                else:
                    from_template = self._extract_template_default_array(template_code)
                    if from_template:
                        shared_data, shared_source = from_template, "template"
                    else:
                        shared_data = meta["default_shared_data"]
        elif kind == "tree_preorder":
            from_plan = self._extract_shared_tree_from_plans(scene_plans)
            if from_plan:
                shared_data, shared_source = from_plan, "plan"
            else:
                # 第二层兜底：扫描 ConceptAnalysis 与 ScenePlan 的自由文本，
                # 抽取用户在知识文档里写的 "先序: A B # # C # #" 这种显式输入。
                text_candidates: List[str] = []
                if concept_analysis is not None:
                    text_candidates.append(concept_analysis.main_concept or "")
                    for sc in concept_analysis.sub_concepts:
                        text_candidates.append(sc.description or "")
                        text_candidates.extend(sc.key_points or [])
                for plan in scene_plans:
                    text_candidates.append(plan.title or "")
                    text_candidates.append(plan.description or "")
                    for action in plan.actions:
                        text_candidates.append(action.description or "")
                from_text = self._extract_shared_tree_from_text(*text_candidates)
                if from_text:
                    shared_data, shared_source = from_text, "concept_text"
                else:
                    from_template = self._extract_template_default_tree(template_code)
                    if from_template:
                        shared_data, shared_source = from_template, "template"
                    else:
                        shared_data = meta["default_shared_data"]
        elif kind == "graph_adjlist":
            from_plan = self._extract_shared_graph_from_plans(scene_plans)
            if from_plan:
                shared_data, shared_source = from_plan, "plan"
            else:
                from_template = self._extract_template_default_graph(template_code)
                if from_template:
                    shared_data, shared_source = from_template, "template"
                else:
                    shared_data = meta["default_shared_data"]
        else:
            shared_data = meta["default_shared_data"]

        base_class_name = meta["base_class_name"]
        base_class_code = self._transform_base_class_for_voiceover(base_code, base_class_name)
        shared_constants: Dict[str, Any] = {}
        if family in {"linked_list", "seq_list"}:
            shared_constants = self._build_linked_list_shared_constants(shared_data, scene_plans)

        contract = {
            "family": family,
            "template_code": template_code,
            "template_name": template_name,
            "base_class_code": base_class_code,
            "base_class_name": base_class_name,
            "shared_data": shared_data,
            "shared_data_kind": kind,
            "shared_var_name": meta["shared_var_name"],
            "shared_constants": shared_constants,
            "first_call_example": meta["first_call_example"],
        }
        self.logger.info(
            "Visual Contract 已构建：family=%s, template=%s, shared_var=%s, "
            "shared_data source=%s (将注入所有 %d 个场景)",
            family,
            template_name,
            meta["shared_var_name"],
            shared_source,
            len(scene_plans),
        )
        return contract

    def _build_skill_prompt_section(
        self,
        template_code: str,
        template_name: str,
        shared_data: Any = None,
        base_class_code: Optional[str] = None,
        class_name: str = "YourScene",
        base_class_name: str = "SortingBase",
        shared_var_name: str = "SHARED_DATA",
        first_call_example: Optional[str] = None,
        family: Optional[str] = None,
        shared_constants: Optional[Dict[str, Any]] = None,
    ) -> str:
        """构建注入到 LLM Prompt 中的 SKILL 模板参考段落（含共享视觉契约）。

        family / base_class_name / shared_var_name 用于多家族（sorting / tree / graph）通用化。
        """
        effective_base = base_class_code or ""
        if not effective_base and base_class_name == "SortingBase":
            effective_base = self._transform_base_class_for_voiceover(
                self.skill_base_code or "", base_class_name
            )

        if shared_data is None:
            shared_data_repr = "[5, 3, 8, 1, 4]"
        elif isinstance(shared_data, str):
            shared_data_repr = repr(shared_data)
        else:
            shared_data_repr = repr(shared_data)
        extra_constants = shared_constants or {}
        extra_constants_lines = "\n".join(
            f"   {name} = {repr(value)}"
            for name, value in extra_constants.items()
        ) or "   # No extra family-specific constants."

        first_call = (first_call_example or "self.show_array({var}, title=...)").format(var=shared_var_name)

        family_label = (family or "algorithm").upper()

        # Family-specific hints
        if family == "sorting":
            domain_rules = (
                "- Colors: BLUE=default, YELLOW=comparing, RED=swapping, GREEN=sorted, PURPLE=pivot.\n"
                "- Sizes: BOX_SIZE=0.8, BOX_BUFF=0.1, FONT_SIZE=32, INDEX_FONT_SIZE=20, TITLE_FONT_SIZE=40.\n"
                "- Pacing: COMPARE_TIME=0.4, SWAP_TIME=0.6, STEP_PAUSE=0.3, PHASE_PAUSE=1.0."
            )
            first_call_note = (
                f"- **OPENING PHASE (phase A) of the single scene**: use the INSTANT variant\n"
                f"  `self.show_array_instant({shared_var_name}, title=None, show_indices=True)` so the\n"
                f"  full array appears in frame 0 (no animation). Build the algorithm-title `Text`\n"
                f"  separately with `Text(<title>, font_size=48, weight=BOLD).to_edge(UP, buff=0.6)`\n"
                f"  and add it via `self.add(algo_title)` BEFORE the voiceover block.\n"
                f"- **For phases B-E (initialization, main trace, completion, complexity)**: the\n"
                f"  same `self.boxes` / `self.labels` mobjects from phase A are STILL ON SCREEN.\n"
                f"  Mutate them in place via the base-class helpers (`self.highlight`,\n"
                f"  `self.swap_elements`, `self.mark_sorted`, `self.show_pointer`, etc.). DO NOT\n"
                f"  call `self.show_array_instant` / `self.show_array` again — that would create\n"
                f"  duplicate mobjects and break visual continuity."
            )
        elif family == "tree":
            domain_rules = (
                "- Colors: BLUE=default node, YELLOW=current, GREEN=visited, ORANGE=stack top, GREY=edge.\n"
                "- Sizes: NODE_RADIUS=0.35, NODE_FONT_SIZE=28, LEVEL_VBUFF=0.9, SIBLING_HBUFF=0.55.\n"
                "- Build the tree via `self.show_tree(preorder_str)`; highlight via `self.highlight_node / pulse_node`;\n"
                "  push/pop recursion via `self.push_stack / pop_stack`; emit visited chars via `self.append_output`.\n"
                "- When you need an edge mobject, MUST call `self.get_edge_mobj(u, v)` and handle missing edge;\n"
                "  NEVER access `self.edge_mobjs[(u, v)]` directly."
            )
            first_call_note = (
                f"- **OPENING PHASE (phase A) of the single scene**: use the INSTANT variant\n"
                f"  `root = self.setup_default_tree_instant({shared_var_name})` so the full tree\n"
                f"  appears in frame 0 (no animation). Build the algorithm-title `Text` separately\n"
                f"  with `Text(<title>, font_size=48, weight=BOLD).to_edge(UP, buff=0.6)` and add it\n"
                f"  via `self.add(algo_title)` BEFORE the voiceover block. Keep `root` as a local\n"
                f"  variable for phases B-E.\n"
                f"- **For phases B-E (initialization, main trace, completion, complexity)**: the\n"
                f"  same `self.tree_mobjects` / `self.edges` / `self.nodes` from phase A are STILL\n"
                f"  ON SCREEN. Mutate them in place via base-class helpers (`self.highlight_node`,\n"
                f"  `self.move_pointer`, `self.get_edge_mobj`, `self.push_stack`,\n"
                f"  `self.append_output`, etc.). DO NOT call `self.setup_default_tree` or\n"
                f"  `self.setup_default_tree_instant` again — the tree is already on screen."
            )
        elif family == "graph":
            domain_rules = (
                "- Colors: BLUE=default, YELLOW=current, GREEN=visited, ORANGE=frontier, RED=relaxed, YELLOW=path.\n"
                "- Sizes: NODE_RADIUS=0.38, EDGE_WIDTH=2.5, NODE_FONT_SIZE=28.\n"
                "- Build the graph via `self.create_graph(vertices, edges, directed=...)`; highlight via\n"
                "  `self.highlight_vertex / highlight_edge / flash_edge`; maintain tables via\n"
                "  `self.create_distance_table / update_distance`, `self.create_visited_set / mark_visited`,\n"
                "  `self.create_path_array / update_path`."
            )
            first_call_note = (
                f"- Use `{first_call}` to render the graph. Do NOT build nodes/edges manually."
            )
        elif family == "linked_list":
            domain_rules = (
                "- Colors: COLOR_HEAD=PURPLE, COLOR_DEFAULT=BLUE, COLOR_CURRENT=YELLOW, "
                "COLOR_TARGET=RED, COLOR_INSERT=GREEN, COLOR_L_PTR=ORANGE.\n"
                "- Sizes and spacing: NODE_WIDTH, NODE_HEIGHT, NODE_SPACING, FONT_SIZE are locked on LinkedListBase.\n"
                "- Build the list only via `self.setup_list_data(SHARED_DATA)`; highlight via "
                "`self.highlight_node` / `self.reset_node_color`; pointers via `self.create_pointer` / "
                "`self.move_pointer`; links via `self.create_arrow_between`; step text via "
                "`self.show_step_text` / `self.update_step_text`.\n"
                "- For deletion, use `SHARED_DELETE_INDEX` as the 1-based data-node position and "
                "`SHARED_DELETE_VALUE` as the deleted value. Remember `self.nodes[0]` is the head node."
            )
            first_call_note = (
                f"- **OPENING PHASE (phase A) of the single scene**: use the INSTANT variant\n"
                f"  `self.setup_list_data_instant({shared_var_name})` so the complete linked list\n"
                f"  (head node + data nodes + arrows + L pointer) appears in frame 0 (no animation).\n"
                f"  Build the algorithm-title `Text` separately with\n"
                f"  `Text(<title>, font_size=48, weight=BOLD).to_edge(UP, buff=0.6)` and add it via\n"
                f"  `self.add(algo_title)` BEFORE the voiceover block.\n"
                f"- **For phases B-E (initialization, main trace, completion, complexity)**: the\n"
                f"  same `self.nodes` / `self.node_mobjects` / `self.arrows` / `self.L_pointer` from\n"
                f"  phase A are STILL ON SCREEN. Mutate them in place via base-class helpers\n"
                f"  (`self.highlight_node`, `self.create_pointer`, `self.move_pointer`,\n"
                f"  `self.create_arrow_between`, `self.show_step_text`, etc.). DO NOT call\n"
                f"  `self.setup_list_data` or `self.setup_list_data_instant` again — the list is\n"
                f"  already on screen."
            )
        elif family == "stack":
            domain_rules = (
                "- Colors: COLOR_DEFAULT=BLUE, COLOR_EMPTY=DARK_GRAY, COLOR_TOP=YELLOW, "
                "COLOR_PUSH=GREEN, COLOR_POP=RED, COLOR_BASE_PTR=ORANGE, COLOR_TOP_PTR=YELLOW.\n"
                "- Sizes/constants: BOX_SIZE, FONT_SIZE, MAXSIZE_DEFAULT, PTR_OFFSET are locked on StackBase.\n"
                "- Layout: stack grows VERTICALLY upward — boxes[0] is the bottom, boxes[maxsize-1] is the top.\n"
                "  `base` arrow points to the left of boxes[0]; `top` arrow points to the left of boxes[length]\n"
                "  (the NEXT empty slot, NOT the top element itself).\n"
                "- Build the stack only via `self.setup_stack_data(SHARED_DATA, maxsize=...)`; never draw boxes\n"
                "  with `Square` / `Rectangle` manually.\n"
                "- Push/pop via the high-level helpers `self.push_element(value)` and `self.pop_element()`;\n"
                "  read top without modification via `self.peek_top()`.\n"
                "- Move only the top pointer via `self.move_top_pointer(new_length)`. Never reposition `base`.\n"
                "- Step text via `self.show_step_text` / `self.update_step_text`.\n"
                "- Empty-stack check: `self.length == 0`. Full-stack check: `self.length == self.maxsize`."
            )
            first_call_note = (
                f"- **OPENING PHASE (phase A) of the single scene**: use the INSTANT variant\n"
                f"  `self.setup_stack_data_instant({shared_var_name}, maxsize=max(len({shared_var_name})+2, 6))`\n"
                f"  so the full stack (boxes + index labels + base/top arrows + stacksize text) appears in\n"
                f"  frame 0 (no animation). Build the algorithm-title `Text` separately with\n"
                f"  `Text(<title>, font_size=48, weight=BOLD).to_edge(UP, buff=0.6)` and add it via\n"
                f"  `self.add(algo_title)` BEFORE the voiceover block.\n"
                f"- **For phases B-E (initialization, main trace, completion, complexity)**: the same\n"
                f"  `self.boxes` / `self.texts` / `self.indices` / `self.base_ptr` / `self.top_ptr` /\n"
                f"  `self.maxsize_text` from phase A are STILL ON SCREEN. Mutate them in place via\n"
                f"  base-class helpers (`self.push_element`, `self.pop_element`, `self.peek_top`,\n"
                f"  `self.highlight_box`, `self.set_value`, `self.move_top_pointer`,\n"
                f"  `self.show_step_text`, etc.). DO NOT call `self.setup_stack_data` or\n"
                f"  `self.setup_stack_data_instant` again — the stack is already on screen."
            )
        elif family == "seq_list":
            domain_rules = (
                "- Colors: COLOR_DEFAULT=BLUE, COLOR_EMPTY=DARK_GRAY, COLOR_TARGET=RED, "
                "COLOR_INSERT=GREEN, COLOR_CURRENT=YELLOW.\n"
                "- Sizes: BOX_SIZE and FONT_SIZE are locked on SeqListBase.\n"
                "- Build the sequence list only via `self.setup_list_data(SHARED_DATA)`; update values via "
                "`self.set_value`; update length via `self.update_length`; highlight via "
                "`self.highlight_box` / `self.reset_box_color`; pointers via "
                "`self.create_pointer` / `self.move_pointer`; step text via "
                "`self.show_step_text` / `self.update_step_text`.\n"
                "- For deletion, use `SHARED_DELETE_INDEX` as the 1-based user-facing position. "
                "Convert to zero-based only for helper calls with `target_idx = SHARED_DELETE_INDEX - 1`; "
                "`SHARED_DELETE_VALUE` is the deleted value."
            )
            first_call_note = (
                f"- **OPENING PHASE (phase A) of the single scene**: use the INSTANT variant\n"
                f"  `self.setup_list_data_instant({shared_var_name})` so the full sequence list\n"
                f"  (boxes, index labels, L struct + elem pointer) appears in frame 0 (no animation).\n"
                f"  Build the algorithm-title `Text` separately with\n"
                f"  `Text(<title>, font_size=48, weight=BOLD).to_edge(UP, buff=0.6)` and add it via\n"
                f"  `self.add(algo_title)` BEFORE the voiceover block.\n"
                f"- **For phases B-E (initialization, main trace, completion, complexity)**: the\n"
                f"  same `self.boxes` / `self.texts` / `self.indices` / `self.struct_L` /\n"
                f"  `self.elem_pointer` from phase A are STILL ON SCREEN. Mutate them in place via\n"
                f"  base-class helpers (`self.highlight_box`, `self.set_value`, `self.update_length`,\n"
                f"  `self.create_pointer`, `self.move_pointer`, `self.show_step_text`, etc.). DO NOT\n"
                f"  call `self.setup_list_data` or `self.setup_list_data_instant` again — the\n"
                f"  sequence list is already on screen."
            )
        else:
            domain_rules = "- Reuse the base class helpers and constants; never invent new ones."
            first_call_note = f"- Use `{first_call}` at the start of each scene that displays the structure."

        skill_section = f"""

============================================================
SHARED VISUAL CONTRACT (MANDATORY — APPLIES TO ALL SCENES, FAMILY={family_label})
============================================================

**This contract is identical for every scene of the current video.**
**Violating it will cause visual inconsistency across scenes, which is forbidden.**
**This contract OVERRIDES the OUTPUT FORMAT example above:**
  - Your `<manim>` block MUST contain ONLY the scene class `{class_name}`.
  - The pipeline will AUTOMATICALLY prepend: (a) imports, (b) warnings filter,
    (c) voiceover TTS imports, (d) the full `{base_class_name}` class.
  - DO NOT output any `import`/`from ...` statements, warnings filter lines, or the
    `{base_class_name}` class definition — they will be stripped/duplicated otherwise.

1. **Parent class (assume {base_class_name} is already defined above)**
   - Write exactly: `class {class_name}({base_class_name}):`
   - `{base_class_name}` inherits from `VoiceoverScene`, so your scene inherits voiceover too.
   - Inside `construct`, call `self.set_speech_service(...)` exactly once before any
     `self.voiceover(...)` block (follow the voiceover setup snippet above).

2. **Shared data (identical across ALL scenes — DO NOT MODIFY)**
   ```python
   {shared_var_name} = {shared_data_repr}
{extra_constants_lines}
   ```
   - Every scene that shows this structure MUST use `{shared_var_name}` verbatim (same content, same order).
   - **NEVER** invent different data, shuffle values, truncate, extend, or rename keys.
   - If the scene depicts a later stage of the algorithm, compute that stage's state
     **deterministically from `{shared_var_name}`** using plain Python instead of hard-coding different data.
   - Extra `SHARED_*` constants above are also locked and must be used verbatim when relevant.

3. **Mandatory rendering call**
{first_call_note}

4. **Locked visual constants (defined on {base_class_name} — never override)**
{domain_rules}
   - **DO NOT** shadow these with scene-local values; always reference the base-class attributes / helpers.

5. **Step text & complexity info**
   - Use `self.show_step_text(...)` and `self.update_step_text(...)` for explanatory text.
   - Show complexity info only via helpers that exist on `{base_class_name}`; otherwise use a small `Text`
     annotation above the subtitle safe zone.

## Base Class (REFERENCE ONLY — DO NOT COPY INTO YOUR OUTPUT)
The pipeline prepends this verbatim; showing it here so you know what helpers exist.
{effective_base if effective_base else '# Base class not available'}

## Algorithm-specific Template ({template_name}.py) — Follow this pattern:
{template_code}

## HARD RULES (violations fail the render):
- Inherit from `{base_class_name}` — write `class {class_name}({base_class_name}):` exactly.
- Use `{shared_var_name} = {shared_data_repr}` verbatim at the top of `construct`.
- Never invent new colors, sizes, or layouts. Reuse base-class helpers for all visuals.
- **FORBIDDEN**: building the tree/graph/array/linked-list/sequence-list manually via `Circle`, `Line`, `Square`, `Rectangle`, `Dot`, `Arrow`, or ad-hoc `VGroup` constructions. You MUST call the base-class helpers (`self.show_tree` / `self.create_graph` / `self.show_array` / `self.setup_list_data`) so all scenes share the same geometry and style. Any scene drawing its own nodes/edges/cells/list nodes will be rejected.
- **FORBIDDEN (tree)**: direct dict indexing like `self.edge_mobjs[(u, v)]`. Use `self.get_edge_mobj(u, v)` and null-check before `.animate`.
- This rule **overrides** any "Graceful Downgrades" / "approximate with Line + Text" guidance in the system prompt above.
- Output ONLY the scene class inside `<manim>...</manim>` — NO imports, NO base class, NO module-level code except `{shared_var_name} = ...` above your class if you prefer.
- DO NOT write `from manim import *`, `from manim_voiceover ...`, or `class {base_class_name}` — they are auto-prepended.
============================================================

## EXPECTED `<manim>` OUTPUT SHAPE (minimal — imports are auto-prepended):
<manim>
{shared_var_name} = {shared_data_repr}

class {class_name}({base_class_name}):
    def construct(self):
        self.set_speech_service(...)  # follow the voiceover setup snippet above
        # ... your scene logic, e.g. {first_call}, etc.
</manim>
"""
        return skill_section

    # -------- Programmatic header-prepending (visual contract assembly) --------

    _WARNINGS_BLOCK = (
        'import warnings\n'
        'warnings.filterwarnings('
        '"ignore", message="pkg_resources is deprecated as an API.*", '
        'category=UserWarning)\n'
        'import numpy as np  # safety import (LLM output may use np)'
    )

    def _build_prepended_header(self, voiceover_imports: str, base_class_code: str) -> str:
        """Assemble the fixed file header that gets prepended to every scene's LLM output.

        Ensures all parallel scenes share byte-identical imports + the skill-family base
        class (SortingBase / BinaryTreeBase / GraphBase / ...), so the LLM only needs to
        emit the scene class body.
        """
        code = base_class_code or ""

        # Insert the TTS service import right after the VoiceoverScene import (if missing).
        if voiceover_imports and voiceover_imports.strip() and voiceover_imports.strip() not in code:
            lines = code.splitlines()
            inserted = False
            new_lines: List[str] = []
            for line in lines:
                new_lines.append(line)
                if not inserted and line.strip() == 'from manim_voiceover import VoiceoverScene':
                    new_lines.append(voiceover_imports.strip())
                    inserted = True
            if not inserted:
                new_lines.insert(0, voiceover_imports.strip())
            code = "\n".join(new_lines)

        # Insert warnings filter right after `from manim import *` (if missing).
        if 'warnings.filterwarnings' not in code:
            lines = code.splitlines()
            inserted = False
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if not inserted and line.strip() == 'from manim import *':
                    new_lines.append(self._WARNINGS_BLOCK)
                    inserted = True
            if not inserted:
                new_lines.insert(0, self._WARNINGS_BLOCK)
            code = "\n".join(new_lines)

        return code.rstrip() + "\n"

    def _extract_target_scene_class(
        self,
        code: str,
        class_name: str,
        base_class_name: str = "SortingBase",
        shared_var_name: str = "SHARED_DATA",
    ) -> Optional[str]:
        """从 LLM 输出中切出 `class {class_name}(...)` 这一段（含可选的 `{shared_var_name} = ...`）。

        参数化 base_class_name / shared_var_name 以支持多家族（sorting / tree / graph）。
        """
        if not code:
            return None

        lines = code.splitlines()
        target_pattern = re.compile(rf'^class\s+{re.escape(class_name)}\s*\(')
        start_idx: Optional[int] = None
        for i, line in enumerate(lines):
            if target_pattern.match(line):
                start_idx = i
                break
        if start_idx is None:
            return None

        # Pipeline 在 header 里会确定性注入 `{shared_var_name} = ...`；
        # 因此这里忽略 LLM 自己写的同名赋值，避免重复定义（值还可能漂移）。
        # 仅从目标类开始截取，不再向上回溯。
        shared_data_start = start_idx

        # 找结束：下一个顶层 `class` / `def`（不是目标本身）或 EOF。
        end_idx = len(lines)
        for i in range(start_idx + 1, len(lines)):
            if re.match(r'^(class|def)\s+\w+', lines[i]):
                end_idx = i
                break

        snippet = "\n".join(lines[shared_data_start:end_idx]).rstrip()

        # 安全网：若 LLM 不遵从指令写成 `class X(VoiceoverScene):`，把父类归一到对应家族基类。
        snippet = re.sub(
            rf'(class\s+{re.escape(class_name)}\s*\(\s*)VoiceoverScene(\s*\))',
            rf'\1{base_class_name}\2',
            snippet,
        )
        # Scene 同理（少数 LLM 会省略家族基类直接写 Scene）。
        snippet = re.sub(
            rf'(class\s+{re.escape(class_name)}\s*\(\s*)Scene(\s*\))',
            rf'\1{base_class_name}\2',
            snippet,
        )
        return snippet

    def _assemble_final_code_with_contract(
        self,
        llm_code: str,
        class_name: str,
        voiceover_imports: str,
        base_class_code: str,
        base_class_name: str = "SortingBase",
        shared_var_name: str = "SHARED_DATA",
        shared_data: Any = None,
        shared_constants: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Combine the auto-prepended header with the LLM-generated scene class body.

        If ``shared_data`` is not None, a deterministic module-level constant
        ``{shared_var_name} = <literal>`` is emitted between the base class header
        and the scene class body. This guarantees every scene in the same video
        shares the *identical* input data (tree preorder / array / graph), even
        if the LLM forgot the assignment or wrote a different value.

        Returns the final self-contained file contents, or None if the LLM output
        did not contain a recognizable `class {class_name}(...)` block (caller falls
        back to the raw LLM output in that case).
        """
        scene_body = self._extract_target_scene_class(
            llm_code, class_name,
            base_class_name=base_class_name,
            shared_var_name=shared_var_name,
        )
        if not scene_body:
            return None
        header = self._build_prepended_header(voiceover_imports, base_class_code)
        shared_literal = self._format_shared_data_literal(shared_data)
        if shared_literal is not None:
            extra_lines: List[str] = []
            for name, value in (shared_constants or {}).items():
                literal = self._format_shared_data_literal(value)
                if literal is not None:
                    extra_lines.append(f"{name} = {literal}")
            extra_constants_block = ("\n" + "\n".join(extra_lines)) if extra_lines else ""
            shared_block = (
                f"# ==== SHARED VISUAL CONTRACT (auto-injected; do not edit) ====\n"
                f"{shared_var_name} = {shared_literal}{extra_constants_block}\n"
            )
            return f"{header}\n\n{shared_block}\n{scene_body}\n"
        return f"{header}\n\n{scene_body}\n"

    def _reapply_visual_contract(
        self,
        full_code: str,
        class_name: str,
    ) -> str:
        """Re-assemble Tier-1 render-fix output so it keeps the shared contract.

        ``_fix_render_error_with_llm`` returns a complete file (imports + base
        class + scene class), which means a careless LLM fix can drop or alter
        the ``SHARED_*`` assignment or rewrite the base-class header. We run
        the output back through ``_assemble_final_code_with_contract`` using
        the cached Visual Contract so the final file always starts with the
        same deterministic header + shared-data block that the initial
        generation produced.

        If there is no cached contract (legacy path) or the extraction fails,
        we return ``full_code`` unchanged so Tier 1 behaviour degrades
        gracefully rather than breaking the scene.
        """
        contract = getattr(self, "_cached_visual_contract", None)
        if not contract:
            return full_code
        try:
            voiceover_imports, _ = self._build_voiceover_prompt_section()
        except Exception as exc:
            self.logger.debug(
                "[visual-contract] re-apply skipped (voiceover prompt build failed: %s)",
                exc,
            )
            return full_code
        try:
            reassembled = self._assemble_final_code_with_contract(
                llm_code=full_code,
                class_name=class_name,
                voiceover_imports=voiceover_imports,
                base_class_code=contract["base_class_code"],
                base_class_name=contract.get("base_class_name", "SortingBase"),
                shared_var_name=contract.get("shared_var_name", "SHARED_DATA"),
                shared_data=contract.get("shared_data"),
                shared_constants=contract.get("shared_constants"),
            )
        except Exception as exc:
            self.logger.debug(
                "[visual-contract] re-apply raised for %s: %s", class_name, exc
            )
            return full_code
        if reassembled is None:
            self.logger.debug(
                "[visual-contract] re-apply could not locate class %s in fix output; "
                "keeping raw LLM code", class_name,
            )
            return full_code
        self.logger.info(
            "[visual-contract] re-applied to Tier 1 fix output: %s", class_name
        )
        return reassembled

    @staticmethod
    def _format_shared_data_literal(shared_data: Any) -> Optional[str]:
        """Render the shared-contract payload as a Python literal.

        ``repr`` handles strings / ints / lists / dicts consistently; for dicts
        we also verify ``ast.literal_eval`` round-trips to catch non-literal
        payloads (e.g. classes, numpy objects) and fall back to ``None`` so the
        caller skips the auto-injection block instead of emitting garbage.
        """
        if shared_data is None:
            return None
        try:
            import ast as _ast
            literal = repr(shared_data)
            _ast.literal_eval(literal)
            return literal
        except Exception:
            return None

    def _visual_contract_summary(self, contract: Dict[str, Any]) -> str:
        """Compact contract text for repair prompts and logs."""
        shared_var = contract.get("shared_var_name", "SHARED_DATA")
        lines = [
            f"family={contract.get('family')}",
            f"base_class={contract.get('base_class_name')}",
            f"{shared_var}={repr(contract.get('shared_data'))}",
        ]
        for name, value in (contract.get("shared_constants") or {}).items():
            lines.append(f"{name}={repr(value)}")
        return "\n".join(lines)

    def _find_visual_contract_violations(
        self,
        code: str,
        class_name: str,
        contract: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Detect scene-code drift from the shared visual contract before rendering."""
        if not contract:
            return []

        family = contract.get("family")
        base_class_name = contract.get("base_class_name", "SortingBase")
        shared_var_name = contract.get("shared_var_name", "SHARED_DATA")
        shared_constants = contract.get("shared_constants") or {}
        violations: List[str] = []

        class_pattern = re.compile(
            rf'class\s+{re.escape(class_name)}\s*\(\s*{re.escape(base_class_name)}\s*\)\s*:',
            re.MULTILINE,
        )
        if not class_pattern.search(code):
            violations.append(f"scene class must inherit from {base_class_name}")

        if shared_var_name not in code:
            violations.append(f"scene must use {shared_var_name}")

        for const_name in shared_constants:
            if const_name not in code:
                violations.append(f"scene must keep shared constant {const_name}")

        scene_body = self._extract_target_scene_class(
            code,
            class_name,
            base_class_name=base_class_name,
            shared_var_name=shared_var_name,
        ) or code

        if family in {"linked_list", "seq_list"}:
            if not re.search(r'setup_list_data\(\s*' + re.escape(shared_var_name) + r'\s*\)', scene_body):
                violations.append(f"{family} scenes must call self.setup_list_data({shared_var_name})")

            hardcoded_list_pattern = re.compile(
                r'(?m)^\s*(?:data|values|node_values|list_values)\s*=\s*\[[\d,\s\-]+\]'
            )
            hardcoded = [
                m.group(0).strip()
                for m in hardcoded_list_pattern.finditer(scene_body)
                if shared_var_name not in m.group(0)
            ]
            if hardcoded:
                violations.append(
                    f"{family} scene hard-codes local values instead of shared data: "
                    + "; ".join(hardcoded[:3])
                )

            manual_shape_pattern = re.compile(r'\b(Square|Rectangle|Arrow)\s*\(')
            if manual_shape_pattern.search(scene_body):
                violations.append(
                    f"{family} scene manually draws cells/nodes/arrows; use base-class helpers instead"
                )

        return violations

    def _repair_visual_contract_code_with_llm(
        self,
        code: str,
        class_name: str,
        scene_plan: Optional[ScenePlan],
        contract: Dict[str, Any],
        violations: List[str],
    ) -> str:
        """Ask the LLM for one targeted rewrite when a scene violates the contract."""
        try:
            scene_plan_json = (
                json.dumps(scene_plan.model_dump(), indent=2, ensure_ascii=False)
                if scene_plan
                else "{}"
            )
            prompt = f"""You are repairing a Manim scene that violates a shared visual contract.

The scene must keep its educational intent, but it must be rewritten to obey the shared contract exactly.

SCENE PLAN:
{scene_plan_json}

SHARED VISUAL CONTRACT:
{self._visual_contract_summary(contract)}

VIOLATIONS:
{chr(10).join(f"- {v}" for v in violations)}

CURRENT CODE:
```python
{code}
```

Return ONLY the corrected scene class inside <manim>...</manim>.
Do not output imports or the base class. Do not change any SHARED_* values.
For linked-list or sequence-list scenes, call self.setup_list_data(SHARED_DATA) and use
the family base-class helpers instead of manually drawing Square/Rectangle/Arrow cells or nodes.
"""
            response = self._call_llm(
                system_prompt=self._build_codegen_system_prompt(prompt),
                user_message="Repair the scene so it fully obeys the shared visual contract.",
                temperature=min(float(getattr(self.config, "temperature", 0.3) or 0.3), 0.2),
                max_retries=2,
            )
            repaired, extraction_method = self._extract_manim_code(response)
            if not repaired:
                self.logger.warning(
                    "Visual Contract repair returned no extractable code for %s",
                    class_name,
                )
                return code
            repaired = self._reapply_visual_contract(repaired, class_name)
            repaired = self._fix_layout_issues(repaired)
            still_violates = self._find_visual_contract_violations(repaired, class_name, contract)
            if still_violates:
                self.logger.warning(
                    "Visual Contract repair for %s still has violations: %s",
                    class_name,
                    "; ".join(still_violates),
                )
            else:
                self.logger.info(
                    "Visual Contract repair applied for %s (extracted via %s)",
                    class_name,
                    extraction_method,
                )
            return repaired
        except Exception as exc:
            self.logger.warning("Visual Contract repair crashed for %s: %s", class_name, exc)
            return code

    def _enforce_visual_contract_on_code(
        self,
        code: str,
        class_name: str,
        scene_plan: Optional[ScenePlan],
        contract: Optional[Dict[str, Any]],
        allow_llm_repair: bool = True,
    ) -> str:
        """Re-apply and validate the cached/shared contract for generated or fixed code."""
        if not contract:
            return code
        code = self._reapply_visual_contract(code, class_name)
        violations = self._find_visual_contract_violations(code, class_name, contract)
        if not violations:
            return code
        self.logger.warning(
            "Visual Contract violations in %s: %s",
            class_name,
            "; ".join(violations),
        )
        if not allow_llm_repair:
            return code
        return self._repair_visual_contract_code_with_llm(
            code=code,
            class_name=class_name,
            scene_plan=scene_plan,
            contract=contract,
            violations=violations,
        )

    def _build_voiceover_prompt_section(self) -> tuple[str, str]:
        """根据当前 tts_provider 构造 Voiceover import 和 set_speech_service 代码片段。"""
        provider = settings.tts_provider
        if provider == "elevenlabs":
            # manim-voiceover 0.3.x does not ship ElevenLabsService in this project env.
            # Fall back to GTTSService to keep generated scenes runnable.
            self.logger.warning("TTS_PROVIDER=elevenlabs is configured, but ElevenLabsService is unavailable; falling back to GTTSService.")
            imports = "from manim_voiceover.services.gtts import GTTSService"
            setup = 'self.set_speech_service(GTTSService(lang="zh-CN"))'
            return imports, setup

        if provider == "openai":
            # manim-voiceover 0.3.x does not ship OpenAIService in this project env.
            # Fall back to GTTSService to keep generated scenes runnable.
            self.logger.warning("TTS_PROVIDER=openai is configured, but OpenAIService is unavailable; falling back to GTTSService.")
            imports = "from manim_voiceover.services.gtts import GTTSService"
            setup = 'self.set_speech_service(GTTSService(lang="zh-CN"))'
            return imports, setup

        if provider == "edge":
            imports = "from generation.tts.edge_service import EdgeTTSService"
            setup = (
                'self.set_speech_service('
                f'EdgeTTSService(voice="{settings.edge_tts_voice}", '
                f'rate="{settings.edge_tts_rate}", '
                f'volume="{settings.edge_tts_volume}", '
                f'pitch="{settings.edge_tts_pitch}"))'
            )
            return imports, setup

        if provider == "coqui":
            imports = "from manim_voiceover.services.coqui import CoquiService"
            setup = "self.set_speech_service(CoquiService())"
            return imports, setup

        raise ValueError(f"Unsupported tts_provider for voiceover prompt: {provider}")

    def execute(
        self,
        concept_analysis: ConceptAnalysis,
        target_language: str = "English",
        render_quality: Optional[str] = None,
    ) -> AnimationResult:

        # Store on self so downstream prompt builders pick it up without needing
        # to thread the parameter through every private helper signature.
        self.target_language = target_language

        start_time = time.time()
        self.logger.info(
            f"Starting animation generation for: {concept_analysis.main_concept} "
            f"(target_language={target_language})"
        )

        try:
            # Step 1: Generate scene plans
            scene_plans, response_json = self._generate_scene_plans(concept_analysis)
            self.logger.info(f"Generated {len(scene_plans)} scene plans")

            # Save scene plans for debugging
            self._save_scene_plans(scene_plans, concept_analysis, response_json)

            # Step 2: Generate Manim code for each scene
            scene_codes = self._generate_scene_codes(scene_plans, concept_analysis=concept_analysis)
            self.logger.info(f"Generated code for {len(scene_codes)} scenes")

            # Step 2.5: manim-lint + optional LLM fix pass
            scene_codes = self._lint_and_fix_scene_codes(scene_codes, scene_plans)

            # Step 3: Render each scene (with LLM auto-fix on runtime errors)
            # render_quality 为 None 时回退到渲染器默认质量；首次生成默认传入 "l" 走低质量快速预览。
            render_results = self._render_scenes(
                scene_codes, scene_plans, render_quality=render_quality
            )
            successful_renders = [r for r in render_results if r.success]
            self.logger.info(f"Successfully rendered {len(successful_renders)}/{len(render_results)} scenes")

            # Step 4: Concatenate scenes into single animation
            if successful_renders:
                silent_animation_path = self._concatenate_scenes(successful_renders)
            else:
                silent_animation_path = None

            # Calculate timing
            generation_time = time.time() - start_time
            total_render_time = sum(r.render_time or 0 for r in render_results)

            # Create result
            result = AnimationResult(
                success=len(successful_renders) > 0,
                concept_id=concept_analysis.main_concept.lower().replace(" ", "_"),
                total_duration=sum(r.duration for r in successful_renders if r.duration),
                scene_count=len(scene_plans),
                silent_animation_path=str(silent_animation_path) if silent_animation_path else None,
                scene_plan=scene_plans,
                scene_codes=scene_codes,
                render_results=render_results,
                generation_time=generation_time,
                total_render_time=total_render_time,
                models_used={"reasoning": self.model},
                token_usage=self.get_token_usage()
            )

            self.logger.info(f"Animation generation completed in {generation_time:.2f}s")
            return result

        except Exception as e:
            self.logger.error(f"Animation generation failed: {e}")
            return AnimationResult(
                success=False,
                concept_id=concept_analysis.main_concept.lower().replace(" ", "_"),
                scene_count=0,
                error_message=str(e),
                scene_plan=[],
                scene_codes=[],
                render_results=[],
                generation_time=time.time() - start_time,
                models_used={"reasoning": self.model},
                token_usage=self.get_token_usage()
            )

    def _generate_scene_plans(self, concept_analysis: ConceptAnalysis) -> tuple[List[ScenePlan], Dict[str, Any]]:
        """Generate scene plans from concept analysis"""

        user_message = f"Analyze this STEM concept and create scene plans:\n\n{json.dumps(concept_analysis.model_dump(), indent=2, ensure_ascii=False)}"

        try:
            response_json = self._call_llm_structured(
                system_prompt=self._build_planning_system_prompt(),
                user_message=user_message,
                temperature=self.config.temperature,
                max_retries=3
            )
            self._latest_planning_response_json = response_json

            # Parse and validate scene plans
            scene_plans = []
            for plan_data in response_json.get("scene_plans", []):
                try:
                    scene_plan = ScenePlan(**plan_data)
                    scene_plans.append(scene_plan)
                except Exception as e:
                    self.logger.warning(f"Invalid scene plan data: {e}")
                    continue

            # SINGLE-SCENE MODE safety net: the planning prompt mandates exactly
            # ONE scene plan covering the full algorithm walk-through. If the LLM
            # ignored the rule and emitted multiple plans, merge their `actions`
            # into the first plan's `actions` (preserving order) so we still get
            # one continuous Manim class with all phases stitched together.
            if len(scene_plans) > 1:
                self.logger.warning(
                    "SINGLE-SCENE MODE violated: planner emitted %d scene plans; "
                    "merging actions of plans 2..N into the first plan.",
                    len(scene_plans),
                )
                merged_first = scene_plans[0]
                for extra in scene_plans[1:]:
                    merged_first.actions.extend(extra.actions)
                # Force the canonical id/title so downstream prompts see it.
                if merged_first.id != "algorithm_full":
                    self.logger.info(
                        "Renaming merged scene id '%s' -> 'algorithm_full'",
                        merged_first.id,
                    )
                    merged_first.id = "algorithm_full"
                merged_first.scene_dependencies = []
                scene_plans = [merged_first]
                response_json["scene_plans"] = [merged_first.model_dump()]

            return scene_plans, response_json

        except Exception as e:
            self.logger.error(f"Scene planning failed: {e}")
            raise ValueError(f"Failed to generate scene plans: {e}")

    def _save_scene_plans(self, scene_plans: List[ScenePlan], concept_analysis: ConceptAnalysis, response_json: Dict[str, Any]) -> Path:
        """Save raw scene plans output to JSON file for debugging"""

        # Generate filename from concept
        safe_name = "".join(c if c.isalnum() else "_" for c in concept_analysis.main_concept.lower())
        safe_name = safe_name[:50]  # Limit length
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_raw_scene_plans_{timestamp}.json"

        filepath = self.output_dir / "scene_plans" / filename

        # Save raw response
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(response_json, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Raw scene plans output saved to {filepath}")
        return filepath

    def _generate_one_scene_code(
        self,
        scene_plan: ScenePlan,
        visual_contract: Optional[Dict[str, Any]],
        temperature_override: Optional[float] = None,
        save_suffix: Optional[str] = None,
        target_duration: str = "25-30",
    ) -> Optional[ManimSceneCode]:
        """Generate Manim code for a single ScenePlan.

        Extracted from the former inner closure so Tier 2 (render-time
        regenerate-from-plan) can reuse the exact same LLM prompt/assembly
        path with a different temperature.

        Args:
            scene_plan: The plan to generate code for.
            visual_contract: Precomputed global visual contract (None falls
                back to the legacy per-scene SKILL matching).
            temperature_override: If provided, use this temperature instead
                of ``self.config.temperature``.
            save_suffix: Optional tag to pass to ``_save_scene_code`` so
                regenerated/stub artifacts don't overwrite the original file.
        """
        try:
            self.logger.info(f"Generating code for scene: {scene_plan.title}")
            self.logger.debug(f"Scene ID: {scene_plan.id}, Actions count: {len(scene_plan.actions)}")

            class_name = self._sanitize_class_name(scene_plan.id)
            self.logger.debug(f"Sanitized class name: {class_name}")

            scene_plan_json = json.dumps(scene_plan.model_dump(), indent=2, ensure_ascii=False)
            self.logger.debug(f"Scene plan JSON length: {len(scene_plan_json)} characters")
            self.logger.debug(
                f"First action parameters: {scene_plan.actions[0].parameters if scene_plan.actions else 'N/A'}"
            )

            try:
                voiceover_imports, tts_setup_snippet = self._build_voiceover_prompt_section()
                formatted_prompt = self.CODE_GENERATION_PROMPT.format(
                    scene_plan=scene_plan_json,
                    class_name=class_name,
                    target_duration=target_duration,
                    voiceover_imports=voiceover_imports,
                    tts_setup_snippet=tts_setup_snippet
                )
                self.logger.debug(f"System prompt formatted successfully, length: {len(formatted_prompt)}")
            except Exception as fmt_error:
                self.logger.error(f"Failed to format system prompt: {fmt_error}")
                self.logger.error(f"Format error type: {type(fmt_error).__name__}")
                raise

            # ========== SKILL 模板 + 全局视觉契约注入 ==========
            user_msg = "Generate the Manim code for the scene plan specified above."

            if visual_contract is not None:
                base_class_name = visual_contract.get("base_class_name", "SortingBase")
                shared_var_name = visual_contract.get("shared_var_name", "SHARED_DATA")
                first_call_example = visual_contract.get("first_call_example")
                family = visual_contract.get("family")
                skill_section = self._build_skill_prompt_section(
                    template_code=visual_contract["template_code"],
                    template_name=visual_contract["template_name"],
                    shared_data=visual_contract["shared_data"],
                    base_class_code=visual_contract["base_class_code"],
                    class_name=class_name,
                    base_class_name=base_class_name,
                    shared_var_name=shared_var_name,
                    first_call_example=first_call_example,
                    family=family,
                    shared_constants=visual_contract.get("shared_constants"),
                )
                formatted_prompt += skill_section
                user_msg = (
                    f"A SHARED VISUAL CONTRACT is provided above. It is IDENTICAL for every "
                    f"scene of this video. You MUST inherit from `{base_class_name}` (already a "
                    f"VoiceoverScene subclass) and use the exact `{shared_var_name}` verbatim. "
                    f"Do NOT invent different data, colors, sizes, or layouts. Use every "
                    f"`SHARED_*` constant verbatim when relevant.\n\n"
                    f"OVERRIDE: Section 9 'Graceful Downgrades for Heavy Visuals' in the system "
                    f"prompt DOES NOT APPLY when a SHARED VISUAL CONTRACT is present. You MUST "
                    f"call the base-class helpers (`self.show_tree` / `self.create_graph` / "
                    f"`self.show_array` / `self.setup_list_data`) to render the data structure. "
                    f"Never draw trees, graphs, arrays, or linked-list nodes manually with "
                    f"`Circle`/`Line`/`Square`/`Rectangle`/`Dot`/`Arrow`/`VGroup` — the "
                    f"geometry and style must come from the base class, not from you."
                )
                if family in {"linked_list", "seq_list"} and scene_plan.id.startswith("continuous_"):
                    user_msg += (
                        "\n\nCONTINUOUS VIDEO REQUIREMENT: generate exactly ONE Manim scene class "
                        "for the whole video. Initialize the data structure once with "
                        f"`self.setup_list_data({shared_var_name})`, then keep manipulating the same "
                        "base-class state and pointer mobjects through every section. "
                        "Do not reset, recreate, or reinitialize the data structure between original sections."
                    )
                self.logger.info(
                    "Visual Contract 已注入场景 %s (family=%s, template=%s, shared_var=%s)",
                    scene_plan.id,
                    family,
                    visual_contract["template_name"],
                    shared_var_name,
                )
            else:
                match_text = f"{scene_plan.title} {scene_plan.description}"
                family, template_code, template_name = self._match_any_skill_template(match_text)
                if template_code:
                    base_class_name = self.SKILL_FAMILIES.get(family, {}).get("base_class_name", "SortingBase")
                    skill_section = self._build_skill_prompt_section(
                        template_code=template_code,
                        template_name=template_name,
                        class_name=class_name,
                        family=family,
                    )
                    formatted_prompt += skill_section
                    user_msg = (
                        "A SKILL template is provided above. "
                        "Generate the Manim code following the template's style and structure. "
                        f"Include the {base_class_name} class inline in your output code."
                    )
                    self.logger.info(f"SKILL 模板已注入到 Prompt：{template_name} (family: {family})")

            effective_temperature = (
                temperature_override
                if temperature_override is not None
                else self.config.temperature
            )

            response = self._call_llm(
                system_prompt=self._build_codegen_system_prompt(formatted_prompt),
                user_message=user_msg,
                temperature=effective_temperature,
                max_retries=3
            )

            self.logger.debug(f"LLM response received, length: {len(response)} characters")
            self.logger.debug(f"Response preview: {response[:200]}...")

            manim_code, extraction_method = self._extract_manim_code(response)
            self.logger.debug(f"Code extraction method: {extraction_method}")

            if manim_code:
                if visual_contract is not None:
                    assembled = self._assemble_final_code_with_contract(
                        llm_code=manim_code,
                        class_name=class_name,
                        voiceover_imports=voiceover_imports,
                        base_class_code=visual_contract["base_class_code"],
                        base_class_name=visual_contract.get("base_class_name", "SortingBase"),
                        shared_var_name=visual_contract.get("shared_var_name", "SHARED_DATA"),
                        shared_data=visual_contract.get("shared_data"),
                        shared_constants=visual_contract.get("shared_constants"),
                    )
                    if assembled is not None:
                        manim_code = assembled
                        extraction_method = f"{extraction_method}+contract_prepend"
                        self.logger.info(
                            "Visual Contract: 已程序化拼接基类 header 到场景 %s", class_name
                        )
                    else:
                        self.logger.warning(
                            "Visual Contract: 在 LLM 输出中未找到 class %s；保留原始输出作为兜底",
                            class_name,
                        )

                manim_code = self._fix_layout_issues(manim_code)
                manim_code = self._enforce_visual_contract_on_code(
                    code=manim_code,
                    class_name=class_name,
                    scene_plan=scene_plan,
                    contract=visual_contract,
                    allow_llm_repair=True,
                )
                self.logger.debug(f"Extracted code length: {len(manim_code)} characters")
                self._save_scene_code(
                    scene_plan.id, class_name, manim_code, response,
                    tag_suffix=save_suffix,
                )

                scene_code = ManimSceneCode(
                    scene_id=scene_plan.id,
                    scene_name=class_name,
                    manim_code=manim_code,
                    raw_llm_output=response,
                    extraction_method=extraction_method
                )

                self.logger.info(f"Successfully generated code for scene: {class_name}")
                return scene_code
            else:
                self.logger.error(f"Failed to extract Manim code from response for scene: {scene_plan.id}")
                self.logger.error(f"Response contained: {response[:500]}...")
                return None

        except Exception as e:
            self.logger.error(f"Code generation failed for scene {scene_plan.id}: {e}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            self.logger.error(f"Exception details: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _build_continuous_scene_plan(
        self,
        scene_plans: List[ScenePlan],
        concept_analysis: Optional[ConceptAnalysis],
        family: str,
    ) -> ScenePlan:
        """Collapse multiple planner scenes into one continuous Manim scene.

        Data-structure videos need object identity inside one `construct`: the
        same boxes/nodes, arrows, and pointers should be transformed through
        the whole explanation instead of being recreated by separate scene classes.
        """
        combined_actions: List[SceneAction] = []
        for plan_index, plan in enumerate(scene_plans, start=1):
            for action_index, action in enumerate(plan.actions, start=1):
                data = action.model_dump()
                original_target = data.get("target") or f"action_{action_index}"
                data["target"] = f"{plan.id}_{original_target}"
                data["description"] = (
                    f"Continuous section {plan_index} ({plan.title}): "
                    f"{data.get('description', '')}"
                )
                params = dict(data.get("parameters") or {})
                params.setdefault("section_title", plan.title)
                params.setdefault("source_scene_id", plan.id)
                data["parameters"] = params
                combined_actions.append(SceneAction(**data))

        main_concept = concept_analysis.main_concept if concept_analysis else family
        section_titles = " -> ".join(plan.title for plan in scene_plans if plan.title)
        continuous_id = f"continuous_{family}_video"
        return ScenePlan(
            id=continuous_id,
            title=f"{main_concept} - continuous demonstration",
            description=(
                f"Generate one continuous Manim scene for the entire {family} video. "
                "Do not split this into multiple Scene classes or recreate the data structure between sections. "
                "Initialize the data structure exactly once with SHARED_DATA, then keep transforming the same "
                "base-class mobjects and pointers through all sections. "
                f"Original section order: {section_titles}"
            ),
            sub_concept_id=continuous_id,
            actions=combined_actions,
            scene_dependencies=[],
        )

    def _generate_scene_codes(
        self,
        scene_plans: List[ScenePlan],
        concept_analysis: Optional[ConceptAnalysis] = None,
    ) -> List[ManimSceneCode]:
        """Generate Manim code for each scene plan in parallel.

        在进入并行之前，先构建一个全局共享的 Visual Contract（含统一的数据数组 + 已适配
        VoiceoverScene 的基类），然后把同一份契约注入到每个场景的 prompt 中，从而保证所
        有并行生成的场景共享完全一致的视觉风格。
        """

        scene_codes = []
        self.logger.info(f"Starting parallel code generation for {len(scene_plans)} scenes")

        # 全局构建一次 Visual Contract（失败则回退到旧的 per-scene 匹配行为）
        visual_contract = self._build_global_visual_contract(scene_plans, concept_analysis)
        # Cache it for downstream render-time fallbacks (Tier 2 regeneration).
        self._cached_visual_contract = visual_contract
        self._continuous_scene_plan = None

        continuous_families = {"linked_list", "seq_list"}
        family = visual_contract.get("family") if visual_contract else None
        if family in continuous_families:
            self.logger.info(
                "%s Visual Contract detected; generating one continuous scene instead of %d split scenes",
                family,
                len(scene_plans),
            )
            continuous_plan = self._build_continuous_scene_plan(scene_plans, concept_analysis, family)
            self._continuous_scene_plan = continuous_plan
            result = self._generate_one_scene_code(
                continuous_plan,
                visual_contract,
                target_duration="full video, preserving the pacing of all original sections",
            )
            if result:
                self.logger.info("Continuous %s code generation complete: 1/1 succeeded", family)
                return [result]
            self.logger.warning(
                "Continuous %s code generation failed; falling back to split-scene generation",
                family,
            )

        with ThreadPoolExecutor(max_workers=min(len(scene_plans), 10)) as executor:
            future_to_plan = {
                executor.submit(self._generate_one_scene_code, plan, visual_contract): plan
                for plan in scene_plans
            }
            
            for future in as_completed(future_to_plan):
                scene_plan = future_to_plan[future]
                try:
                    result = future.result()
                    if result:
                        scene_codes.append(result)
                except Exception as e:
                    self.logger.error(f"Exception in parallel code generation for {scene_plan.id}: {e}")

        scene_codes.sort(key=lambda x: scene_plans.index(next(p for p in scene_plans if p.id == x.scene_id)))
        self.logger.info(f"Parallel code generation complete: {len(scene_codes)}/{len(scene_plans)} succeeded")

        return scene_codes

    def _lint_and_fix_scene_codes(
        self,
        scene_codes: List[ManimSceneCode],
        scene_plans: List[ScenePlan],
    ) -> List[ManimSceneCode]:
        """Run manim-lint on generated code; on errors, ask LLM to fix up to lint_max_fix_attempts times."""

        if not self.config.lint_enabled:
            return scene_codes
        if not scene_codes:
            return scene_codes

        lint_dir = self.output_dir / "lint_reports"
        lint_dir.mkdir(parents=True, exist_ok=True)
        plan_by_id = {p.id: p for p in scene_plans}
        if self._continuous_scene_plan is not None:
            plan_by_id[self._continuous_scene_plan.id] = self._continuous_scene_plan
        max_attempts = self.config.lint_max_fix_attempts
        geometry = self.config.lint_geometry
        lint_timeout = self.config.lint_timeout

        def process_one(sc: ManimSceneCode) -> ManimSceneCode:
            code = sc.manim_code
            plan = plan_by_id.get(sc.scene_id)
            scene_plan_json = (
                json.dumps(plan.model_dump(), indent=2, ensure_ascii=False) if plan else "{}"
            )
            class_name = sc.scene_name
            last_raw = sc.raw_llm_output

            for fix_round in range(max_attempts + 1):
                report_path = lint_dir / f"{sc.scene_id}_attempt{fix_round}.json"
                report = lint_manim_code(
                    code,
                    save_to=report_path,
                    geometry=geometry,
                    timeout=lint_timeout,
                    project_root=Path(__file__).resolve().parent.parent,
                )
                if report.cli_error and fix_round == 0:
                    self.logger.debug("manim-lint: %s", report.cli_error)

                if not report.has_errors():
                    if fix_round > 0:
                        self.logger.info(
                            "Lint clean for scene %s after %s fix round(s)",
                            sc.scene_id,
                            fix_round,
                        )
                    return ManimSceneCode(
                        scene_id=sc.scene_id,
                        scene_name=sc.scene_name,
                        manim_code=code,
                        raw_llm_output=last_raw,
                        extraction_method=sc.extraction_method,
                    )

                if fix_round >= max_attempts:
                    self.logger.warning(
                        "Lint still has errors for scene %s after %s fix attempt(s); proceeding to render",
                        sc.scene_id,
                        max_attempts,
                    )
                    return ManimSceneCode(
                        scene_id=sc.scene_id,
                        scene_name=sc.scene_name,
                        manim_code=code,
                        raw_llm_output=last_raw,
                        extraction_method=sc.extraction_method,
                    )

                errors = [d for d in report.diagnostics if d.severity.lower() == "error"]
                diag_lines = []
                for d in errors[:30]:
                    loc = f"{d.line or 0}:{d.column or 0}"
                    diag_lines.append(f"{loc} [{d.code}] {d.message}")
                diagnostics_text = "\n".join(diag_lines) if diag_lines else "(no error rows parsed)"

                fix_prompt = self.LINT_FIX_PROMPT.format(
                    scene_plan=scene_plan_json,
                    current_code=code,
                    class_name=class_name,
                    diagnostics=diagnostics_text,
                )
                response = self._call_llm(
                    system_prompt=self._build_codegen_system_prompt(fix_prompt),
                    user_message="Apply the lint fixes and return the full corrected code in <manim> tags.",
                    temperature=min(self.config.temperature, 0.4),
                    max_retries=2,
                )
                manim_code, extraction_method = self._extract_manim_code(response)
                if manim_code:
                    code = self._fix_layout_issues(manim_code)
                    code = self._enforce_visual_contract_on_code(
                        code=code,
                        class_name=class_name,
                        scene_plan=plan,
                        contract=self._cached_visual_contract,
                        allow_llm_repair=True,
                    )
                    last_raw = response
                    self._save_scene_code(
                        sc.scene_id,
                        class_name,
                        code,
                        response,
                        tag_suffix=f"lintfix{fix_round + 1}",
                    )
                    self.logger.info(
                        "Lint fix round %s applied for scene %s (extracted via %s)",
                        fix_round + 1,
                        sc.scene_id,
                        extraction_method,
                    )
                else:
                    self.logger.warning(
                        "Lint fix failed to extract <manim> code for scene %s",
                        sc.scene_id,
                    )

            return ManimSceneCode(
                scene_id=sc.scene_id,
                scene_name=sc.scene_name,
                manim_code=code,
                raw_llm_output=last_raw,
                extraction_method=sc.extraction_method,
            )

        updated: List[ManimSceneCode] = []
        with ThreadPoolExecutor(max_workers=min(len(scene_codes), 10)) as executor:
            futures = {executor.submit(process_one, sc): sc for sc in scene_codes}
            for fut in as_completed(futures):
                updated.append(fut.result())

        id_to_code = {x.scene_id: x for x in updated}
        return [id_to_code[sc.scene_id] for sc in scene_codes if sc.scene_id in id_to_code]

    def _extract_manim_code(self, response: str) -> tuple[str, str]:
        """Extract Manim code from LLM response using <manim> tags"""

        # Method 1: Try to extract from <manim>...</manim> tags
        manim_pattern = r'<manim>(.*?)</manim>'
        matches = re.findall(manim_pattern, response, re.DOTALL)

        if matches:
            # Take the first (most complete) match
            manim_code = matches[0].strip()
            # Clean the code by removing backticks
            manim_code = self._clean_manim_code(manim_code)
            return manim_code, "tags"

        # Method 2: Try to extract class definition if no tags found
        class_pattern = r'class\s+(\w+)\s*\(\s*Scene\s*\):.*?(?=\n\nclass|\Z)'
        matches = re.findall(class_pattern, response, re.DOTALL)

        if matches:
            # Find the complete code block
            class_start = response.find(f"class {matches[0]}(")
            if class_start != -1:
                # Find the end of this class (next class or end of response)
                remaining = response[class_start:]
                next_class = re.search(r'\n\nclass\s+\w+', remaining)
                if next_class:
                    manim_code = remaining[:next_class.start()]
                else:
                    manim_code = remaining

                # Add imports if missing
                if "from manim import" not in manim_code:
                    manim_code = "from manim import *\n\n" + manim_code

                # Clean the code by removing backticks
                manim_code = self._clean_manim_code(manim_code)
                return manim_code.strip(), "parsing"

        # Method 3: Last resort - try to fix common formatting issues
        if "class" in response and "def construct" in response:
            # Basic cleanup
            cleaned = response.strip()
            if not cleaned.startswith("from"):
                cleaned = "from manim import *\n\n" + cleaned

            # Clean the code by removing backticks
            cleaned = self._clean_manim_code(cleaned)
            return cleaned, "cleanup"

        return "", "failed"

    def _clean_manim_code(self, code: str) -> str:
        """Clean Manim code by removing backticks and fixing common issues"""

        # Remove all backticks - this is the main issue
        code = code.replace('`', '')

        # Fix common triple-backtick code block markers that might leave extra formatting
        code = re.sub(r'python\n', '', code, flags=re.IGNORECASE)
        code = re.sub(r'\npython', '', code, flags=re.IGNORECASE)

        # Remove any remaining markdown-style code formatting
        code = re.sub(r'^```.*\n', '', code, flags=re.MULTILINE)
        code = re.sub(r'\n```.*$', '', code, flags=re.MULTILINE)

        # Clean up any double newlines that might have been created
        code = re.sub(r'\n{3,}', '\n\n', code)

        # Strip leading/trailing whitespace
        code = code.strip()

        # Log the cleaning if significant changes were made
        original_length = len(code.replace('`', ''))
        if original_length != len(code):
            self.logger.debug("Applied Manim code cleaning (removed backticks and formatting)")

        return code

    def _fix_layout_issues(self, code: str) -> str:
        """Post-process generated Manim code to fix common layout/overlap issues.
        
        Applies static transformations to reduce visual overlap:
        1. Cap excessive font sizes
        2. Ensure minimum buff between stacked elements
        3. Scale down overly large side_length values
        4. Warn about too many self.add() calls (skip layout awareness)
        """
        original = code
        fixes_applied = []

        # Fix 1: Cap font_size to 48 (titles) — catch font_size=56, 60, 72 etc.
        def cap_font_size(match):
            size = int(match.group(1))
            if size > 48:
                fixes_applied.append(f"font_size {size} -> 48")
                return f"font_size={48}"
            return match.group(0)
        code = re.sub(r'font_size\s*=\s*(\d+)', cap_font_size, code)

        # Fix 2: Ensure buff >= 0.3 for next_to with DOWN/UP (prevent tight stacking)
        def fix_small_buff(match):
            prefix = match.group(1)
            direction = match.group(2)
            buff_val = float(match.group(3))
            if buff_val < 0.3:
                fixes_applied.append(f"buff {buff_val} -> 0.4 (direction={direction})")
                return f"{prefix}{direction}, buff={0.4})"
            return match.group(0)
        code = re.sub(
            r'(\.next_to\([^,]+,\s*)(DOWN|UP)\s*,\s*buff\s*=\s*([\d.]+)\)',
            fix_small_buff, code
        )

        # Fix 3: Cap side_length to 1.2 for squares/rectangles to prevent oversized boxes
        def cap_side_length(match):
            size = float(match.group(1))
            if size > 1.5:
                fixes_applied.append(f"side_length {size} -> 1.2")
                return f"side_length={1.2}"
            return match.group(0)
        code = re.sub(r'side_length\s*=\s*([\d.]+)', cap_side_length, code)

        # Fix 4: Replace self.add(obj) with self.play(FadeIn(obj)) for layout awareness
        # Only replace standalone self.add() calls that aren't inside setup/helper methods
        add_pattern = re.compile(r'^(\s+)(self\.add\(([^)]+)\))\s*$', re.MULTILINE)
        add_matches = add_pattern.findall(code)
        if len(add_matches) > 2:
            # Too many self.add() calls — suggests missing animations
            self.logger.warning(
                f"Found {len(add_matches)} self.add() calls. "
                "Consider using self.play(FadeIn(...)) for better layout control."
            )

        # Fix 5: Subtitle safe zone — keep mobjects out of y ∈ [-4.0, -3.33].
        # Rewrite bare bottom-hugging calls so they stay above the subtitle band.
        def patch_to_edge_down(match):
            fixes_applied.append("to_edge(DOWN) -> to_edge(DOWN, buff=0.9)")
            return ".to_edge(DOWN, buff=0.9)"
        code = re.sub(r'\.to_edge\(\s*DOWN\s*\)', patch_to_edge_down, code)

        def patch_to_edge_down_small_buff(match):
            buff_val = float(match.group(1))
            if buff_val < 0.9:
                fixes_applied.append(f"to_edge(DOWN, buff={buff_val}) -> buff=0.9")
                return ".to_edge(DOWN, buff=0.9)"
            return match.group(0)
        code = re.sub(
            r'\.to_edge\(\s*DOWN\s*,\s*buff\s*=\s*([\d.]+)\s*\)',
            patch_to_edge_down_small_buff, code
        )

        def patch_down_corner(match):
            corner = match.group(1)
            replacement = "UR" if corner == "DR" else "UL"
            fixes_applied.append(f"to_corner({corner}) -> to_corner({replacement})")
            return f".to_corner({replacement})"
        code = re.sub(r'\.to_corner\(\s*(DR|DL)\s*\)', patch_down_corner, code)

        def patch_down_shift(match):
            prefix = match.group(1)
            factor = float(match.group(2))
            if factor > 2.2:
                fixes_applied.append(f"{prefix}DOWN * {factor} -> DOWN * 2.0")
                return f"{prefix}DOWN * 2.0"
            return match.group(0)
        code = re.sub(
            r'(move_to\(|shift\(|\+\s*)DOWN\s*\*\s*([\d.]+)',
            patch_down_shift, code
        )

        # Fix 6: Manim CE v0.19 Code API — `code=` 关键字不存在，必须用 `code_string=`。
        # 负前瞻 `(?!_)` 避免把已经正确的 `code_string=` 再次替换。
        pattern_code_kwarg = re.compile(r'\bCode\(\s*code(?!_)\s*=')
        if pattern_code_kwarg.search(code):
            before_count = len(pattern_code_kwarg.findall(code))
            code = pattern_code_kwarg.sub('Code(code_string=', code)
            fixes_applied.append(
                f"Code(code=...) -> Code(code_string=...) x{before_count}"
            )

        # Fix 7: `<var>.code[i]` 在 Manim CE v0.19 里无效（`code` 属性不存在）；
        # 必须用 `<var>.code_lines[i]`。先识别哪些变量是 Code(...) 赋值得来的，
        # 再把对这些变量的 `.code[` 访问替换为 `.code_lines[`。
        code_vars = set(re.findall(r'(\w+)\s*=\s*Code\(', code))
        for var in code_vars:
            attr_pattern = re.compile(rf'\b{re.escape(var)}\.code\[')
            if attr_pattern.search(code):
                hits = len(attr_pattern.findall(code))
                code = attr_pattern.sub(f'{var}.code_lines[', code)
                fixes_applied.append(
                    f"{var}.code[i] -> {var}.code_lines[i] x{hits}"
                )

        if fixes_applied:
            self.logger.info(f"Layout fixes applied: {', '.join(fixes_applied)}")

        return code

    def _sanitize_class_name(self, scene_id: str) -> str:
        """Convert scene ID to valid Python class name"""
        # Remove invalid characters and convert to PascalCase
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', scene_id)
        # Capitalize first letter and ensure it starts with letter or underscore
        if sanitized and sanitized[0].isdigit():
            sanitized = "Scene_" + sanitized
        sanitized = sanitized.title().replace('_', '')

        # Ensure it's not empty
        if not sanitized:
            sanitized = "AnimationScene"

        return sanitized

    def _save_scene_code(
        self,
        scene_id: str,
        class_name: str,
        manim_code: str,
        raw_output: str,
        tag_suffix: Optional[str] = None,
    ) -> Path:
        """Save generated Manim code to file"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"{scene_id}_{class_name}"
        if tag_suffix:
            base = f"{base}_{tag_suffix}"
        filename = f"{base}_{timestamp}.py"
        filepath = self.output_dir / "scene_codes" / filename

        # Save both the clean code and raw output for debugging
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Generated Manim code for scene: {scene_id}\n")
            f.write(f"# Class: {class_name}\n")
            f.write(f"# Generated at: {timestamp}\n\n")
            f.write(manim_code)

        # Also save raw LLM output
        raw_filepath = filepath.with_suffix('.raw.txt')
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Raw LLM output for scene: {scene_id}\n")
            f.write(f"# Class: {class_name}\n")
            f.write(f"# Generated at: {timestamp}\n\n")
            f.write(raw_output)

        return filepath

    def _build_render_error_excerpt(
        self,
        stderr: Optional[str],
        stdout: Optional[str],
        max_chars: int = 3500,
    ) -> str:
        """Produce a compact error excerpt suitable for LLM context.

        We keep the tail of stderr (most recent traceback) and a small tail of
        stdout (for logger-formatted errors Manim sometimes writes there).
        """
        stderr = (stderr or "").strip()
        stdout = (stdout or "").strip()

        tail_chars = max_chars if not stdout else max(512, max_chars - 800)
        stderr_part = stderr[-tail_chars:] if stderr else ""
        stdout_part = stdout[-800:] if stdout else ""

        excerpt_parts: List[str] = []
        if stderr_part:
            excerpt_parts.append(f"--- STDERR (tail) ---\n{stderr_part}")
        if stdout_part:
            excerpt_parts.append(f"--- STDOUT (tail) ---\n{stdout_part}")
        if not excerpt_parts:
            return "(no output captured)"
        return "\n".join(excerpt_parts)

    def _fix_render_error_with_llm(
        self,
        current_code: str,
        class_name: str,
        scene_plan: Optional[ScenePlan],
        stderr: Optional[str],
        stdout: Optional[str],
    ) -> Optional[tuple[str, str]]:
        """Ask the LLM to fix a scene that crashed at render time.

        Returns (fixed_code, raw_response) on success, or None if the LLM did
        not produce extractable code.
        """
        try:
            scene_plan_json = (
                json.dumps(scene_plan.model_dump(), indent=2, ensure_ascii=False)
                if scene_plan
                else "{}"
            )
            error_output = self._build_render_error_excerpt(stderr, stdout)
            fix_prompt = self.RENDER_FIX_PROMPT.format(
                scene_plan=scene_plan_json,
                class_name=class_name,
                current_code=current_code,
                error_output=error_output,
            )
            response = self._call_llm(
                system_prompt=self._build_codegen_system_prompt(fix_prompt),
                user_message=(
                    "Return ONLY the full corrected Manim file in <manim>...</manim> tags."
                ),
                temperature=min(self.config.temperature, 0.3),
                max_retries=2,
            )
            fixed_code, extraction_method = self._extract_manim_code(response)
            if not fixed_code:
                self.logger.warning(
                    "Render-fix LLM returned no extractable <manim> code for %s",
                    class_name,
                )
                return None
            fixed_code = self._fix_layout_issues(fixed_code)
            self.logger.info(
                "Render-fix LLM produced candidate for %s (extracted via %s)",
                class_name,
                extraction_method,
            )
            return fixed_code, response
        except Exception as llm_exc:  # defensive: LLM call itself failed
            self.logger.warning(
                "Render-fix LLM call crashed for %s: %s", class_name, llm_exc
            )
            return None

    def _regenerate_scene_from_plan(
        self,
        scene_plan: ScenePlan,
        class_name: str,
    ) -> Optional[str]:
        """Tier 2: regenerate the full scene code from its original ScenePlan.

        Uses a conservative temperature when a Visual Contract is active so
        regenerated scenes do not drift from successful siblings.
        Falls back to the cached Visual Contract so the regenerated scene
        stays visually consistent with successful siblings.

        Returns the new Manim code string, or None if the LLM failed to
        produce extractable code.
        """
        try:
            base_temp = float(getattr(self.config, "temperature", 0.3) or 0.3)
            boost = float(getattr(self.config, "render_regen_temperature_boost", 0.3) or 0.0)
            if self._cached_visual_contract:
                boosted = min(base_temp, 0.25)
                boost = 0.0
            else:
                boosted = min(1.0, max(0.0, base_temp + boost))
            self.logger.info(
                "[Tier 2 REGEN] %s: regenerating from plan with temperature=%.2f "
                "(base=%.2f, boost=%.2f)",
                class_name,
                boosted,
                base_temp,
                boost,
            )
            sc = self._generate_one_scene_code(
                scene_plan=scene_plan,
                visual_contract=self._cached_visual_contract,
                temperature_override=boosted,
                save_suffix="regen",
            )
            if sc is None:
                self.logger.warning(
                    "[Tier 2 REGEN] %s: regeneration produced no extractable code",
                    class_name,
                )
                return None
            return sc.manim_code
        except Exception as exc:
            self.logger.warning(
                "[Tier 2 REGEN] %s: regeneration crashed: %s", class_name, exc
            )
            return None

    def _build_stub_scene_code(
        self,
        class_name: str,
        title: str,
        description: str,
    ) -> str:
        """Tier 3: build a deterministic placeholder VoiceoverScene.

        This scene never calls LLM-generated code; it simply shows ``title``
        and ``description`` on screen while narrating ``description`` via the
        configured TTS provider. Purpose: guarantee the final concatenated
        video keeps a slot for this scene (no scene lost) and the SRT/audio
        timeline stays aligned even when all LLM repair tiers fail.
        """
        voiceover_imports, tts_setup_snippet = self._build_voiceover_prompt_section()

        def _safe_literal(s: str) -> str:
            """Embed arbitrary user/LLM text into a Python triple-double-quoted string safely.

            Escapes backslashes first (so subsequent escapes are not re-escaped),
            then replaces every ``"`` with ``\\"``. That way no sequence of
            ``"`` characters can close the surrounding ``\"\"\"`` literal, no
            matter how many quotes the input contains.
            """
            if not s:
                return ""
            # Strip control chars; keep newlines/tabs + printable ASCII + non-Latin unicode.
            cleaned = "".join(
                ch if (ch == "\n" or ch == "\t" or 0x20 <= ord(ch) < 0x7F or ord(ch) >= 0xA0) else " "
                for ch in s
            )
            cleaned = cleaned.replace("\\", "\\\\").replace('"', '\\"')
            return cleaned

        title_safe = _safe_literal(title or "Scene")
        description_safe = _safe_literal(description or title or "Scene placeholder")

        # Keep voiceover text reasonable (TTS engines clip very long strings anyway).
        narration_safe = description_safe[:800] if description_safe else title_safe
        # On-screen description: cap length to avoid overflowing the frame.
        onscreen_description = description_safe[:240] if description_safe else ""

        return f'''import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim import *
from manim_voiceover import VoiceoverScene
{voiceover_imports}


class {class_name}(VoiceoverScene):
    """Auto-generated fallback stub: original scene code failed all repair tiers."""

    def construct(self):
        {tts_setup_snippet}

        title_text = """{title_safe}"""
        description_text = """{onscreen_description}"""
        narration_text = """{narration_safe}"""

        title_mobject = Text(title_text, font_size=52, weight=BOLD).to_edge(UP, buff=1.0)

        description_mobject = None
        if description_text.strip():
            description_mobject = Text(
                description_text,
                font_size=28,
                line_spacing=1.2,
            )
            # Wrap long lines manually to keep width within the frame.
            if description_mobject.width > config.frame_width - 1.5:
                description_mobject.scale((config.frame_width - 1.5) / description_mobject.width)
            description_mobject.next_to(title_mobject, DOWN, buff=0.8)

        with self.voiceover(text=narration_text) as tracker:
            total_duration = max(1.0, float(tracker.duration or 1.0))
            reveal_time = min(2.0, max(0.6, total_duration * 0.3))
            self.play(Write(title_mobject), run_time=reveal_time)
            consumed = reveal_time
            if description_mobject is not None:
                fade_time = min(2.0, max(0.5, total_duration * 0.3))
                self.play(FadeIn(description_mobject, shift=UP * 0.2), run_time=fade_time)
                consumed += fade_time
            remaining = max(0.1, total_duration - consumed)
            self.wait(remaining)

        fadeout_targets = [title_mobject]
        if description_mobject is not None:
            fadeout_targets.append(description_mobject)
        self.play(*[FadeOut(m) for m in fadeout_targets], run_time=0.5)
'''

    def _render_with_repair_chain(
        self,
        scene_code: ManimSceneCode,
        scene_plan: Optional[ScenePlan],
        output_filename: str,
        disable_auto_repair: bool = False,
        render_quality: Optional[str] = None,
    ) -> RenderResult:
        """Render a single scene with the full Tier 1 → 2 → 3 repair chain.

        Tier 1: LLM patch fix (``RENDER_FIX_PROMPT``), up to ``render_fix_max_attempts``.
        Tier 2: Regenerate the whole scene from its ``ScenePlan`` with boosted temperature.
                Followed by one additional Tier-1-style patch attempt if needed.
        Tier 3: Build a deterministic stub scene (title + description + voiceover)
                so the final video never loses a slot.

        Returns a ``RenderResult`` (Pydantic) with ``success`` reflecting the
        eventual render outcome. When Tier 3 is engaged, ``error_message`` is
        prefixed with ``"fallback_stub: "`` so downstream consumers can detect
        the substitution without extra metadata.
        """
        fix_enabled = bool(getattr(self.config, "render_fix_enabled", True))
        fix_max_attempts = int(getattr(self.config, "render_fix_max_attempts", 2))
        regen_enabled = bool(getattr(self.config, "render_regen_enabled", True))
        stub_enabled = bool(getattr(self.config, "render_stub_enabled", True))

        # 重新渲染（rerender）时关闭全部自动修复，仅保留首渲。
        # Tier 1（补丁修复）/ Tier 2（整段重生成）会调用 LLM 花 token；
        # Tier 3（占位兜底）也一并关闭——rerender 渲染失败直接返回错误、由上层中止渲染。
        if disable_auto_repair:
            if fix_enabled or regen_enabled or stub_enabled:
                self.logger.info(
                    f"[Worker] 🔕 rerender 模式：已关闭全部自动修复（Tier 1/2/3），"
                    f"{scene_code.scene_name} 渲染失败将直接抛错并取消渲染"
                )
            fix_enabled = False
            regen_enabled = False
            stub_enabled = False

        current_code = scene_code.manim_code
        class_name = scene_code.scene_name
        scene_id = scene_code.scene_id

        def _do_render(code: str):
            """Run the underlying Manim render and catch subprocess exceptions."""
            try:
                return self.renderer.render(
                    manim_code=code,
                    scene_name=class_name,
                    output_filename=output_filename,
                    quality=render_quality,
                ), None
            except Exception as exc:
                self.logger.error(f"[Worker] ❌ 渲染异常: {class_name}: {exc}")
                return None, str(exc)

        # ---------- Tier 1: initial render + LLM patch fix loop ----------
        total_attempts = 1 + (fix_max_attempts if fix_enabled else 0)
        render_result = None
        render_exc: Optional[str] = None
        for fix_round in range(total_attempts):
            render_result, render_exc = _do_render(current_code)
            if render_exc is not None:
                # Hard subprocess crash — skip straight to Tier 2/3.
                render_result = None
                break

            if render_result.success:
                break

            if fix_round >= total_attempts - 1:
                self.logger.error(
                    f"[Worker] ❌ Tier 1 耗尽: {class_name}: "
                    f"{render_result.error_message} (已尝试 {fix_round + 1} 轮，含 {fix_round} 轮 LLM 修复)"
                )
                break

            self.logger.warning(
                f"[Worker] [Tier 1 FIX] 渲染失败，准备 LLM 修复 ({fix_round + 1}/{fix_max_attempts}): "
                f"{class_name}: {render_result.error_message}"
            )
            fix_outcome = self._fix_render_error_with_llm(
                current_code=current_code,
                class_name=class_name,
                scene_plan=scene_plan,
                stderr=render_result.stderr,
                stdout=render_result.stdout,
            )
            if not fix_outcome:
                self.logger.error(
                    f"[Worker] [Tier 1 FIX] LLM 修复未产出可用代码，停止重试: {class_name}"
                )
                break

            fixed_code, raw_response = fix_outcome
            if fixed_code.strip() == current_code.strip():
                self.logger.warning(
                    f"[Worker] [Tier 1 FIX] LLM 修复返回的代码与原代码相同，停止重试: {class_name}"
                )
                break

            # 让 Tier 1 修复输出也走 Visual Contract 组装，确保 LLM 即便重写了
            # 基类/共享常量/imports，最终文件仍与其他场景保持 header 与共享数据一致。
            fixed_code = self._reapply_visual_contract(fixed_code, class_name)
            current_code = fixed_code
            try:
                self._save_scene_code(
                    scene_id=scene_id,
                    class_name=class_name,
                    manim_code=current_code,
                    raw_output=raw_response,
                    tag_suffix=f"renderfix{fix_round + 1}",
                )
            except Exception as save_exc:
                self.logger.debug(
                    f"Failed to persist render-fix code for {class_name}: {save_exc}"
                )

        if render_result is not None and render_result.success:
            return self._wrap_render_ok(scene_id, render_result)

        tier1_error = (render_result.error_message if render_result else render_exc) or "unknown"

        # ---------- Tier 2: regenerate the full scene from its plan ----------
        # Require a real (non-synthetic) ScenePlan: at minimum it must carry
        # actions, otherwise regenerating yields nothing useful. Rerender
        # scenes — which have no plan — go straight to Tier 3.
        has_real_plan = (
            scene_plan is not None
            and getattr(scene_plan, "actions", None)
            and len(scene_plan.actions) > 0
        )
        if regen_enabled and has_real_plan:
            self.logger.warning(
                "[Tier 2 REGEN] %s: Tier 1 耗尽，启动整段重生成。上轮错误: %s",
                class_name,
                tier1_error[:300],
            )
            regen_code = self._regenerate_scene_from_plan(scene_plan, class_name)
            if regen_code and regen_code.strip() and regen_code.strip() != current_code.strip():
                current_code = regen_code
                render_result, render_exc = _do_render(current_code)
                if render_result is not None and render_result.success:
                    self.logger.info(
                        "[Tier 2 REGEN] ✅ %s: 重生成后渲染成功", class_name
                    )
                    return self._wrap_render_ok(
                        scene_id, render_result,
                        tier_prefix="tier2_regen: succeeded after prior failures",
                    )
                # One bonus Tier-1-style patch round on the regenerated code.
                if render_result is not None and not render_result.success and fix_enabled:
                    self.logger.warning(
                        "[Tier 2 REGEN] %s: 重生成后仍失败，尝试一轮 LLM 补丁: %s",
                        class_name,
                        render_result.error_message,
                    )
                    fix_outcome = self._fix_render_error_with_llm(
                        current_code=current_code,
                        class_name=class_name,
                        scene_plan=scene_plan,
                        stderr=render_result.stderr,
                        stdout=render_result.stdout,
                    )
                    if fix_outcome:
                        fixed_code, raw_response = fix_outcome
                        if fixed_code.strip() and fixed_code.strip() != current_code.strip():
                            fixed_code = self._reapply_visual_contract(fixed_code, class_name)
                            current_code = fixed_code
                            try:
                                self._save_scene_code(
                                    scene_id=scene_id,
                                    class_name=class_name,
                                    manim_code=current_code,
                                    raw_output=raw_response,
                                    tag_suffix="regen_fix",
                                )
                            except Exception as save_exc:
                                self.logger.debug(
                                    f"Failed to persist regen_fix code for {class_name}: {save_exc}"
                                )
                            render_result, render_exc = _do_render(current_code)
                            if render_result is not None and render_result.success:
                                self.logger.info(
                                    "[Tier 2 REGEN] ✅ %s: 补丁修复后渲染成功", class_name
                                )
                                return self._wrap_render_ok(
                                    scene_id, render_result,
                                    tier_prefix="tier2_regen: succeeded after prior failures",
                                )
                self.logger.error(
                    "[Tier 2 REGEN] ❌ %s: 重生成路径仍失败: %s",
                    class_name,
                    (render_result.error_message if render_result else render_exc) or "unknown",
                )
            else:
                self.logger.warning(
                    "[Tier 2 REGEN] %s: 重生成未产出新代码或与原代码相同，跳过",
                    class_name,
                )
        elif regen_enabled and not has_real_plan:
            self.logger.info(
                "[Tier 2 REGEN] %s: 无有效 ScenePlan（rerender 场景）跳过重生成", class_name
            )

        last_error = (render_result.error_message if render_result else render_exc) or tier1_error

        # ---------- Tier 3: deterministic stub scene ----------
        if stub_enabled:
            # Resolve title/description from whatever context we have.
            if scene_plan is not None:
                stub_title = scene_plan.title or class_name
                stub_description = scene_plan.description or scene_plan.title or class_name
            else:
                stub_title = class_name
                stub_description = f"Scene {class_name} (content unavailable)."

            self.logger.warning(
                "[Tier 3 STUB] %s: 启用占位场景兜底。前面错误: %s",
                class_name,
                (last_error or "unknown")[:300],
            )
            stub_code = self._build_stub_scene_code(
                class_name=class_name,
                title=stub_title,
                description=stub_description,
            )
            try:
                self._save_scene_code(
                    scene_id=scene_id,
                    class_name=class_name,
                    manim_code=stub_code,
                    raw_output="<deterministic stub>",
                    tag_suffix="stub",
                )
            except Exception as save_exc:
                self.logger.debug(
                    f"Failed to persist stub scene for {class_name}: {save_exc}"
                )
            stub_result, stub_exc = _do_render(stub_code)
            if stub_result is not None and stub_result.success:
                self.logger.info(
                    "[Tier 3 STUB] ✅ %s: 占位场景渲染成功 (duration=%.2fs)",
                    class_name,
                    stub_result.duration or 0.0,
                )
                return RenderResult(
                    scene_id=scene_id,
                    success=True,
                    video_path=stub_result.video_path,
                    error_message=f"fallback_stub: {last_error}",
                    duration=stub_result.duration,
                    resolution=stub_result.resolution,
                    render_time=stub_result.render_time,
                    subtitle_path=stub_result.subtitle_path,
                )

            # If even the stub cannot render (extremely unusual — broken Manim
            # install or missing TTS), fall through to the failure path below.
            stub_err = (stub_result.error_message if stub_result else stub_exc) or "unknown"
            self.logger.error(
                "[Tier 3 STUB] ❌ %s: 占位场景也渲染失败: %s",
                class_name,
                stub_err,
            )
            last_error = f"stub_render_failed: {stub_err} (prior: {last_error})"

        # Final failure — every tier exhausted. The upstream loop records this
        # as a failed scene; the concat step will skip it.
        return RenderResult(
            scene_id=scene_id,
            success=False,
            error_message=last_error or "unknown render failure",
        )

    def _wrap_render_ok(
        self,
        scene_id: str,
        render_result,
        tier_prefix: Optional[str] = None,
    ) -> RenderResult:
        """Convert the low-level RenderResult dataclass into the Pydantic model."""
        if render_result.success:
            self.logger.info(
                "[Worker] ✅ 渲染成功: %s (%.2fs, 耗时 %.1fs)",
                scene_id,
                render_result.duration or 0.0,
                render_result.render_time or 0.0,
            )
        return RenderResult(
            scene_id=scene_id,
            success=render_result.success,
            video_path=render_result.video_path,
            error_message=(
                tier_prefix
                if tier_prefix and render_result.success
                else render_result.error_message
            ),
            duration=render_result.duration,
            resolution=render_result.resolution,
            render_time=render_result.render_time,
            subtitle_path=render_result.subtitle_path,
        )

    def render_single_with_repair(
        self,
        code: str,
        class_name: str,
        output_filename: str,
        scene_id: Optional[str] = None,
        scene_plan: Optional[ScenePlan] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        disable_auto_repair: bool = False,
        render_quality: Optional[str] = None,
    ) -> RenderResult:
        """Public entry point for repairing + rendering a single scene.

        Used by ``pipeline.rerender`` so the re-render path shares the same
        Tier 1 + (Tier 2 if plan available) + Tier 3 safety net.

        Args:
            code: Complete Manim source code (including imports + voiceover setup).
            class_name: Name of the ``Scene`` subclass to render.
            output_filename: Desired mp4 filename (under the renderer's output dir).
            scene_id: Identifier used for artifact filenames; defaults to ``class_name``.
            scene_plan: Original plan if available (enables Tier 2); pass ``None``
                for rerender where no plan exists.
            title / description: Optional overrides for the Tier 3 stub fallback.
                If both ``scene_plan`` and these are ``None``, the stub uses
                ``class_name`` plus a generic description.
            disable_auto_repair: When ``True`` (used by the rerender path), skip
                the entire repair chain — Tier 1/2 (token-costing LLM repair)
                and Tier 3 (stub fallback). A failed render returns a
                ``RenderResult`` with ``success=False`` so the caller can abort.
                First-time generation leaves this ``False`` so auto-repair and
                the stub safety net stay active.
        """
        effective_id = scene_id or class_name
        sc = ManimSceneCode(
            scene_id=effective_id,
            scene_name=class_name,
            manim_code=code,
            raw_llm_output="",
            extraction_method="external",
        )

        # If caller provided title/description but no ScenePlan, synthesize a
        # lightweight ScenePlan-like object so the stub fallback has content.
        synthetic_plan: Optional[ScenePlan] = scene_plan
        if synthetic_plan is None and (title or description):
            try:
                synthetic_plan = ScenePlan(
                    id=effective_id,
                    title=title or class_name,
                    description=description or class_name,
                    sub_concept_id=effective_id,
                    actions=[],
                    scene_dependencies=[],
                )
            except Exception:
                synthetic_plan = None

        return self._render_with_repair_chain(
            scene_code=sc,
            scene_plan=synthetic_plan,
            output_filename=output_filename,
            disable_auto_repair=disable_auto_repair,
            render_quality=render_quality,
        )

    def _render_scenes(
        self,
        scene_codes: List[ManimSceneCode],
        scene_plans: Optional[List[ScenePlan]] = None,
        render_quality: Optional[str] = None,
    ) -> List[RenderResult]:
        """Render scenes in parallel using multiple CPU cores.

        render_quality: 逐次质量覆盖（首次生成默认 "l" 走低质量快速预览）。为 None 时
        回退到渲染器默认质量（settings.manim_quality）。
        """

        if not scene_codes:
            return []

        # ========== 检测 CPU 核心数，确定并行度 ==========
        cpu_count = os.cpu_count() or 1
        # 保留 1 核给系统，至少使用 1 个 worker
        max_workers = max(1, min(cpu_count - 1, len(scene_codes)))
        self.logger.info(
            f"并行渲染策略：检测到 {cpu_count} 个 CPU 核心，"
            f"使用 {max_workers} 个 worker 并行渲染 {len(scene_codes)} 个场景"
        )

        plan_by_id: Dict[str, ScenePlan] = {p.id: p for p in (scene_plans or [])}
        if self._continuous_scene_plan is not None:
            plan_by_id[self._continuous_scene_plan.id] = self._continuous_scene_plan

        # 使用字典保持场景顺序：{scene_id: (index, result)}
        results_map: Dict[str, tuple] = {}

        def render_single(index_and_scene):
            """渲染单个场景（在线程中执行），完整走 Tier 1 → Tier 2 → Tier 3 修复链。"""
            index, scene_code = index_and_scene
            self.logger.info(
                f"[Worker] 开始渲染场景 ({index + 1}/{len(scene_codes)}): {scene_code.scene_name}"
            )
            scene_plan = plan_by_id.get(scene_code.scene_id)
            result = self._render_with_repair_chain(
                scene_code=scene_code,
                scene_plan=scene_plan,
                output_filename=f"{scene_code.scene_id}_{scene_code.scene_name}.mp4",
                render_quality=render_quality,
            )
            return index, result

        # ========== 并行渲染 ==========
        start_time = time.time()
        indexed_scenes = list(enumerate(scene_codes))

        # 使用线程池（而非进程池），因为实际渲染在 subprocess 中进行
        # 线程池避免了序列化开销，且 subprocess 天然绕过 GIL
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(render_single, item): item 
                for item in indexed_scenes
            }

            for future in as_completed(futures):
                try:
                    index, result = future.result()
                    results_map[index] = result
                except Exception as e:
                    item = futures[future]
                    idx, sc = item
                    self.logger.error(f"[Worker] 并行渲染异常: {sc.scene_name}: {e}")
                    results_map[idx] = RenderResult(
                        scene_id=sc.scene_id,
                        success=False,
                        error_message=str(e)
                    )

        # ========== 按原始顺序组装结果 ==========
        render_results = [results_map[i] for i in range(len(scene_codes))]

        total_time = time.time() - start_time
        success_count = sum(1 for r in render_results if r.success)
        self.logger.info(
            f"并行渲染完成：{success_count}/{len(scene_codes)} 成功，"
            f"总耗时 {total_time:.1f}s（{max_workers} worker 并行）"
        )

        return render_results

    def _concatenate_scenes(self, render_results: List[RenderResult]) -> Optional[Path]:
        """Concatenate rendered scenes into single silent animation.

        Uses FFmpeg's ``concat`` filter (not the demuxer) so each scene's audio
        is explicitly padded (``apad``) to match that scene's video duration.
        This prevents per-scene audio-shorter-than-video gaps from being
        collapsed by the demuxer, which otherwise causes scene N+1 audio to
        leak backward into scene N's video tail.
        """

        if not render_results:
            self.logger.error("No render results to concatenate")
            return None

        video_paths: List[Path] = []
        for r in render_results:
            if r.success and r.video_path:
                video_path = Path(r.video_path)
                if not video_path.is_absolute():
                    video_path = (Path.cwd() / video_path).resolve()
                if video_path.exists():
                    video_paths.append(video_path)
                else:
                    self.logger.warning(f"Video path does not exist: {video_path}")

        if not video_paths:
            self.logger.error("No successfully rendered scenes with valid video paths to concatenate")
            self.logger.error(f"Render results: {[(r.scene_id, r.success, r.video_path) for r in render_results]}")
            return None

        self.logger.info(f"Found {len(video_paths)} videos to concatenate")

        try:
            # 微秒精度：两次重渲染落在同一秒会撞同一个中间文件名，而这条 ffmpeg
            # 命令带 -y，会直接覆盖另一次运行正在使用的产物。
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            output_filename = f"animation_{timestamp}.mp4"
            output_path = self.output_dir / "animations" / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)

            scene_durations: List[float] = []
            for video_path in video_paths:
                duration = self._probe_video_duration(video_path)
                if duration is None or duration <= 0:
                    self.logger.error(f"Unable to probe duration for {video_path}")
                    return None
                scene_durations.append(duration)

            # Hard guard: every scene MUST have an audio stream here. The
            # ManimRenderer already fails the render when voiceover didn't
            # produce audio, so hitting this branch indicates an upstream
            # regression; fail loudly rather than silently inserting silence.
            scene_has_audio: List[bool] = [
                self._has_audio_stream(vp) for vp in video_paths
            ]
            missing_audio = [
                str(video_paths[i]) for i, ok in enumerate(scene_has_audio) if not ok
            ]
            if missing_audio:
                self.logger.error(
                    "Refusing to concatenate: the following scenes have no "
                    "audio stream (voiceover missing). Silent output is "
                    "disallowed by policy. Offending scenes: %s",
                    missing_audio,
                )
                return None

            filter_parts: List[str] = []
            concat_inputs: List[str] = []
            for index, duration in enumerate(scene_durations):
                # setpts + asetpts reset timestamps; apad + atrim pin audio to
                # the exact video duration so A/V never drifts across scenes.
                filter_parts.append(f"[{index}:v]setpts=PTS-STARTPTS[v{index}]")
                filter_parts.append(
                    f"[{index}:a]aresample=async=1:first_pts=0,"
                    f"apad,atrim=0:{duration:.6f},asetpts=PTS-STARTPTS[a{index}]"
                )
                concat_inputs.append(f"[v{index}][a{index}]")

            concat_expr = "".join(concat_inputs) + f"concat=n={len(scene_durations)}:v=1:a=1[v][a]"
            filter_complex = ";".join(filter_parts + [concat_expr])

            cmd: List[str] = ["ffmpeg"]
            for video_path in video_paths:
                cmd.extend(["-i", str(video_path.resolve())])

            if len(video_paths) == 1:
                # Single scene: concat=n=1 is an identity operation on the video
                # stream, which Manim already wrote in exactly the target format
                # (h264 / yuv420p / the requested quality preset). Decoding and
                # re-encoding it costs ~11s of the ~18s this pass used to take
                # and changes nothing, so stream-copy the video instead.
                #
                # The AUDIO filter chain must stay. Manim's mp4 carries an audio
                # track ~1.9s shorter than its video (measured on every scene
                # file), and VideoCompositor runs with -shortest downstream, so
                # handing it an unpadded track silently truncates the tail of
                # the final video. apad/atrim pins audio to the video duration.
                cmd.extend([
                    "-filter_complex",
                    f"[0:a]aresample=async=1:first_pts=0,apad,"
                    f"atrim=0:{scene_durations[0]:.6f},asetpts=PTS-STARTPTS[a]",
                    "-map", "0:v",
                    "-map", "[a]",
                    "-c:v", "copy",
                    "-c:a", _fast_aac_encoder(),
                    "-b:a", settings.audio_bitrate,
                    "-movflags", "+faststart",
                    "-y",
                    str(output_path.resolve()),
                ])
            else:
                cmd.extend([
                    "-filter_complex", filter_complex,
                    "-map", "[v]",
                    "-map", "[a]",
                    "-c:v", settings.video_codec,
                    "-preset", settings.video_preset,
                    "-crf", str(settings.video_crf),
                    "-pix_fmt", "yuv420p",
                    "-c:a", settings.audio_codec,
                    "-b:a", settings.audio_bitrate,
                    "-movflags", "+faststart",
                    "-y",
                    str(output_path.resolve()),
                ])

            self.logger.info(
                "Running FFmpeg command (concat filter with per-scene apad): %s",
                " ".join(cmd),
            )

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=max(120, int(sum(scene_durations) * 3) + 60),
            )

            if result.returncode == 0 and output_path.exists():
                self.logger.info(f"Successfully concatenated animation: {output_filename}")
                self.logger.info(f"Final video path: {output_path}")
                return output_path

            self.logger.error(f"FFmpeg concatenation failed with return code {result.returncode}")
            self.logger.error(f"STDERR: {result.stderr}")
            self.logger.error(f"STDOUT: {result.stdout}")
            return None

        except Exception as e:
            self.logger.error(f"Scene concatenation failed: {e}")
            return None

    def _has_audio_stream(self, video_path: Path) -> bool:
        """Return True iff the given media file exposes at least one audio stream."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-select_streams", "a",
                    "-show_entries", "stream=index",
                    "-of", "csv=p=0",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
            if result.returncode != 0:
                return False
            return bool(result.stdout.strip())
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def _probe_video_duration(self, video_path: Path) -> Optional[float]:
        """Return the v:0 stream duration (seconds) for a given mp4 path."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
            if result.returncode != 0:
                return None
            text = result.stdout.strip()
            return float(text) if text else None
        except (subprocess.TimeoutExpired, ValueError, subprocess.SubprocessError):
            return None

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about animation generation performance"""
        return {
            "token_usage": self.get_token_usage(),
            "model_used": self.model,
            "reasoning_tokens": self.reasoning_tokens,
            "config": self.config.model_dump(),
            "renderer_status": "ready" if self.renderer.validate_manim_installation() else "not_ready"
        }