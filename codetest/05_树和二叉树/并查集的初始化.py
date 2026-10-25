# coding=utf-8
"""并查集初始化的 Manim 动画。

动画按照“思想讲解 -> 代码讲解 -> 时空复杂度讲解”的顺序展开。
数组中的负数既表示根结点，又可以在合并时累计集合大小；因此初始化时
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


# 与动画对应的完整 C++ 上下文。动画重点追踪 Init_UFSet 以及 main 中的调用，
# Find、Union 和 CompressionFind 会在后续并查集专题中单独展开。
FULL_CPP_SOURCE = r"""#include <iostream>
using namespace std;

void Init_UFSet(int UFSet[], int size)
{// 初始化并查集
    for (int i = 0; i < size; ++i)
        UFSet[i] = -1; // 每个由单个元素组成的集合
}

int Find_UFSet(int UFSet[], int x)
{// 查找元素 x 所属的集合
    while (UFSet[x] >= 0)
        x = UFSet[x];
    return x;
}

void Union_UFSet(int UFSet[], int Root1, int Root2)
{// 将两个子集合并
    Root1 = Find_UFSet(UFSet, Root1);
    Root2 = Find_UFSet(UFSet, Root2);
    if (Root1 == Root2) return;
    UFSet[Root1] += UFSet[Root2];
    UFSet[Root2] = Root1;
}

int CompressionFind(int UFSet[], int x)
{// 递归实现路径压缩
    if (UFSet[x] < 0) return x;
    return UFSet[x] = CompressionFind(UFSet, UFSet[x]);
}

