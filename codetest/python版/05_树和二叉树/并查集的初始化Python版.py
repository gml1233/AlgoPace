# coding=utf-8
"""并查集初始化的 Manim 动画（Python版）。

动画按照“思想讲解 -> 代码讲解 -> 时空复杂度讲解”的顺序展开。
列表中负数既表示根结点，又可以在合并时累计集合大小；因此初始化时
每个位置都写入 -1，代表一个只含自身的单元素集合。
"""

from manim import *
import warnings
import numpy as np

warnings.filterwarnings(
    "ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning
)

from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


# =========================================================================
# Python 版并查集算法逻辑
# =========================================================================
def init_ufset(ufset, size):
    # 初始化并查集
    for i in range(size):
        ufset[i] = -1  # 每个由单个元素组成的集合


def find_ufset(ufset, x):
    # 查找元素 x 所属的集合根结点
    while ufset[x] >= 0:
        x = ufset[x]
    return x


def union_ufset(ufset, root1, root2):
    # 将两个子集合并
    r1 = find_ufset(ufset, root1)
    r2 = find_ufset(ufset, root2)
    if r1 == r2:
        return
    ufset[r1] += ufset[r2]
    ufset[r2] = r1


def compression_find(ufset, x):
    # 递归实现路径压缩
    if ufset[x] < 0:
        return x
    ufset[x] = compression_find(ufset, ufset[x])
    return ufset[x]


class UFSet:
    def __init__(self, size):
        self.size = size
        self.parent = [-1] * size

    def find(self, x):
        return find_ufset(self.parent, x)

    def union(self, root1, root2):
        return union_ufset(self.parent, root1, root2)

    def compression_find(self, x):
        return compression_find(self.parent, x)


