"""Knowledge Curator Agent.

Takes raw, human-authored algorithm materials (four sections: title, steps,
code, analysis) and rewrites them into an animation-ready knowledge document
that mirrors the structure of ``test_knowledge.txt`` (the project's reference
example known to produce good animations).

The curator exists because raw textbook-style materials tend to have four
systematic gaps that hurt the downstream animation pipeline:

1. The code listing includes I/O, ``main``, struct declarations, etc., which
   dilutes the LLM's focus on the core function that actually needs line-by-
   line tracing.
2. No concrete example data, so the animator cannot show step-by-step
   concrete state transitions.
3. No explicit "animation requirements" (which data structures to visualize,
   how to highlight code lines, how to break the video into scenes).
4. Steps phrased in abstract recursive/mathematical language instead of
   concrete visual actions ("pointer moves to left child" vs "recurse on the
   left subtree").

The agent's job is to close all four gaps in a single LLM call, emitting a
structured JSON object that is then rendered to Markdown with the same
headings as the reference document.
"""

from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel, Field

from agents.base import BaseAgent


class SceneOutline(BaseModel):
    """A single scene in the scene breakdown."""

    title: str
    goal: str


class ConcreteExample(BaseModel):
    """A concrete example instance used to drive the animation."""

    input: str = Field(description="Concrete input data (small, visualizable)")
    expected_output: str = Field(description="Expected output / trace result")
    diagram_hint: str = Field(
        default="",
        description="Optional ASCII / textual hint for the initial diagram",
    )


class AnimationRequirements(BaseModel):
    """Explicit, actionable animation requirements."""

    data_structures_to_visualize: List[str] = Field(default_factory=list)
    code_tracing_rules: List[str] = Field(default_factory=list)
    scene_breakdown: List[SceneOutline] = Field(default_factory=list)


class CuratedKnowledge(BaseModel):
    """The structured curated output produced by the LLM."""

    title: str
    algorithm_description: str = Field(
        default="",
        description=(
            "A short, narration-ready overview of the algorithm in 2-4"
            " sentences. This is read aloud over the opening scene of the"
            " video while the title and the complete data structure are"
            " already on screen. It should answer: what the algorithm does,"
            " on what data structure, and the core idea / key invariant —"
            " NO step-by-step trace, NO code references."
        ),
    )
    visual_steps: List[str] = Field(
        description=(
            "Steps rewritten as concrete, visualizable actions. Preserve any"
            " numbering markers (e.g. '①', '(a)') present in the source."
        )
    )
    core_code: str = Field(
        description=(
            "Only the core function(s) that need to be traced on screen."
            " Boilerplate (includes, struct definitions, main, I/O, helpers"
            " like tree-building) MUST be removed. Inline comments should"
            " reference the numbered steps above."
        )
    )
    concrete_example: ConcreteExample
    animation_requirements: AnimationRequirements
    complexity_analysis: str = Field(
        description="Lightly voiced-over rewrite of the original analysis."
    )


