#!/usr/bin/env python3
# 声明脚本使用Python3解释器执行，这是Unix/Linux系统的标准写法

"""
Gradio web app for STEM Animation Generator
Simple UI: Input concept -> Progress bar -> Video player
"""
# 文档字符串（Docstring）：描述整个脚本的功能
# 这是一个用于STEM（科学、技术、工程、数学）动画生成的Gradio网页应用
# 简单UI流程：输入概念 -> 进度条展示 -> 视频播放器展示结果

# 导入Gradio库，用于快速构建网页交互界面，别名gr是行业常用简写
import json
import html
import re
import gradio as gr
import logging
# 导入自定义的Pipeline类（来自同级目录的pipeline.py文件），负责处理动画生成的核心流程
from pipeline import Pipeline
from edit_pipeline import EditPipeline
from config import settings

logger = logging.getLogger(__name__)
# 导入pathlib库的Path类，用于更优雅、跨平台地处理文件路径（比传统os.path更易用）
from pathlib import Path
from utils.history import (
    save_record,
    list_records,
    get_record,
    delete_record as history_delete_record,
    export_record as history_export_record,
    RECORD_TYPE_GENERATE,
    RECORD_TYPE_RERENDER,
)

# 实例化Pipeline类，创建一个pipeline对象，后续用于调用动画生成的核心方法
pipeline = Pipeline()
# 修改 pipeline：根据用户指令编辑 Manim/SRT，与生成 pipeline 分离
edit_pipeline = EditPipeline()

# Langfuse 可观测性：配置加载完成后初始化客户端
def _ensure_langfuse_client():
    try:
        import os
        from config import settings
        if getattr(settings, "langfuse_enabled", False) and settings.langfuse_enabled:
            # Langfuse SDK reads LANGFUSE_* from os.environ; inject from config when set
            if settings.langfuse_public_key:
                os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
            if settings.langfuse_secret_key:
                os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
            if settings.langfuse_base_url:
                os.environ["LANGFUSE_BASE_URL"] = settings.langfuse_base_url
            logger.info("Langfuse observability enabled; pipeline and LLM calls will be reported to Langfuse")
            try:
                from langfuse import get_client as get_langfuse_client
                get_langfuse_client()
            except Exception as e:
                logger.warning("Langfuse client init failed (tracing may be disabled): %s", e)
    except Exception:
        pass
_ensure_langfuse_client()


# ========== Edge TTS 中文音色映射表 ==========
# 格式："显示名称" → Edge TTS voice name
# Edge TTS 免费、中文发音准确（不会把"2"读成"two"）
VOICE_CHOICES = {
    "🎯 云希 - 男声·专业讲解 (YunxiNeural)": "zh-CN-YunxiNeural",
    "🎯 晓晓 - 女声·温暖自然 (XiaoxiaoNeural)": "zh-CN-XiaoxiaoNeural",
    "🎯 云阳 - 男声·新闻播报 (YunyangNeural)": "zh-CN-YunyangNeural",
    "🎤 晓伊 - 女声·活泼清晰 (XiaoyiNeural)": "zh-CN-XiaoyiNeural",
    "🎤 云健 - 男声·浑厚有力 (YunjianNeural)": "zh-CN-YunjianNeural",
    "🎤 云夏 - 男声·年轻阳光 (YunxiaNeural)": "zh-CN-YunxiaNeural",
    "👤 晓墨 - 女声·温柔甜美 (XiaomoNeural)": "zh-CN-XiaomoNeural",
    "👤 晓睿 - 女声·知性优雅 (XiaoruiNeural)": "zh-CN-XiaoruiNeural",
    "👤 晓双 - 女声·童声清脆 (XiaoshuangNeural)": "zh-CN-XiaoshuangNeural",
    "👤 晓涵 - 女声·成熟稳重 (XiaohanNeural)": "zh-CN-XiaohanNeural",
    "👤 晓梦 - 女声·甜美可爱 (XiaomengNeural)": "zh-CN-XiaomengNeural",
    "👤 晓萱 - 女声·清新活力 (XiaoxuanNeural)": "zh-CN-XiaoxuanNeural",
    "👤 晓语 - 女声·温婉知性 (XiaoyuNeural)": "zh-CN-XiaoyuNeural",
    "👤 晓甄 - 女声·端庄大方 (XiaozhenNeural)": "zh-CN-XiaozhenNeural",
}

# 默认音色（云希 - 男声专业讲解，非常适合算法教学）
DEFAULT_VOICE = "🎯 云希 - 男声·专业讲解 (YunxiNeural)"