int main() {
    int size;
    cin >> size;
    int* ufset = new int[size];
    Init_UFSet(ufset, size);
    for (int i = 0; i < size; ++i) {
        cout << ufset[i];
        if (i != size - 1) cout << " ";
    }
    int m;
    cin >> m;
    for (int i = 0; i < m; ++i) {
        int x, y;
        cin >> x >> y;
        Union_UFSet(ufset, x, y);
    }
    int q;
    cin >> q;
    for (int i = 0; i < q; ++i) {
        int k;
        cin >> k;
        int root = CompressionFind(ufset, k);
        cout << root << endl;
    }
    delete[] ufset;
    return 0;
}"""


class UnionFindInitVideo(VoiceoverScene):
    """并查集 Init_UFSet 算法动画。"""

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
            "并查集的初始化", font="Microsoft YaHei", font_size=46, weight=BOLD
        ).to_edge(UP, buff=0.48)
        self.play(FadeIn(title), run_time=0.8)

        with self.voiceover(
            text="本节学习并查集的初始化算法 Init_UFSet。它为后续的查找、合并和路径压缩操作准备底层数组。"
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
        # 固定各层的纵坐标，避免 next_to 链式布局在不同字体 fallback 下产生挤压。
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
        array_label = Text("UFSet[i]", font="Consolas", font_size=19, color=TEAL_A).next_to(
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
            "UFSet[i] < 0  ⇒  i 是根结点",
            font="Microsoft YaHei",
            font_size=21,
            color=GREEN,
        ).next_to(array_group, DOWN, buff=0.35)

        with self.voiceover(
            text="把并查集看成一片森林。初始化时，零到五号元素彼此没有关系，每个元素都单独构成一棵只有一个结点的小树。"
        ) as tracker:
            self.play(FadeIn(nodes), FadeIn(root_tags), Write(forest_caption), run_time=tracker.duration)

        with self.voiceover(
            text="数组 UFSet 用负数标记根结点。这里的负一表示：当前结点是根，并且集合大小为一。"
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

        # 中英文拆成两个文本对象，避免 Consolas 遇到中文时触发字体 fallback，
        # 从而造成中文和数组内容错位或重叠。
        result_array = VGroup(
            Text("初始化后：", font="Microsoft YaHei", font_size=21, color=GREEN),
            Text("UFSet = [-1, -1, -1, -1, -1, -1]", font="Consolas", font_size=22, color=GREEN),
        ).arrange(RIGHT, buff=0.12).move_to(np.array([-0.1, -2.42, 0]))
        with self.voiceover(
            text="循环结束后，数组得到六个负一。此时六个集合互不相交，后续 Union 才能在这个基础上建立父子关系。"
        ) as tracker:
            self.play(Write(result_array), run_time=tracker.duration)

        # 为代码讲解清理思想区，只保留标题和 logo。
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
        # 给淡出和下一阶段之间留出一个干净的过渡帧，防止数组残影与代码标题叠加。
        self.wait(0.15)

        # =====================================================================
        # PHASE B — 代码讲解：函数体和 main 中的调用
        # =====================================================================
        code_title = Text(
            "二、代码：for 循环逐项写入 -1",
            font="Microsoft YaHei",
            font_size=28,
            color=YELLOW,
        ).next_to(title, DOWN, buff=0.24)
        self.play(FadeIn(code_title), run_time=0.45)

        # 代码区域使用 ASCII 等宽字体，并采用显式坐标排版。
        # 不把中文注释放进 Text：Windows 字体 fallback 会改变行高/字宽，导致多行代码重叠。
        # 讲解所需的中文含义由旁白和左侧状态面板承担。
        code_lines = [
            "void Init_UFSet(int UFSet[], int size)",
            "{",
            "    for (int i = 0; i < size; ++i)",
            "        UFSet[i] = -1;",
            "}",
            "int* ufset = new int[size];",
            "Init_UFSet(ufset, size);",
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
        code_y = [1.12, 0.78, 0.43, 0.08, -0.27, -0.88, -1.23]
        indent_width = 0.076
        for i, line in enumerate(code_lines):
            stripped = line.lstrip(" ")
            indent = len(line) - len(stripped)
            text = Text(stripped, font=code_font, font_size=code_font_size, color=WHITE)
            # 逐行设置左边界和基线，避免 VGroup.arrange 对空行/字体 fallback 的不稳定行为。
            text.move_to(
                np.array([code_left + indent * indent_width + text.width / 2, code_y[i], 0])
            )
            code_texts.append(text)

        init_label = Text("Init_UFSet", font="Consolas", font_size=16, color=TEAL_A)
        init_label.move_to(np.array([code_left + init_label.width / 2, 1.47, 0]))
        main_label = Text("main()", font="Consolas", font_size=16, color=TEAL_A)
        main_label.move_to(np.array([code_left + main_label.width / 2, -0.58, 0]))
        divider = DashedLine(
            np.array([code_left, -0.70, 0]),
            np.array([code_bg.get_right()[0] - 0.28, -0.70, 0]),
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
            # 只改变颜色，不改变字号和位置，避免高亮时重新计算文字包围盒造成重叠。
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

        # 代码讲解区左侧数组，与上半段相同但只显示关键执行状态。
        exec_n = 6
        exec_indices = VGroup(
            *[self.make_cell(i, width=0.74, height=0.44, value_color=ORANGE) for i in range(exec_n)]
        ).arrange(RIGHT, buff=0)
        exec_values = VGroup(
            *[self.make_cell("?", width=0.74, height=0.58) for _ in range(exec_n)]
        ).arrange(RIGHT, buff=0)
        exec_indices.move_to(LEFT * 3.0 + DOWN * 0.35)
        exec_values.next_to(exec_indices, DOWN, buff=0)
        exec_label = Text("UFSet", font="Consolas", font_size=22, color=TEAL_A).next_to(
            exec_values, LEFT, buff=0.22
        )
        exec_panel = VGroup(exec_indices, exec_values, exec_label)
        call_caption = Text(
            "main：new int[size]  →  Init_UFSet(ufset, size)",
            font="Microsoft YaHei",
            font_size=18,
            color=GRAY_A,
        ).next_to(exec_panel, DOWN, buff=0.55)
        self.play(FadeIn(code_block), FadeIn(exec_panel), FadeIn(call_caption), run_time=0.8)

        with self.voiceover(
            text="先看 main 函数。程序根据输入的 size 动态申请一个整型数组 ufset，再把数组指针和长度传给 Init_UFSet。"
        ) as tracker:
            self.play(*track_line(5), run_time=0.35)
            self.play(*track_line(6), run_time=0.35)
            self.play(Indicate(exec_panel, color=BLUE, scale_factor=1.08), run_time=max(0.2, tracker.duration - 0.7))

        with self.voiceover(
            text="进入函数后，for 循环让 i 从零开始，只要 i 还小于 size，就继续处理下一个数组位置。"
        ) as tracker:
            self.play(*track_line(2), run_time=0.5)
            cursor = SurroundingRectangle(exec_values[0], color=YELLOW, buff=0.05)
            self.play(FadeIn(cursor), run_time=max(0.2, tracker.duration - 0.5))

        with self.voiceover(
            text="循环体只有一条语句：UFSet[i] 等于负一。它把当前元素标记为根结点，并说明该集合目前只有一个成员。"
        ) as tracker:
            self.play(*track_line(3), run_time=0.35)
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
            text="当 i 增加到 size 时，循环条件不成立，函数返回，并查集的初始化全部完成。",
            subcaption="当 i 增加到 size 时，循环条件不成立，函数返回，并查集的初始化全部完成。"
        ) as tracker:
            self.play(*track_line(4), FadeOut(cursor), run_time=0.4)
            self.play(Indicate(exec_values, color=GREEN, scale_factor=1.08), run_time=max(0.2, tracker.duration - 0.4))
        self.play(*track_line(None), run_time=0.35)

        # =========================================================================
        # ===== PHASE C — COMPLEXITY ANALYSIS (时空复杂度分析) =====
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
            text="在初始化算法中，需要通过循环遍历大小为 n 的数组，逐个将元素赋值为负一，因此时间复杂度为 O(n)。",
            subcaption="在初始化算法中，需要通过循环遍历大小为 n 的数组，逐个将元素赋值为 -1，因此时间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
            text="整个初始化过程在运行期间仅使用了少量的循环控制变量，因此辅助空间复杂度为 O(1)。",
            subcaption="整个初始化过程在运行期间仅使用了少量的循环控制变量，因此辅助空间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(
            text="以上就是并查集初始化算法的完整演示过程。",
            subcaption="以上就是并查集初始化算法的完整演示过程。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)


if __name__ == "__main__":
    # 通过 manim 命令行渲染时，场景名为 UnionFindInitVideo。
    pass
