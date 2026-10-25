# coding=utf-8
"""并查集的路径压缩（compression_find）Manim 动画（Python版）。

动画按照“原理与深层链问题 -> 代码逐行追踪演示 -> 时空复杂度分析”的顺序展开。
算法通过递归实现：
“递进”时向上深入寻根，“回溯”时将路径上所有结点直接链接到根结点，
从而将深树瞬间拍平，极大地优化后续查找性能。
"""

from manim import *
import warnings
import numpy as np

warnings.filterwarnings(
    "ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning
)

from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
from codetest.tree_video_support import TreeVideoScene


# =========================================================================
# Python 版并查集算法逻辑
# =========================================================================
def init_ufset(size):
    """初始化并查集：每个元素自成一个集合，根结点值为 -1。"""
    return [-1] * size


def find_ufset(ufset, x):
    """非递归查找元素 x 所属集合的根结点。"""
    while ufset[x] >= 0:
        x = ufset[x]
    return x


def union_ufset(ufset, root1, root2):
    """子集合并：将以 root2 为根的子集并入以 root1 为根的子集。"""
    if root1 != root2:
        ufset[root1] += ufset[root2]
        ufset[root2] = root1


def compression_find(ufset, x):
    """递归实现路径压缩：在深入查找根结点的同时，回溯拍平路径上所有结点的指针。"""
    if ufset[x] < 0:  # 递归基：找到根结点
        return x
    ufset[x] = compression_find(ufset, ufset[x])  # 递归深入并回溯更新双亲
    return ufset[x]


class UFSet:
    """并查集类封装。"""

    def __init__(self, size):
        self.size = size
        self.parent = init_ufset(size)

    def find(self, x):
        return find_ufset(self.parent, x)

    def union(self, root1, root2):
        return union_ufset(self.parent, root1, root2)

    def compression_find(self, x):
        return compression_find(self.parent, x)


