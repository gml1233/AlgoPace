import datetime
import logging
import re
from pathlib import Path
from typing import List, Tuple

import srt

from agents.manim_models import ManimSceneCode, RenderResult


logger = logging.getLogger(__name__)


# CJK 字符范围：汉字 + CJK 标点/全角符号
_CJK_CHAR = r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef]'

# 删除 CJK 与 ASCII 变量/数字/标点之间的多余空格（双向）。
# 1) 中文字符 + 空白 + ASCII（字母/数字/常见起始符） → 去掉空白
_RE_CJK_LEFT_ASCII_RIGHT = re.compile(
    rf'({_CJK_CHAR})[ \t]+(?=[A-Za-z0-9\(\[\{{\"\'\$])'
)
# 2) ASCII（字母/数字/常见结尾符） + 空白 + 中文字符 → 去掉空白
_RE_ASCII_LEFT_CJK_RIGHT = re.compile(
    rf'(?<=[A-Za-z0-9\)\]\}}\"\'\$%])[ \t]+({_CJK_CHAR})'
)


def _normalize_cjk_spacing(text: str) -> str:
    """去掉 CJK 字符与 ASCII 字母/数字/符号之间被 LLM 错误插入的空格。

    典型场景：
      "移动到节点 D 的左子树" → "移动到节点D的左子树"
      "空间复杂度是 N"         → "空间复杂度是N"
      "比较第 i 个元素"        → "比较第i个元素"
    """
    if not text:
        return text
    out = _RE_CJK_LEFT_ASCII_RIGHT.sub(r'\1', text)
    out = _RE_ASCII_LEFT_CJK_RIGHT.sub(r'\1', out)
    return out


def _strip_terminal_period(text: str) -> str:
    """Remove terminal period-like punctuation for subtitle style consistency."""
    stripped = text.rstrip()
    while stripped.endswith(("。", ".", "．")):
        stripped = stripped[:-1].rstrip()
    return stripped


def merge_scene_srts(
    scene_codes: List[ManimSceneCode],
    render_results: List[RenderResult],
    output_dir: Path,
    output_stem: str = "voiceover_script",
) -> Tuple[Path, str]:
    """Merge per-scene Manim-generated SRT files into one timeline."""
    output_dir.mkdir(parents=True, exist_ok=True)

    render_by_scene_id = {item.scene_id: item for item in render_results if item.success}
    merged_subtitles: List[srt.Subtitle] = []
    scene_offset = 0.0

    for scene_code in scene_codes:
        scene_result = render_by_scene_id.get(scene_code.scene_id)
        scene_duration = float(scene_result.duration or 0.0) if scene_result else 0.0
        subtitle_path = Path(scene_result.subtitle_path) if scene_result and scene_result.subtitle_path else None

        if subtitle_path is None or not subtitle_path.exists():
            logger.warning(
                "Subtitle file missing for scene %s (scene_id=%s): %s",
                scene_code.scene_name,
                scene_code.scene_id,
                subtitle_path,
            )
            scene_offset += scene_duration
            continue

        try:
            scene_subtitles = list(srt.parse(subtitle_path.read_text(encoding="utf-8")))
        except Exception as exc:
            logger.warning("Failed to parse subtitle file %s: %s", subtitle_path, exc)
            scene_offset += scene_duration
            continue

        delta = datetime.timedelta(seconds=scene_offset)
        for subtitle in scene_subtitles:
            merged_subtitles.append(
                srt.Subtitle(
                    index=0,
                    start=subtitle.start + delta,
                    end=subtitle.end + delta,
                    content=_normalize_cjk_spacing(_strip_terminal_period(subtitle.content)),
                    proprietary=subtitle.proprietary,
                )
            )

        scene_offset += scene_duration

    for index, subtitle in enumerate(merged_subtitles, start=1):
        subtitle.index = index

    srt_content = srt.compose(merged_subtitles).strip()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{output_stem}_{timestamp}.srt"
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(srt_content)
        if srt_content:
            file.write("\n")

    return output_path, srt_content