def validate_knowledge_file(file_path):
    """
    验证上传的知识文档文件类型和内容
    
    Args:
        file_path: 上传的文件路径
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file_path:
        return True, None
    
    from pathlib import Path
    import mimetypes
    
    try:
        path = Path(file_path)
        file_ext = path.suffix.lower()
        file_name = path.name
        
        if not path.exists():
            return False, f"文件不存在: {file_path}"
        
        # 检查文件大小（最大 50MB）
        file_size = path.stat().st_size
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            return False, f"文件过大。最大允许大小: 50MB，当前: {file_size / 1024 / 1024:.2f}MB"
        
        # 如果有扩展名，检查是否在允许列表中
        allowed_extensions = {'.txt', '.md'}
        if file_ext and file_ext not in allowed_extensions:
            return False, f"不支持的文件类型: {file_ext}。仅支持: {', '.join(sorted(allowed_extensions))}"
        
        # 尝试读取文件以确保其是文本文件（可读且包含有效内容）
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read(4096)  # 读取前 4KB 来验证
                
                # 检查是否为空文件
                if not content.strip():
                    return False, f"文件为空。请上传包含有效内容的文档"
                    
        except UnicodeDecodeError:
            # 尝试用其他编码
            try:
                with open(path, 'r', encoding='gbk') as f:
                    _ = f.read(1024)
            except:
                return False, f"文件编码错误。请确保文件是符合 UTF-8 编码的纯文本文件"
        except Exception as e:
            return False, f"无法读取文件: {str(e)}"
        
        return True, None
    except Exception as e:
        return False, f"文件验证失败: {str(e)}"


def _build_agent_overrides(
    ci_temperature, ci_max_tokens, ci_top_p, ci_reasoning_tokens, ci_reasoning_effort,
    ma_temperature, ma_max_tokens, ma_top_p, ma_reasoning_tokens, ma_reasoning_effort, ma_lint_enabled,
    sg_temperature, sg_max_tokens, sg_top_p,
):
    """从表单值构建 agent_overrides 与 agent_params（结构一致）。"""
    def _num(v):
        if v is None:
            return None
        try:
            n = int(float(v))
            return n if n > 0 else None
        except (TypeError, ValueError):
            return None

    def _float(v):
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    concept_interpreter = {
        "temperature": _float(ci_temperature) if ci_temperature is not None else 0.5,
        "max_tokens": _num(ci_max_tokens) or 16384,
        "top_p": _float(ci_top_p) if ci_top_p is not None else 1.0,
        "reasoning_tokens": _num(ci_reasoning_tokens),
        "reasoning_effort": ci_reasoning_effort if ci_reasoning_effort in ("low", "medium", "high") else "low",
    }
    if concept_interpreter["top_p"] == 1.0:
        concept_interpreter.pop("top_p", None)
    if not concept_interpreter.get("reasoning_tokens"):
        concept_interpreter["reasoning_tokens"] = None
    if not concept_interpreter.get("reasoning_effort"):
        concept_interpreter["reasoning_effort"] = None

    manim_agent = {
        "temperature": _float(ma_temperature) if ma_temperature is not None else 0.5,
        "max_tokens": _num(ma_max_tokens) or 16384,
        "top_p": _float(ma_top_p) if ma_top_p is not None else 1.0,
        "reasoning_tokens": _num(ma_reasoning_tokens),
        "reasoning_effort": ma_reasoning_effort if ma_reasoning_effort in ("low", "medium", "high") else "medium",
        "lint_enabled": bool(ma_lint_enabled),
    }
    if manim_agent["top_p"] == 1.0:
        manim_agent.pop("top_p", None)
    if not manim_agent.get("reasoning_tokens"):
        manim_agent["reasoning_tokens"] = None
    if not manim_agent.get("reasoning_effort"):
        manim_agent["reasoning_effort"] = None

    script_generator = {
        "temperature": _float(sg_temperature) if sg_temperature is not None else 0.5,
        "max_tokens": _num(sg_max_tokens) or 4096,
        "top_p": _float(sg_top_p) if sg_top_p is not None else 1.0,
    }
    if script_generator["top_p"] == 1.0:
        script_generator.pop("top_p", None)

    return {
        "concept_interpreter": concept_interpreter,
        "manim_agent": manim_agent,
        "script_generator": script_generator,
    }


def _render_quality_choices():
    """首次生成 / 二次渲染共用的质量单选项。

    返回 (choices, default_value)。default 永远是低质量 "l"（480p 快速预览，
    帧率取 settings.manim_preview_fps），
    让用户最快看到渲染结果；确认无误后再切高质量重渲。
    高质量取自 settings.manim_quality；若它本身就是 "l"，回退到 "p"(1080p60)，
    以免与「低质量预览」选项重值。
    """
    hq_value = getattr(settings, "manim_quality", "p")
    if hq_value == "l":
        hq_value = "p"
    hq_labels = {
        "m": "720p30", "h": "1080p30", "p": "1080p60",
        "k": "1440p60", "720p30": "720p30", "1080p30": "1080p30",
        "1080p60": "1080p60", "1440p60": "1440p60", "4k60": "1440p60",
    }
    hq_label = hq_labels.get(hq_value, str(hq_value))
    preview_fps = getattr(settings, "manim_preview_fps", 0) or 15
    choices = [
        (f"⚡ 快速预览（480p{preview_fps}，最快，默认）", "l"),
        (f"🎬 高质量（{hq_label}，发布用，更慢）", hq_value),
    ]
    return choices, "l"


def generate_animation(
    concept: str,
    language: str = "English",
    voice_name: str = None,
    knowledge_file=None,
    subtitle_font: str = None,
    subtitle_font_size: float = None,
    subtitle_font_color: str = None,
    subtitle_auto_wrap: bool = True,
    subtitle_alignment: str = "居中对齐",
    subtitle_margin_v: float = 0,
    ci_temperature=None,
    ci_max_tokens=None,
    ci_top_p=None,
    ci_reasoning_tokens=None,
    ci_reasoning_effort=None,
    ma_temperature=None,
    ma_max_tokens=None,
    ma_top_p=None,
    ma_reasoning_tokens=None,
    ma_reasoning_effort=None,
    ma_lint_enabled=None,
    sg_temperature=None,
    sg_max_tokens=None,
    sg_top_p=None,
    langfuse_user_id=None,
    langfuse_session_id=None,
    render_quality: str = "l",
    progress=gr.Progress(),
):
    """
    Main generation function called by Gradio

    Args:
        concept: User input STEM concept
        language: Target language for narration
        voice_name: Selected voice display name (mapped to voice_id)
        knowledge_file: Optional uploaded knowledge document file (.txt/.md)
        subtitle_*: Toolbox options for saving in history
        ci_* / ma_* / sg_*: Agent 请求参数（概念解释 / 动画生成 / 脚本生成）
        progress: Gradio progress tracker

    Returns:
        tuple: (video_path, manim_code, srt_content, scene_durations) — 视频路径、Manim源代码、SRT字幕、每个场景持续时长映射
    """

    # 校验用户输入
    if not concept or concept.strip() == "":
        print("请输入有效内容")
        return None, "", "", None

    # 处理知识文档文件
    knowledge_document_path = None
    if knowledge_file is not None:
        is_valid, error_msg = validate_knowledge_file(knowledge_file)
        if not is_valid:
            error_info = f"知识文档验证失败: {error_msg}"
            print(error_info)
            raise gr.Error(error_info)
        knowledge_document_path = knowledge_file
        print(f"使用知识文档: {knowledge_document_path}")

    # 进度回调
    def update_progress(message: str, percentage: float):
        progress(percentage, desc=message)

    # 解析音色
    voice_id = VOICE_CHOICES.get(voice_name) if voice_name else None
    if voice_id:
        print(f"使用音色: {voice_name} → {voice_id}")

    # 构建 Agent 参数覆盖与历史用 agent_params
    agent_overrides = _build_agent_overrides(
        ci_temperature, ci_max_tokens, ci_top_p, ci_reasoning_tokens, ci_reasoning_effort,
        ma_temperature, ma_max_tokens, ma_top_p, ma_reasoning_tokens, ma_reasoning_effort, ma_lint_enabled,
        sg_temperature, sg_max_tokens, sg_top_p,
    )
    agent_params = dict(agent_overrides)
    agent_params["langfuse"] = {
        "user_id": (langfuse_user_id or "").strip(),
        "session_id": (langfuse_session_id or "").strip(),
    }
    try:
        _margin_v_for_history = int(float(subtitle_margin_v or 0))
    except (TypeError, ValueError):
        _margin_v_for_history = 0
    agent_params["subtitle"] = {"margin_v": _margin_v_for_history}

    # 旁白字幕样式（与重新渲染一致，默认与 FFmpeg 一致：字号 20 等）
    # 说明：margin_v 未显式设置时，VideoCompositor 会根据实际视频高度和
    # settings.subtitle_safe_zone_ratio 自动计算像素值，保证字幕落在底部安全区内，
    # 避免与 Manim 动画（已在生成侧约束在 y >= -3.3）重叠。
    alignment_map = {"左对齐": 1, "居中对齐": 2, "右对齐": 3}
    wrap_style = 0 if subtitle_auto_wrap else 2
    subtitle_style = {
        "font_name": subtitle_font or "Arial",
        "font_size": int(subtitle_font_size) if subtitle_font_size is not None else 20,
        "font_color": subtitle_font_color or "#FFFFFF",
        "alignment": alignment_map.get(subtitle_alignment, 2),
        "wrap_style": wrap_style,
        # margin_v: 未设置则由 VideoCompositor 依据视频高度 × 安全区比例自动填入。
    }
    try:
        margin_v_override = int(float(subtitle_margin_v or 0))
    except (TypeError, ValueError):
        margin_v_override = 0
    if margin_v_override > 0:
        subtitle_style["margin_v"] = margin_v_override

    # 首次生成质量：默认低质量（"l"）快速预览，最快看到渲染结果；
    # 确认无误后再用二次渲染切高质量重渲。
    render_quality = (render_quality or "l").strip() or "l"
    print(f"首次生成渲染质量: {render_quality}")

    # 调用核心 pipeline 生成
    result = pipeline.run(
        concept,
        progress_callback=update_progress,
        target_language=language,
        knowledge_document_path=knowledge_document_path,
        voice_id=voice_id,
        agent_overrides=agent_overrides,
        langfuse_user_id=(langfuse_user_id or "").strip() or None,
        subtitle_style=subtitle_style,
        render_quality=render_quality,
    )

    # 判断结果
    if result["status"] == "success" and result.get("video_result"):
        video_path = result["video_result"]["output_path"]
        manim_code = result.get("manim_source_code", "") or ""
        srt_content = result.get("srt_content", "") or ""
        scene_durations = result.get("scene_durations") or None
        try:
            save_record(
                concept=concept.strip(),
                language=language or "English",
                voice_name=voice_name,
                knowledge_file_path=knowledge_document_path,
                manim_code=manim_code,
                srt_content=srt_content,
                subtitle_font=subtitle_font,
                subtitle_font_size=subtitle_font_size,
                subtitle_font_color=subtitle_font_color,
                subtitle_auto_wrap=subtitle_auto_wrap,
                subtitle_alignment=subtitle_alignment,
                record_type=RECORD_TYPE_GENERATE,
                agent_params=agent_params,
                scene_durations=scene_durations,
            )
        except Exception as e:
            print(f"历史记录保存失败: {e}")
        if Path(video_path).exists():
            return video_path, manim_code, srt_content, scene_durations
        else:
            return None, manim_code, srt_content, scene_durations
    else:
        error_msg = result.get("error", "生成失败，请查看日志")
        print(f"生成失败: {error_msg}")
        return None, "", "", None


def _messages_to_chatbot_format(raw_json: str) -> list[dict]:
    """Convert agent messages JSON to gr.Chatbot messages format.

    Important: Gradio 6.x expects each message to be a dict with `role` and `content`.
    To make arbitrary HTML render (details/summary/code blocks), we wrap HTML fragments
    as `gr.HTML` components inside the message `content`.
    """
    try:
        messages = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError):
        return []

    chatbot_msgs: list[dict] = []

    def _short_tool_call_id(tool_call_id: str) -> str:
        text = (tool_call_id or "").strip()
        if len(text) <= 14:
            return text
        return f"...{text[-12:]}"

    def _mk_code_block(text: str) -> str:
        safe = html.escape(text or "")
        return f"<pre><code>{safe}</code></pre>"

    def _mk_details(kind: str, title: str, body: str, meta: str = "", full_id: str = "") -> str:
        safe_title = html.escape(title or "")
        safe_meta = html.escape(meta or "")
        safe_full_id = html.escape(full_id or "")
        summary_meta = f'<span class="agent-msg__meta">{safe_meta}</span>' if safe_meta else ""
        id_attr = f' title="{safe_full_id}"' if safe_full_id else ""
        return (
            f'<div class="agent-msg agent-msg--{kind}">'
            f'<details><summary{id_attr}><span class="agent-msg__title">{safe_title}</span>{summary_meta}</summary>'
            f"{body}</details></div>"
        )

    def _as_html_component(html_fragment: str) -> "gr.HTML":
        # Wrap HTML so Chatbot renders it as a component (not as plain escaped text).
        # show_label=False hides the HTML component's label if any.
        return gr.HTML(html_fragment, show_label=False)

    def _render_user_content(user_content: str) -> "list[str | gr.HTML] | str":
        """
        EditAgent user_message uses a stable structure:
        - "## Workspace overview"
        - a workspace listing inside a markdown fenced code block (``` ... ```)
        - "## User instruction"

        Gradio converts fenced code blocks into internal HTML like `code_wrap` on the frontend.
        Since that HTML is not present in raw `user_content`, we transform the fenced block
        into our own collapsible `<details>` HTML here (default collapsed).
        """
        s = user_content or ""

        ws_heading = "## Workspace overview"
        ui_heading = "## User instruction"
        ws_idx = s.find(ws_heading)
        ui_idx = s.find(ui_heading)

        if ws_idx == -1 or ui_idx == -1 or ui_idx <= ws_idx:
            # Fallback: if structure is not detected, keep as Markdown string.
            return s

        workspace_block = s[ws_idx:ui_idx]
        instruction_block = s[ui_idx:]  # keep the "## User instruction" heading

        # Extract the first fenced code block (``` ... ```).
        # This is where the workspace listing lives.
        fence_start = workspace_block.find("```")
        if fence_start == -1:
            return s
        fence_end = workspace_block.find("```", fence_start + 3)
        if fence_end == -1:
            return s

        fence_content = workspace_block[fence_start + 3 : fence_end].rstrip("\n")
        escaped = html.escape(fence_content)

        # Keep `code_wrap` class for styling compatibility.
        code_html = (
            '<div class="code_wrap">'
            '<pre><code>'
            f"{escaped}"
            "</code></pre>"
            "</div>"
        )

        # Use the same HTML wrapper structure as assistant messages so CSS applies.
        # Collapse by default (no `open` attribute inside `_mk_details`).
        details_html = _mk_details("user", "Workspace overview", code_html)

        # Return HTML as a component, not a plain string, so Chatbot renders it as HTML.
        out: list[str | gr.HTML] = []
        out.append(_as_html_component(details_html))
        if instruction_block.strip():
            out.append(instruction_block)
        return out

    for msg in messages:
        role = msg.get("role")
        if role == "system":
            continue
        if role == "user":
            user_content = msg.get("content") or ""
            rendered = _render_user_content(user_content)

            chatbot_msgs.append({"role": "user", "content": rendered})
        elif role == "assistant":
            parts = []
            reasoning = (msg.get("reasoning_content") or "").strip()
            if reasoning:
                parts.append(
                    _as_html_component(
                        _mk_details(
                            "thinking",
                            "思考 / Thinking",
                            _mk_code_block(reasoning),
                        )
                    )
                )
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    fn = tc.get("function", {})
                    fn_name = fn.get("name", "?")
                    fn_args = fn.get("arguments", "")
                    args_text = fn_args if isinstance(fn_args, str) else json.dumps(fn_args, ensure_ascii=False)
                    if len(args_text) > 1200:
                        args_text = args_text[:1200] + "\n... (truncated)"
                    tc_id = tc.get("id", "")
                    call_text = f"tool_call_id: {tc_id}\nname: {fn_name}\narguments:\n{args_text}"
                    parts.append(
                        _as_html_component(
                            _mk_details(
                                "tool-call",
                                "工具调用 / ToolCall",
                                _mk_code_block(call_text),
                                meta=fn_name,
                            )
                        )
                    )
            content = msg.get("content") or ""
            if content.strip():
                # Main assistant content should use Markdown rendering.
                parts.append(content)
            if parts:
                chatbot_msgs.append({"role": "assistant", "content": parts})
        elif role == "tool":
            content = msg.get("content", "")
            if len(content) > 2000:
                content = content[:2000] + "\n... (truncated)"
            tool_call_id = msg.get("tool_call_id") or ""
            body_text = content
            if tool_call_id:
                body_text = f"tool_call_id: {tool_call_id}\n\n{content}"
            chatbot_msgs.append(
                {
                    "role": "assistant",
                    "content": [
                        _as_html_component(
                            _mk_details(
                                "tool-result",
                                "工具结果 / Tool Result",
                                _mk_code_block(body_text),
                                meta=_short_tool_call_id(tool_call_id),
                                full_id=tool_call_id,
                            )
                        )
                    ],
                }
            )
    return chatbot_msgs


def ai_edit_code(
    manim_code: str,
    srt_content: str,
    edit_instruction: str,
    langfuse_user_id: str = None,
    langfuse_session_id: str = None,
    scene_durations: dict | None = None,
    conversation_history: list | None = None,
    max_history_rounds: float | int | None = None,
    concept: str = "",
    language: str = "English",
    voice_name: str = None,
    knowledge_file=None,
    subtitle_font: str = None,
    subtitle_font_size: float = None,
    subtitle_font_color: str = None,
    subtitle_auto_wrap: bool = True,
    subtitle_alignment: str = "居中对齐",
):
    if manim_code:
        manim_code = manim_code.replace("\xa0", " ")
    if srt_content:
        srt_content = srt_content.replace("\xa0", " ")
    """
    根据用户修改指令，使用 EditPipeline 自动编辑 Manim 代码和 SRT 字幕。
    返回 (manim_code, srt_content) 写回编辑器。
    """
    if not (manim_code or "").strip():
        gr.Warning("请先生成视频或导入历史记录，确保有 Manim 代码后再使用 AI 编辑。")
        yield gr.update(), gr.update(), gr.update(), "", history
        return
    instruction = (edit_instruction or "").strip()
    history = conversation_history if isinstance(conversation_history, list) else []
    rounds = None
    if max_history_rounds is not None:
        try:
            rounds = int(max_history_rounds)
        except (TypeError, ValueError):
            rounds = None
    if not instruction:
        yield manim_code, srt_content, _messages_to_chatbot_format(json.dumps(history, ensure_ascii=False)), "", history
        return

    stream_messages = list(history)
    stream_messages.append({"role": "user", "content": instruction})
    stream_messages.append(
        {"role": "assistant", "content": "", "reasoning_content": "", "tool_calls": []}
    )

    latest_result = None
    for event in edit_pipeline.edit_stream(
        manim_code=manim_code,
        srt_content=srt_content,
        user_instruction=instruction,
        langfuse_user_id=(langfuse_user_id or "").strip() or None,
        langfuse_session_id=(langfuse_session_id or "").strip() or None,
        scene_durations=scene_durations,
        conversation_history=history,
        max_history_rounds=rounds,
    ):
        etype = event.get("type")
        current_assistant = stream_messages[-1] if stream_messages and stream_messages[-1].get("role") == "assistant" else None
        if etype == "assistant_content_delta" and current_assistant is not None:
            current_assistant["content"] = (current_assistant.get("content") or "") + (event.get("delta") or "")
        elif etype == "reasoning_delta" and current_assistant is not None:
            current_assistant["reasoning_content"] = (current_assistant.get("reasoning_content") or "") + (event.get("delta") or "")
        elif etype == "tool_call_delta" and current_assistant is not None:
            idx = event.get("index", 0)
            try:
                idx = int(idx)
            except (TypeError, ValueError):
                idx = 0
            tool_calls = current_assistant.setdefault("tool_calls", [])
            while len(tool_calls) <= idx:
                tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
            slot = tool_calls[idx]
            if event.get("tool_call_id"):
                slot["id"] = event.get("tool_call_id")
            if event.get("tool_name"):
                slot["function"]["name"] = event.get("tool_name")
            if event.get("arguments") is not None:
                slot["function"]["arguments"] = event.get("arguments")
        elif etype == "assistant_message_final":
            if stream_messages and stream_messages[-1].get("role") == "assistant":
                stream_messages[-1] = event.get("message", stream_messages[-1])
            else:
                stream_messages.append(event.get("message", {"role": "assistant", "content": ""}))
        elif etype == "tool_result":
            stream_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": event.get("tool_call_id"),
                    "content": event.get("content") or "",
                }
            )
            stream_messages.append({"role": "assistant", "content": "", "reasoning_content": "", "tool_calls": []})
        elif etype == "final_result":
            latest_result = event.get("result")
            continue

        chatbot_msgs = _messages_to_chatbot_format(json.dumps(stream_messages, ensure_ascii=False))
        yield manim_code, srt_content, chatbot_msgs, "AI 正在编辑中...", history

    if result is None:
        gr.Warning("AI 编辑失败：未收到最终结果。")
        yield gr.update(), gr.update(), gr.update(), "AI 编辑失败", history
        return
    if not result.success:
        gr.Warning(result.error_message or "AI 编辑失败，请查看日志。")
        yield gr.update(), gr.update(), gr.update(), "AI 编辑失败", history
        return

    updated_history = history
    try:
        updated_history = json.loads(result.raw_llm_output or "[]")
        if not isinstance(updated_history, list):
            updated_history = history
    except (json.JSONDecodeError, TypeError):
        updated_history = history

    chatbot_msgs = _messages_to_chatbot_format(json.dumps(updated_history, ensure_ascii=False))
    summary = result.manim_diff_preview or ""
    if result.srt_diff_preview and "未对 SRT" not in result.srt_diff_preview:
        summary += "\n\n" + result.srt_diff_preview

    # Persist edit conversation history immediately so that "history import"
    # can restore agent chat + edit state even if the user doesn't click
    # "re-render" right after AI editing.
    try:
        effective_rounds = rounds
        if effective_rounds is None:
            try:
                effective_rounds = int(max_history_rounds)
            except (TypeError, ValueError):
                effective_rounds = None
        if effective_rounds is None:
            effective_rounds = int(getattr(settings, "edit_chat_history_rounds", 8))

        save_record(
            concept=(concept or "").strip(),
            language=language or "English",
            voice_name=voice_name,
            knowledge_file_path=knowledge_file,
            manim_code=result.manim_code,
            srt_content=result.srt_content,
            subtitle_font=subtitle_font,
            subtitle_font_size=subtitle_font_size,
            subtitle_font_color=subtitle_font_color,
            subtitle_auto_wrap=subtitle_auto_wrap,
            subtitle_alignment=subtitle_alignment,
            record_type=RECORD_TYPE_RERENDER,
            agent_params={
                "langfuse": {
                    "user_id": (langfuse_user_id or "").strip(),
                    "session_id": (langfuse_session_id or "").strip(),
                },
                "edit_agent": {
                    "history_rounds": effective_rounds,
                },
            },
            scene_durations=scene_durations,
            conversation_history=updated_history,
        )
    except Exception as e:
        # Saving history should never break the edit UX.
        print(f"历史记录保存失败（AI 编辑结束时）：{e}")

    yield result.manim_code, result.srt_content, chatbot_msgs, summary, updated_history


def clear_agent_chat():
    """Clear agent chat UI and in-memory conversation history."""
    return [], "", []


def rerender_video(
    manim_code: str,
    srt_content: str,
    voice_name: str = None,
    subtitle_font: str = None,
    subtitle_font_size: float = None,
    subtitle_font_color: str = None,
    subtitle_auto_wrap: bool = True,
    subtitle_alignment: str = "居中对齐",
    subtitle_margin_v: float = 0,
    render_quality: str = "l",
    concept: str = "",
    language: str = "English",
    knowledge_file=None,
    langfuse_user_id: str = None,
    langfuse_session_id: str = None,
    conversation_history: list | None = None,
    edit_history_rounds: float | int | None = None,
    progress=gr.Progress(),
):
    # 清理 Gradio 文本框可能引入的不间断空格（\xa0），这会导致 Python SyntaxError 和正则表达式匹配失败
    if manim_code:
        manim_code = manim_code.replace("\xa0", " ")

    """
    重新渲染：根据用户修改后的 Manim 代码和 SRT 字幕重新生成视频，并应用旁白字幕样式。

    Args:
        manim_code: 用户编辑后的 Manim 源代码
        srt_content: 用户编辑后的 SRT 字幕内容
        voice_name: 语音音色选择
        subtitle_*: 字幕样式（并用于保存历史）
        concept, language, knowledge_file: 当前页面上的生成设置，用于保存历史
        progress: Gradio progress tracker

    Returns:
        tuple: (video_path, manim_code, srt_content)
    """
    # 校验输入
    if not manim_code or manim_code.strip() == "":
        gr.Warning("请提供 Manim 源代码。请先生成视频，或手动粘贴 Manim 代码。")
        return gr.update(), gr.update(), gr.update(), gr.update()


    # 进度回调
    def update_progress(message: str, percentage: float):
        progress(percentage, desc=message)

    # 解析音色
    voice_id = VOICE_CHOICES.get(voice_name) if voice_name else None
    if voice_id:
        print(f"重新渲染使用音色: {voice_name} → {voice_id}")

    # 旁白字幕样式：对齐 左/中/右 -> ASS Alignment 1/2/3，换行 -> WrapStyle 0 或 2
    # 说明：margin_v 未显式设置时，VideoCompositor 会根据视频高度和安全区比例自动填入，
    # 将字幕固定在底部安全区内以避免和 Manim 动画重叠。
    alignment_map = {"左对齐": 1, "居中对齐": 2, "右对齐": 3}
    wrap_style = 0 if subtitle_auto_wrap else 2
    subtitle_style = {
        "font_name": subtitle_font or "Arial",
        "font_size": int(subtitle_font_size) if subtitle_font_size is not None else 20,
        "font_color": subtitle_font_color or "#FFFFFF",
        "alignment": alignment_map.get(subtitle_alignment, 2),
        "wrap_style": wrap_style,
        # margin_v: 未设置则由 VideoCompositor 依据视频高度 × 安全区比例自动填入。
    }
    try:
        margin_v_override = int(float(subtitle_margin_v or 0))
    except (TypeError, ValueError):
        margin_v_override = 0
    if margin_v_override > 0:
        subtitle_style["margin_v"] = margin_v_override

    # 二次渲染质量：默认低质量（"l"）快速预览，确认无误后用户可切高质量重渲。
    render_quality = (render_quality or "l").strip() or "l"
    print(f"二次渲染质量: {render_quality}")

    # 调用 pipeline 重新渲染
    result = pipeline.rerender(
        manim_code=manim_code,
        srt_content=srt_content,
        progress_callback=update_progress,
        voice_id=voice_id,
        subtitle_style=subtitle_style,
        render_quality=render_quality,
    )

    if result["status"] == "success" and result.get("video_result"):
        video_path = result["video_result"]["output_path"]
        returned_code = result.get("manim_source_code", manim_code)
        returned_srt = result.get("srt_content", srt_content)
        scene_durations = result.get("scene_durations") or None
        try:
            rounds = None
            if edit_history_rounds is not None:
                try:
                    rounds = int(edit_history_rounds)
                except (TypeError, ValueError):
                    rounds = None
            if rounds is None:
                rounds = int(getattr(settings, "edit_chat_history_rounds", 8))
            save_record(
                concept=(concept or "").strip(),
                language=language or "English",
                voice_name=voice_name,
                knowledge_file_path=knowledge_file,
                manim_code=returned_code,
                srt_content=returned_srt,
                subtitle_font=subtitle_font,
                subtitle_font_size=subtitle_font_size,
                subtitle_font_color=subtitle_font_color,
                subtitle_auto_wrap=subtitle_auto_wrap,
                subtitle_alignment=subtitle_alignment,
                record_type=RECORD_TYPE_RERENDER,
                agent_params={
                    "langfuse": {
                        "user_id": (langfuse_user_id or "").strip(),
                        "session_id": (langfuse_session_id or "").strip(),
                    },
                    "edit_agent": {
                        "history_rounds": rounds,
                    },
                    "subtitle": {
                        "margin_v": margin_v_override,
                    },
                },
                scene_durations=scene_durations,
                conversation_history=conversation_history if isinstance(conversation_history, list) else [],
            )
        except Exception as e:
            print(f"历史记录保存失败: {e}")
        if Path(video_path).exists():
            return video_path, returned_code, returned_srt, scene_durations
        else:
            gr.Warning("视频文件生成后未找到，请查看日志。")
            return gr.update(), gr.update(), gr.update(), gr.update()
    else:
        error_msg = result.get("error", "重新渲染失败，请查看日志")
        gr.Warning(f"重新渲染失败: {error_msg}")
        return gr.update(), gr.update(), gr.update(), gr.update()


def _history_dropdown_choices(record_type_filter=None):
    """返回用于历史记录下拉框的 choices：[(label, id), ...]。"""
    limit = 100
    records = list_records(limit=limit, record_type=record_type_filter or None)
    choices = []
    for r in records:
        concept_short = (r.get("concept") or "")[:28]
        if len((r.get("concept") or "")) > 28:
            concept_short += "…"
        label = f"{concept_short} | {r.get('saved_at', '')} | {r.get('record_type', '')}"
        choices.append((label, str(r["id"])))
    return choices


def refresh_history_list(filter_value):
    """刷新历史列表。filter_value 为 '' / RECORD_TYPE_GENERATE / RECORD_TYPE_RERENDER。"""
    record_type = None if filter_value == "" else filter_value
    choices = _history_dropdown_choices(record_type)
    return gr.update(choices=choices, value=choices[0][1] if choices else None)


def _agent_params_defaults():
    """返回用于历史导入时 Agent 参数的默认值（与表单默认一致）。"""
    return {
        "concept_interpreter": {
            "temperature": getattr(settings, "animation_temperature", 0.5),
            "max_tokens": 16384,
            "top_p": 1.0,
            "reasoning_tokens": 4096,
            "reasoning_effort": getattr(settings, "interpreter_reasoning_effort", "low") or "low",
        },
        "manim_agent": {
            "temperature": getattr(settings, "animation_temperature", 0.5),
            "max_tokens": 16384,
            "top_p": 1.0,
            "reasoning_tokens": 4096,
            "reasoning_effort": getattr(settings, "animation_reasoning_effort", "medium") or "medium",
            "lint_enabled": bool(getattr(settings, "manim_lint_enabled", True)),
        },
        "script_generator": {
            "temperature": getattr(settings, "script_generation_temperature", 0.5),
            "max_tokens": 4096,
            "top_p": 1.0,
        },
        "langfuse": {"user_id": "", "session_id": ""},
        "edit_agent": {
            "history_rounds": int(getattr(settings, "edit_chat_history_rounds", 8)),
        },
    }


def import_history_record(record_id):
    """根据 record_id 获取记录并返回用于更新左侧所有组件的 gr.update 列表（含 Agent 参数）。"""
    empty_agent = (
        gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
        gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
        gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
        gr.update(),
    )
    empty_state_updates = (gr.update(value=[]), gr.update(value=""), gr.update(value={}), gr.update(value=[]))
    # 左侧基础字段 12 项（concept, language, voice, knowledge, manim, srt,
    # subtitle_font/size/color/wrap/alignment/margin_v）。
    empty_left = tuple(gr.update() for _ in range(12))
    if not record_id:
        return empty_left + empty_agent + empty_state_updates
    try:
        rid = int(record_id)
    except (TypeError, ValueError):
        return empty_left + empty_agent + empty_state_updates
    rec = get_record(rid)
    if not rec:
        return empty_left + empty_agent + empty_state_updates
    ap = rec.get("agent_params") or {}
    defs = _agent_params_defaults()
    ci = ap.get("concept_interpreter") or defs["concept_interpreter"]
    ma = ap.get("manim_agent") or defs["manim_agent"]
    sg = ap.get("script_generator") or defs["script_generator"]
    lf = ap.get("langfuse") or {}
    ea = ap.get("edit_agent") or defs["edit_agent"]
    imported_history = rec.get("conversation_history") or []
    imported_chatbot = _messages_to_chatbot_format(json.dumps(imported_history, ensure_ascii=False))
    agent_updates = (
        gr.update(value=float(ci.get("temperature", 0.5))),
        gr.update(value=int(ci.get("max_tokens", 16384))),
        gr.update(value=float(ci.get("top_p", 1.0))),
        gr.update(value=int(ci.get("reasoning_tokens") or 0)),
        gr.update(value=ci.get("reasoning_effort") or "low"),
        gr.update(value=float(ma.get("temperature", 0.5))),
        gr.update(value=int(ma.get("max_tokens", 16384))),
        gr.update(value=float(ma.get("top_p", 1.0))),
        gr.update(value=int(ma.get("reasoning_tokens") or 0)),
        gr.update(value=ma.get("reasoning_effort") or "medium"),
        gr.update(value=bool(ma.get("lint_enabled", bool(getattr(settings, "manim_lint_enabled", True))))),
        gr.update(value=float(sg.get("temperature", 0.5))),
        gr.update(value=int(sg.get("max_tokens", 4096))),
        gr.update(value=float(sg.get("top_p", 1.0))),
        gr.update(value=(lf.get("user_id") or "")),
        gr.update(value=(lf.get("session_id") or "")),
        gr.update(value=int(ea.get("history_rounds") or int(getattr(settings, "edit_chat_history_rounds", 8)))),
    )
    subtitle_meta = ap.get("subtitle") or {}
    try:
        margin_v_restored = int(subtitle_meta.get("margin_v", 0) or 0)
    except (TypeError, ValueError):
        margin_v_restored = 0
    return (
        gr.update(value=rec.get("concept") or ""),
        gr.update(value=rec.get("language") or "English"),
        gr.update(value=rec.get("voice_name") or ""),
        gr.update(value=rec.get("knowledge_file_path")),
        gr.update(value=rec.get("manim_code") or ""),
        gr.update(value=rec.get("srt_content") or ""),
        gr.update(value=rec.get("subtitle_font") or "Arial"),
        gr.update(value=float(rec.get("subtitle_font_size") or 20)),
        gr.update(value=rec.get("subtitle_font_color") or "#FFFFFF"),
        gr.update(value=bool(rec.get("subtitle_auto_wrap", True))),
        gr.update(value=rec.get("subtitle_alignment") or "居中对齐"),
        gr.update(value=margin_v_restored),
    ) + agent_updates + (
        gr.update(value=imported_chatbot),
        gr.update(value=""),
        gr.update(value=rec.get("scene_durations") or {}),
        gr.update(value=imported_history),
    )


def delete_history_record_ui(record_id, filter_value):
    """删除一条历史记录并返回更新后的下拉选项与状态文案。"""
    if not record_id:
        return gr.update(), "请先选择一条记录。"
    try:
        rid = int(record_id)
    except (TypeError, ValueError):
        return gr.update(), "无效的记录 ID。"
    ok = history_delete_record(rid)
    if not ok:
        return gr.update(), "删除失败或记录不存在。"
    record_type = None if filter_value == "" else filter_value
    choices = _history_dropdown_choices(record_type)
    return gr.update(choices=choices, value=choices[0][1] if choices else None), "已删除该条记录。"


def export_history_record_ui(record_id):
    """导出一条记录为 JSON 文件，返回供 gr.File 使用的路径。"""
    if not record_id:
        return gr.update(), "请先选择一条记录。"
    try:
        rid = int(record_id)
    except (TypeError, ValueError):
        return gr.update(), "无效的记录 ID。"
    path = history_export_record(rid)
    if not path:
        return gr.update(), "导出失败或记录不存在。"
    return gr.update(value=path), "已生成导出文件，请点击下方下载。"


# ========== 知识材料梳理 Agent：工具函数 ==========
def _curator_output_dir() -> Path:
    """返回知识库目录（按需创建）。"""
    raw = getattr(settings, "curator_output_dir", "data/knowledge") or "data/knowledge"
    out_dir = Path(raw)
    if not out_dir.is_absolute():
        out_dir = Path.cwd() / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _slugify_filename(name: str, fallback: str = "curated") -> str:
    """把用户输入的文件名规范化为安全的小写下划线形式，并保证 .md 后缀。"""
    if not name:
        name = fallback
    name = name.strip()
    stem = Path(name).stem or fallback
    stem = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff_\-]+", "_", stem).strip("_").lower()
    if not stem:
        stem = fallback
    return f"{stem}.md"


def _list_knowledge_library() -> list[str]:
    try:
        out_dir = _curator_output_dir()
    except Exception:
        return []
    return sorted(p.name for p in out_dir.glob("*.md"))


def curate_materials_ui(
    raw_title: str,
    raw_steps: str,
    raw_code: str,
    raw_analysis: str,
    target_language: str,
    example_hint: str,
):
    """Gradio 回调：调用 KnowledgeCuratorAgent，返回 (预览 Markdown, 原始 Markdown, 状态)。"""
    try:
        from agents.knowledge_curator import (
            KnowledgeCuratorAgent,
            format_curated_to_markdown,
        )
    except Exception as e:
        return "", "", f"❌ 加载 Agent 失败：{e}"

    if not (raw_title and raw_title.strip()):
        return "", "", "❌ 请先填写算法标题。"
    if not (raw_steps and raw_steps.strip()):
        return "", "", "❌ 请先填写算法步骤。"
    if not (raw_code and raw_code.strip()):
        return "", "", "❌ 请先填写算法代码。"

    try:
        agent = KnowledgeCuratorAgent(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.reasoning_model,
            reasoning_tokens=getattr(settings, "curator_reasoning_tokens", 4096),
            reasoning_effort=getattr(settings, "curator_reasoning_effort", "medium"),
            temperature=getattr(settings, "curator_temperature", 0.3),
            max_tokens=getattr(settings, "curator_max_tokens", 16384),
        )
        curated = agent.execute(
            raw_title=raw_title,
            raw_steps=raw_steps,
            raw_code=raw_code,
            raw_analysis=raw_analysis or "",
            target_language=target_language or "Chinese",
            example_hint=example_hint or None,
        )
        md = format_curated_to_markdown(curated)
        status = (
            f"✅ 梳理完成：{curated.title} | "
            f"{len(curated.visual_steps)} 步 | "
            f"{len(curated.animation_requirements.scene_breakdown)} 个场景 | "
            f"共 {len(md)} 字符。"
        )
        return md, md, status
    except Exception as e:
        logger.exception("Knowledge curator failed")
        return "", "", f"❌ 梳理失败：{e}"


def save_curated_to_library(markdown_text: str, filename: str):
    """保存 Markdown 到 data/knowledge/<slug>.md，并刷新知识库下拉。"""
    if not markdown_text or not markdown_text.strip():
        return "❌ 当前没有可保存的内容，请先点击「梳理并预览」。", gr.update()
    safe_name = _slugify_filename(filename)
    try:
        out_dir = _curator_output_dir()
        out_path = out_dir / safe_name
        out_path.write_text(markdown_text, encoding="utf-8")
    except Exception as e:
        return f"❌ 保存失败：{e}", gr.update()
    choices = _list_knowledge_library()
    return f"✅ 已保存到 `{out_path}`。", gr.update(choices=choices, value=safe_name)


def send_curated_to_upload(markdown_text: str, filename: str):
    """把当前预览的 Markdown 写到临时 .md 文件并赋值给主界面的 knowledge_upload。"""
    if not markdown_text or not markdown_text.strip():
        return gr.update(), "❌ 请先点击「梳理并预览」生成内容。"
    safe_name = _slugify_filename(filename)
    try:
        out_dir = _curator_output_dir()
        out_path = out_dir / safe_name
        out_path.write_text(markdown_text, encoding="utf-8")
    except Exception as e:
        return gr.update(), f"❌ 写入失败：{e}"
    return gr.update(value=str(out_path)), f"✅ 已送入「知识文档」上传框：{out_path.name}"


def load_from_knowledge_library(name: str):
    """选择知识库中的已存文档，将其内容载入预览与 Code 编辑器。"""
    if not name:
        return "", "", "请先从下拉列表选择一条记录。"
    try:
        out_dir = _curator_output_dir()
        path = out_dir / name
        if not path.exists():
            return "", "", f"❌ 文件不存在：{path}"
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return "", "", f"❌ 读取失败：{e}"
    return text, text, f"✅ 已载入 `{path.name}`（{len(text)} 字符）。"


def refresh_knowledge_library():
    return gr.update(choices=_list_knowledge_library())


# ========== Gradio UI 构建 ==========
APP_CSS = """
    .code-editor textarea { font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important; font-size: 13px !important; }
    .rerender-btn { background: #f59e0b !important; color: white !important; }
    #algo_agent_chatbot .agent-msg { border-left: 4px solid transparent; border-radius: 10px; margin: 8px 0; }
    #algo_agent_chatbot .agent-msg details { border-radius: 10px; padding: 8px 10px; }
    #algo_agent_chatbot .agent-msg summary { cursor: pointer; display: flex; align-items: center; justify-content: space-between; gap: 10px; font-weight: 600; }
    #algo_agent_chatbot .agent-msg summary::-webkit-details-marker { display: none; }
    #algo_agent_chatbot .agent-msg__meta { font-size: 12px; opacity: 0.8; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
    #algo_agent_chatbot .agent-msg pre { margin: 8px 0 0; padding: 10px; border-radius: 8px; background: rgba(0, 0, 0, 0.08); overflow-x: auto; white-space: pre-wrap; word-break: break-word; font-size: 12px; line-height: 1.45; }
    #algo_agent_chatbot .code_wrap pre { margin: 8px 0 0; padding: 10px; border-radius: 8px; background: rgba(0, 0, 0, 0.08); overflow-x: auto; white-space: pre-wrap; word-break: break-word; font-size: 12px; line-height: 1.45; }
    #algo_agent_chatbot .agent-msg--thinking { border-left-color: #7c3aed; }
    #algo_agent_chatbot .agent-msg--thinking details { background: rgba(124, 58, 237, 0.09); }
    #algo_agent_chatbot .agent-msg--tool-call { border-left-color: #0ea5e9; }
    #algo_agent_chatbot .agent-msg--tool-call details { background: rgba(14, 165, 233, 0.1); }
    #algo_agent_chatbot .agent-msg--tool-result { border-left-color: #10b981; }
    #algo_agent_chatbot .agent-msg--tool-result details { background: rgba(16, 185, 129, 0.1); }
    #algo_agent_chatbot .agent-msg--assistant details { background: rgba(255, 255, 255, 0.06); }
    #algo_agent_chatbot .agent-msg--user { border-left-color: #f59e0b; }
    #algo_agent_chatbot .agent-msg--user details { background: rgba(245, 158, 11, 0.10); }
"""

with gr.Blocks(title="AlgoT2V") as demo:
    gr.Markdown("# 🎬 AlgoT2V — 算法动画生成系统")
    gr.Markdown("输入算法概念 → 自动生成教学动画 → 支持编辑源代码和字幕后**重新渲染**")

    with gr.Row():
        # ==================== 左侧主内容 ====================
        with gr.Column(scale=3):
            # ==================== 第一部分：生成设置 ====================
            with gr.Row():
                with gr.Column(scale=1):
                    concept_input = gr.Textbox(
                        label="🎯 输入算法概念 / Enter Algorithm Concept",
                        placeholder="例如: Explain Bubble Sort, 解释快速排序, Dijkstra's Algorithm...",
                        lines=2
                    )
                    language_dropdown = gr.Dropdown(
                        choices=[ "Chinese", "English", "Spanish", "Vietnamese"],
                        value="Chinese",
                        label="🌐 旁白语言 / Narration Language"
                    )
                    voice_dropdown = gr.Dropdown(
                        choices=list(VOICE_CHOICES.keys()),
                        value=DEFAULT_VOICE,
                        label="🎙️ 语音音色 / Voice (Edge TTS)"
                    )
                    knowledge_upload = gr.File(
                        label="📄 知识文档 / Knowledge Document (可选)",
                        file_count="single",
                        type="filepath"
                    )

                    # ========== 知识材料梳理 Agent ==========
                    with gr.Accordion("📝 知识材料梳理 / Curate Raw Materials", open=False):
                        gr.Markdown(
                            "把教材式的 4 段原材料（标题 / 步骤 / 代码 / 分析）"
                            "一键重写为与 `test_knowledge.txt` 同款的动画就绪文档：自动抽取核心函数、"
                            "补充具体示例与动画要求、拆分场景。生成后可保存到本地知识库或直接送入上方的「知识文档」。"
                        )
                        cur_raw_title = gr.Textbox(
                            label="① 算法标题 / Title",
                            placeholder="例如：中序遍历的递归算法",
                            lines=1,
                        )
                        cur_raw_steps = gr.Textbox(
                            label="② 算法步骤 / Steps",
                            placeholder="原文步骤（可保留 ①②③ / (a)(b)(c) 编号）",
                            lines=8,
                        )
                        cur_raw_code = gr.Code(
                            label="③ 算法代码 / Code",
                            language="cpp",
                            lines=14,
                            interactive=True,
                            value="",
                        )
                        cur_raw_analysis = gr.Textbox(
                            label="④ 算法分析 / Complexity Analysis",
                            placeholder="时间复杂度、空间复杂度等",
                            lines=4,
                        )
                        with gr.Row():
                            cur_language = gr.Dropdown(
                                choices=["Chinese", "English", "Spanish", "Vietnamese"],
                                value="Chinese",
                                label="目标语言 / Language",
                            )
                            cur_filename = gr.Textbox(
                                label="保存文件名（可选）",
                                placeholder="例如：inorder_traversal_recursive",
                                lines=1,
                            )
                        cur_example_hint = gr.Textbox(
                            label="示例提示（可选）/ Example Hint",
                            placeholder="可选：提示 Agent 使用的具体示例，例如：先序输入 ABDH#I##E#J##CF##G##",
                            lines=2,
                        )
                        with gr.Row():
                            cur_generate_btn = gr.Button("🧠 梳理并预览", variant="primary", size="sm")
                            cur_save_btn = gr.Button("💾 保存到知识库", size="sm")
                            cur_send_btn = gr.Button("↗️ 送入「知识文档」", size="sm")
                        cur_status = gr.Markdown("")
                        cur_library_dropdown = gr.Dropdown(
                            choices=_list_knowledge_library(),
                            label="📚 知识库（data/knowledge/）",
                            value=None,
                            allow_custom_value=False,
                        )
                        with gr.Row():
                            cur_library_refresh = gr.Button("🔄 刷新列表", size="sm")
                            cur_library_load = gr.Button("📥 载入所选", size="sm")
                        with gr.Tabs():
                            with gr.TabItem("预览（渲染）"):
                                cur_preview_md = gr.Markdown("（点击「梳理并预览」后，Markdown 预览会显示在此处）")
                            with gr.TabItem("原文（可复制）"):
                                cur_preview_code = gr.Code(
                                    label="Markdown 源码",
                                    language="markdown",
                                    lines=18,
                                    interactive=True,
                                    value="",
                                )

                    # 参数设置：可展开，按 Agent 分选项卡
                    with gr.Accordion("⚙️ 参数设置（可展开）", open=False):
                        with gr.Tabs():
                            with gr.TabItem("概念解释"):
                                ci_temperature = gr.Slider(0, 2, value=getattr(settings, "animation_temperature", 0.5), step=0.1, label="Temperature")
                                ci_max_tokens = gr.Number(value=16384, minimum=256, maximum=128000, step=256, label="Max Tokens")
                                ci_top_p = gr.Slider(0, 1, value=1.0, step=0.05, label="Top P")
                                ci_reasoning_tokens = gr.Number(value=4096, minimum=0, maximum=65536, step=256, label="Reasoning Tokens (0=关)")
                                ci_reasoning_effort = gr.Dropdown(choices=["low", "medium", "high"], value=getattr(settings, "interpreter_reasoning_effort", "low") or "low", label="Reasoning Effort")
                            with gr.TabItem("动画生成"):
                                ma_temperature = gr.Slider(0, 2, value=getattr(settings, "animation_temperature", 0.5), step=0.1, label="Temperature")
                                ma_max_tokens = gr.Number(value=16384, minimum=256, maximum=128000, step=256, label="Max Tokens")
                                ma_top_p = gr.Slider(0, 1, value=1.0, step=0.05, label="Top P")
                                ma_reasoning_tokens = gr.Number(value=getattr(settings, "animation_reasoning_tokens", 4096) or 4096, minimum=0, maximum=65536, step=256, label="Reasoning Tokens (0=关)")
                                ma_reasoning_effort = gr.Dropdown(choices=["low", "medium", "high"], value=getattr(settings, "animation_reasoning_effort", "medium") or "medium", label="Reasoning Effort")
                                ma_lint_enabled = gr.Checkbox(
                                    label="启用 Manim Linter (manim-lint)",
                                    value=bool(getattr(settings, "manim_lint_enabled", True)),
                                )
                            with gr.TabItem("脚本生成"):
                                sg_temperature = gr.Slider(0, 2, value=getattr(settings, "script_generation_temperature", 0.5), step=0.1, label="Temperature")
                                sg_max_tokens = gr.Number(value=4096, minimum=256, maximum=128000, step=256, label="Max Tokens")
                                sg_top_p = gr.Slider(0, 1, value=1.0, step=0.05, label="Top P")
                            with gr.TabItem("Langfuse设置"):
                                langfuse_user_id = gr.Textbox(
                                    label="User ID（可选）",
                                    placeholder="用于在 Langfuse 中按用户区分 trace，如用户名、邮箱等",
                                    value="",
                                    lines=1,
                                )
                                langfuse_session_id = gr.Textbox(
                                    label="Session ID（可选）",
                                    placeholder="用于将同一编辑会话归并到同一 Langfuse session",
                                    value="",
                                    lines=1,
                                )
                    # 首次生成质量：默认低质量快速预览，确认效果后再用二次渲染切高质量。
                    _gen_quality_choices, _gen_quality_default = _render_quality_choices()
                    generate_quality = gr.Radio(
                        label="🎚️ 生成质量 / Generation Quality",
                        choices=_gen_quality_choices,
                        value=_gen_quality_default,
                        info="默认用低质量快速预览，最快看到渲染结果；确认无误后再用下方「二次渲染」切高质量重渲。",
                    )

                    generate_btn = gr.Button("🚀 生成动画 / Generate Animation", variant="primary", size="lg")

            # 示例
            gr.Examples(
                examples=[
                    ["解释冒泡排序"],
                    ["解释快速排序"],
                    ["解释迪杰斯特拉算法"]
                ],
                inputs=concept_input
            )

            gr.Markdown("---")

            # ==================== 第二部分：视频输出 + 源代码编辑 ====================
            gr.Markdown("## 📺 生成结果与二次编辑")
            gr.Markdown("> 视频生成完成后，下方将显示 Manim 源代码和 SRT 字幕。您可以自由编辑，然后点击 **🔄 重新渲染** 生成新视频。")

            # 视频工具箱：可展开，内含旁白字幕等选项
            with gr.Accordion("🛠️ 视频工具箱", open=False):
                with gr.Tabs():
                    with gr.TabItem("旁白字幕"):
                        subtitle_font = gr.Dropdown(
                            label="字体 / Font",
                            choices=[
                                "Arial",
                                "SimHei",
                                "SimSun",
                                "Noto Sans CJK SC",
                                "Noto Sans CJK TC",
                                "DejaVu Sans",
                                "Microsoft YaHei",
                            ],
                            value="Arial",
                        )
                        subtitle_font_size = gr.Slider(
                            minimum=12,
                            maximum=72,
                            value=20,
                            step=1,
                            label="字体大小 / Font Size",
                        )
                        subtitle_font_color = gr.ColorPicker(
                            label="字体颜色 / Font Color",
                            value="#FFFFFF",
                        )
                        subtitle_auto_wrap = gr.Checkbox(
                            label="开启自动换行 / Auto Wrap",
                            value=True,
                        )
                        subtitle_alignment = gr.Radio(
                            label="对齐方式 / Alignment",
                            choices=["左对齐", "居中对齐", "右对齐"],
                            value="居中对齐",
                        )
                        subtitle_margin_v = gr.Slider(
                            minimum=0,
                            maximum=200,
                            value=0,
                            step=2,
                            label="底部边距 MarginV（像素，0=自动）",
                            info="libass MarginV。0 表示按 settings.subtitle_margin_ratio 自动；数值越大字幕越远离底部。",
                        )
                    with gr.TabItem("编辑Agent设置"):
                        edit_history_rounds = gr.Slider(
                            minimum=1,
                            maximum=20,
                            value=int(getattr(settings, "edit_chat_history_rounds", 8)),
                            step=1,
                            label="保留最近对话轮数 N",
                        )

            with gr.Row():
                with gr.Column(scale=1):
                    video_output = gr.Video(
                        label="🎬 生成的动画 / Generated Animation",
                        autoplay=True,
                        elem_id="video_output"
                    )
                    playback_speed = gr.Slider(
                        minimum=0.25, maximum=4.0, value=1.0, step=0.25, 
                        label="▶️ 倍速播放 / Playback Speed"
                    )
                    playback_speed.change(
                        fn=None,
                        inputs=[playback_speed],
                        outputs=None,
                        js="(speed) => { const vid = document.querySelector('#video_output video'); if(vid) vid.playbackRate = speed; }"
                    )
                    video_output.change(
                        fn=None,
                        inputs=[playback_speed],
                        outputs=None,
                        js="(speed) => { setTimeout(() => { const vid = document.querySelector('#video_output video'); if(vid) vid.playbackRate = speed; }, 500); }"
                    )

            with gr.Row():
                # 左侧：Manim 源代码
                with gr.Column(scale=1):
                    manim_code_editor = gr.Code(
                        label="🐍 Manim 源代码 / Manim Source Code",
                        language="python",
                        lines=25,
                        interactive=True,
                        value=""
                    )
                # 右侧：上方为 AI 编辑过程，中间为修改指令，下方为 SRT 字幕
                with gr.Column(scale=1):
                    with gr.Accordion("AI 编辑过程 / Agent Conversation", open=True):
                        agent_chatbot = gr.Chatbot(
                            label="Agent 对话过程",
                            height=350,
                            elem_id="algo_agent_chatbot",
                            sanitize_html=True,
                            render_markdown=True,
                            # 允许我们在 chatbot message 中使用结构化折叠卡片 HTML
                            allow_tags=["details", "summary", "div", "span", "pre", "code"],
                        )
                        edit_summary = gr.Textbox(
                            label="修改摘要 / Edit Summary",
                            lines=3,
                            interactive=False,
                            value="",
                        )
                    edit_instruction = gr.Textbox(
                        label="✏️ 修改指令 / Edit Instruction",
                        placeholder="输入修改指令，例如：把第一句旁白改短；或：在第一个场景标题下增加一行说明文字",
                        lines=4,
                        max_lines=6,
                    )
                    with gr.Row():
                        ai_edit_btn = gr.Button(
                            "🤖 AI 编辑 / AI Edit",
                            variant="secondary",
                            size="lg",
                        )
                        clear_chat_btn = gr.Button(
                            "🧹 清空聊天记录",
                            variant="secondary",
                            size="lg",
                        )
                    srt_editor = gr.Textbox(
                        label="📝 SRT 字幕 / Subtitles",
                        lines=18,
                        interactive=True,
                        value="",
                        placeholder="视频生成后，SRT 字幕将显示在此处...\n您可以编辑字幕内容和时间轴，然后重新渲染。\n\n格式示例:\n1\n00:00:00,000 --> 00:00:04,000\n这里是第一句旁白文字。\n\n2\n00:00:04,500 --> 00:00:08,500\n这里是第二句旁白文字。"
                    )

            # 二次渲染质量选择：默认低质量快速预览，确认效果后再切高质量发布。
            _rr_quality_choices, _rr_quality_default = _render_quality_choices()
            with gr.Row():
                rerender_quality = gr.Radio(
                    label="🎚️ 二次渲染质量 / Re-render Quality",
                    choices=_rr_quality_choices,
                    value=_rr_quality_default,
                    info="默认用低质量快速预览，最快看到渲染结果；确认无误后切到高质量重新渲染。",
                )

            with gr.Row():
                rerender_btn = gr.Button(
                    "🔄 重新渲染 / Re-render Video",
                    variant="secondary",
                    size="lg",
                    elem_classes=["rerender-btn"]
                )

            gr.Markdown("""
            ---
            ### 💡 使用提示
            - **Manim 源代码**: 每个 `class XxxScene(Scene)` 对应一个动画场景，按顺序拼接生成最终视频
            - **SRT 字幕**: 控制旁白内容和时间轴。修改文字会重新生成配音;修改时间轴会改变字幕和语音的同步
            - **AI 编辑**: 输入自然语言修改指令，AI agent 会自动阅读并编辑代码/字幕，对话过程实时展示
            - **重新渲染**: 仅重新执行「渲染动画 → 合成语音 → 合成视频」，无需重新调用 AI 生成代码
            - **注意**: 请确保 Manim 代码语法正确，否则渲染会失败
            """)

        # ==================== 右侧：历史记录侧栏 ====================
        with gr.Column(scale=1):
            gr.Markdown("## 📋 历史记录")
            history_filter = gr.Radio(
                choices=[("全部", ""), ("仅生成", RECORD_TYPE_GENERATE), ("仅重新渲染", RECORD_TYPE_RERENDER)],
                value="",
                label="类型筛选",
            )
            history_refresh_btn = gr.Button("🔄 刷新列表", size="sm")
            history_dropdown = gr.Dropdown(
                choices=[],
                label="选择记录",
                value=None,
                allow_custom_value=False,
            )
            with gr.Row():
                history_import_btn = gr.Button("📥 导入", size="sm")
                history_delete_btn = gr.Button("🗑️ 删除", size="sm")
                history_export_btn = gr.Button("📤 导出", size="sm")
            history_status = gr.Markdown("", visible=True)
            history_export_file = gr.File(label="导出文件", visible=True, interactive=False)

    # ==================== 事件绑定 ====================

    # 生成按钮 → 输出视频 + 填充代码编辑器和字幕编辑器
    scene_durations_state = gr.State({})
    edit_conversation_state = gr.State([])

    generate_btn.click(
        fn=generate_animation,
        inputs=[
            concept_input,
            language_dropdown,
            voice_dropdown,
            knowledge_upload,
            subtitle_font,
            subtitle_font_size,
            subtitle_font_color,
            subtitle_auto_wrap,
            subtitle_alignment,
            subtitle_margin_v,
            ci_temperature,
            ci_max_tokens,
            ci_top_p,
            ci_reasoning_tokens,
            ci_reasoning_effort,
            ma_temperature,
            ma_max_tokens,
            ma_top_p,
            ma_reasoning_tokens,
            ma_reasoning_effort,
            ma_lint_enabled,
            sg_temperature,
            sg_max_tokens,
            sg_top_p,
            langfuse_user_id,
            langfuse_session_id,
            generate_quality,
        ],
        outputs=[video_output, manim_code_editor, srt_editor, scene_durations_state],
    )

    # AI 编辑按钮 → agent 自动编辑代码/字幕，展示对话过程和修改摘要
    ai_edit_btn.click(
        fn=ai_edit_code,
        inputs=[
            manim_code_editor,
            srt_editor,
            edit_instruction,
            langfuse_user_id,
            langfuse_session_id,
            scene_durations_state,
            edit_conversation_state,
            edit_history_rounds,
            concept_input,
            language_dropdown,
            voice_dropdown,
            knowledge_upload,
            subtitle_font,
            subtitle_font_size,
            subtitle_font_color,
            subtitle_auto_wrap,
            subtitle_alignment,
        ],
        outputs=[manim_code_editor, srt_editor, agent_chatbot, edit_summary, edit_conversation_state],
    )
    clear_chat_btn.click(
        fn=clear_agent_chat,
        inputs=[],
        outputs=[agent_chatbot, edit_summary, edit_conversation_state],
    )

    # ==================== 知识材料梳理事件绑定 ====================
    cur_generate_btn.click(
        fn=curate_materials_ui,
        inputs=[
            cur_raw_title,
            cur_raw_steps,
            cur_raw_code,
            cur_raw_analysis,
            cur_language,
            cur_example_hint,
        ],
        outputs=[cur_preview_md, cur_preview_code, cur_status],
    )
    cur_save_btn.click(
        fn=save_curated_to_library,
        inputs=[cur_preview_code, cur_filename],
        outputs=[cur_status, cur_library_dropdown],
    )
    cur_send_btn.click(
        fn=send_curated_to_upload,
        inputs=[cur_preview_code, cur_filename],
        outputs=[knowledge_upload, cur_status],
    )
    cur_library_refresh.click(
        fn=refresh_knowledge_library,
        inputs=[],
        outputs=[cur_library_dropdown],
    )
    cur_library_load.click(
        fn=load_from_knowledge_library,
        inputs=[cur_library_dropdown],
        outputs=[cur_preview_md, cur_preview_code, cur_status],
    )

    # 重新渲染按钮 → 使用编辑后的代码、字幕及工具箱中的旁白字幕设置重新生成视频
    rerender_btn.click(
        fn=rerender_video,
        inputs=[
            manim_code_editor,
            srt_editor,
            voice_dropdown,
            subtitle_font,
            subtitle_font_size,
            subtitle_font_color,
            subtitle_auto_wrap,
            subtitle_alignment,
            subtitle_margin_v,
            rerender_quality,
            concept_input,
            language_dropdown,
            knowledge_upload,
            langfuse_user_id,
            langfuse_session_id,
            edit_conversation_state,
            edit_history_rounds,
        ],
        outputs=[video_output, manim_code_editor, srt_editor, scene_durations_state],
    )

    # 历史记录：刷新列表
    history_refresh_btn.click(
        fn=refresh_history_list,
        inputs=[history_filter],
        outputs=[history_dropdown],
    )
    # 历史记录：导入
    history_import_btn.click(
        fn=import_history_record,
        inputs=[history_dropdown],
        outputs=[
            concept_input,
            language_dropdown,
            voice_dropdown,
            knowledge_upload,
            manim_code_editor,
            srt_editor,
            subtitle_font,
            subtitle_font_size,
            subtitle_font_color,
            subtitle_auto_wrap,
            subtitle_alignment,
            subtitle_margin_v,
            ci_temperature,
            ci_max_tokens,
            ci_top_p,
            ci_reasoning_tokens,
            ci_reasoning_effort,
            ma_temperature,
            ma_max_tokens,
            ma_top_p,
            ma_reasoning_tokens,
            ma_reasoning_effort,
            ma_lint_enabled,
            sg_temperature,
            sg_max_tokens,
            sg_top_p,
            langfuse_user_id,
            langfuse_session_id,
            edit_history_rounds,
            agent_chatbot,
            edit_summary,
            scene_durations_state,
            edit_conversation_state,
        ],
    )
    # 历史记录：删除
    history_delete_btn.click(
        fn=delete_history_record_ui,
        inputs=[history_dropdown, history_filter],
        outputs=[history_dropdown, history_status],
    )
    # 历史记录：导出
    history_export_btn.click(
        fn=export_history_record_ui,
        inputs=[history_dropdown],
        outputs=[history_export_file, history_status],
    )
    # 页面加载时刷新历史列表
    demo.load(
        fn=refresh_history_list,
        inputs=[history_filter],
        outputs=[history_dropdown],
    )

# 脚本入口
if __name__ == "__main__":
    demo.launch(
        share=False,
        inbrowser=True,
        css=APP_CSS,
    )