def format_curated_to_markdown(curated: CuratedKnowledge) -> str:
    """Render a :class:`CuratedKnowledge` as a Markdown document.

    The output is intentionally shaped like ``test_knowledge.txt`` so that
    the existing pipeline (concept interpreter + script generator) can consume
    it without any changes.
    """
    title = curated.title.strip()

    steps_section = "\n".join(step.strip() for step in curated.visual_steps)

    code_block = curated.core_code.strip()
    # Heuristically detect language tag for the fenced code block.
    lang = ""
    if re.search(r"\b(void|int|struct|class|typedef|cout|cin)\b", code_block):
        lang = "cpp"
    elif re.search(r"\bdef\s+\w+\s*\(", code_block):
        lang = "python"
    code_section = f"```{lang}\n{code_block}\n```"

    ex = curated.concrete_example
    ds_lines = "\n".join(
        f"   - {item.strip()}" for item in curated.animation_requirements.data_structures_to_visualize
    )
    trace_lines = "\n".join(
        f"   - {item.strip()}" for item in curated.animation_requirements.code_tracing_rules
    )
    scene_lines = "\n".join(
        f"   - 场景{i + 1}：{s.title.strip()} —— {s.goal.strip()}"
        for i, s in enumerate(curated.animation_requirements.scene_breakdown)
    )

    example_block_lines = [
        f"1. 具体示例：输入 `{ex.input.strip()}`，期望输出 `{ex.expected_output.strip()}`。",
    ]
    if ex.diagram_hint.strip():
        example_block_lines.append(f"   初始图示提示：{ex.diagram_hint.strip()}")

    animation_section = (
        "\n".join(example_block_lines)
        + "\n2. 需要可视化的数据结构（在动画中始终保持可见并实时更新）：\n"
        + ds_lines
        + "\n3. 代码跟踪要求：\n"
        + trace_lines
        + "\n4. 场景划分建议：\n"
        + scene_lines
    )

    analysis_section = curated.complexity_analysis.strip()

    description_section = curated.algorithm_description.strip()
    description_block = (
        f"#### {title}的算法简介\n\n"
        f"{description_section}\n\n\n"
        if description_section
        else ""
    )

    return (
        f"{description_block}"
        f"#### {title}的算法步骤\n\n"
        f"{steps_section}\n\n\n"
        f"#### {title}的核心代码\n\n"
        f"注意：下面的代码是核心函数片段，动画需要逐行跟踪代码执行过程，展示每个变量的变化。\n\n"
        f"{code_section}\n\n\n"
        f"#### 动画要求（非常重要）\n\n"
        f"{animation_section}\n\n\n"
        f"#### {title}的算法分析\n\n"
        f"{analysis_section}\n"
    )


class KnowledgeCuratorAgent(BaseAgent):
    """LLM agent that rewrites raw algorithm materials into animation-ready docs."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        reasoning_tokens: Optional[float] = None,
        reasoning_effort: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 16384,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            reasoning_tokens=reasoning_tokens,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
        )
        self.temperature = temperature

    SYSTEM_PROMPT = """
You are the Knowledge Curator Agent in an AI-powered STEM animation pipeline.

YOUR INPUT
The user supplies FOUR sections of raw, textbook-style material for a single
data-structure / algorithm topic:
  1) Algorithm title
  2) Algorithm steps (often written in abstract / recursive language)
  3) Algorithm code (usually a full compilable program, including I/O, main,
     struct declarations, helper builders, etc.)
  4) Algorithm analysis (time / space complexity)

YOUR JOB
Rewrite these four sections into an ANIMATION-READY knowledge document that a
downstream Manim-based animation agent can consume. You MUST close FIVE
systematic gaps found in raw materials:

GAP 0 — Write a SHORT ALGORITHM DESCRIPTION (for the opening scene narration)
- EXACTLY 3 to 4 sentences. Each sentence MUST end with proper terminal
  punctuation: `。`/`！`/`？` for Chinese, `.`/`!`/`?` for English. NO em
  dashes, NO ellipses, NO mid-sentence line breaks. The downstream pipeline
  SPLITS this paragraph on those terminal marks into individual subtitle
  entries, so each sentence appears on screen one at a time.
- Each sentence should be SHORT and self-contained:
  * Chinese: ≤ ~28 characters per sentence.
  * English: ≤ ~12 words per sentence.
  Prefer 4 short sentences over 2 long compound sentences.
- It MUST answer: (a) what the algorithm does, (b) on what data structure /
  problem setting, and (c) the core idea or key invariant in one line.
- It MUST NOT: enumerate step-by-step actions, reference code lines, use code
  identifiers, contain bullet lists, repeat the title verbatim, or use
  semicolons / commas to chain what should be separate sentences.
- The TTS engine reads this aloud over the opening scene while the title and
  complete data structure are already on screen.
- Put it in the `algorithm_description` field as ONE paragraph (no manual
  newlines inside it — the splitter uses punctuation, not line breaks).

