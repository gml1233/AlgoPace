# 导入logging模块，用于记录程序运行日志（调试、错误、信息等）
import logging
# 导入time模块，用于计算程序运行耗时
import time
# 导入json模块，用于处理JSON格式数据的读写
import json
# 导入contextlib，用于可选 Langfuse 的 no-op context
from contextlib import nullcontext
# 导入shutil模块，用于高级文件操作（如删除目录、复制文件等）
import shutil
# 导入hashlib模块，用于为二次渲染的场景产物计算内容指纹
import hashlib
# 从pathlib库导入Path类，用于优雅地处理跨平台文件路径
from pathlib import Path
# 从typing模块导入类型注解相关工具，提升代码可读性和可维护性
# Dict: 字典类型, Any: 任意类型, Optional: 可选类型（可以是指定类型或None）, Callable: 可调用对象（函数等）
from typing import Dict, Any, Optional, Callable, List, Tuple
# 从datetime模块导入datetime类，用于处理时间戳和日期格式化
from datetime import datetime

# 从自定义config模块导入settings配置对象，包含整个项目的所有配置参数（如API密钥、输出目录等）
from config import settings
# 从自定义agents.concept_interpreter模块导入概念解释器代理类和概念分析结果类
from agents.concept_interpreter import ConceptInterpreterAgent, ConceptAnalysis
# 从自定义agents.manim_agent模块导入Manim动画生成代理类
from agents.manim_agent import ManimAgent
# 从自定义agents.manim_models模块导入动画配置类
from agents.manim_models import AnimationConfig
# 从自定义generation.video_compositor模块导入视频合成器类
from generation.video_compositor import VideoCompositor
from generation.voiceover_srt import merge_scene_srts

# Langfuse 可观测性（可选；配置 LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY 后启用）
try:
    from langfuse import get_client as get_langfuse_client, propagate_attributes
    _LANGFUSE_AVAILABLE = True
except ImportError:
    get_langfuse_client = None
    propagate_attributes = None
    _LANGFUSE_AVAILABLE = False


