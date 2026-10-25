# coding=utf-8
"""并查集的合并（union_ufset）Manim 动画（Python版）。

动画按照“原理与合并模型 -> 代码逐行追踪演示 -> 时空复杂度分析”的顺序展开。
合并算法首先通过 find_ufset 分别找到两元素所在集合的根结点；
若根不同，则累加树规模，并将其中一棵树的根结点链接到另一棵树的根结点下。
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
    # 初始化并查集
    return [-1] * size


def find_ufset(ufset, x):
    # 查找元素 x 所属集合的根结点
    while ufset[x] >= 0:
        x = ufset[x]
    return x


def union_ufset(ufset, root1, root2):
    # 将两个子集合并
    root1 = find_ufset(ufset, root1)  # 查找root1所在根
    root2 = find_ufset(ufset, root2)  # 查找root2所在根
    if root1 == root2:
        return  # 已在同一集合则无需合并
    ufset[root1] += ufset[root2]  # 累加集合结点规模
    ufset[root2] = root1  # 将root2链接到root1下面


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
class UnionFindUnionPythonVideo(TreeVideoScene):
    """并查集 union_ufset 算法讲解动画（Python版）。"""

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
            "并查集的合并 (Python版)", font="Microsoft YaHei", font_size=36, weight=BOLD
        ).to_edge(UP, buff=0.25)
        self.play(FadeIn(title), run_time=0.7)

        with self.voiceover(
            text="本节学习并查集的合并算法 union_ufset 的Python实现。它的目标是将两个元素所在的集合合并为一个集合。"
        ) as tracker:
            self.wait(tracker.duration)

        # =====================================================================
        # PHASE A — 原理与合并前森林模型
        # =====================================================================
        node_coords = {
            0: np.array([-4.5, 1.55, 0]),
            1: np.array([-5.4, 0.45, 0]),
            2: np.array([-5.4, -0.65, 0]),
            3: np.array([-3.6, 0.45, 0]),
            4: np.array([-1.8, 0.45, 0]),
            5: np.array([-1.8, -0.65, 0]),
        }

        tree_nodes = {}
        for k, pt in node_coords.items():
            tree_nodes[k] = self.make_node(k, pt)

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

        # 初始底层列表 ufset
        n_elems = 6
        ufset_data = [-4, 0, 1, 0, -2, 4]
        idx_cells = VGroup(
            *[self.make_cell(i, width=0.66, height=0.42, value_color=ORANGE) for i in range(n_elems)]
        ).arrange(RIGHT, buff=0)
        val_cells = VGroup(
            *[self.make_cell(ufset_data[i], width=0.66, height=0.52, value_color=WHITE) for i in range(n_elems)]
        ).arrange(RIGHT, buff=0)
        idx_cells.move_to(LEFT * 3.35 + DOWN * 1.5)
        val_cells.next_to(idx_cells, DOWN, buff=0)

        label_ufset = Text("ufset", font="Consolas", font_size=20, color=TEAL_A).next_to(
            val_cells, LEFT, buff=0.18
        )
        label_idx = Text("下标", font="Microsoft YaHei", font_size=15, color=ORANGE).next_to(
            idx_cells, LEFT, buff=0.22
        )
        ufset_panel = VGroup(idx_cells, val_cells, label_ufset, label_idx)

        # 根结点头部初始高亮为绿色
        tree_nodes[0].circle.set_color(GREEN)
        tree_nodes[4].circle.set_color(GREEN)
        val_cells[0].box.set_stroke(GREEN, width=2)
        val_cells[4].box.set_stroke(GREEN, width=2)

        with self.voiceover(
            text="当前并查集包含两个不相交集合：集合 S1 的根结点为 0，集合 S2 的根结点为 4。列表中根位置分别记录了集合规模的负数值。"
        ) as tracker:
            self.play(FadeIn(forest_group), FadeIn(ufset_panel), run_time=tracker.duration)

        # =====================================================================
        # PHASE B — 代码逐行追踪演示
        # =====================================================================
        py_lines = [
            "def union_ufset(ufset, root1, root2):",
            "    # 将两个子集合并",
            "    root1 = find_ufset(ufset, root1)  # 查找root1所在根",
            "    root2 = find_ufset(ufset, root2)  # 查找root2所在根",
            "    if root1 == root2: return         # 已在同一集合则无需合并",
            "    ufset[root1] += ufset[root2]      # 累加集合结点规模",
            "    ufset[root2] = root1              # 将root2链接到root1下面",
        ]
        IDX_FUNC = 0
        IDX_FIND1 = 2
        IDX_FIND2 = 3
        IDX_IF = 4
        IDX_ACCUM = 5
        IDX_LINK = 6

        code_texts = []
        for line in py_lines:
            stripped_line = line.lstrip(" ")
            # Consolas 缺少中文字形；含中文注释的整行使用中文字体，
            # 否则 Manim 会把缺失字形绘制成白色方块。
            code_font = "Microsoft YaHei" if any("\u4e00" <= char <= "\u9fff" for char in stripped_line) else "Consolas"
            t = Text(stripped_line, font_size=11.5, font=code_font, color=WHITE)
            code_texts.append(t)
        self.code_texts = code_texts

        code_group = VGroup(*code_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.09)
        SPACE_WIDTH = 0.08
        for i, line in enumerate(py_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            code_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 5.8:
            code_group.scale_to_fit_width(5.8)
        if code_group.height > 3.6:
            code_group.scale_to_fit_height(3.6)

        code_bg = RoundedRectangle(
            corner_radius=0.15,
            height=code_group.get_height() + 0.45,
            width=code_group.get_width() + 0.78,
            color=GRAY,
            fill_opacity=0.1,
            stroke_width=1,
        )
        code_bg.move_to(code_group)
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.20).to_edge(RIGHT, buff=0.35)

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
            # 这行同时包含中文和代码；Consolas 没有中文字形，会产生白色方块。
            "执行调用：union_ufset(ufset, 2, 5)", font="Microsoft YaHei", font_size=18, color=YELLOW
        ).next_to(ufset_panel, DOWN, buff=0.35).align_to(ufset_panel, LEFT)

        with self.voiceover(
            text="假设我们要将元素 2 和元素 5 所在的集合进行合并，调用 union_ufset(ufset, 2, 5)。"
        ) as tracker:
            self.play(FadeIn(call_banner), *get_track_anims(IDX_FUNC), run_time=tracker.duration)

        # 1. 查找 root1
        ring1 = Circle(radius=self.NODE_RADIUS + 0.08, color=YELLOW, stroke_width=3.5).move_to(node_coords[2])
        with self.voiceover(
            text="第一步，调用 find_ufset 查找元素 2 的根结点。沿双亲路径 2 经过 1 追溯到根结点 0，因此 root1 更新为 0。"
        ) as tracker:
            self.play(*get_track_anims(IDX_FIND1), FadeIn(ring1), run_time=0.4)
            self.play(
                ring1.animate.move_to(node_coords[1]),
                ShowPassingFlash(parent_arrows[2].copy().set_color(YELLOW).set_stroke(width=5), time_width=0.4),
                run_time=0.45
            )
            self.play(
                ring1.animate.move_to(node_coords[0]),
                ShowPassingFlash(parent_arrows[1].copy().set_color(YELLOW).set_stroke(width=5), time_width=0.4),
                run_time=max(0.4, tracker.duration - 0.85)
            )

        # 2. 查找 root2
        ring2 = Circle(radius=self.NODE_RADIUS + 0.08, color=YELLOW, stroke_width=3.5).move_to(node_coords[5])
        with self.voiceover(
            text="第二步，查找元素 5 的根结点。沿双亲指针向上追溯到根结点 4，因此 root2 更新为 4。"
        ) as tracker:
            self.play(*get_track_anims(IDX_FIND2), FadeIn(ring2), run_time=0.4)
            self.play(
                ring2.animate.move_to(node_coords[4]),
                ShowPassingFlash(parent_arrows[5].copy().set_color(YELLOW).set_stroke(width=5), time_width=0.4),
                run_time=max(0.4, tracker.duration - 0.4)
            )

        # 3. 根结点判重
        with self.voiceover(
            text="第三步，比较两根是否相同。由于 root1 为 0，root2 为 4，两者不相等，说明不在同一集合，继续执行合并。"
        ) as tracker:
            self.play(*get_track_anims(IDX_IF), run_time=0.35)
            self.play(
                Indicate(tree_nodes[0].circle, color=YELLOW),
                Indicate(tree_nodes[4].circle, color=YELLOW),
                run_time=max(0.3, tracker.duration - 0.35)
            )

        # 4. 累加集合规模
        new_val0 = Text("-6", font="Consolas", font_size=20, color=GREEN).move_to(val_cells[0].box)
        with self.voiceover(
            text="第四步，累加集合规模：ufset[root1] 加上 ufset[root2]。负四加上负二等于负六，记录新集合共包含 6 个元素。"
        ) as tracker:
            self.play(*get_track_anims(IDX_ACCUM), run_time=0.35)
            self.play(
                Transform(val_cells[0].text, new_val0),
                Indicate(val_cells[0].box, color=GREEN),
                run_time=max(0.4, tracker.duration - 0.35)
            )

        # 5. 链接子树
        new_union_arrow = self.make_parent_arrow(node_coords[4], node_coords[0], color=GREEN)
        new_val4 = Text("0", font="Consolas", font_size=20, color=GREEN).move_to(val_cells[4].box)

        with self.voiceover(
            text="第五步，将 root2 链接到 root1 下面。在树中由结点 4 引出指向结点 0 的双亲箭头，列表中 ufset[4] 也被直接赋值为 0。"
        ) as tracker:
            self.play(*get_track_anims(IDX_LINK), run_time=0.35)
            self.play(
                GrowArrow(new_union_arrow),
                FadeOut(tree_label2),
                tree_label1.animate.become(Text("合并后的新集合", font="Microsoft YaHei", font_size=16, color=YELLOW).next_to(tree_nodes[0], UP, buff=0.15)),
                Transform(val_cells[4].text, new_val4),
                val_cells[4].box.animate.set_stroke(GRAY_B, width=1.5),
                tree_nodes[4].circle.animate.set_color(BLUE_D),
                FadeOut(ring1),
                FadeOut(ring2),
                run_time=max(0.5, tracker.duration - 0.35)
            )

        with self.voiceover(
            text="至此，原本独立的集合 S2 成功作为一棵子树并入集合 S1，整个合并操作圆满完成。"
        ) as tracker:
            self.play(
                Indicate(new_union_arrow, color=YELLOW),
                Indicate(tree_nodes[0].circle, color=GREEN),
                run_time=tracker.duration
            )

        self.play(*get_track_anims(None), FadeOut(call_banner), run_time=0.4)

        # =====================================================================
        # PHASE C — 时空复杂度分析
        # =====================================================================
        self.play(FadeOut(forest_group), FadeOut(new_union_arrow),
                  ufset_panel.animate.move_to(LEFT * 3.3 + UP * 0.8), run_time=0.6)
        time_box = VGroup(
            Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(n)", font_size=24, color=YELLOW),
        ).arrange(RIGHT, buff=0.1)

        space_box = VGroup(
            Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(1)", font_size=24, color=YELLOW),
        ).arrange(RIGHT, buff=0.1)

        complexity_panel = VGroup(time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        complexity_panel.next_to(ufset_panel, DOWN, buff=0.4).align_to(ufset_panel, LEFT)

        with self.voiceover(
            text="合并操作通常需要先分别查找两个元素所在集合的根结点，然后将其中一个根结点连接到另一个根结点下。因此，时间复杂度主要取决于两次查找操作。若普通查找在最坏情况下的时间复杂度为 O(n)，则合并操作的时间复杂度也为 O(n)。",
            subcaption="合并操作通常需要先分别查找两个元素所在集合的根结点，然后将其中一个根结点连接到另一个根结点下。因此，时间复杂度主要取决于两次查找操作。若普通查找在最坏情况下的时间复杂度为 O(n)，则合并操作的时间复杂度也为 O(n)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
            text="合并过程中只使用少量临时变量，并直接修改 ufset 列表中的双亲信息，不需要额外开辟随 n 增长的辅助空间，因此空间复杂度为 O(1)。",
            subcaption="合并过程中只使用少量临时变量，并直接修改 ufset 列表中的双亲信息，不需要额外开辟随 n 增长的辅助空间，因此空间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(
            text="以上就是并查集合并算法Python版的完整演示过程。",
            subcaption="以上就是并查集合并算法Python版的完整演示过程。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)


ContinuousUnionFindUnionPythonVideo = UnionFindUnionPythonVideo
