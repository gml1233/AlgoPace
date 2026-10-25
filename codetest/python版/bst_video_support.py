"""83–86 共用的 Python 代码面板：固定安全区域、按执行阶段翻页。"""
import inspect
import textwrap

from manim import *


def method_lines(method):
    """直接展示实际执行的方法，去除教学代码之外的注释和空行。"""
    source = textwrap.dedent(inspect.getsource(method))
    return [line.split("  #", 1)[0].rstrip() for line in source.splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


class PythonCodePanel(VGroup):
    """右侧 x=0.25..6.85，y=-3.05..2.55；高亮不放大代码。"""

    def __init__(self, lines, title="Python 核心代码", page_starts=None):
        super().__init__()
        self.lines = lines
        self.texts = []
        self.pages = []
        self.page_for_line = {}
        self.active_page = 0
        self.active_line = None
        starts = list(page_starts or [0]) + [len(lines)]
        self.background = RoundedRectangle(
            width=6.6, height=5.6, corner_radius=0.16,
            color=GRAY_B, fill_color=BLACK, fill_opacity=0.88,
            stroke_width=1.2,
        ).move_to([3.55, -0.25, 0])
        for page_index, (start, end) in enumerate(zip(starts, starts[1:])):
            heading = Text(
                f"{title}  {page_index + 1}/{len(starts) - 1}",
                font="Microsoft YaHei", font_size=19, color=YELLOW,
            )
            if heading.width > 6.0:
                heading.scale_to_fit_width(6.0)
            heading.move_to([3.55, 2.2, 0])
            rows = VGroup()
            for index in range(start, end):
                line = lines[index]
                indent = len(line) - len(line.lstrip())
                text = Text(line.lstrip(), font="Consolas", font_size=18,
                            color=WHITE, disable_ligatures=True)
                text.move_to([0, 0, 0], aligned_edge=LEFT)
                text.shift(RIGHT * indent * 0.105 + DOWN * (index - start) * 0.31)
                rows.add(text)
                self.texts.append(text)
                self.page_for_line[index] = page_index
            rows.scale(min(1, 5.7 / max(rows.width, 0.01), 4.55 / max(rows.height, 0.01)))
            rows.move_to([0.80, 1.75, 0], aligned_edge=UL)
            self.pages.append(VGroup(heading, rows))
        self.pointer = Triangle(color=YELLOW, fill_opacity=1).scale(0.085).rotate(-PI / 2)
        self.add(self.background, self.pages[0])

    def track(self, index):
        animations = []
        if self.active_line is not None:
            self.texts[self.active_line].set_color(WHITE)
        if index is None:
            self.remove(self.pointer)
            self.active_line = None
            return [Wait(0.01)]
        page = self.page_for_line[index]
        if page != self.active_page:
            self.remove(self.pages[self.active_page])
            self.add(self.pages[page])
            self.active_page = page
        target = self.texts[index]
        self.pointer.move_to([0.52, target.get_center()[1], 0])
        self.add(self.pointer)
        animations.append(target.animate.set_color(YELLOW))
        self.active_line = index
        return animations


def fit_right(mobject, max_width=6.1, max_height=4.8, center=(3.55, -0.3, 0)):
    mobject.scale(min(1, max_width / mobject.width, max_height / mobject.height))
    return mobject.move_to(center)
