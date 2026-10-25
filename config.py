# 导入os模块，用于处理系统环境变量相关操作
import os
# 从pydantic_settings模块导入BaseSettings类，用于构建配置类（支持从.env文件和环境变量加载配置）
from pydantic_settings import BaseSettings
# 从pydantic模块导入Field（用于配置项约束）和validator（用于自定义配置校验逻辑）
from pydantic import Field, validator
# 从pathlib模块导入Path类，用于优雅处理跨平台文件路径
from pathlib import Path
# 从typing模块导入Optional（可选类型）和Any（任意类型），用于类型注解
from typing import Optional, Any


class Settings(BaseSettings):
    # 配置类：继承自BaseSettings，用于管理整个项目的所有配置参数
    # 特性：自动从.env文件加载配置，支持环境变量覆盖，自带数据校验功能

    # ========== API 密钥配置区 ==========
    # OpenRouter API密钥（必填，用于调用大模型进行推理）
    openrouter_api_key: str
    # Google API密钥（必填，用于调用Gemini多模态模型生成脚本）
    google_api_key: str
    # ElevenLabs API密钥（可选，用于ElevenLabs语音合成，仅当tts_provider为elevenlabs时需要）
    elevenlabs_api_key: Optional[str] = None
    # OpenAI API密钥（可选，用于OpenAI语音合成，仅当tts_provider为openai时需要）
    openai_api_key: Optional[str] = None
    # Azure Speech 订阅密钥（可选，当前 edge provider 不需要；仅保留历史兼容）
    azure_subscription_key: Optional[str] = None
    # Azure Speech 服务区域（可选，当前 edge provider 不需要；仅保留历史兼容）
    azure_service_region: Optional[str] = None

    # ========== OpenRouter 配置区 ==========
    # OpenRouter API的基础请求地址（默认值固定，无需修改）
    openrouter_base_url: str = "https://api.jiekou.ai/openai"

    # ========== 模型选择配置区（OpenRouter 模型ID） ==========
    # 推理模型（用于概念解释、动画规划等逻辑推理任务，默认使用deepseek-v3.2）
    reasoning_model: str = "gemini-3.1-pro-preview"
    # 多模态模型（用于生成旁白脚本，支持图文理解，默认使用google/gemini-2.5-pro）
    multimodal_model: str = "gemini-3.1-pro-preview"

    # ========== TTS（语音合成）提供商选择 ==========
    # 语音服务商选择（支持"elevenlabs"、"openai"、"edge"、"coqui"；edge 为免费在线 TTS）
    tts_provider: str = "edge"  # "elevenlabs", "openai", "edge(=EdgeTTSService)", "coqui"

    # ========== ElevenLabs 专属配置（当tts_provider="elevenlabs"时生效） ==========
    # ElevenLabs 语音音色ID（对应特定的发音人，默认值为一个预配置音色）
    # Bella - Professional, Bright, Warm (免费可用，适合教学内容)
    elevenlabs_voice_id: str = "hpp4J3VqNfWAUOO0d1Us"
    # ElevenLabs 语音合成模型ID（默认使用eleven_v3，效果更优）
    elevenlabs_model_id: str = "eleven_v3"
    # 语音稳定性（只能是 0.0/0.5/1.0，0.0=创意，0.5=自然，1.0=稳健，默认0.5）
    elevenlabs_stability: float = 0.5
    # 语音相似度增强（只能是 0.0/0.5/1.0，值越高越贴近选定音色，默认0.5）
    elevenlabs_similarity_boost: float = 0.5
    # 语音风格化程度（0-1，值越高风格越鲜明，默认0.0）
    elevenlabs_style: float = 0.0
    # 是否启用说话人增强（提升音色辨识度，默认开启）
    elevenlabs_use_speaker_boost: bool = True

    # ========== Edge 专属配置（当tts_provider="edge"时生效） ==========
    # Edge 语音音色（默认使用云希，男声专业讲解风格，中文发音极佳）
    # 可选音色: zh-CN-XiaoxiaoNeural(女), zh-CN-YunxiNeural(男), zh-CN-YunyangNeural(男播报)
    #          zh-CN-XiaoyiNeural(女), zh-CN-YunjianNeural(男浑厚), zh-CN-XiaomoNeural(女温柔)
    edge_tts_voice: str = "zh-CN-YunxiNeural"
    # Edge 语速调节（-50% ~ +200%，默认+0%正常语速）
    edge_tts_rate: str = "+0%"
    # Edge 音量调节（-50% ~ +100%，默认+0%正常音量）
    edge_tts_volume: str = "+0%"
    # Edge 音调调节（-50Hz ~ +50Hz，默认+0Hz正常音调）
    edge_tts_pitch: str = "+0Hz"

    # ========== OpenAI 专属配置（当tts_provider="openai"时生效） ==========
    # OpenAI 语音音色选择（支持alloy、echo、fable、onyx、nova、shimmer，默认alloy）
    openai_voice: str = "nova"
    # OpenAI 语音合成模型（默认tts-1，另有tts-1-hd（高清音质，速度较慢））
    openai_model: str = "tts-1"
    # OpenAI API 自定义端点（为空时使用官方默认端点，支持代理地址，默认空字符串）
    openai_endpoint: str = ""
    # OpenAI 音频输出格式（默认mp3，支持opus、aac、flac等）
    openai_response_format: str = "mp3"
    # 语音播放速度（0.5-4.0，默认1.0为正常速度）
    openai_speed: float = 1.0

    # ========== TTS 通用配置（所有语音合成服务商均生效） ==========
    # 语音合成失败后的最大重试次数（默认3次）
    tts_max_retries: int = 3
    # 语音合成单次请求的超时时间（单位：秒，默认120秒）
    tts_timeout: int = 120  # seconds

    # ========== 项目文件路径配置 ==========
    # 项目根输出目录（所有生成文件的父目录，默认在当前工作目录下创建output文件夹）
    output_dir: Path = Path("output")

    # ========== 动态路径属性（使用@property装饰器，基于output_dir自动生成子目录，无需手动赋值） ==========
    @property
    def scenes_dir(self) -> Path:
        # 场景文件输出目录（output/scenes）
        return self.output_dir / "scenes"

    @property
    def animations_dir(self) -> Path:
        # 动画文件输出目录（output/animations）
        return self.output_dir / "animations"

    @property
    def audio_dir(self) -> Path:
        # 音频文件输出目录（output/audio）
        return self.output_dir / "audio"

    @property
    def scripts_dir(self) -> Path:
        # 脚本文件输出目录（output/scripts）
        return self.output_dir / "scripts"

    @property
    def final_dir(self) -> Path:
        # 最终成品视频输出目录（output/final）
        return self.output_dir / "final"

    @property
    def analyses_dir(self) -> Path:
        # 概念分析结果输出目录（output/analyses）
        return self.output_dir / "analyses"

    @property
    def rendering_dir(self) -> Path:
        # 渲染过程文件输出目录（output/rendering）
        return self.output_dir / "rendering"

    @property
    def generation_dir(self) -> Path:
        # 生成过程文件输出目录（output/generation）
        return self.output_dir / "generation"

    @property
    def lint_reports_dir(self) -> Path:
        """manim-lint JSON 报告目录（output/lint_reports）"""
        return self.output_dir / "lint_reports"

    @property
    def langfuse_enabled(self) -> bool:
        """True when both Langfuse public and secret keys are set (non-empty)."""
        return bool(
            self.langfuse_public_key and self.langfuse_public_key.strip()
            and self.langfuse_secret_key and self.langfuse_secret_key.strip()
        )
    # ========== Manim 动画渲染配置 ==========
    # Manim 动画渲染质量（默认"p"表示生产环境质量（1080p60），另有"l"（低质量）、"m"（中等质量））
    manim_quality: str = "p"  # Production quality (1080p60)
    # Manim 动画背景色（十六进制颜色码，默认深灰黑色#0f0f0f）
    manim_background_color: str = "#0f0f0f"
    # Manim 动画帧率（默认60帧/秒，对应高清视频标准）
    manim_frame_rate: int = 60
    # 快速预览（quality="l"）的渲染帧率。-q l 只把分辨率降到 854x480，帧率仍是
    # 15fps，而 voiceover 场景的时长由旁白锁死，每一帧静止画面都要真实光栅化并
    # 编码——帧数才是预览耗时的主要杠杆。设为 0 表示沿用 -q l 自带的 15fps。
    manim_preview_fps: int = 10
    # Manim 单个场景渲染的超时时间（单位：秒，默认300秒）
    manim_render_timeout: int = 1800  # seconds
    # Manim 动画渲染整体失败后的最大重试次数（3→2 降本，重试会重复调用 LLM 是隐形成本大头）
    manim_max_retries: int = 2
    # Manim 单个场景的最长时长（单位：秒，默认60秒，复杂算法代码跟踪需要更长）
    manim_max_scene_duration: float = 60.0  # seconds
    # Manim 整体动画的目标总时长（单位：秒，默认240秒，详细代码跟踪需要更长视频）
    manim_total_video_duration_target: float = 240.0  # seconds

    # manim-linter：对生成代码做静态检查（与当前环境已安装的 Manim 版本一致）
    manim_lint_enabled: bool = True
    manim_lint_max_fix_attempts: int = 2
    manim_lint_geometry: str = "manim_points"  # auto, aabb, manim_points
    manim_lint_timeout: int = 60  # seconds per file

    # 渲染失败自动修复：Manim 渲染子进程报错时，把 stderr 喂给 LLM 重新生成代码并再渲染
    # （覆盖静态 lint 抓不到的运行时错误，例如 ManimColor==str TypeError、AttributeError 等）
    manim_render_fix_enabled: bool = True
    manim_render_fix_max_attempts: int = 1  # 2→1 降本：每轮修复都重新调用 LLM 重生成代码

    # ========== 场景修复三级策略（防止场景丢失）==========
    # Tier 2：Tier 1（RENDER_FIX_PROMPT 补丁修复）全部失败后，按原 ScenePlan 整段重生成代码
    manim_render_regen_enabled: bool = True
    # Tier 2 重生成时的温度加成（与 animation_temperature 叠加，最高 clamp 到 1.0）
    manim_render_regen_temperature_boost: float = 0.3
    # Tier 3：Tier 2 仍失败时，落地为"标题+描述+voiceover"的极简占位场景
    # 关键承诺：该兜底保证永不丢场景，对应"不允许有场景丢失"
    manim_render_stub_enabled: bool = True

    ### NOTE: For Anthropic models (Sonnet 4/4.5, Opus 4/4.1), use only either reasoning tokens or reasoning effort, if both are used, reasoning effort will be prioritized
    ### For OpenAI models (GPT-5, o3, o4-mini), only reasoning effort can trigger reasoning
    # 注释说明：
    # 1. 对于Anthropic模型（Sonnet 4/4.5, Opus 4/4.1），tokens和effort二选一即可，若同时配置，effort优先级更高
    # 2. 对于OpenAI模型（GPT-5, o3, o4-mini），仅支持effort配置来触发推理优化

    # ========== 推理配置（Anthropic 风格）- 概念解释专用 ==========
    # 概念解释步骤的最大推理token数限制（可选，默认2048）
    interpreter_reasoning_tokens: Optional[int] = 2048
    # 动画生成步骤的最大推理token数限制（可选，4096→2048 降本，代码生成推理token减半）
    animation_reasoning_tokens: Optional[int] = 2048

    # ========== 推理配置（Anthropic 风格）- 推理力度 ==========
    # 概念解释步骤的推理力度（可选，支持"low"、"medium"、"high"，默认"low"）
    interpreter_reasoning_effort: Optional[str] = "low"
    # 动画生成步骤的推理力度（high→medium 降本，代码生成是最大开销项，medium 通常仍可用）
    animation_reasoning_effort: Optional[str] = "medium"

    # ========== 知识材料梳理（Curator）Agent 配置 ==========
    # 用于把原始的 4 段材料（标题/步骤/代码/分析）重写成动画就绪的知识文档。
    # 最大推理token数限制（可选，默认4096；需要抽核心函数+补动画要求，建议略高）
    curator_reasoning_tokens: Optional[int] = 4096
    # 推理力度（low/medium/high，默认medium）
    curator_reasoning_effort: Optional[str] = "medium"
    # 温度（越低越保守，默认 0.3）
    curator_temperature: float = 0.3
    # 最大输出 token（默认 16384，知识文档可能较长）
    curator_max_tokens: int = 16384
    # 梳理结果的本地知识库落盘目录（相对项目根目录）
    curator_output_dir: str = "data/knowledge"

    # ========== 动画生成配置 ==========
    # 动画生成的随机性（0-1，值越低越精确，代码跟踪类动画建议低值，默认0.3）
    animation_temperature: float = 0.3
    # 单个场景动画生成失败后的最大重试次数（3→2 降本，每次重试都重新调用 LLM 生成整段代码）
    animation_max_retries_per_scene: int = 2
    # 是否启用动画逻辑简化（提升渲染成功率，默认开启）
    animation_enable_simplification: bool = True

    # ========== 编辑 Agent 配置（修改 pipeline，用于根据用户指令修改 Manim/SRT） ==========
    # 编辑步骤使用的模型（为空时使用 reasoning_model）
    edit_model: Optional[str] = "MiniMax-M2.7-highspeed"
    # 编辑步骤使用的 OpenRouter API Key（为空时使用全局 openrouter_api_key）
    edit_openrouter_api_key: Optional[str] = "sk-cp-oT9jL1b-u_0ou6nbOZn6r4VNDS06jUzV_Vdfb-TKVMl11kyP3OrfTQNfVdLAJ-EMs88n8qA-w0aOZvAbD9umqbZYZGBWoV-YbzSTX1OntL2kJJjaSa7xZPY"
    # 编辑步骤使用的 OpenRouter Base URL（为空时使用全局 openrouter_base_url）
    edit_openrouter_base_url: Optional[str] = "https://api.minimaxi.com/v1"
    # 编辑步骤的随机性（默认 0.3，偏保守）
    edit_temperature: float = 0.3
    # 编辑步骤的最大输出 token 数
    edit_max_tokens: int = 32768
    # 编辑步骤的最大推理 token 数（可选，默认 None）
    edit_reasoning_tokens: Optional[int] = None
    # 编辑步骤的推理力度（可选，支持"low"、"medium"、"high"）
    edit_reasoning_effort: Optional[str] = None
    # 编辑 Agent 多轮会话保留的最近轮数（按 user 回合计数）
    edit_chat_history_rounds: int = 8

    # ========== 脚本生成配置 ==========
    # 脚本生成的随机性（0-1，值越高脚本内容越灵活，默认0.5）
    script_generation_temperature: float = 0.5
    # 脚本生成失败后的最大重试次数（默认3次）
    script_generation_max_retries: int = 3
    # 脚本生成单次请求的超时时间（单位：秒，默认180秒）
    script_generation_timeout: int = 180  # seconds

    # ========== 语音合成配置（重复配置，兼容旧代码，与上方TTS配置一致） ==========
    tts_voice_id: str = "Qggl4b0xRMiqOwhPtVWT"
    tts_model_id: str = "eleven_v3"
    tts_stability: float = 0.75
    tts_similarity_boost: float = 0.75
    tts_style: float = 0.0
    tts_use_speaker_boost: bool = True
    tts_max_retries: int = 3
    tts_timeout: int = 120  # seconds

    # ========== 视频编码配置 ==========
    # 视频编码器（默认libx264，兼容性最好、压缩比最优）
    video_codec: str = "libx264"
    # 视频编码预设（默认medium，平衡编码速度和文件大小，可选fast（快）、slow（优））
    video_preset: str = "medium"
    # 字幕烧录那一遍的编码预设，独立于 video_preset。烧录是重渲染里唯一一次全片
    # 编码，而它的输出质量由 crf 锁定，preset 只影响压缩效率：实测 medium→veryfast
    # 省 1.35s，音频逐比特不变、PSNR 47dB、文件反而更小。
    # 单独一项而不是改 video_preset，因为后者还被多场景拼接分支用于首次生成。
    subtitle_burn_preset: str = "veryfast"
    # 视频恒定速率因子（0-51，值越低质量越高、文件越大，默认23为平衡值）
    video_crf: int = 23  # Constant Rate Factor (0-51, lower = higher quality)
    # 音频编码器（默认aac，兼容性最好）
    audio_codec: str = "aac"
    # 音频比特率（默认128k，平衡音频质量和文件大小，可选192k、256k）
    audio_bitrate: str = "128k"

    # ========== 字幕配置 ==========
    # 是否将字幕烧录到视频中（硬字幕，不可修改，默认开启）
    subtitle_burn_in: bool = True  # Burn subtitles into video (hard subs)
    # 字幕字体大小（默认20，与 FFmpeg/libass 常见默认一致，适合1080p视频）
    subtitle_font_size: int = 20
    # 字幕字体颜色（默认白色，对比鲜明）
    subtitle_font_color: str = "white"
    # 是否显示字幕背景（默认开启，提升字幕可读性）
    subtitle_background: bool = True
    # 字幕背景透明度（0-1，值越低越透明，默认0.5）
    subtitle_background_opacity: float = 0.5
    # 字幕在视频中的位置（支持top、center、bottom，默认bottom底部）
    subtitle_position: str = "bottom"  # top, center, bottom
    # 底部字幕安全区占画面高度的比例（约 90/1080 ≈ 8.3%，动画避让用）
    subtitle_safe_zone_ratio: float = 0.083
    # 字幕安全区对应的 Manim 逻辑单位高度（= 8 * subtitle_safe_zone_ratio ≈ 0.67）
    # Manim 默认画面高 8 单位，y 范围约 -4 ~ +4；该值定义 y ∈ [-4, -4 + subtitle_safe_zone_units] 为禁放区
    subtitle_safe_zone_units: float = 0.67
    # 自动计算 MarginV 时在安全区内部的比例因子：越小字幕越贴底；
    # 旧默认为 0.35（1440p 下 ≈42px，视觉偏上）；现改为 0.15（≈18px，更贴底）。
    subtitle_margin_ratio: float = 0.15

    # ========== 视频合成配置 ==========
    # 视频合成失败后的最大重试次数（默认3次）
    video_composition_max_retries: int = 3
    # 视频合成单次请求的超时时间（单位：秒，默认600秒）
    video_composition_timeout: int = 600  # seconds

    # ========== LLM（大语言模型）通用配置 ==========
    # LLM 请求失败后的最大重试次数（默认3次）
    llm_max_retries: int = 3
    # LLM 单次请求的超时时间（单位：秒，默认120秒）
    llm_timeout: int = 120  # seconds

    # ========== Langfuse 可观测性配置（可选） ==========
    # Langfuse 公钥（与 secret_key 同时配置时启用 trace，否则不上报）
    langfuse_public_key: Optional[str] = "pk-lf-4eed4cd4-ac11-405b-a222-78da6252ece1"
    # Langfuse 私钥
    langfuse_secret_key: Optional[str] = "sk-lf-d04f7336-40aa-46fb-9099-f0d51a5327a9"
    # Langfuse 服务地址（可选，默认 EU cloud；自托管或 US 需设置）
    langfuse_base_url: Optional[str] = "https://langfuse.mcpnet.cn"

    # ========== 知识文档配置（可选，用于基于本地文档生成视频脚本） ==========
    # 是否启用知识文档模式（开启后将优先参考知识文档内容生成脚本，默认关闭）
    use_knowledge_document: bool = False
    # 知识文档文件路径（可选，支持.txt/.md文件，当use_knowledge_document为True时生效）
    knowledge_document_path: Optional[str] = None

    # ========== 语言配置 ==========
    # 目标语言（支持English、Chinese、Spanish、Vietnamese，默认English）
    target_language: str = "English"  # Supported: English, Chinese, Spanish, Vietnamese

    # ========== 自定义配置校验器 ==========
    @validator("tts_provider")
    def validate_tts_provider(cls, v):
        allowed = {"elevenlabs", "openai", "edge", "coqui"}
        provider = (v or "").strip().lower()
        if provider not in allowed:
            raise ValueError("tts_provider must be one of: elevenlabs, openai, edge, coqui")
        return provider

    # ========== 配置类的内部配置 ==========
    class Config:
        # 指定.env文件作为配置来源（默认读取当前工作目录下的.env文件）
        env_file = ".env"
        # 指定.env文件的编码格式为utf-8（避免中文配置乱码）
        env_file_encoding = "utf-8"
        # 允许接收额外的配置项（来自.env或环境变量，不强制与类中定义的字段匹配）
        extra = "allow"  # Allow extra fields from environment

    # ========== 目录创建方法 ==========
    def create_directories(self):
        """Create all output directories if they don't exist"""
        # 方法功能：创建所有项目所需的输出目录，若目录已存在则不报错

        # 遍历所有需要创建的目录路径列表
        for dir_path in [
            self.output_dir,
            self.scenes_dir,
            self.animations_dir,
            self.audio_dir,
            self.scripts_dir,
            self.final_dir,
            self.analyses_dir,
            self.rendering_dir,
            self.generation_dir,
            self.lint_reports_dir,
        ]:
            # 创建目录：
            #   parents=True：自动创建父目录（如output不存在则先创建output）
            #   exist_ok=True：目录已存在时不抛出异常
            dir_path.mkdir(parents=True, exist_ok=True)


# ========== 配置实例化工具函数 ==========
# Initialize settings and create directories
# Note: Settings will be initialized with environment variables
# Use Settings() in your code to get the configuration
def get_settings():
    """Get settings instance with environment variables"""
    # 函数功能：获取Settings配置实例（自动从.env文件和环境变量加载配置）
    return Settings()


# ========== 全局配置实例化 & 目录初始化 ==========
# 创建全局配置实例（整个项目可直接导入该实例使用配置）
settings = get_settings()
# 调用配置实例的create_directories方法，创建所有必要的输出目录
settings.create_directories()