GAP 1 — Extract the CORE function(s) from the code
- Keep only the function that will be line-by-line traced on screen
  (e.g. `InOrderTraverse`, `ShortestPath_DIJ`, `QuickSort`).
- REMOVE: `#include`, `using namespace`, full struct/class declarations,
  `main()`, I/O (cin/cout/scanf/printf), helper tree/graph builders, test
  harness. If a tiny typedef is essential for reading the core function,
  inline it as a short comment.
- Preserve the original function signature and body exactly; do NOT rewrite
  logic.
- Add short inline comments on key lines that reference the step numbers
  produced in `visual_steps` (e.g. `// 第②(a)步：递归进入左子树`).

GAP 2 — Produce a CONCRETE example
- Pick a small, visualizable instance (small array, 3–8 node tree, 4–6 vertex
  graph). If the raw material already provides one, reuse it. Otherwise
  invent a minimal example that exercises all code paths of the core
  function.
- Provide `input`, `expected_output`, and an optional `diagram_hint` (ASCII
  sketch or brief textual layout).

GAP 3 — Write explicit ANIMATION REQUIREMENTS
- `data_structures_to_visualize`: list every on-screen structure that must
  stay visible and update in real time (e.g. the graph drawing, the `D[]`
  array, the recursion stack, the output sequence). Be concrete and
  exhaustive.
