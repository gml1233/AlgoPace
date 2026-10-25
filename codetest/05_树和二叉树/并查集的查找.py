# coding=utf-8
"""并查集的查找（Find_UFSet）Manim 动画。

动画按照“原理与森林模型 -> 代码逐行追踪演示 -> 时空复杂度分析”的顺序展开。
算法利用双亲表示法（Parent Representation），从当前元素出发沿双亲指针逐层向上，
直到找到存储值为负数的根结点并返回。
"""

from manim import *
import warnings
import numpy as np

warnings.filterwarnings(
    "ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning
)

from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class UnionFindFindVideo(VoiceoverScene):
    """并查集 Find_UFSet 算法讲解动画。"""

    NODE_RADIUS = 0.32

    def make_node(self, value, center, color=BLUE_D):
        """构造带有圆形边框与数值的树结点。"""
        circle = Circle(
            radius=self.NODE_RADIUS,
            color=color,
            fill_color=color,
            fill_opacity=0.22,
            stroke_width=2.5,
        ).move_to(center)
        label = Text(str(value), font="Consolas", font_size=22, color=WHITE).move_to(center)
        group = VGroup(circle, label)
        group.circle = circle
        group.label = label
        return group

    def make_parent_arrow(self, child_center, parent_center, color=GRAY_A):
        """构造由孩子指向双亲结点的有向箭头。"""
        p_child = np.array(child_center, dtype=float)
        p_parent = np.array(parent_center, dtype=float)
        vec = p_parent - p_child
        dist = np.linalg.norm(vec)
        if dist == 0:
            unit = UP
        else:
            unit = vec / dist
        start = p_child + unit * (self.NODE_RADIUS + 0.05)
        end = p_parent - unit * (self.NODE_RADIUS + 0.05)
        arrow = Arrow(
            start,
            end,
            buff=0,
            color=color,
            stroke_width=2.2,
            max_tip_length_to_length_ratio=0.22,
            tip_length=0.18,
        )
        return arrow

    def make_cell(self, value, width=0.68, height=0.52, value_color=WHITE, stroke_color=GRAY_B):
        """构造一维数组的单元格。"""
        box = Rectangle(width=width, height=height, color=stroke_color, stroke_width=1.5)
        text = Text(str(value), font="Consolas", font_size=20, color=value_color).move_to(box)
        group = VGroup(box, text)
        group.box = box
        group.text = text
        return group

    def construct(self):
        # 1. 语音服务与片头 Logo
        self.set_speech_service(
            EdgeTTSService(
                voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"
            )
        )

        logo = (
            ImageMobject(r"resource\Pitcure\front.png")
            .scale_to_fit_height(1.4)
            .to_corner(UR, buff=0.1)
        )
        self.add(logo)

        # 2. 视频标题
        title = Text(
            "并查集的查找", font="Microsoft YaHei", font_size=36, weight=BOLD
        ).to_edge(UP, buff=0.25)
        self.play(FadeIn(title), run_time=0.7)

        with self.voiceover(
            text="本节学习并查集的核心操作之一：查找算法 Find_UFSet。它的目标是确定一个元素究竟属于哪一个集合，即找到该集合的代表根结点。"
        ) as tracker:
            self.wait(tracker.duration)

        # =====================================================================
        # PHASE A — 原理与双亲表示法模型
        # =====================================================================
        # 定义并查集森林（以包含 6 个元素的两个树集合为例）
        # 集合 1：根为 0 (UFSet[0]=-1)，孩子 1 (UFSet[1]=0) 和 3 (UFSet[3]=0)，1 的孩子 2 (UFSet[2]=1)
        # 集合 2：根为 4 (UFSet[4]=-1)，孩子 5 (UFSet[5]=4)
        node_coords = {
            0: np.array([-4.0, 1.55, 0]),
            1: np.array([-4.9, 0.45, 0]),
            2: np.array([-4.9, -0.65, 0]),
            3: np.array([-3.1, 0.45, 0]),
            4: np.array([-1.4, 1.55, 0]),
            5: np.array([-1.4, 0.45, 0]),
        }

        tree_nodes = {}
        for k, pt in node_coords.items():
            tree_nodes[k] = self.make_node(k, pt)

        # 指向双亲的箭头
        parent_arrows = {
            2: self.make_parent_arrow(node_coords[2], node_coords[1], color=TEAL_A),
            1: self.make_parent_arrow(node_coords[1], node_coords[0], color=TEAL_A),
            3: self.make_parent_arrow(node_coords[3], node_coords[0], color=TEAL_A),
            5: self.make_parent_arrow(node_coords[5], node_coords[4], color=TEAL_A),
        }

        forest_mobs = VGroup(
            *tree_nodes.values(),
            *parent_arrows.values()
        )

        tree_label1 = Text("集合 S1", font="Microsoft YaHei", font_size=16, color=YELLOW).next_to(
            tree_nodes[0], UP, buff=0.15
        )
        tree_label2 = Text("集合 S2", font="Microsoft YaHei", font_size=16, color=YELLOW).next_to(
            tree_nodes[4], UP, buff=0.15
        )
        forest_group = VGroup(forest_mobs, tree_label1, tree_label2)

        # 构造一维数组 UFSet
        n_elems = 6
        ufset_data = [-1, 0, 1, 0, -1, 4]
        idx_cells = VGroup(
            *[self.make_cell(i, width=0.66, height=0.42, value_color=ORANGE) for i in range(n_elems)]
        ).arrange(RIGHT, buff=0)
        val_cells = VGroup(
            *[self.make_cell(ufset_data[i], width=0.66, height=0.52, value_color=WHITE) for i in range(n_elems)]
        ).arrange(RIGHT, buff=0)
        idx_cells.move_to(LEFT * 3.15 + DOWN * 1.5)
        val_cells.next_to(idx_cells, DOWN, buff=0)

        label_ufset = Text("UFSet", font="Consolas", font_size=20, color=TEAL_A).next_to(
            val_cells, LEFT, buff=0.18
        )
        label_idx = Text("下标", font="Microsoft YaHei", font_size=15, color=ORANGE).next_to(
            idx_cells, LEFT, buff=0.22
        )
        ufset_panel = VGroup(idx_cells, val_cells, label_ufset, label_idx)

        with self.voiceover(
            text="并查集在计算机中通过一维数组 UFSet 实现双亲表示法。每个结点的数值记录其双亲结点的下标。"
        ) as tracker:
            self.play(FadeIn(forest_group), FadeIn(ufset_panel), run_time=tracker.duration)

        with self.voiceover(
            text="若 UFSet 中存储的是非负数，表示指向双亲；若存储的是负数，则说明它是根结点，代表整个集合。"
        ) as tracker:
            self.play(
                Indicate(val_cells[0].box, color=GREEN),
                Indicate(val_cells[4].box, color=GREEN),
                tree_nodes[0].circle.animate.set_color(GREEN),
                tree_nodes[4].circle.animate.set_color(GREEN),
                run_time=tracker.duration
            )

        # =====================================================================
        # PHASE B — 代码逐行追踪演示
        # =====================================================================
        c_lines = [
            "int Find_UFSet(int UFSet[], int x)",
            "{// 查找元素x所属集合的根结点",
            "    while(UFSet[x] >= 0) // 循环寻找元素x的根",
            "        x = UFSet[x];    // 沿双亲指针向上移动",
            "    return x;            // 返回根结点的下标",
            "}"
        ]
        IDX_WHILE = 2
        IDX_MOVE = 3
        IDX_RETURN = 4

        code_texts = []
        for line in c_lines:
            t = Text(line.lstrip(" "), font_size=11.5, font="Microsoft YaHei", color=WHITE)
            code_texts.append(t)

        code_group = VGroup(*code_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.10)
        SPACE_WIDTH = 0.08
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            code_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 5.5:
            code_group.scale_to_fit_width(5.5)
        if code_group.height > 3.2:
            code_group.scale_to_fit_height(3.2)

        code_bg = RoundedRectangle(
            corner_radius=0.15,
            height=code_group.get_height() + 0.45,
            width=code_group.get_width() + 0.65,
            color=GRAY,
            fill_opacity=0.1,
            stroke_width=1,
        )
        code_bg.move_to(code_group)
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.22).to_edge(RIGHT, buff=0.35)

        current_line = [None]

        def get_track_anims(new_idx):
            anims = []
            if current_line[0] is not None:
                anims.append(code_texts[current_line[0]].animate.set_color(WHITE))
            if new_idx is not None:
                anims.append(code_texts[new_idx].animate.set_color(YELLOW))
                if not hasattr(self, "code_pointer"):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.12).rotate(-PI / 2)
                    self.code_pointer.next_to(code_texts[new_idx], LEFT, buff=0.10)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(code_texts[new_idx], LEFT, buff=0.10)
                    anims.append(MoveToTarget(self.code_pointer))
            else:
                if hasattr(self, "code_pointer"):
                    anims.append(FadeOut(self.code_pointer))
            current_line[0] = new_idx
            return anims

        self.play(FadeIn(code_block), run_time=0.6)

        # 活动指示环与数组光标
        ring = Circle(radius=self.NODE_RADIUS + 0.08, color=YELLOW, stroke_width=3.5).move_to(node_coords[2])
        cursor = SurroundingRectangle(val_cells[2].box, color=YELLOW, buff=0.04, stroke_width=2.5)

        with self.voiceover(
            text="现在我们结合右侧代码，以查找元素 2 所属的集合为例，演示 Find_UFSet 的完整追踪过程。"
        ) as tracker:
            self.play(
                FadeIn(ring),
                FadeIn(cursor),
                *get_track_anims(0),
                run_time=tracker.duration
            )

        # 第 1 轮循环 (x = 2)
        with self.voiceover(
            text="进入函数，首先检查循环条件。当前 x 等于 2，查看 UFSet[2] 的值为 1，大于等于 0，条件成立。"
        ) as tracker:
            self.play(*get_track_anims(IDX_WHILE), run_time=0.35)
            self.play(Indicate(val_cells[2], color=YELLOW), run_time=max(0.2, tracker.duration - 0.35))

        with self.voiceover(
            text="执行循环体：x 赋值为 UFSet[x]，即 x 更新为 1。在树中我们沿双亲指针由结点 2 向上移动到结点 1。"
        ) as tracker:
            self.play(*get_track_anims(IDX_MOVE), run_time=0.35)
            self.play(
                ring.animate.move_to(node_coords[1]),
                cursor.animate.move_to(val_cells[1].box),
                ShowPassingFlash(parent_arrows[2].copy().set_color(YELLOW).set_stroke(width=5), time_width=0.4),
                run_time=max(0.4, tracker.duration - 0.35)
            )

        # 第 2 轮循环 (x = 1)
        with self.voiceover(
            text="继续下一轮判断。当前 x 等于 1，UFSet[1] 的值为 0，依然大于等于 0，循环条件成立。"
        ) as tracker:
            self.play(*get_track_anims(IDX_WHILE), run_time=0.35)
            self.play(Indicate(val_cells[1], color=YELLOW), run_time=max(0.2, tracker.duration - 0.35))

        with self.voiceover(
            text="再次执行 x 等于 UFSet[x]，x 更新为 0。在树中继续沿双亲指针向上移动到根结点 0。"
        ) as tracker:
            self.play(*get_track_anims(IDX_MOVE), run_time=0.35)
            self.play(
                ring.animate.move_to(node_coords[0]),
                cursor.animate.move_to(val_cells[0].box),
                ShowPassingFlash(parent_arrows[1].copy().set_color(YELLOW).set_stroke(width=5), time_width=0.4),
                run_time=max(0.4, tracker.duration - 0.35)
            )

        # 第 3 轮判断 (x = 0)
        with self.voiceover(
            text="再次回到循环判断。当前 x 等于 0，UFSet[0] 为负一，不满足大于等于 0 的条件，循环结束。"
        ) as tracker:
            self.play(*get_track_anims(IDX_WHILE), run_time=0.35)
            self.play(Indicate(val_cells[0], color=RED), run_time=max(0.2, tracker.duration - 0.35))

        # 返回结果
        with self.voiceover(
            text="执行返回语句 return x。成功返回根结点下标 0，说明元素 2 所属集合的根就是 0，查找操作完成。"
        ) as tracker:
            self.play(*get_track_anims(IDX_RETURN), run_time=0.35)
            self.play(
                ring.animate.set_color(GREEN),
                cursor.animate.set_stroke(color=GREEN),
                tree_nodes[0].circle.animate.set_fill(GREEN, opacity=0.4),
                run_time=max(0.3, tracker.duration - 0.35)
            )

        self.play(*get_track_anims(None), FadeOut(ring), FadeOut(cursor), run_time=0.4)

        # =====================================================================
        # PHASE C — 时空复杂度分析（全库统一标准风格）
        # =====================================================================
        time_box = VGroup(
            Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(n)", font_size=24, color=YELLOW),
        ).arrange(RIGHT, buff=0.1)

        space_box = VGroup(
            Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(1)", font_size=24, color=YELLOW),
        ).arrange(RIGHT, buff=0.1)

        complexity_panel = VGroup(time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        complexity_panel.next_to(ufset_panel, DOWN, buff=0.45).align_to(ufset_panel, LEFT)

        with self.voiceover(
            text="普通查找操作需要从当前元素沿双亲指针不断向上查找，直到找到根结点。在最坏情况下，并查集可能退化为一条链，此时一次查找最多需要访问 n 个元素，因此时间复杂度为 O(n)。",
            subcaption="普通查找操作需要从当前元素沿双亲指针不断向上查找，直到找到根结点。在最坏情况下，并查集可能退化为一条链，此时一次查找最多需要访问 n 个元素，时间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
            text="该算法只使用少量变量进行下标记录和判断，不需要额外的辅助数组或栈，因此空间复杂度为 O(1)。",
            subcaption="该算法只使用少量变量进行下标记录和判断，不需要额外的辅助数组或栈，因此空间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(
            text="以上就是并查集查找算法的完整演示过程。",
            subcaption="以上就是并查集查找算法的完整演示过程。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)


if __name__ == "__main__":
    pass