# =========================================================================
# Manim 动画场景
# =========================================================================
class UnionFindInitPythonVideo(VoiceoverScene):
    """并查集 init_ufset 算法动画（Python版）。"""

    NODE_RADIUS = 0.34

    def make_node(self, value, center, color=BLUE):
        circle = Circle(
            radius=self.NODE_RADIUS,
            color=color,
            fill_color=color,
            fill_opacity=0.18,
            stroke_width=2.5,
        ).move_to(center)
        label = Text(str(value), font="Consolas", font_size=22, color=WHITE).move_to(center)
        return VGroup(circle, label)

    def make_cell(self, value, width=0.78, height=0.58, value_color=WHITE):
        box = Rectangle(width=width, height=height, color=GRAY_B, stroke_width=1.5)
        text = Text(str(value), font="Consolas", font_size=21, color=value_color).move_to(box)
        group = VGroup(box, text)
        group.box = box
        group.text = text
        return group

    def construct(self):
        self.set_speech_service(
            EdgeTTSService(
                voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"
            )
        )

        logo = (
            ImageMobject(r"resource\Pitcure\front.png")
            .scale_to_fit_height(1.65)
            .to_corner(UR, buff=0.05)
            .shift(UP * 0.08)
        )
        self.add(logo)

        title = Text(
            "并查集的初始化 (Python版)", font="Microsoft YaHei", font_size=46, weight=BOLD
        ).to_edge(UP, buff=0.48)
        self.play(FadeIn(title), run_time=0.8)

        with self.voiceover(
            text="本节学习并查集初始化算法的Python实现。它为后续的查找、合并和路径压缩操作准备底层列表。"
        ) as tracker:
            self.wait(tracker.duration)

        # =====================================================================
        # PHASE A — 思想讲解：森林模型与 -1 的含义
        # =====================================================================
        idea_title = Text(
            "一、思想：先把每个元素变成独立集合",
            font="Microsoft YaHei",
            font_size=28,
            color=YELLOW,
        ).next_to(title, DOWN, buff=0.24)
        self.play(FadeIn(idea_title), run_time=0.45)

        n = 6
        node_x = np.linspace(-3.15, 2.85, n)
        node_y = 0.82
        nodes = VGroup(
            *[self.make_node(i, np.array([node_x[i], node_y, 0])) for i in range(n)]
        )
        root_tags = VGroup(
            *[
                Text("根", font="Microsoft YaHei", font_size=15, color=GREEN).next_to(
                    nodes[i], UP, buff=0.13
                )
                for i in range(n)
            ]
        )

        index_row = VGroup(
            *[
                self.make_cell(i, value_color=ORANGE, width=0.78, height=0.48)
                for i in range(n)
            ]
        ).arrange(RIGHT, buff=0)
        value_row = VGroup(
            *[
                self.make_cell("-", value_color=GRAY_B, width=0.78, height=0.58)
                for _ in range(n)
            ]
        ).arrange(RIGHT, buff=0)
        index_row.move_to(np.array([-0.15, -0.58, 0]))
        value_row.next_to(index_row, DOWN, buff=0)
        index_label = Text("下标 i", font="Microsoft YaHei", font_size=19, color=ORANGE).next_to(
            index_row, LEFT, buff=0.22
        )
        array_label = Text("ufset[i]", font="Consolas", font_size=19, color=TEAL_A).next_to(
            value_row, LEFT, buff=0.22
        )
        array_group = VGroup(index_row, value_row, index_label, array_label)

        forest_caption = Text(
            "初始化前：每个元素都是一个只含自身的集合",
            font="Microsoft YaHei",
            font_size=20,
            color=WHITE,
        ).next_to(nodes, DOWN, buff=0.2)
        minus_hint = Text(
            "ufset[i] < 0  ⇒  i 是根结点",
            font="Microsoft YaHei",
            font_size=21,
            color=GREEN,
        ).next_to(array_group, DOWN, buff=0.35)

        with self.voiceover(
            text="把并查集看成一片森林。初始化时，零到五号元素彼此没有关系，每个元素都单独构成一棵只有一个结点的小树。"
        ) as tracker:
            self.play(FadeIn(nodes), FadeIn(root_tags), Write(forest_caption), run_time=tracker.duration)

        with self.voiceover(
            text="列表 ufset 用负数标记根结点。这里的负一表示：当前结点是根，并且集合大小为一。"
        ) as tracker:
            self.play(FadeIn(index_row), FadeIn(index_label), FadeIn(array_label), FadeIn(value_row), run_time=0.5)
            self.play(FadeIn(minus_hint), run_time=max(0.2, tracker.duration - 0.5))

        # 逐格展示初始化写入 -1；同时用绿色环突出当前处理的元素。
        loop_ring = SurroundingRectangle(value_row[0], color=YELLOW, buff=0.06)
        loop_pointer = Arrow(
            start=value_row[0].get_bottom() + DOWN * 0.52,
            end=value_row[0].get_bottom() + DOWN * 0.08,
            buff=0,
            color=YELLOW,
            stroke_width=3,
        )
        loop_label = Text("i", font="Consolas", font_size=20, color=YELLOW).next_to(
            loop_pointer, DOWN, buff=0.04
        )

        with self.voiceover(
            text="所以初始化的动作非常直接：让下标 i 从零遍历到 size 减一，把每一个位置都写成负一。"
        ) as tracker:
            self.play(FadeIn(loop_ring), FadeIn(loop_pointer), FadeIn(loop_label), run_time=0.45)
            step_time = max(0.22, (tracker.duration - 0.45) / n)
            for i in range(n):
                if i > 0:
                    self.play(
                        loop_ring.animate.move_to(value_row[i]),
                        loop_pointer.animate.next_to(value_row[i], DOWN, buff=0.08),
                        loop_label.animate.next_to(value_row[i], DOWN, buff=0.04),
                        run_time=step_time * 0.45,
                    )
                value_row[i].text.become(
                    Text("-1", font="Consolas", font_size=21, color=GREEN).move_to(value_row[i].box)
                )
                self.play(
                    value_row[i].box.animate.set_stroke(GREEN, width=2.5),
                    Indicate(nodes[i][0], color=GREEN, scale_factor=1.14),
                    run_time=step_time * 0.55,
                )

        result_array = VGroup(
            Text("初始化后：", font="Microsoft YaHei", font_size=21, color=GREEN),
            Text("ufset = [-1, -1, -1, -1, -1, -1]", font="Consolas", font_size=22, color=GREEN),
        ).arrange(RIGHT, buff=0.12).move_to(np.array([-0.1, -2.42, 0]))

        with self.voiceover(
            text="循环结束后，列表得到六个负一。此时六个集合互不相交，后续合并操作才能在这个基础上建立父子关系。"
        ) as tracker:
            self.play(Write(result_array), run_time=tracker.duration)

        idea_group = VGroup(
            idea_title,
            nodes,
            root_tags,
            array_group,
            forest_caption,
            minus_hint,
            loop_ring,
            loop_pointer,
            loop_label,
            result_array,
        )
        self.play(FadeOut(idea_group), run_time=0.7)
        self.wait(0.15)

        # =====================================================================
        # PHASE B — 代码讲解：函数体和调用
        # =====================================================================
        code_title = Text(
            "二、代码：for 循环逐项写入 -1",
            font="Microsoft YaHei",
            font_size=28,
            color=YELLOW,
        ).next_to(title, DOWN, buff=0.24)
        self.play(FadeIn(code_title), run_time=0.45)

        code_lines = [
            "def init_ufset(ufset, size):",
            "    for i in range(size):",
            "        ufset[i] = -1",
            "",
            "ufset = [None] * size",
            "init_ufset(ufset, size)",
        ]
        code_texts = []
        code_font = "Consolas"
        code_font_size = 12.0
        code_bg = RoundedRectangle(
            corner_radius=0.18,
            width=5.65,
            height=3.62,
            color=GRAY,
            fill_opacity=0.10,
            stroke_width=1,
        ).move_to(RIGHT * 3.25 + DOWN * 0.05)
        code_left = code_bg.get_left()[0] + 0.32
        code_y = [1.12, 0.70, 0.28, -0.14, -0.68, -1.10]
        indent_width = 0.076
        for i, line in enumerate(code_lines):
            stripped = line.lstrip(" ")
            indent = len(line) - len(stripped)
            text = Text(stripped, font=code_font, font_size=code_font_size, color=WHITE)
            text.move_to(
                np.array([code_left + indent * indent_width + text.width / 2, code_y[i], 0])
            )
            code_texts.append(text)

        init_label = Text("init_ufset", font="Consolas", font_size=16, color=TEAL_A)
        init_label.move_to(np.array([code_left + init_label.width / 2, 1.47, 0]))
        main_label = Text("主程序", font="Microsoft YaHei", font_size=16, color=TEAL_A)
        main_label.move_to(np.array([code_left + main_label.width / 2, -0.36, 0]))
        divider = DashedLine(
            np.array([code_left, -0.48, 0]),
            np.array([code_bg.get_right()[0] - 0.28, -0.48, 0]),
            color=GRAY_B,
            stroke_width=1,
            dash_length=0.08,
        )
        code_group = VGroup(init_label, main_label, divider, *code_texts)
        code_block = VGroup(code_bg, code_group)

        current_line = {"index": None}

        def track_line(index):
            """高亮代码行，并移动左侧黄色指针。"""
            if index == current_line["index"]:
                return []
            animations = []
            old = current_line["index"]
            if old is not None:
                animations.append(code_texts[old].animate.set_color(WHITE))
            if index is None:
                if hasattr(self, "code_pointer"):
                    animations.append(FadeOut(self.code_pointer))
                    delattr(self, "code_pointer")
                current_line["index"] = None
                return animations
            animations.append(code_texts[index].animate.set_color(YELLOW))
            if not hasattr(self, "code_pointer"):
                self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.14).rotate(-PI / 2)
                self.code_pointer.next_to(code_texts[index], LEFT, buff=0.10)
                animations.append(FadeIn(self.code_pointer))
            else:
                self.code_pointer.generate_target()
                self.code_pointer.target.next_to(code_texts[index], LEFT, buff=0.10)
                animations.append(MoveToTarget(self.code_pointer))
            current_line["index"] = index
            return animations

        # 代码讲解区左侧列表
        exec_n = 6
        exec_indices = VGroup(
            *[self.make_cell(i, width=0.74, height=0.44, value_color=ORANGE) for i in range(exec_n)]
        ).arrange(RIGHT, buff=0)
        exec_values = VGroup(
            *[self.make_cell("?", width=0.74, height=0.58) for _ in range(exec_n)]
        ).arrange(RIGHT, buff=0)
        exec_indices.move_to(LEFT * 3.0 + DOWN * 0.35)
        exec_values.next_to(exec_indices, DOWN, buff=0)
        exec_label = Text("ufset", font="Consolas", font_size=22, color=TEAL_A).next_to(
            exec_values, LEFT, buff=0.22
        )
        exec_panel = VGroup(exec_indices, exec_values, exec_label)
        call_caption = Text(
            "主程序：ufset = [None] * size  →  init_ufset(ufset, size)",
            font="Microsoft YaHei",
            font_size=18,
            color=GRAY_A,
        ).next_to(exec_panel, DOWN, buff=0.55)
        self.play(FadeIn(code_block), FadeIn(exec_panel), FadeIn(call_caption), run_time=0.8)

        with self.voiceover(
            text="先看主程序。程序根据输入的 size 构造一个长度为 size 的列表 ufset，再把列表和长度传给 init_ufset 函数。"
        ) as tracker:
            self.play(*track_line(4), run_time=0.35)
            self.play(*track_line(5), run_time=0.35)
            self.play(Indicate(exec_panel, color=BLUE, scale_factor=1.08), run_time=max(0.2, tracker.duration - 0.7))

        with self.voiceover(
            text="进入函数后，for 循环让 i 从零开始，只要 i 还小于 size，就继续处理下一个列表位置。"
        ) as tracker:
            self.play(*track_line(1), run_time=0.5)
            cursor = SurroundingRectangle(exec_values[0], color=YELLOW, buff=0.05)
            self.play(FadeIn(cursor), run_time=max(0.2, tracker.duration - 0.5))

        with self.voiceover(
            text="循环体只有一条语句：ufset[i] 等于负一。它把当前元素标记为根结点，并说明该集合目前只有一个成员。"
        ) as tracker:
            self.play(*track_line(2), run_time=0.35)
            step_time = max(0.22, (tracker.duration - 0.35) / exec_n)
            for i in range(exec_n):
                if i > 0:
                    self.play(cursor.animate.move_to(exec_values[i]), run_time=step_time * 0.35)
                exec_values[i].text.become(
                    Text("-1", font="Consolas", font_size=20, color=GREEN).move_to(exec_values[i].box)
                )
                self.play(
                    exec_values[i].box.animate.set_stroke(GREEN, width=2.5),
                    Indicate(exec_indices[i].box, color=YELLOW, scale_factor=1.08),
                    run_time=step_time * 0.65,
                )

        with self.voiceover(
            text="当 i 遍历完所有位置时，函数执行完毕返回，并查集的初始化全部完成。",
            subcaption="当 i 遍历完所有位置时，函数执行完毕返回，并查集的初始化全部完成。"
        ) as tracker:
            self.play(*track_line(None), FadeOut(cursor), run_time=0.4)
            self.play(Indicate(exec_values, color=GREEN, scale_factor=1.08), run_time=max(0.2, tracker.duration - 0.4))

        # =========================================================================
        # PHASE C — 时空复杂度分析
        # =========================================================================
        self.play(FadeOut(call_caption), run_time=0.4)

        time_box = VGroup(
            Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(n)", font_size=24, color=YELLOW),
        ).arrange(RIGHT, buff=0.1)

        space_box = VGroup(
            Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(1)", font_size=24, color=YELLOW),
        ).arrange(RIGHT, buff=0.1)

        complexity_panel = VGroup(time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        complexity_panel.next_to(exec_panel, DOWN, buff=0.45).align_to(exec_panel, LEFT)

        with self.voiceover(
            text="在初始化算法中，需要通过循环遍历大小为 n 的列表，逐个将元素赋值为负一，因此时间复杂度为 O(n)。",
            subcaption="在初始化算法中，需要通过循环遍历大小为 n 的列表，逐个将元素赋值为 -1，因此时间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
            text="整个初始化过程在运行期间仅使用了少量的循环控制变量，因此辅助空间复杂度为 O(1)。",
            subcaption="整个初始化过程在运行期间仅使用了少量的循环控制变量，因此辅助空间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(
            text="以上就是并查集初始化算法Python版的完整演示过程。",
            subcaption="以上就是并查集初始化算法Python版的完整演示过程。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)


ContinuousUnionFindInitPythonVideo = UnionFindInitPythonVideo
