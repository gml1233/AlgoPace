"""排序讲解专用的配音、完整字幕分页和代码框布局。

显示文本与配音文本分开处理；不修改项目共用的 TTS 服务。
画面底部 y < -2.65 留给最多两行字幕。
"""
import re


def display_caption(text):
    """字幕中的数组下标和增量使用数字，保留其余原文。"""
    digits = {c: str(i) for i, c in enumerate("零一二三四五六七八九")}
    text = re.sub(r"(?<![A-Za-z])r\s*([零一二三四五六七八九])(?![十百])",
                  lambda m: f"r[{digits[m[1]]}]", text)
    text = re.sub(r"(?<![A-Za-z])r\s+(\d+)", r"r[\1]", text)
    return re.sub(r"(?<![A-Za-z])(dk|d)\s*等于一", r"\1 = 1", text)


def spoken_sorting_text(text):
    """只用于合成语音：先展开运算，再读变量，避免符号被忽略。"""
    text = text.replace("当前子表", "当前待排序区间").replace("一段子表", "一段待排序区间")
    text = text.replace("本趟", "这一轮").replace("整体后移", "全部向后移动")
    text = text.replace("后移", "向后移动").replace("if判断语句", "条件判断语句")
    text = text.replace("if 判断语句", "条件判断语句").replace("r零暂存语句", "暂存到零号单元的语句")
    text = re.sub(r"第\s*i\s*趟", "当前这一轮", text)
    # 支持前置和后置自增、自减，不把 --high 直接念成 high。
    text = re.sub(r"(\+\+|--)([A-Za-z]+)|([A-Za-z]+)(\+\+|--)",
                  lambda m: (m[2] or m[3]) + ("加一" if (m[1] or m[4]) == "++" else "减一"), text)
    text = re.sub(r"r\[(\d+)\.\.(\d+)\]", r"第\1项到第\2项", text)
    text = re.sub(r"(?:L\.)?r\[(\d+)\]", r"第\1号单元", text)
    text = re.sub(r"(?<![A-Za-z])r\s*([零一二三四五六七八九]|\d+)(?:号单元)?", r"第\1号单元", text)
    for symbol, words in [("<=", "小于或等于"), (">=", "大于或等于"), ("!=", "不等于"),
                          ("==", "等于"), ("<", "小于"), (">", "大于"), ("=", "等于"),
                          ("&&", "并且"), ("≤", "小于或等于"), ("≥", "大于或等于")]:
        text = text.replace(symbol, words)
    text = re.sub(r"(?<![A-Za-z])log\s*(?:₂|2)?\s*\(?n\)?", "以二为底的恩的对数", text)
    for variable, words in {"low": "左边界", "high": "右边界", "mid": "中点", "pivotkey": "枢轴关键字",
                            "dk": "增量", "flag": "交换标志", "n": "恩", "i": "艾", "j": "杰"}.items():
        text = re.sub(r"(?<![A-Za-z])" + variable + r"(?![A-Za-z])", words, text)
    # 先明确数值，再进入下一句，避免“等于，一时”的歧义。
    return text.replace("等于一时", "等于一的时候")


def caption_pages(text, line_chars=24, lines_per_page=2):
    """中文按标点/字符换行并分页，所有内容都保留，不截断成省略号。"""
    if line_chars < 1 or lines_per_page < 1:
        raise ValueError("字幕行长与每页行数必须为正数")
    remaining = " ".join(text.split())
    lines = []
    while remaining:
        end = min(line_chars, len(remaining))
        if end < len(remaining):
            candidates = [i + 1 for i, char in enumerate(remaining[:end])
                          if char in "，。；：、！？,;!?" and i + 1 >= line_chars // 2]
            if candidates:
                end = candidates[-1]
            else:
                # 尽量保持 r[10]、low 等代码记号完整。
                for match in re.finditer(r"[A-Za-z0-9_]+(?:\[[^\]]+\])?", remaining):
                    if 0 < match.start() < end < match.end():
                        end = match.start()
                        break
        lines.append(remaining[:end].strip())
        remaining = remaining[end:].lstrip()
    return ["\n".join(lines[i:i + lines_per_page]) for i in range(0, len(lines), lines_per_page)]


class SortingNarrationMixin:
    def voiceover(self, text="", subcaption=None, **kwargs):
        return super().voiceover(
            text=spoken_sorting_text(text),
            subcaption=display_caption(text if subcaption is None else subcaption),
            **kwargs,
        )

    def add_wrapped_subcaption(self, subcaption, duration, subcaption_buff=0.1, max_subcaption_len=70):
        # manim-voiceover 默认按空格分段，不适合没有空格的中文长句。
        pages = caption_pages(subcaption, line_chars=min(24, max_subcaption_len))
        weights = [len(page.replace("\n", "")) for page in pages]
        total = sum(weights)
        offset = 0.0
        for page, weight in zip(pages, weights):
            part_duration = duration * weight / total
            self.add_subcaption(page, duration=part_duration, offset=offset)
            offset += part_duration


def fit_code_block(block, max_width=5.6, max_height=5.4, bottom=-2.65):
    """整体缩放代码和背景；高亮只改颜色，避免长行伸出边框。"""
    factor = min(1, max_width / block.width, max_height / block.height)
    block.scale(factor)
    if block.get_bottom()[1] < bottom:
        block.shift([0, bottom - block.get_bottom()[1], 0])
    return block