# =========================================================================
# Manim 动画场景
# =========================================================================
class UnionFindCompressionPythonVideo(TreeVideoScene):
    """并查集 compression_find 算法讲解动画（Python版）。"""

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

    def make_cell(self, value, width=0.66, height=0.52, value_color=WHITE, stroke_color=GRAY_B):
        """构造一维列表的单元格。"""
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
            "并查集的路径压缩 (Python版)", font="Microsoft YaHei", font_size=36, weight=BOLD
        ).to_edge(UP, buff=0.25)
        self.play(FadeIn(title), run_time=0.7)

        with self.voiceover(
            text="本节学习并查集的高级优化技术：路径压缩算法 compression_find 的Python实现。它能在查找过程中同步拍平树形结构，显著提升后续查询效率。"
        ) as tracker:
            self.wait(tracker.duration)

        # =====================================================================
        # PHASE A — 原理与深层链问题
        # =====================================================================
        # 建立树模型：根 0 (ufset[0]=-5)，孩子 1 (ufset[1]=0)，2 (ufset[2]=1)，3 (ufset[3]=2)，4 (ufset[4]=0)
        # 采用阶梯优雅弧度布局，确保路径压缩重连时所有指向根结点的箭头互不遮挡碰撞
        node_coords = {
            0: np.array([-3.5, 1.75, 0]),
            1: np.array([-2.5, 0.85, 0]),
            4: np.array([-1.3, 0.75, 0]),
            2: np.array([-4.2, 0.05, 0]),
            3: np.array([-5.4, -0.75, 0]),
        }

        tree_nodes = {}
        for k, pt in node_coords.items():
            tree_nodes[k] = self.make_node(k, pt)

        parent_arrows = {
            1: self.make_parent_arrow(node_coords[1], node_coords[0], color=TEAL_A),
            2: self.make_parent_arrow(node_coords[2], node_coords[1], color=TEAL_A),
            3: self.make_parent_arrow(node_coords[3], node_coords[2], color=TEAL_A),
            4: self.make_parent_arrow(node_coords[4], node_coords[0], color=TEAL_A),
        }

        forest_mobs = VGroup(
            *tree_nodes.values(),
            *parent_arrows.values()
        )

        tree_label = Text("退化的深层树", font="Microsoft YaHei", font_size=16, color=YELLOW).next_to(
            tree_nodes[0], UP, buff=0.15
        )
        forest_group = VGroup(forest_mobs, tree_label)

        # 构造一维列表 ufset
        n_elems = 5
        ufset_data = [-5, 0, 1, 2, 0]
        idx_cells = VGroup(
            *[self.make_cell(i, width=0.66, height=0.42, value_color=ORANGE) for i in range(n_elems)]
        ).arrange(RIGHT, buff=0)
        val_cells = VGroup(
            *[self.make_cell(ufset_data[i], width=0.66, height=0.52, value_color=WHITE) for i in range(n_elems)]
        ).arrange(RIGHT, buff=0)
        idx_cells.move_to(LEFT * 3.5 + DOWN * 1.50)
        val_cells.next_to(idx_cells, DOWN, buff=0)

        label_ufset = Text("ufset", font="Consolas", font_size=20, color=TEAL_A).next_to(
            val_cells, LEFT, buff=0.18
        )
        label_idx = Text("下标", font="Microsoft YaHei", font_size=15, color=ORANGE).next_to(
            idx_cells, LEFT, buff=0.22
        )
        ufset_panel = VGroup(idx_cells, val_cells, label_ufset, label_idx)

        # 根结点高亮
        tree_nodes[0].circle.set_color(GREEN)
        val_cells[0].box.set_stroke(GREEN, width=2)

        with self.voiceover(
            text="当多次合并后，树可能退化成较长的单链。此时从底层结点 3 查找根结点 0，需要经过多层指针追溯。"
        ) as tracker:
            self.play(FadeIn(forest_group), FadeIn(ufset_panel), run_time=tracker.duration)

        # =====================================================================
        # PHASE B — 代码逐行追踪演示（递归深入 + 回溯拍平）
        # =====================================================================
        python_lines = [
            "def compression_find(ufset, x):",
            "    # 递归实现路径压缩",
            "    if ufset[x] < 0:  # 递归基：找到根结点",
            "        return x",
            "    ufset[x] = compression_find(ufset, ufset[x])",
            "    return ufset[x]"
        ]
        IDX_FUNC = 0
        IDX_COMMENT = 1
        IDX_IF = 2
        IDX_RETURN_BASE = 3
        IDX_RECURSE = 4
        IDX_RETURN = 5

        code_texts = []
        for line in python_lines:
            t = Text(line.lstrip(" "), font_size=12, font="Microsoft YaHei", color=WHITE)
            code_texts.append(t)

        code_group = VGroup(*code_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.11)
        SPACE_WIDTH = 0.09
        for i, line in enumerate(python_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            code_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 5.8:
            code_group.scale_to_fit_width(5.8)
        if code_group.height > 3.4:
            code_group.scale_to_fit_height(3.4)

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
            if not anims:
                anims.append(Wait(0.001))
            return anims

        self.play(FadeIn(code_block), run_time=0.6)

        call_banner = Text(
            "执行调用：compression_find(ufset, 3)", font="Microsoft YaHei", font_size=18, color=YELLOW
        ).next_to(ufset_panel, DOWN, buff=0.35).align_to(ufset_panel, LEFT)

        with self.voiceover(
            text="现在调用 compression_find(ufset, 3)，开始对结点 3 所在的查找路径进行压缩。"
        ) as tracker:
            self.play(FadeIn(call_banner), *get_track_anims(IDX_FUNC), run_time=tracker.duration)

        # 1. 递进阶段：从 3 -> 2 -> 1 -> 0
        ring = Circle(radius=self.NODE_RADIUS + 0.08, color=YELLOW, stroke_width=3.5).move_to(node_coords[3])

        with self.voiceover(
            text="首先进入第一层调用：x 等于 3。ufset[3] 为 2，不是根结点，于是递归调用 compression_find(ufset, 2)。"
        ) as tracker:
            self.play(*get_track_anims(IDX_IF), FadeIn(ring), run_time=0.35)
            self.play(*get_track_anims(IDX_RECURSE), run_time=0.35)
            self.play(
                ring.animate.move_to(node_coords[2]),
                ShowPassingFlash(parent_arrows[3].copy().set_color(YELLOW).set_stroke(width=5), time_width=0.4),
                run_time=max(0.4, tracker.duration - 0.7)
            )

        with self.voiceover(
            text="第二层调用：x 等于 2。ufset[2] 为 1，继续递归调用 compression_find(ufset, 1)。"
        ) as tracker:
            self.play(*get_track_anims(IDX_IF), run_time=0.35)
            self.play(*get_track_anims(IDX_RECURSE), run_time=0.35)
            self.play(
                ring.animate.move_to(node_coords[1]),
                ShowPassingFlash(parent_arrows[2].copy().set_color(YELLOW).set_stroke(width=5), time_width=0.4),
                run_time=max(0.4, tracker.duration - 0.7)
            )

        with self.voiceover(
            text="第三层调用：x 等于 1。ufset[1] 为 0，继续深入递归调用 compression_find(ufset, 0)。"
        ) as tracker:
            self.play(*get_track_anims(IDX_IF), run_time=0.35)
            self.play(*get_track_anims(IDX_RECURSE), run_time=0.35)
            self.play(
                ring.animate.move_to(node_coords[0]),
                ShowPassingFlash(parent_arrows[1].copy().set_color(YELLOW).set_stroke(width=5), time_width=0.4),
                run_time=max(0.4, tracker.duration - 0.7)
            )

        with self.voiceover(
            text="第四层调用：x 等于 0。ufset[0] 为负五，小于 0，触底命中递归基，直接返回根结点 0！"
        ) as tracker:
            self.play(*get_track_anims(IDX_IF), run_time=0.35)
            self.play(*get_track_anims(IDX_RETURN_BASE), run_time=0.35)
            self.play(
                ring.animate.set_color(GREEN),
                Indicate(val_cells[0].box, color=GREEN),
                run_time=max(0.3, tracker.duration - 0.7)
            )

        # 2. 回溯重连阶段：关键高潮动画
        # 回溯到 1
        with self.voiceover(
            text="开始回溯。返回第三层 x 等于 1，ufset[1] 被赋值为返回的根 0，保持不变，函数返回 0。"
        ) as tracker:
            self.play(*get_track_anims(IDX_RECURSE), ring.animate.move_to(node_coords[1]).set_color(YELLOW), run_time=tracker.duration * 0.6)
            self.play(*get_track_anims(IDX_RETURN), run_time=tracker.duration * 0.4)

        # 回溯到 2：重连 2 -> 0！
        new_arrow2 = self.make_parent_arrow(node_coords[2], node_coords[0], color=GREEN)
        val_cell2_text = Text("0", font="Consolas", font_size=20, color=GREEN).move_to(val_cells[2].box)

        with self.voiceover(
            text="回溯到第二层 x 等于 2：执行赋值 ufset[2] = 0！结点 2 的双亲直接被修改为根结点 0！"
        ) as tracker:
            self.play(*get_track_anims(IDX_RECURSE), ring.animate.move_to(node_coords[2]), run_time=0.35)
            self.play(
                Transform(parent_arrows[2], new_arrow2),
                Transform(val_cells[2].text, val_cell2_text),
                Indicate(val_cells[2].box, color=GREEN),
                run_time=max(0.5, tracker.duration - 0.7)
            )
            self.play(*get_track_anims(IDX_RETURN), run_time=0.35)

        # 回溯到 3：重连 3 -> 0！
        new_arrow3 = self.make_parent_arrow(node_coords[3], node_coords[0], color=GREEN)
        val_cell3_text = Text("0", font="Consolas", font_size=20, color=GREEN).move_to(val_cells[3].box)

        with self.voiceover(
            text="回溯到第一层 x 等于 3：执行赋值 ufset[3] = 0！结点 3 也越过中间所有结点，直接直连到根结点 0！"
        ) as tracker:
            self.play(*get_track_anims(IDX_RECURSE), ring.animate.move_to(node_coords[3]), run_time=0.35)
            self.play(
                Transform(parent_arrows[3], new_arrow3),
                Transform(val_cells[3].text, val_cell3_text),
                Indicate(val_cells[3].box, color=GREEN),
                run_time=max(0.5, tracker.duration - 0.7)
            )
            self.play(*get_track_anims(IDX_RETURN), run_time=0.35)

        flattened_label = Text("拍平后的扁平树", font="Microsoft YaHei", font_size=16, color=GREEN).next_to(
            tree_nodes[0], UP, buff=0.15
        )
        with self.voiceover(
            text="最后返回根结点 0。整条深链上的所有结点都被直接拉平到了根结点下，树的高度降低为 2，路径压缩彻底完成！"
        ) as tracker:
            self.play(
                FadeOut(ring),
                Transform(tree_label, flattened_label),
                run_time=tracker.duration
            )

        self.play(*get_track_anims(None), FadeOut(call_banner), run_time=0.4)

        # =====================================================================
        # PHASE C — 时空复杂度分析
        # =====================================================================
        self.play(FadeOut(forest_group),
                  ufset_panel.animate.move_to(LEFT * 3.3 + UP * 0.8), run_time=0.6)
        time_box = VGroup(
            Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(n)", font_size=24, color=YELLOW),
        ).arrange(RIGHT, buff=0.1)

        space_box = VGroup(
            Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(h)", font_size=24, color=YELLOW),
            Text("，最坏 ", font_size=18, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(n)", font_size=24, color=YELLOW),
        ).arrange(RIGHT, buff=0.08)

        complexity_panel = VGroup(time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        complexity_panel.next_to(ufset_panel, DOWN, buff=0.35).align_to(ufset_panel, LEFT)

        with self.voiceover(
            text="路径压缩查找在查找根结点的同时，会将查找路径上的元素直接连接到根结点，从而降低后续查找的路径长度。对于单次查找，在最坏情况下，并查集仍可能退化为一条链，需要沿路径递归到根结点，因此最坏时间复杂度为 O(n)。",
            subcaption="路径压缩查找在查找根结点的同时，会将查找路径上的元素直接连接到根结点，从而降低后续查找的路径长度。对于单次查找，在最坏情况下，并查集仍可能退化为一条链，需要沿路径递归到根结点，因此最坏时间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
            text="由于该算法采用递归实现，空间复杂度主要来自递归调用栈。递归深度等于查找路径的长度，记为 h，则空间复杂度为 O(h)。最坏情况下路径长度为 n，因此空间复杂度为 O(n)。",
            subcaption="由于该算法采用递归实现，空间复杂度主要来自递归调用栈。递归深度等于查找路径的长度，记为 h，则空间复杂度为 O(h)。最坏情况下路径长度为 n，因此空间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(
            text="以上就是并查集路径压缩算法Python版的完整演示过程。",
            subcaption="以上就是并查集路径压缩算法Python版的完整演示过程。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)


ContinuousUnionFindCompressionPythonVideo = UnionFindCompressionPythonVideo


if __name__ == "__main__":
    # 快速自测
    test_ufset = [-5, 0, 1, 2, 0]
    r = compression_find(test_ufset, 3)
    print("Find root:", r)
    print("ufset after compression:", test_ufset)
    assert r == 0
    assert test_ufset == [-5, 0, 0, 0, 0]
    print("Self-test passed!")
