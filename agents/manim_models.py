from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import re




class SceneAction(BaseModel):
    """Represents a single visual action within a scene"""
    action_type: str
    element_type: str
    description: str
    target: str
    duration: float
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ScenePlan(BaseModel):
    """Complete plan for a single animation scene"""
    id: str
    title: str
    description: str
    sub_concept_id: str
    actions: List[SceneAction]
    scene_dependencies: List[str] = Field(default_factory=list)

class ManimSceneCode(BaseModel):
    """Generated Manim code for a single scene"""
    scene_id: str
    scene_name: str
    manim_code: str
    raw_llm_output: str
    extraction_method: str = "tags"


class RenderResult(BaseModel):
    """Result of rendering a single scene"""
    scene_id: str
    success: bool
    video_path: Optional[str] = None
    error_message: Optional[str] = None
    duration: Optional[float] = None
    resolution: Optional[Tuple[int, int]] = None
    render_time: Optional[float] = None
    subtitle_path: Optional[str] = None
    file_size_mb: Optional[float] = None


class AnimationResult(BaseModel):
    """Complete result of animation generation for a concept"""
    success: bool
    concept_id: str
    total_duration: Optional[float] = None
    scene_count: int
    silent_animation_path: Optional[str] = None
    error_message: Optional[str] = None

    # Detailed results
    scene_plan: List[ScenePlan]
    scene_codes: List[ManimSceneCode]
    render_results: List[RenderResult]

    # Metadata
    generation_time: Optional[float] = None
    total_render_time: Optional[float] = None
    models_used: Dict[str, str] = Field(default_factory=dict)
    token_usage: Dict[str, int] = Field(default_factory=dict)


class AnimationConfig(BaseModel):
    """Configuration for animation generation"""
    quality: str = "1080p60"
    background_color: str = "#0f0f0f"
    frame_rate: int = 60
    # Frame rate used for the fast-preview quality preset ("l"); 0 disables.
    preview_fps: int = 10
    max_scene_duration: float = 30.0
    total_video_duration_target: float = 120.0

    max_retries_per_scene: int = 3
    temperature: float = 0.7

    render_timeout: int = 300
    enable_simplification: bool = True
    simplify_on_retry: bool = True

    # manim-linter (static checks before render; version comes from installed Manim)
    lint_enabled: bool = True
    lint_max_fix_attempts: int = 2
    lint_geometry: str = "manim_points"  # auto | aabb | manim_points
    lint_timeout: int = 60

    # Render-failure auto-fix: feed stderr back to the LLM and re-render when
    # Manim raises a runtime error that static lint cannot catch (e.g.
    # TypeError / AttributeError from buggy generated code).
    render_fix_enabled: bool = True
    render_fix_max_attempts: int = 2  # additional LLM fix + re-render rounds after the first render

    # Multi-tier scene repair (guarantees no scene is lost):
    #   Tier 1 = render_fix_enabled loop above (LLM patch fix using RENDER_FIX_PROMPT)
    #   Tier 2 = regenerate the entire scene from its ScenePlan with a higher temperature
    #   Tier 3 = deterministic stub scene (title + description + voiceover) so the
    #            narrative/SRT stays intact even when LLM repair fully fails
    render_regen_enabled: bool = True
    render_regen_temperature_boost: float = 0.3  # clamped to 1.0 when applied
    render_stub_enabled: bool = True  # keep True to honor the "no scene lost" contract


class SceneTransition(BaseModel):
    """Defines how scenes transition to each other"""
    from_scene: str
    to_scene: str
    transition_type: str = "fade"
    duration: float = 0.5


class AnimationMetadata(BaseModel):
    """Metadata for the complete animation generation process"""
    concept_name: str
    timestamp: str
    version: str = "2.0"

    # Generation statistics
    total_scenes_planned: int
    total_scenes_rendered: int
    successful_renders: int
    failed_renders: int

    # Timing information
    planning_time: Optional[float] = None
    code_generation_time: Optional[float] = None
    rendering_time: Optional[float] = None
    concatenation_time: Optional[float] = None
    total_time: Optional[float] = None

    # Resource usage
    total_tokens_used: int = 0
    estimated_cost_usd: Optional[float] = None

    # File information
    total_video_size_mb: Optional[float] = None
    intermediate_files_count: int = 0


class EditResult(BaseModel):
    """Result of EditAgent: modified manim/srt content or error."""
    success: bool
    manim_code: str
    srt_content: str
    error_message: Optional[str] = None
    # Latest raw LLM output from EditAgent (for frontend display / debugging)
    raw_llm_output: Optional[str] = None
    # Simple diff-style previews for frontend display (Manim and SRT)
    manim_diff_preview: Optional[str] = None
    srt_diff_preview: Optional[str] = None