def _langfuse_output_without_local_paths(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """移除 output 中的本地路径字段，避免 Langfuse 尝试上传媒体到其存储（若服务端 MinIO 为 localhost 会失败）。"""
    if data is None or not isinstance(data, dict):
        return data
    out = {}
    for k, v in data.items():
        if k.endswith("_path") or k == "output_path" or k == "input_video_path" or k == "input_audio_path" or k == "input_subtitle_path":
            out[k] = "<local path>"
        elif isinstance(v, dict):
            out[k] = _langfuse_output_without_local_paths(v)
        elif isinstance(v, list):
            out[k] = [_langfuse_output_without_local_paths(x) if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out


class Pipeline:
    """
    Main orchestration pipeline for STEM animation generation
    Phase 4: Concept interpretation + voiceover animation generation + subtitle burn-in
    """

    # 类文档字符串：描述该类是STEM动画生成的核心编排流水线
    # 第4阶段包含3个核心步骤：概念解释 → 生成带配音动画 → 字幕烧录合成

    def __init__(self):
        # 类的构造方法：初始化Pipeline对象时自动执行，用于加载配置、初始化各个子模块

        # 保存项目全局配置到实例属性，方便后续类内方法调用
        self.config = settings
        # 调用内部私有方法，配置日志系统
        self._setup_logging()

        # 初始化第1步：概念解释器代理（负责分析用户输入的STEM概念，提取核心知识点）
        self.concept_interpreter = ConceptInterpreterAgent(
            api_key=settings.openrouter_api_key,  # OpenRouter API密钥（用于调用大模型）
            base_url=settings.openrouter_base_url,  # OpenRouter API基础地址
            model=settings.reasoning_model,  # 用于推理的大模型名称
            reasoning_tokens=settings.interpreter_reasoning_tokens,  # 概念解释的最大token数限制
            reasoning_effort=settings.interpreter_reasoning_effort  # 概念解释的推理力度（控制生成质量）
        )

        # 初始化动画配置对象（封装所有Manim动画生成的相关配置）
        animation_config = AnimationConfig(
            quality=settings.manim_quality,  # Manim动画渲染质量（如480p、720p）
            background_color=settings.manim_background_color,  # 动画背景色
            frame_rate=settings.manim_frame_rate,  # 动画帧率
            preview_fps=settings.manim_preview_fps,  # 快速预览档（"l"）的渲染帧率
            max_scene_duration=settings.manim_max_scene_duration,  # 单个场景的最长时长
            total_video_duration_target=settings.manim_total_video_duration_target,  # 整体动画目标总时长
            temperature=settings.animation_temperature,  # 动画生成的随机性（0-1，值越高越灵活）
            max_retries_per_scene=settings.animation_max_retries_per_scene,  # 单个场景渲染失败的最大重试次数
            enable_simplification=settings.animation_enable_simplification,  # 是否启用动画逻辑简化（提升渲染成功率）
            render_timeout=settings.manim_render_timeout,  # 单个场景渲染的超时时间限制
            lint_enabled=settings.manim_lint_enabled,
            lint_max_fix_attempts=settings.manim_lint_max_fix_attempts,
            lint_geometry=settings.manim_lint_geometry,
            lint_timeout=settings.manim_lint_timeout,
            render_fix_enabled=settings.manim_render_fix_enabled,
            render_fix_max_attempts=settings.manim_render_fix_max_attempts,
            render_regen_enabled=settings.manim_render_regen_enabled,
            render_regen_temperature_boost=settings.manim_render_regen_temperature_boost,
            render_stub_enabled=settings.manim_render_stub_enabled,
        )

        # 初始化第2步：Manim动画生成代理（负责根据概念分析结果生成无声动画视频）
        self.manim_agent = ManimAgent(
            api_key=settings.openrouter_api_key,  # OpenRouter API密钥
            base_url=settings.openrouter_base_url,  # OpenRouter API基础地址
            model=settings.reasoning_model,  # 用于推理的大模型名称
            output_dir=settings.output_dir,  # 动画文件输出目录
            config=animation_config,  # 上面初始化的动画配置对象
            reasoning_tokens=settings.animation_reasoning_tokens,  # 动画生成的最大token数限制
            reasoning_effort=settings.animation_reasoning_effort  # 动画生成的推理力度
        )

        # 初始化视频合成器（负责为带配音动画烧录字幕）
        self.video_compositor = VideoCompositor(
            output_dir=settings.final_dir,  # 最终成品视频输出目录
            video_codec=settings.video_codec,  # 视频编码格式（如h264）
            video_preset=settings.video_preset,  # 视频编码预设（控制压缩比和速度）
            subtitle_burn_preset=settings.subtitle_burn_preset,  # 字幕烧录专用预设
            video_crf=settings.video_crf,  # 视频质量系数（值越低质量越高，文件越大）
            audio_codec=settings.audio_codec,  # 音频编码格式（如mp3）
            audio_bitrate=settings.audio_bitrate,  # 音频比特率（控制音频质量和文件大小）
            subtitle_burn_in=settings.subtitle_burn_in,  # 是否将字幕烧录到视频中（不可修改）
            subtitle_font_size=settings.subtitle_font_size,  # 字幕字体大小
            subtitle_font_color=settings.subtitle_font_color,  # 字幕字体颜色
            subtitle_background=settings.subtitle_background,  # 字幕背景色
            subtitle_background_opacity=settings.subtitle_background_opacity,  # 字幕背景透明度
            subtitle_position=settings.subtitle_position,  # 字幕在视频中的位置
            subtitle_safe_zone_ratio=settings.subtitle_safe_zone_ratio,  # 底部字幕安全区占画面高度比
            max_retries=settings.video_composition_max_retries,  # 视频合成失败的最大重试次数
            timeout=settings.video_composition_timeout  # 视频合成的超时时间限制
        )

        # 记录日志：提示Pipeline已成功初始化，具备第4阶段的全部功能
        self.logger.info("Pipeline initialized with Voiceover capabilities")

    def _setup_logging(self):
        """Configure logging for pipeline"""
        # 内部私有方法：配置Pipeline的日志系统（同时输出到文件和控制台）

        import sys

        # 配置全局日志基础设置
        logging.basicConfig(
            level=logging.INFO,  # 日志级别：INFO及以上级别（INFO、WARNING、ERROR、CRITICAL）会被记录
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 日志格式：时间 - 日志器名称 - 级别 - 消息
            handlers=[
                # 日志处理器1：将日志写入到配置目录下的pipeline.log文件
                logging.FileHandler(self.config.output_dir / 'pipeline.log', encoding='utf-8'),
                # 日志处理器2：将日志输出到控制台（使用 UTF-8 编码）
                logging.StreamHandler(sys.stdout)
            ]
        )
        # 创建并保存名为"Pipeline"的日志器实例，方便后续类内方法调用记录日志
        self.logger = logging.getLogger("Pipeline")

    def run(
            self,
            concept: str,
            progress_callback: Optional[Callable[[str, float], None]] = None,
            target_language: str = "English",
            knowledge_document_path: Optional[str] = None,
            voice_id: Optional[str] = None,
            agent_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
            langfuse_user_id: Optional[str] = None,
            subtitle_style: Optional[Dict[str, Any]] = None,
            render_quality: Optional[str] = None
    ) -> Dict[str, Any]:
        # 首次生成渲染质量：前端可传入 render_quality="l" 走低质量快速预览，确认效果后
        # 再用二次渲染切高质量重渲。质量作为「逐次参数」一路下传到渲染器
        # （execute → _render_scenes → _render_with_repair_chain → renderer.render(quality=...)），
        # 而不是改写共享的 manim_agent.renderer 实例，从而避免并发渲染时互相污染。
        _valid_qualities = {
            "l", "m", "h", "p", "k",
            "480p15", "720p30", "1080p30", "1080p60", "1440p60", "4k60",
        }
        effective_render_quality = None
        if render_quality:
            if render_quality in _valid_qualities:
                effective_render_quality = render_quality
                self.logger.info(f"First-gen using quality: {render_quality}")
            else:
                self.logger.warning(
                    f"Ignoring invalid first-gen quality '{render_quality}', "
                    f"using renderer default."
                )

        # 应用 Agent 参数覆盖（当次运行）
        if agent_overrides:
            for agent_name, overrides in agent_overrides.items():
                if not overrides:
                    continue
                if agent_name == "concept_interpreter":
                    for k, v in overrides.items():
                        if hasattr(self.concept_interpreter, k):
                            setattr(self.concept_interpreter, k, v)
                elif agent_name == "manim_agent":
                    for k, v in overrides.items():
                        if k == "temperature" and hasattr(self.manim_agent, "config") and self.manim_agent.config is not None:
                            self.manim_agent.config.temperature = v
                        elif k == "lint_enabled" and hasattr(self.manim_agent, "config") and self.manim_agent.config is not None:
                            self.manim_agent.config.lint_enabled = bool(v)
                        elif hasattr(self.manim_agent, k):
                            setattr(self.manim_agent, k, v)
                elif agent_name == "script_generator":
                    # Voiceover 模式下已移除独立 script_generator，保留兼容入口但不执行。
                    self.logger.info("script_generator overrides ignored in voiceover mode")

        start_time = time.time()
        self.logger.info(f"Starting pipeline for concept: {concept} in {target_language}")

        knowledge_content = None
        if knowledge_document_path:
            knowledge_content = self._load_knowledge_document(knowledge_document_path)
            if knowledge_content:
                self.logger.info(f"Loaded knowledge document: {knowledge_document_path} ({len(knowledge_content)} characters)")

        # Langfuse 可观测：根 trace 与 session（可选）
        langfuse = get_langfuse_client() if (self.config.langfuse_enabled and _LANGFUSE_AVAILABLE) else None
        if langfuse:
            root_ctx = langfuse.start_as_current_observation(
                as_type="span",
                name="algo-t2v-pipeline",
                input={"concept": (concept[:200] + "..." if len(concept) > 200 else concept) if concept else "", "target_language": target_language},
            )
            attr_kwargs = {"session_id": f"run-{start_time}"}
            if langfuse_user_id and langfuse_user_id.strip():
                attr_kwargs["user_id"] = langfuse_user_id.strip()
            attr_ctx = propagate_attributes(**attr_kwargs)
        else:
            root_ctx = nullcontext()
            attr_ctx = nullcontext()

        try:
            with root_ctx, attr_ctx:
                if progress_callback:
                    progress_callback("Analyzing concept...", 0.1)

                if langfuse:
                    with langfuse.start_as_current_observation(
                        as_type="agent",
                        name="concept-interpreter",
                        input={"concept": (concept[:200] + "..." if len(concept) > 200 else concept) if concept else ""},
                    ) as obs:
                        analysis = self._execute_concept_interpretation(
                            concept,
                            knowledge_content,
                            target_language=target_language,
                        )
                        obs.update(output=_langfuse_output_without_local_paths(analysis.model_dump()))
                else:
                    analysis = self._execute_concept_interpretation(
                        concept,
                        knowledge_content,
                        target_language=target_language,
                    )

                # 更新进度：概念分析完成，进度30%
                if progress_callback:
                    progress_callback("Concept analysis complete", 0.3)

                analysis_path = self._save_analysis(analysis, concept)

                if progress_callback:
                    progress_callback("Generating Voiceover animation...", 0.5)

                if langfuse:
                    with langfuse.start_as_current_observation(
                        as_type="agent",
                        name="manim-agent",
                        input={"concept": (concept[:200] + "..." if len(concept) > 200 else concept) if concept else ""},
                    ) as obs:
                        animation_result = self._execute_manim_generation(
                            analysis, target_language=target_language,
                            render_quality=effective_render_quality,
                        )
                        obs.update(output=_langfuse_output_without_local_paths(animation_result.model_dump() if hasattr(animation_result, "model_dump") else {"success": animation_result.success}))
                else:
                    animation_result = self._execute_manim_generation(
                        analysis, target_language=target_language,
                        render_quality=effective_render_quality,
                    )

                if progress_callback:
                    progress_callback("Animation generation complete", 0.7)

                scene_codes_list = animation_result.scene_codes if animation_result and animation_result.success else []
                combined_manim_code = None
                srt_content = None
                script_result = None

                if animation_result and animation_result.success and animation_result.silent_animation_path:
                    if progress_callback:
                        progress_callback("Building subtitles from voiceover timings...", 0.8)

                    srt_path, srt_content = merge_scene_srts(
                        scene_codes=animation_result.scene_codes,
                        render_results=animation_result.render_results,
                        output_dir=self.config.scripts_dir,
                        output_stem="voiceover_script",
                    )
                    script_result = {
                        "success": True,
                        "script_path": str(srt_path),
                        "srt_content": srt_content,
                    }

                    if langfuse:
                        with langfuse.start_as_current_observation(
                            as_type="span",
                            name="video-composition",
                            input={
                                "silent_animation_path": str(animation_result.silent_animation_path),
                                "script_path": str(srt_path),
                            },
                        ) as obs:
                            video_result = self._execute_video_composition(
                                animation_result.silent_animation_path,
                                None,
                                str(srt_path),
                                subtitle_style=subtitle_style
                            )
                            obs.update(output=_langfuse_output_without_local_paths(video_result.model_dump() if video_result and hasattr(video_result, "model_dump") else None))
                    else:
                        video_result = self._execute_video_composition(
                            animation_result.silent_animation_path,
                            None,
                            str(srt_path),
                            subtitle_style=subtitle_style
                        )

                    if progress_callback:
                        if video_result.success:
                            progress_callback("Video composition complete", 1.0)
                        else:
                            progress_callback("Video composition failed", 1.0)

                    combined_manim_code = self._build_combined_manim_code(scene_codes_list)
                else:
                    video_result = None

                steps_completed = ["concept_interpretation"]
                if animation_result.success:
                    steps_completed.append("animation_generation")
                if script_result and script_result.get("success"):
                    steps_completed.append("script_generation")
                if video_result and video_result.success:
                    steps_completed.append("video_composition")

                metadata = {
                    "total_duration": time.time() - start_time,
                    "steps_completed": steps_completed,
                    "timestamp": datetime.now().isoformat(),
                    "token_usage": {
                        "concept_interpreter": self.concept_interpreter.get_token_usage(),
                        "manim_agent": self.manim_agent.get_token_usage()
                    },
                    "models_used": {
                        "reasoning": settings.reasoning_model,
                        "multimodal": settings.multimodal_model,
                        "tts_provider": settings.tts_provider,
                        "voiceover_service": (
                            "EdgeTTSService" if settings.tts_provider == "edge"
                            else "ElevenLabsService" if settings.tts_provider == "elevenlabs"
                            else "CoquiService" if settings.tts_provider == "coqui"
                            else "OpenAIService"
                        ),
                    },
                    "animation_stats": {
                        "scenes_planned": animation_result.scene_count,
                        "scenes_rendered": len([r for r in animation_result.render_results if r.success]),
                        "total_animation_duration": animation_result.total_duration,
                        "generation_time": animation_result.generation_time
                    } if animation_result.success else None,
                    "script_stats": {
                        "subtitle_lines_generated": len([line for line in (srt_content or "").splitlines() if "-->" in line]),
                        "script_path": script_result.get("script_path") if script_result else None,
                    } if script_result else None,
                    "video_stats": {
                        "output_duration": video_result.output_duration if video_result else None,
                        "file_size_mb": video_result.file_size_mb if video_result else None,
                        "resolution": video_result.resolution if video_result else None,
                        "video_composition_time": video_result.generation_time if video_result else None
                    } if video_result else None
                }

                self.logger.info(f"Pipeline completed successfully in {metadata['total_duration']:.2f}s")

                scene_durations_map = None
                try:
                    if animation_result and animation_result.render_results:
                        scene_durations_map = {
                            r.scene_id: float(r.duration)
                            for r in animation_result.render_results
                            if r.duration is not None
                        } or None
                except Exception:
                    scene_durations_map = None

                return {
                    "status": "success",
                    "concept_analysis": analysis.model_dump(),
                    "analysis_path": str(analysis_path),
                    "animation_result": animation_result.model_dump() if animation_result.success else None,
                    "script_result": script_result,
                    "audio_result": None,
                    "video_result": video_result.model_dump() if video_result else None,
                    "metadata": metadata,
                    "error": None,
                    "manim_source_code": combined_manim_code if video_result and video_result.success else None,
                    "srt_content": srt_content if video_result and video_result.success else None,
                    "audio_path": None,
                    "scene_durations": scene_durations_map,
                }

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Pipeline failed: {e}")

            return {
                "status": "error",
                "concept_analysis": None,
                "analysis_path": None,
                "animation_result": None,
                "script_result": None,
                "audio_result": None,
                "video_result": None,
                "metadata": {
                    "total_duration": duration,
                    "steps_completed": [],
                    "timestamp": datetime.now().isoformat()
                },
                "error": str(e)
            }
        finally:
            if langfuse is not None:
                langfuse.flush()

    def _build_combined_manim_code(self, scene_codes) -> Optional[str]:
        """
        将多个场景的 Manim 源代码合并为一个完整的代码字符串
        用于返回给前端，供用户编辑和重新渲染

        Args:
            scene_codes: ManimSceneCode 对象列表（来自 AnimationResult.scene_codes）

        Returns:
            合并后的 Manim 源代码字符串，或 None（无有效代码时）
        """
        if not scene_codes:
            return None

        combined_parts = []
        combined_parts.append("# ========== AlgoT2V 生成的 Manim 动画源代码 ==========")
        combined_parts.append("# 您可以在此编辑代码，然后点击「重新渲染」按钮生成新视频")
        combined_parts.append("# 每个 Scene 类对应一个动画场景，按顺序拼接")
        combined_parts.append("# 注意：请确保每个 Scene 类名唯一且正确")
        combined_parts.append("")

        for i, scene_code in enumerate(scene_codes):
            combined_parts.append(f"# ========== 场景 {i + 1}: {scene_code.scene_name} (ID: {scene_code.scene_id}) ==========")
            combined_parts.append(scene_code.manim_code)
            combined_parts.append("")

        return "\n".join(combined_parts)

    def _scan_class_defs(self, manim_code: str) -> List[Dict[str, Any]]:
        """扫描 Manim 代码里的所有 class 定义并分类。

        每个类返回 dict：name / bases / start_line / end_line /
        has_construct（类体内是否定义 construct）/ is_scene（是否传递性继承自
        Scene 系基类）。

        is_scene 用传递闭包推断：基类名包含 "Scene"（如 VoiceoverScene），
        或继承自本文件中另一个已判定为 scene 的类（如自定义的 SeqListBase）。
        这样既能识别 `class X(VoiceoverScene)`，也能识别继承自项目公共基类的
        `class X(SeqListBase)` 这类真实场景。
        """
        import re

        lines = manim_code.split('\n')
        class_pat = re.compile(r'^class\s+(\w+)\s*\(([^)]*)\)\s*:', re.MULTILINE)

        classes: List[Dict[str, Any]] = []
        for m in class_pat.finditer(manim_code):
            bases = [b.strip().split('.')[-1] for b in m.group(2).split(',') if b.strip()]
            classes.append({
                'name': m.group(1),
                'bases': bases,
                'start_line': manim_code[:m.start()].count('\n'),
            })

        for i, c in enumerate(classes):
            c['end_line'] = classes[i + 1]['start_line'] if i + 1 < len(classes) else len(lines)
            block = '\n'.join(lines[c['start_line']:c['end_line']])
            c['has_construct'] = bool(
                re.search(r'^[ \t\xa0]+def\s+construct\s*\(', block, re.MULTILINE)
            )

        # 传递闭包：反复扫描直到没有新的 scene 类被发现。
        scene_names: set = set()
        changed = True
        while changed:
            changed = False
            for c in classes:
                if c['name'] in scene_names:
                    continue
                if any('Scene' in b or b in scene_names for b in c['bases']):
                    scene_names.add(c['name'])
                    changed = True
        for c in classes:
            c['is_scene'] = c['name'] in scene_names

        return classes

    def _extract_scene_classes_from_code(self, manim_code: str) -> list:
        """
        从合并的 Manim 代码中解析出所有【可渲染】的 Scene 类。

        可渲染场景 = 传递性继承自 Scene 系基类（is_scene）且类体内定义了
        construct 方法（has_construct）。仅靠「基类名包含 Scene」会漏掉
        继承自项目基类（如 SeqListBase）的真实场景，并会误把没有 construct
        的公共基类当成场景，因此这里同时要求 is_scene 与 has_construct。

        Returns:
            [(class_name, code_block), ...] 列表
        """
        lines = manim_code.split('\n')
        classes = self._scan_class_defs(manim_code)

        renderable = [c for c in classes if c['is_scene'] and c['has_construct']]
        if not renderable:
            self.logger.warning(
                "No renderable Scene classes (with construct) found in provided Manim code"
            )
            return []

        scene_classes = []
        for c in renderable:
            code_block = '\n'.join(lines[c['start_line']:c['end_line']]).rstrip()
            scene_classes.append((c['name'], code_block))

        skipped = [c['name'] for c in classes if c['is_scene'] and not c['has_construct']]
        if skipped:
            self.logger.info(f"Skipped base/helper scene classes (no construct): {skipped}")

        self.logger.info(f"Extracted {len(scene_classes)} renderable scene classes from code")
        return scene_classes

    def _parse_scene_headers_from_manim(self, manim_code: str) -> List[Tuple[str, str]]:
        """
        解析合并代码中 AlgoT2V 场景注释头，顺序与文件中 Scene 类出现顺序一致。
        返回 [(header 中的场景名, header 中的 ID), ...]，供 scene_durations 与 VirtualFileSystem 对齐。
        """
        import re

        pattern = r"^# ==========\s*场景\s*\d+:\s*(\S+)\s*\(ID:\s*(\S+)\)\s*$"
        return [(m.group(1), m.group(2)) for m in re.finditer(pattern, manim_code, re.MULTILINE)]

    def rerender(
            self,
            manim_code: str,
            srt_content: str,
            progress_callback: Optional[Callable[[str, float], None]] = None,
            voice_id: Optional[str] = None,
            subtitle_style: Optional[Dict[str, Any]] = None,
            render_quality: Optional[str] = None
    ) -> Dict[str, Any]:
        if manim_code:
            manim_code = manim_code.replace('\xa0', ' ')
        start_time = time.time()
        self.logger.info("Starting re-render pipeline")

        # 二次渲染质量：前端可传入 render_quality="l" 走低质量快速预览，确认效果后
        # 再用高质量重渲。质量作为「逐次参数」一路下传到渲染器（render_single_with_repair
        # → _render_with_repair_chain → renderer.render(quality=...)），而不是改写共享的
        # manim_agent.renderer 实例，从而避免并发渲染时互相污染、或泄漏到后续的首次生成。
        _valid_qualities = {
            "l", "m", "h", "p", "k",
            "480p15", "720p30", "1080p30", "1080p60", "1440p60", "4k60",
        }
        effective_render_quality = None
        if render_quality:
            if render_quality in _valid_qualities:
                effective_render_quality = render_quality
                self.logger.info(f"Re-render using quality: {render_quality}")
            else:
                self.logger.warning(
                    f"Ignoring invalid re-render quality '{render_quality}', "
                    f"using renderer default."
                )

        try:
            if progress_callback:
                progress_callback("解析 Manim 代码...", 0.05)

            manim_code = self._rewrite_speech_service_in_code(manim_code, voice_id=voice_id)

            scene_classes = self._extract_scene_classes_from_code(manim_code)
            if not scene_classes:
                return {
                    "status": "error",
                    "video_result": None,
                    "error": "未在代码中找到有效的 Scene 类。请确保代码包含继承自 Scene 的类定义。",
                    "manim_source_code": manim_code,
                    "srt_content": srt_content,
                }

            self.logger.info(f"Found {len(scene_classes)} scene classes to render")

            if progress_callback:
                progress_callback(f"渲染 {len(scene_classes)} 个动画场景...", 0.1)

            render_results = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            header_pairs_for_stub = self._parse_scene_headers_from_manim(manim_code)

            for i, (class_name, code_block) in enumerate(scene_classes):
                if progress_callback:
                    pct = 0.1 + (0.5 * (i / len(scene_classes)))
                    progress_callback(f"渲染场景 {i + 1}/{len(scene_classes)}: {class_name}...", pct)

                # 为每个场景构建完整可执行代码
                # 需要包含 import 和类之前的所有代码（共享的函数、基类等）
                full_code = self._build_renderable_code(manim_code, class_name)

                output_filename = f"rerender_{class_name}_{timestamp}.mp4"
                scene_id = f"rerender_scene_{i + 1}"

                # 用注释头里记录的场景名作为 Tier 3 占位场景的标题，
                # 其次退回到类名；rerender 场景没有 ScenePlan，会自动跳过 Tier 2。
                stub_title = class_name
                if i < len(header_pairs_for_stub):
                    hname, _hid = header_pairs_for_stub[i]
                    if hname:
                        stub_title = hname
                stub_description = (
                    f"{stub_title} (场景代码渲染失败后的占位片段)。"
                    "This is a fallback placeholder generated because the user-edited "
                    "Manim code could not be rendered after all repair attempts."
                )

                # 场景级产物缓存：代码与渲染质量都没变时直接复用上一次的 mp4 +
                # .srt，跳过整段 Manim 渲染（实测该步骤占二次渲染 85% 的耗时）。
                cache_key = self._scene_render_cache_key(
                    full_code, effective_render_quality
                )
                render_result = self._load_cached_scene_render(
                    cache_key, output_filename, scene_id
                )

                if render_result is not None:
                    self.logger.info(
                        "Scene '%s' unchanged since last render — reusing cached "
                        "artifacts (%s), skipping Manim render",
                        class_name,
                        cache_key,
                    )
                    if progress_callback:
                        progress_callback(
                            f"场景 {i + 1}/{len(scene_classes)}: {class_name} 未改动，复用上次渲染结果",
                            pct,
                        )
                else:
                    reason = self._explain_cache_miss(cache_key, full_code, class_name)
                    if reason:
                        self.logger.info(
                            "Scene '%s' cache MISS (%s): %s - full Manim render required",
                            class_name, cache_key, reason,
                        )
                        if progress_callback:
                            progress_callback(
                                f"场景 {i + 1}/{len(scene_classes)}: {class_name} 需要重新渲染 - {reason}",
                                pct,
                            )
                    else:
                        self.logger.info(
                            "Scene '%s' cache MISS (%s): no previous render of this scene to compare",
                            class_name, cache_key,
                        )

                    render_result = self.manim_agent.render_single_with_repair(
                        code=full_code,
                        class_name=class_name,
                        output_filename=output_filename,
                        scene_id=scene_id,
                        scene_plan=None,
                        title=stub_title,
                        description=stub_description,
                        # 二次渲染质量（None 时回退到渲染器默认的高质量）。
                        render_quality=effective_render_quality,
                        # 重新渲染时关闭全部自动修复（Tier 1/2/3）；首次生成不受影响。
                        disable_auto_repair=True,
                    )
                    self._store_cached_scene_render(
                        cache_key, render_result, full_code=full_code, scene_name=class_name
                    )

                render_results.append(render_result)

                if not render_result.success:
                    # 二次渲染失败：不走占位兜底，直接抛出错误信息并取消整个重渲染。
                    self.logger.error(
                        f"Scene '{class_name}' render failed during rerender, "
                        f"aborting: {render_result.error_message}"
                    )
                    return {
                        "status": "error",
                        "video_result": None,
                        "error": (
                            f"重新渲染已取消：场景 '{class_name}' 渲染失败。\n"
                            f"{render_result.error_message}"
                        ),
                        "manim_source_code": manim_code,
                        "srt_content": srt_content,
                    }

                self.logger.info(f"Scene '{class_name}' rendered successfully")

            successful_renders = [r for r in render_results if r.success]
            if not successful_renders:
                error_messages = [f"  - {r.scene_id}: {r.error_message}" for r in render_results if not r.success]
                return {
                    "status": "error",
                    "video_result": None,
                    "error": "所有场景渲染均失败:\n" + "\n".join(error_messages),
                    "manim_source_code": manim_code,
                    "srt_content": srt_content,
                }

            if progress_callback:
                progress_callback("拼接动画场景...", 0.6)

            # 单场景（日志里 240/255 次重渲染都是）：concat=n=1 是恒等操作，产出的
            # 中间文件下一步立刻又被读一遍。跳过整趟 ffmpeg，把场景 mp4 直接交给
            # 合成步骤，把音频补齐挪到那一遍里一起做。
            # 多场景仍走 _concatenate_scenes —— 场景顺序由它保证。
            fused_audio_pad_to = None
            if len(successful_renders) == 1:
                single = Path(successful_renders[0].video_path)

                # 静音策略守卫。绕过 _concatenate_scenes 也就绕过了它内部的
                # _has_audio_stream 检查；不补回来的话，无音轨的输入会退化成一条
                # 难懂的 ffmpeg 映射错误，并在 output/final 留下 0 字节文件。
                if not self.manim_agent._has_audio_stream(single):
                    return {
                        "status": "error",
                        "video_result": None,
                        "error": f"拒绝合成：场景 {single.name} 没有音频流（旁白缺失）。",
                        "manim_source_code": manim_code,
                        "srt_content": srt_content,
                    }

                # 时长必须取视频流(v:0)，不能用 RenderResult.duration —— 后者是容器
                # 时长（取所有流的最大值）。实测 output/scenes 里 6.8% 的 mp4 两者
                # 相差 25-51ms，而合成那步不再带 -shortest，多出来的音频会挂在最后
                # 一帧视频之后。
                fused_audio_pad_to = self.manim_agent._probe_video_duration(single)
                if not fused_audio_pad_to or fused_audio_pad_to <= 0:
                    return {
                        "status": "error",
                        "video_result": None,
                        "error": f"无法探测场景视频时长: {single}",
                        "manim_source_code": manim_code,
                        "srt_content": srt_content,
                    }

                silent_animation_path = single
                self.logger.info(
                    "Single scene: skipping the concat pass, folding audio padding "
                    "into the subtitle burn (pad target %.6fs from v:0)",
                    fused_audio_pad_to,
                )
            else:
                silent_animation_path = self.manim_agent._concatenate_scenes(successful_renders)
                if not silent_animation_path:
                    return {
                        "status": "error",
                        "video_result": None,
                        "error": "动画场景拼接失败",
                        "manim_source_code": manim_code,
                        "srt_content": srt_content,
                    }

            if progress_callback:
                progress_callback("根据 Voiceover 时序生成字幕...", 0.7)

            scene_codes = []
            for scene_id, (class_name, code_block) in enumerate(scene_classes, start=1):
                scene_codes.append({
                    "scene_id": f"rerender_scene_{scene_id}",
                    "scene_name": class_name,
                    "manim_code": code_block,
                    "raw_llm_output": "",
                    "extraction_method": "rerender",
                })

            from agents.manim_models import ManimSceneCode
            typed_scene_codes = [ManimSceneCode(**item) for item in scene_codes]
            srt_path, rebuilt_srt_content = merge_scene_srts(
                scene_codes=typed_scene_codes,
                render_results=render_results,
                output_dir=self.config.scripts_dir,
                output_stem="rerender_voiceover_script",
            )

            if progress_callback:
                progress_callback("合成最终视频...", 0.9)

            video_result = self._execute_video_composition(
                str(silent_animation_path),
                None,
                str(srt_path),
                subtitle_style=subtitle_style,
                audio_pad_to=fused_audio_pad_to
            )

            if not video_result or not video_result.success:
                error_msg = video_result.error_message if video_result else "视频合成返回空结果"
                return {
                    "status": "error",
                    "video_result": None,
                    "error": f"视频合成失败: {error_msg}",
                    "manim_source_code": manim_code,
                    "srt_content": srt_content,
                }

            if progress_callback:
                progress_callback("重新渲染完成！", 1.0)

            duration = time.time() - start_time
            self.logger.info(f"Re-render completed successfully in {duration:.2f}s")

            # 构建 scene_durations
            header_pairs = self._parse_scene_headers_from_manim(manim_code)
            scene_durations: Dict[str, float] = {}
            for i, r in enumerate(render_results):
                if not r.success or r.duration is None:
                    continue
                d = float(r.duration)
                scene_durations[r.scene_id] = d
                class_name = scene_classes[i][0]
                scene_durations[class_name] = d
                if i < len(header_pairs):
                    hname, hid = header_pairs[i]
                    scene_durations[hname] = d
                    scene_durations[hid] = d

            return {
                "status": "success",
                "video_result": video_result.model_dump(),
                "error": None,
                "manim_source_code": manim_code,
                "srt_content": rebuilt_srt_content or srt_content,
                "scene_durations": scene_durations,
                "metadata": {
                    "total_duration": duration,
                    "scenes_rendered": len(successful_renders),
                    "scenes_total": len(scene_classes),
                    "timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Re-render pipeline failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

            return {
                "status": "error",
                "video_result": None,
                "error": str(e),
                "manim_source_code": manim_code,
                "srt_content": srt_content,
                "metadata": {
                    "total_duration": duration,
                    "timestamp": datetime.now().isoformat()
                }
            }

    def _build_renderable_code(self, full_manim_code: str, target_class_name: str) -> str:
        """
        从合并的 Manim 代码中提取出可独立渲染的单个场景代码
        包含 import 语句、共享函数/基类、和目标 Scene 类

        会排除「其它可渲染场景类」，但保留公共基类（is_scene 但无 construct，
        例如 SeqListBase）——它们是目标场景的父类，必须作为 preamble 保留。

        Args:
            full_manim_code: 完整的合并 Manim 代码
            target_class_name: 需要渲染的目标 Scene 类名

        Returns:
            可独立执行的 Manim Python 代码字符串
        """
        lines = full_manim_code.split('\n')
        classes = self._scan_class_defs(full_manim_code)

        # 可渲染场景 = is_scene 且 has_construct；其余类（含公共基类）保留为 preamble。
        renderable = {
            c['name']: c for c in classes if c['is_scene'] and c['has_construct']
        }
        if target_class_name not in renderable:
            # 目标类未找到，返回全部代码
            self.logger.warning(f"Target class '{target_class_name}' not found, returning full code")
            return full_manim_code

        # 仅排除「其它」可渲染场景类的行范围
        other_scene_ranges = [
            (c['start_line'], c['end_line'])
            for name, c in renderable.items()
            if name != target_class_name
        ]

        # 构建可渲染代码：排除其他 Scene 类，保留 import、共享代码、基类和目标类
        result_lines = []
        for line_num, line in enumerate(lines):
            # 跳过注释行（AlgoT2V 添加的场景标题注释）
            if line.startswith("# ========== 场景") or line.startswith("# ========== AlgoT2V"):
                continue
            if line.startswith("# 您可以在此编辑") or line.startswith("# 每个 Scene 类") or line.startswith("# 注意：请确保"):
                continue

            # 判断是否在「其他」Scene 类的范围内
            in_other_scene = any(start <= line_num < end for start, end in other_scene_ranges)

            if not in_other_scene:
                result_lines.append(line)

        return '\n'.join(result_lines)

    # ---- 二次渲染的场景级产物缓存 -------------------------------------
    #
    # rerender() 以前从解析代码直奔 render_single_with_repair，中间没有任何
    # 判断。于是「只改了字幕字号」这种编辑也会把整段动画从第 0 帧重渲一遍：
    # 日志里同一场景连续两次重渲各花 77.7s / 81.8s，产物时长一模一样，唯一
    # 变化的字幕样式其实只在最后的合成步骤才被消费。
    #
    # 这里按「场景的可渲染代码 + 渲染质量」做指纹，命中就直接复用上一次的
    # mp4 与 .srt 旁挂文件。注意这与 manim.cfg 里 disable_caching = True 不
    # 冲突：那条禁的是 Manim 自己的分段/帧缓存（命中会置 skip_animations，
    # 导致 Scene.add_sound 提前返回、旁白丢失），而这里复用的是一个已经渲染
    # 完成的整段 mp4，根本不会再进 Manim 渲染器。

    _SCENE_CACHE_MAX_ENTRIES = 40

    @property
    def _scene_cache_dir(self) -> Path:
        return Path(self.config.output_dir) / "rerender_cache"

    @staticmethod
    def _normalize_code_for_fingerprint(code: str) -> str:
        """Canonicalise whitespace so cosmetic edits do not defeat the cache.

        The Gradio code editor round-trips the source on every re-render and is
        free to drop the trailing newline, convert line endings, or strip
        trailing spaces. None of that changes what Manim renders, but a raw
        sha256 treats each as a different program (verified: a missing final
        newline alone produced a different key). Line endings, per-line
        trailing whitespace and trailing blank lines are folded away here;
        indentation and everything inside a line are kept verbatim.
        """
        text = (code or "").replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.rstrip() for line in text.split("\n")]
        while lines and not lines[-1]:
            lines.pop()
        return "\n".join(lines) + "\n"

    def _scene_render_cache_key(
        self,
        full_code: str,
        render_quality: Optional[str],
    ) -> str:
        """Fingerprint everything that can change the rendered scene file.

        ``full_code`` already carries the speech-service setup line rewritten by
        _rewrite_speech_service_in_code, so the voice and every TTS knob that
        feeds the voiceover cache key are covered by hashing it. Subtitle style
        is deliberately NOT part of the key — it is applied later, during video
        composition, and is exactly the kind of edit this cache exists to make
        instant.
        """
        try:
            from generation.tts.edge_service import _CACHE_VERSION as tts_cache_version
        except Exception:
            tts_cache_version = "unknown"

        parts = [
            self._normalize_code_for_fingerprint(full_code),
            str(render_quality or ""),
            str(getattr(settings, "manim_preview_fps", "")),
            str(tts_cache_version),
            str(getattr(settings, "manim_background_color", "")),
        ]
        digest = hashlib.sha256("|__SEP__|".join(parts).encode("utf-8")).hexdigest()
        return digest[:32]

    def _load_cached_scene_render(
        self,
        cache_key: str,
        output_filename: str,
        scene_id: str,
    ):
        """Return a RenderResult rebuilt from cache, or None on any miss.

        Deliberately strict: a hit requires the mp4, the .srt sidecar AND the
        metadata to all be present. merge_scene_srts only logs a warning when a
        sidecar is missing and then carries on (generation/voiceover_srt.py),
        so a half-populated cache entry would silently ship a video with a
        scene's subtitles dropped.
        """
        from agents.manim_models import RenderResult

        cache_dir = self._scene_cache_dir
        cached_video = cache_dir / f"{cache_key}.mp4"
        cached_srt = cache_dir / f"{cache_key}.srt"
        cached_meta = cache_dir / f"{cache_key}.json"

        if not (cached_video.exists() and cached_srt.exists() and cached_meta.exists()):
            return None

        try:
            meta = json.loads(cached_meta.read_text(encoding="utf-8"))
            duration = float(meta["duration"])
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            self.logger.warning("Ignoring unreadable scene cache entry %s: %s", cache_key, exc)
            return None

        if duration <= 0:
            return None

        scenes_dir = Path(self.config.output_dir) / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)
        target_video = scenes_dir / output_filename
        target_srt = target_video.with_suffix(".srt")

        try:
            shutil.copy2(cached_video, target_video)
            shutil.copy2(cached_srt, target_srt)
        except OSError as exc:
            self.logger.warning("Failed to restore scene cache entry %s: %s", cache_key, exc)
            return None

        resolution = meta.get("resolution")
        return RenderResult(
            scene_id=scene_id,
            success=True,
            video_path=str(target_video),
            subtitle_path=str(target_srt),
            duration=duration,
            resolution=tuple(resolution) if resolution else None,
            render_time=0.0,
            file_size_mb=meta.get("file_size_mb"),
        )

    def _store_cached_scene_render(
        self,
        cache_key: str,
        render_result,
        full_code: Optional[str] = None,
        scene_name: Optional[str] = None,
    ) -> None:
        """Persist a successful scene render for reuse; failures are non-fatal.

        The fingerprinted source is stored next to the artifacts so that a later
        MISS for the same scene can be explained by diffing against it.
        """
        if not (render_result.success and render_result.video_path and render_result.duration):
            return

        video_path = Path(render_result.video_path)
        srt_path = (
            Path(render_result.subtitle_path)
            if render_result.subtitle_path
            else video_path.with_suffix(".srt")
        )
        if not (video_path.exists() and srt_path.exists()):
            # No sidecar means a cache hit would later drop this scene's
            # subtitles, so refuse to store a partial entry.
            self.logger.debug(
                "Not caching scene render %s: missing video or subtitle sidecar", cache_key
            )
            return

        cache_dir = self._scene_cache_dir
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(video_path, cache_dir / f"{cache_key}.mp4")
            shutil.copy2(srt_path, cache_dir / f"{cache_key}.srt")
            meta = {
                "duration": float(render_result.duration),
                "resolution": list(render_result.resolution) if render_result.resolution else None,
                "file_size_mb": render_result.file_size_mb,
                "stored_at": datetime.now().isoformat(timespec="seconds"),
                "scene_name": scene_name,
            }
            (cache_dir / f"{cache_key}.json").write_text(
                json.dumps(meta, ensure_ascii=False), encoding="utf-8"
            )
            if full_code is not None:
                (cache_dir / f"{cache_key}.py").write_text(
                    self._normalize_code_for_fingerprint(full_code), encoding="utf-8"
                )
            self._prune_scene_cache()
        except OSError as exc:
            self.logger.warning("Failed to cache scene render %s: %s", cache_key, exc)

    def _explain_cache_miss(
        self,
        cache_key: str,
        full_code: str,
        scene_name: str,
    ) -> Optional[str]:
        """Say WHY this scene missed the cache, in one line, for the log and UI.

        Compares the fingerprinted source against the most recent cached entry
        for the same scene class. Returns None when there is nothing to compare
        against (first render of this scene, or older entries pruned).
        """
        import difflib

        cache_dir = self._scene_cache_dir
        try:
            metas = sorted(
                cache_dir.glob("*.json"), key=lambda q: q.stat().st_mtime, reverse=True
            )
        except OSError:
            return None

        previous_src = None
        for meta_path in metas:
            if meta_path.stem == cache_key:
                continue
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if meta.get("scene_name") != scene_name:
                continue
            src_path = meta_path.with_suffix(".py")
            if src_path.exists():
                previous_src = src_path.read_text(encoding="utf-8")
                break

        if previous_src is None:
            return None

        current = self._normalize_code_for_fingerprint(full_code)
        if current == previous_src:
            return "代码与上次渲染完全一致，但渲染参数不同（质量 / 预览帧率 / 背景色 / TTS 版本）"

        old_lines = previous_src.splitlines()
        new_lines = current.splitlines()
        changed = []
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            snippet = (new_lines[j1] if j1 < len(new_lines) else old_lines[i1]).strip()
            changed.append((j1 + 1, tag, snippet))

        if not changed:
            return None

        first_line, first_tag, first_snippet = changed[0]
        if len(first_snippet) > 60:
            first_snippet = first_snippet[:57] + "..."
        tag_zh = {"replace": "修改", "insert": "新增", "delete": "删除"}.get(first_tag, first_tag)
        more = f"，另有 {len(changed) - 1} 处改动" if len(changed) > 1 else ""
        return f"代码第 {first_line} 行有{tag_zh}（{first_snippet}）{more}"

    def _prune_scene_cache(self) -> None:
        """Keep the newest N entries so this cache cannot grow without bound."""
        cache_dir = self._scene_cache_dir
        try:
            metas = sorted(
                cache_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
            )
        except OSError:
            return

        for stale in metas[self._SCENE_CACHE_MAX_ENTRIES:]:
            for suffix in (".json", ".mp4", ".srt", ".py"):
                try:
                    stale.with_suffix(suffix).unlink(missing_ok=True)
                except OSError:
                    pass

    def _rewrite_speech_service_in_code(
        self,
        manim_code: str,
        voice_id: Optional[str] = None,
    ) -> str:
        """Force the scene code's speech service to follow current settings.

        Rewrites:
          - Any speech-service import line (manim_voiceover.services.* or the
            project-local EdgeTTSService) to the one matching ``settings.tts_provider``.
          - Every ``self.set_speech_service(...)`` call to the matching constructor.

        ``voice_id`` (optional) overrides ``settings.edge_tts_voice`` for this
        rewrite only — so that UI voice selection takes effect on re-render.
        """
        import re

        try:
            original_voice = settings.edge_tts_voice
            if voice_id:
                settings.edge_tts_voice = voice_id
            try:
                import_line, setup_line = self.manim_agent._build_voiceover_prompt_section()
            finally:
                settings.edge_tts_voice = original_voice
        except Exception as build_error:
            self.logger.warning(
                "Failed to build voiceover prompt section, keeping original speech service: %s",
                build_error,
            )
            return manim_code

        service_import_pattern = re.compile(
            r"^(?P<indent>[ \t]*)from\s+"
            r"(?:manim_voiceover\.services\.\w+|generation\.tts\.edge_service)"
            r"\s+import\s+\w+Service\s*$",
            re.MULTILINE,
        )
        legacy_patch_import_pattern = re.compile(
            r"^[ \t]*from\s+tools\.voiceover_tracker\s+import\s+patch_voiceover\s*;\s*patch_voiceover\(\)\s*$",
            re.MULTILINE,
        )
        set_service_pattern = re.compile(
            r"(?P<indent>[ \t]*)self\.set_speech_service\([^)]*\([^)]*\)\s*\)",
            re.MULTILINE,
        )

        first_import_seen = {"done": False}

        def replace_import(match: "re.Match[str]") -> str:
            indent = match.group("indent")
            if first_import_seen["done"]:
                return ""
            first_import_seen["done"] = True
            return f"{indent}{import_line}"

        new_code = legacy_patch_import_pattern.sub("", manim_code)
        new_code = service_import_pattern.sub(replace_import, new_code)
        if not first_import_seen["done"]:
            self.logger.info(
                "No speech-service import found in rerender code; inserting current provider import."
            )
            anchor_pattern = re.compile(
                r"^(?P<indent>[ \t]*)from\s+manim_voiceover\s+import\s+VoiceoverScene[^\n]*$",
                re.MULTILINE,
            )
            if anchor_pattern.search(new_code):
                new_code = anchor_pattern.sub(
                    lambda m: f"{m.group(0)}\n{m.group('indent')}{import_line}",
                    new_code,
                    count=1,
                )
            else:
                new_code = f"{import_line}\n{new_code}"

        new_code = re.sub(r"\n{3,}", "\n\n", new_code)

        def replace_setup(match: "re.Match[str]") -> str:
            return f"{match.group('indent')}{setup_line}"

        new_code = set_service_pattern.sub(replace_setup, new_code)

        if new_code != manim_code:
            self.logger.info(
                "Rewrote speech service to provider=%s (voice=%s) for re-render.",
                settings.tts_provider,
                voice_id or settings.edge_tts_voice,
            )
        return new_code

    def _execute_concept_interpretation(
        self,
        concept: str,
        knowledge_content: str = None,
        target_language: str = "English",
    ) -> ConceptAnalysis:
        """Execute concept interpretation step"""
        # 内部私有方法：执行概念解释步骤
        self.logger.info(
            "Step 1: Concept Interpretation (target_language=%s)", target_language
        )
        # 调用概念解释器的execute方法，返回概念分析结果（可传入知识文档内容）
        return self.concept_interpreter.execute(
            concept,
            knowledge_content=knowledge_content,
            target_language=target_language,
        )

    def _save_analysis(self, analysis: ConceptAnalysis, original_concept: str) -> Path:
        """Save concept analysis to JSON file"""
        # 内部私有方法：将概念分析结果保存到JSON文件，便于追溯和调试

        # 步骤1：生成安全的文件名（避免特殊字符导致文件操作失败）
        # 遍历原始概念字符串，只保留字母和数字，其他字符替换为下划线
        safe_name = "".join(c if c.isalnum() else "_" for c in original_concept.lower())
        safe_name = safe_name[:50]  # 限制文件名长度（避免超过系统限制），最多50个字符
        # 步骤2：生成时间戳（年月日_时分秒），保证文件名唯一，避免覆盖
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 步骤3：拼接最终文件名（安全名称_时间戳.json）
        filename = f"{safe_name}_{timestamp}.json"

        # 步骤4：构建完整的文件路径（配置的分析目录 + 文件名）
        filepath = self.config.analyses_dir / filename

        # 步骤5：将概念分析结果转为字典并写入JSON文件（缩进2个空格，便于阅读）
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis.model_dump(), f, indent=2, ensure_ascii=False)

        # 步骤6：记录日志，提示文件已保存
        self.logger.info(f"Analysis saved to {filepath}")
        # 步骤7：返回文件路径对象
        return filepath

    # Phase 2-3 methods（第2-3阶段相关方法）

    def _execute_manim_generation(
        self,
        analysis: ConceptAnalysis,
        target_language: str = "English",
        render_quality: Optional[str] = None,
    ):
        """Phase 2: Generate Manim animations"""
        # 内部私有方法：执行Manim动画生成步骤
        self.logger.info(
            "Step 2: Animation Generation (target_language=%s)", target_language
        )
        # 调用Manim代理的execute方法，传入概念分析结果，返回动画生成结果
        # render_quality 为 None 时回退到渲染器默认质量（settings.manim_quality）。
        return self.manim_agent.execute(
            analysis,
            target_language=target_language,
            render_quality=render_quality,
        )

    def _load_knowledge_document(self, document_path: str) -> Optional[str]:
        """Load knowledge document content from file"""
        # 内部私有方法：从文件加载知识文档内容
        try:
            doc_path = Path(document_path)
            if not doc_path.exists():
                self.logger.warning(f"Knowledge document not found: {document_path}")
                return None
            
            # 读取文件内容（支持 .txt 和 .md 文件）
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                self.logger.warning(f"Knowledge document is empty: {document_path}")
                return None
            
            self.logger.info(f"Successfully loaded knowledge document: {doc_path.name}")
            return content
        except Exception as e:
            self.logger.error(f"Failed to load knowledge document: {e}")
            return None

    def _execute_video_composition(
        self,
        animation_path: str,
        audio_path: Optional[str],
        script_path: str,
        subtitle_style: Optional[Dict[str, Any]] = None,
        audio_pad_to: Optional[float] = None
    ):
        """Phase 4: Compose final video"""
        # 内部私有方法：执行最终视频合成步骤（合并动画、音频、字幕）
        self.logger.info("Step 5: Video Composition")

        # 生成最终视频的输出文件名（基于无声动画名称 + 时间戳 + _final.mp4）
        animation_name = Path(animation_path).stem  # 获取无声动画文件的名称（不含后缀）
        # 精确到微秒。原来是秒级时间戳，而 animation_name 本身就带同一秒的时间戳
        # （见 _concatenate_scenes），两次合成落在同一秒就会撞同一个文件名。以前
        # ffmpeg 缺 -y 时这会静默返回旧文件；补上 -y 之后则会覆盖别人的产物。
        # 重渲染越快撞车概率越高，所以文件名必须自带唯一性。
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # 时间戳（含微秒）
        output_filename = f"{animation_name}_final_{timestamp}.mp4"  # 最终视频文件名

        # 调用视频合成器的execute方法，传入相关文件路径和输出文件名，返回视频合成结果
        return self.video_compositor.execute(
            video_path=animation_path,  # 无声动画路径
            audio_path=audio_path,  # 旁白音频路径
            subtitle_path=script_path if script_path else None,  # 字幕路径（SRT/脚本路径）
            output_filename=output_filename,  # 最终视频输出文件名
            subtitle_style_overrides=subtitle_style,  # 旁白字幕样式覆盖（重新渲染时生效）
            audio_pad_to=audio_pad_to  # 单场景融合路径：在本步补齐音频到视频时长
        )

    def _cleanup_temp_files(self, animation_result, audio_result):
        """Clean up temporary files after successful final video composition"""
        # 内部私有方法：视频合成成功后，清理过程中的临时文件（节省磁盘空间）
        self.logger.info("Starting cleanup of temporary files")

        # 用于记录已清理的文件/目录列表，便于日志输出
        cleaned_items = []

        try:
            # 1. 清理单个场景的动画视频文件
            if animation_result and animation_result.render_results:
                for render_result in animation_result.render_results:
                    if render_result.video_path:
                        video_path = Path(render_result.video_path)
                        if video_path.exists():  # 确认文件存在
                            video_path.unlink()  # 删除文件
                            cleaned_items.append(f"scene video: {video_path.name}")

            # 2. 清理拼接后的无声动画视频文件
            if animation_result and animation_result.silent_animation_path:
                silent_path = Path(animation_result.silent_animation_path)
                if silent_path.exists():
                    silent_path.unlink()
                    cleaned_items.append(f"silent animation: {silent_path.name}")

            # 3. 清理单个音频片段文件
            if audio_result and audio_result.audio_segments:
                for segment in audio_result.audio_segments:
                    if segment.audio_path:
                        segment_path = Path(segment.audio_path)
                        if segment_path.exists():
                            segment_path.unlink()
                            cleaned_items.append(f"audio segment: {segment_path.name}")

            # 4. 清理非填充版的拼接音频文件（保留填充版用于最终视频）
            if audio_result and audio_result.audio_path:
                audio_path = Path(audio_result.audio_path)
                # 查找所有填充版音频文件
                padded_files = list(audio_path.parent.glob(f"{audio_path.stem}_padded_*.mp3"))
                if padded_files:
                    # 如果存在填充版，删除原始非填充版音频文件
                    if audio_path.exists():
                        audio_path.unlink()
                        cleaned_items.append(f"non-padded audio: {audio_path.name}")

            # 5. 清理空的音频片段目录
            segments_dir = settings.audio_dir / "segments"
            if segments_dir.exists() and not any(segments_dir.iterdir()):  # 目录存在且为空
                segments_dir.rmdir()  # 删除空目录
                cleaned_items.append("empty segments directory")

            # 6. 清理场景代码文件（.py和.raw.txt）
            scene_codes_dir = settings.output_dir / "scene_codes"
            if scene_codes_dir.exists():
                for code_file in scene_codes_dir.glob("*"):  # 遍历目录下所有文件
                    # 只删除.py文件和.raw.txt文件
                    if code_file.is_file() and (code_file.suffix == ".py" or code_file.name.endswith(".raw.txt")):
                        try:
                            code_file.unlink()
                            cleaned_items.append(f"scene code: {code_file.name}")
                        except Exception as e:
                            # 单个文件删除失败不中断整体清理，记录警告日志
                            self.logger.warning(f"Could not remove {code_file}: {e}")

            # 7. 清理Manim媒体目录下的临时文件
            media_dir = Path("media")
            if media_dir.exists():
                # 清理临时视频目录
                videos_dir = media_dir / "videos"
                if videos_dir.exists():
                    for temp_dir in videos_dir.iterdir():
                        if temp_dir.is_dir() and temp_dir.name.startswith("tmp"):  # 匹配以tmp开头的目录
                            try:
                                shutil.rmtree(temp_dir)  # 删除非空目录（递归删除所有内容）
                                cleaned_items.append(f"temp video dir: {temp_dir.name}")
                            except Exception as e:
                                self.logger.warning(f"Could not remove temp dir {temp_dir}: {e}")

                # 清理临时图片目录
                images_dir = media_dir / "images"
                if images_dir.exists():
                    for temp_dir in images_dir.iterdir():
                        if temp_dir.is_dir() and temp_dir.name.startswith("tmp"):
                            try:
                                shutil.rmtree(temp_dir)
                                cleaned_items.append(f"temp image dir: {temp_dir.name}")
                            except Exception as e:
                                self.logger.warning(f"Could not remove temp dir {temp_dir}: {e}")

            # 记录日志：提示清理完成，输出已清理的文件/目录数量
            self.logger.info(f"Cleanup complete: removed {len(cleaned_items)} items")
            # 输出前10个已清理项（避免日志过长）
            for item in cleaned_items[:10]:
                self.logger.debug(f"  - Removed {item}")
            # 如果清理项超过10个，提示还有更多
            if len(cleaned_items) > 10:
                self.logger.debug(f"  - ... and {len(cleaned_items) - 10} more items")

        except Exception as e:
            # 清理过程中发生异常不中断流水线，记录错误日志
            self.logger.error(f"Error during cleanup: {e}")
            # Don't raise - cleanup errors shouldn't fail the pipeline（清理错误不应该导致流水线失败）