- `code_tracing_rules`: list rules for synchronizing the highlighted code
  line with the data-structure panel updates (e.g. "highlight the current
  line in yellow", "pulse a node when it is visited", "turn an edge red when
  relaxation updates it").
- `scene_breakdown`: 3–6 scenes that follow the pedagogical arc
  INTRO → DATA STRUCTURES / INIT → MAIN LOOP or RECURSION (1–2 iterations) →
  COMPLETION & VERIFICATION → COMPLEXITY. Each scene has a `title` and a
  one-line `goal`.

GAP 4 — Rewrite steps as CONCRETE VISUAL ACTIONS
- Translate abstract recursive language ("inorder-traverse the left subtree")
  into concrete pointer / stack / array actions that can literally be drawn
  ("move the current-node pointer down to its left child and push the parent
  onto the recursion-stack panel").
- Preserve the original step numbering markers (e.g. `①②③`, `(a)(b)(c)`)
  so the inline code comments can reference them.

STYLE
- Keep text tight. Prefer short, imperative sentences.
- Do not introduce variants or related topics. Stay strictly on the algorithm
  given.
- Every sentence in `visual_steps` and every item in `animation_requirements`
  should imply a concrete on-screen action.

OUTPUT FORMAT (Strict)
Return ONLY valid JSON matching exactly this schema (no extra text, no
backticks, no commentary):
{
  "title": "string",
  "algorithm_description": "string (2-4 sentence overview for opening narration)",
  "visual_steps": ["string", ...],
  "core_code": "string (only the core function body, with inline step-ref comments)",
  "concrete_example": {
    "input": "string",
    "expected_output": "string",
    "diagram_hint": "string"
  },
  "animation_requirements": {
    "data_structures_to_visualize": ["string", ...],
    "code_tracing_rules": ["string", ...],
    "scene_breakdown": [
      {"title": "string", "goal": "string"}
    ]
  },
  "complexity_analysis": "string"
}
"""

    _LANGUAGE_DIRECTIVE_TEMPLATE = (
        "LANGUAGE DIRECTIVE (HARD - OVERRIDES EVERYTHING ELSE)\n"
        "- target_language = {target_language}\n"
        "- All human-readable fields MUST be written in {target_language}:\n"
        "  title, algorithm_description, visual_steps,\n"
        "  concrete_example.diagram_hint,\n"
        "  animation_requirements.data_structures_to_visualize,\n"
        "  animation_requirements.code_tracing_rules,\n"
        "  animation_requirements.scene_breakdown[*].title / goal,\n"
        "  complexity_analysis.\n"
        "- `core_code` MUST preserve the original programming language of the\n"
        "  source; only the INLINE COMMENTS inside the code should follow\n"
        "  {target_language}.\n"
        "- `concrete_example.input` and `concrete_example.expected_output` are\n"
        "  raw data strings; keep them in their natural notation (numbers,\n"
        "  symbols). Do not translate symbols into words.\n"
        "- When {target_language} is Chinese, do NOT include English\n"
        "  translations in parentheses.\n"
        "\n"
    )

    def _build_system_prompt(self, target_language: str) -> str:
        directive = self._LANGUAGE_DIRECTIVE_TEMPLATE.format(
            target_language=target_language
        )
        return directive + self.SYSTEM_PROMPT

    def _sanitize(self, text: str) -> str:
        if text is None:
            return ""
        return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text).strip()

    def execute(
        self,
        raw_title: str,
        raw_steps: str,
        raw_code: str,
        raw_analysis: str,
        target_language: str = "Chinese",
        example_hint: Optional[str] = None,
    ) -> CuratedKnowledge:
        """Curate raw algorithm materials into structured animation-ready form."""
        raw_title = self._sanitize(raw_title)
        raw_steps = self._sanitize(raw_steps)
        raw_code = self._sanitize(raw_code)
        raw_analysis = self._sanitize(raw_analysis)
        example_hint = self._sanitize(example_hint) if example_hint else ""

        if not raw_title:
            raise ValueError("raw_title cannot be empty")
        if not raw_steps:
            raise ValueError("raw_steps cannot be empty")
        if not raw_code:
            raise ValueError("raw_code cannot be empty")

        self.logger.info(
            "Curating knowledge for: %s (target_language=%s)",
            raw_title,
            target_language,
        )

        hint_block = (
            f"\n## OPTIONAL EXAMPLE HINT (use as the concrete example if compatible):\n{example_hint}\n"
            if example_hint
            else ""
        )

        user_message = f"""Curate the following raw algorithm materials into the required JSON schema.

## RAW TITLE
{raw_title}

## RAW STEPS
{raw_steps}

## RAW CODE
{raw_code}

## RAW ANALYSIS
{raw_analysis}
{hint_block}
## REMINDERS
- Write `algorithm_description` as a 2-4 sentence narration-ready overview
  (what the algorithm does, on what data structure, the core idea). NO step
  enumeration, NO code references, NO bullet lists.
- Trim `core_code` to ONLY the function(s) that must be traced on screen.
- Inline comments in `core_code` should reference the numbered markers used
  in `visual_steps` (e.g. "第②(a)步").
- Provide a small, concrete example. Invent one if the raw material has none.
- Scene breakdown must cover intro, setup, main work (1-2 iterations), and
  completion + complexity in 3 to 6 scenes.
"""

        try:
            response_json = self._call_llm_structured(
                system_prompt=self._build_system_prompt(target_language),
                user_message=user_message,
                temperature=self.temperature,
                max_retries=3,
            )

            curated = CuratedKnowledge(**response_json)
            self.logger.info(
                "Curated '%s': %d steps, %d scenes",
                curated.title,
                len(curated.visual_steps),
                len(curated.animation_requirements.scene_breakdown),
            )
            return curated

        except Exception as e:
            self.logger.error(f"Knowledge curation failed: {e}")
            raise ValueError(f"Knowledge curation failed: {e}")

    def curate_to_markdown(
        self,
        raw_title: str,
        raw_steps: str,
        raw_code: str,
        raw_analysis: str,
        target_language: str = "Chinese",
        example_hint: Optional[str] = None,
    ) -> str:
        """Convenience wrapper: curate and render straight to Markdown."""
        curated = self.execute(
            raw_title=raw_title,
            raw_steps=raw_steps,
            raw_code=raw_code,
            raw_analysis=raw_analysis,
            target_language=target_language,
            example_hint=example_hint,
        )
        return format_curated_to_markdown(curated)
