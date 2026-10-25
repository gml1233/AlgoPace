"""树算法视频的标题布局与中文字幕分段。"""

import re

from manim import UP, config
from manim_voiceover import VoiceoverScene


def split_tree_subcaptions(text, max_length=42):
    """按中文标点分段，保留英文名称、变量和简单公式的完整性。"""
    text = " ".join(text.split())
    tokens = re.findall(r"[A-Za-z_][A-Za-z_0-9]*(?:\[[^\]\n]*\])?(?:\([^\)\n]*\))?|\d+|.", text)
    lines = []
    line_length = max(1, max_length // 2)
    while tokens:
        length = 0
        end = 0
        punctuation_end = 0
        for index, token in enumerate(tokens):
            if length + len(token) > line_length and end:
                break
            length += len(token)
            end = index + 1
            if token in "。！？；，：" and length >= line_length / 2:
                punctuation_end = end
        if end < len(tokens) and punctuation_end:
            end = punctuation_end
        caption = "".join(tokens[:end]).strip()
        if caption:
            lines.append(caption)
        tokens = tokens[end:]
    return ["\n".join(lines[i:i + 2]) for i in range(0, len(lines), 2)]


class TreeVideoScene(VoiceoverScene):
    """将长中文旁白拆成短字幕，避免空格分词产生四行字幕。"""

    def add_wrapped_subcaption(self, subcaption, duration, subcaption_buff=0.1,
                              max_subcaption_len=70):
        captions = split_tree_subcaptions(subcaption, min(max_subcaption_len, 42))
        total_length = sum(len(caption.replace("\n", "")) for caption in captions)
        offset = 0.0
        for caption in captions:
            caption_duration = duration * len(caption.replace("\n", "")) / total_length
            self.add_subcaption(caption, duration=max(0, caption_duration - subcaption_buff),
                                offset=offset)
            offset += caption_duration


def fit_tree_title(title, logo, top_buff=0.55):
    """把标题放在标志左侧的可用宽度内。"""
    left = -config.frame_width / 2 + 0.45
    right = logo.get_left()[0] - 0.3
    if title.width > right - left:
        title.scale_to_fit_width(right - left)
    title.set_x((left + right) / 2).to_edge(UP, buff=top_buff)
    return title


def place_tree_summary(panel, title):
    """让核心思想看板位于标题下方，并保留底部两行字幕空间。"""
    top = min(title.get_bottom()[1] - 0.3, 1.9)
    bottom = -2.2
    scale = min(1.0, 11.8 / panel.width, (top - bottom) / panel.height)
    panel.scale(scale).set_x(0).set_y(top - panel.height / 2)
    return panel
