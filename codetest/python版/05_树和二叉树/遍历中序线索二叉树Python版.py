# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
from codetest.tree_video_support import TreeVideoScene, fit_tree_title


# =========================================================================
# Python 版二叉树定义与中序线索二叉树遍历算法
# =========================================================================
class BinaryTree:
    def __init__(self, data=None):
        self.data = data  # 数据域data默认为None，data为None时表示一颗空树
        self.lchild = None
        self.rchild = None
        self.ltag = 0  # 左线索标记
        self.rtag = 0  # 右线索标记


def create_bitree(preorder):
    # 按先序次序输入二叉树中结点的值（一个字符），创建二叉链表表示的二叉树
    if not preorder:
        return None
    ch = preorder.pop(0)  # 获取当前字符
    if ch == '#':  # 递归结束，建空树
        return None
    else:  # 递归创建二叉树
        node = BinaryTree(ch)  # 创建新节点
        node.lchild = create_bitree(preorder)  # 递归创建左子树
        node.rchild = create_bitree(preorder)  # 递归创建右子树
        return node


pre = None


def in_threading(p):
    # 以结点p为根的子树中序线索化
    global pre
    if p:
        in_threading(p.lchild)  # 递归左子树线索化
        if not p.lchild:  # 没有左孩子，建立前驱线索
            p.ltag = 1
            p.lchild = pre
        else:
            p.ltag = 0
        if pre and not pre.rchild:  # 前驱没有右孩子，建立后继线索
            pre.rtag = 1
            pre.rchild = p
        else:
            if pre:
                pre.rtag = 0
        pre = p  # 保持pre指向p的前驱
        in_threading(p.rchild)  # 递归右子树线索化


def in_order_threading(t):
    # 带头结点的二叉树中序线索化
    global pre
    thrt = BinaryTree()  # 创建头结点
    thrt.ltag = 0
    thrt.rtag = 1
    thrt.rchild = thrt  # 右指针回指
    if not t:  # 若树为空，左指针回指
        thrt.lchild = thrt
    else:
        thrt.lchild = t  # 头结点左孩子指向根
        pre = thrt
        in_threading(t)  # 中序遍历线索化
        pre.rchild = thrt  # 最后一个结点线索化
        pre.rtag = 1
        thrt.rchild = pre
    return thrt


def in_order_traverse_thr(t):
    # 遍历中序线索二叉树
    if t is None:
        return
    p = t.lchild  # p 指向根结点
    while p != t:  # 空树或遍历结束时，p == t
        while p.ltag == 0:
            p = p.lchild  # 沿左孩子向下
        print(p.data, end='')  # 访问其左子树为空的结点
        while p.rtag == 1 and p.rchild != t:
            p = p.rchild  # 沿右线索访问后继结点
            print(p.data, end='')
        p = p.rchild  # 转向 p 的右子树


# =========================================================================
# Manim 动画场景
# =========================================================================
class TraverseInOrderThreadedTreePythonVideo(TreeVideoScene):
    NODE_R = 0.28
    ORANGE = "#FF8C1A"   # 前驱线索
    TEAL = "#1AC7C7"     # 后继线索

    def make_node(self, label, center, r=None, color=BLUE):
        r = self.NODE_R if r is None else r
        c = Circle(radius=r, color=color, fill_color=color, fill_opacity=0.15, stroke_width=2.5).move_to(center)
        t = Text(str(label), font_size=20, color=WHITE).move_to(center)
        g = VGroup(c, t)
        g.circle = c
        g.label = t
        g.radius = r
        return g

    def make_head_node(self, center):
        c = Circle(radius=self.NODE_R, color=PURPLE, fill_color=PURPLE, fill_opacity=0.15, stroke_width=2.5).move_to(center)
        t = Text("T", font_size=20, color=WHITE).move_to(center)
        g = VGroup(c, t)
        g.circle = c
        g.label = t
        g.radius = self.NODE_R
        return g

    def edge(self, p1, p2, r1=None, r2=None, color=GRAY, sw=2.5):
        r1 = self.NODE_R if r1 is None else r1
        r2 = self.NODE_R if r2 is None else r2
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        return Line(p1 + u * r1, p2 - u * r2, color=color, stroke_width=sw)

    def thread_edge(self, p1, p2, r1=None, r2=None, color="#FF8C1A", angle=-TAU/4):
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        start = p1 + u * self.NODE_R
        end = p2 - u * self.NODE_R
        ca = CurvedArrow(start, end, angle=angle, color=color, stroke_width=2.5, tip_length=0.16)
        return DashedVMobject(ca, num_dashes=9, dashed_ratio=0.55)

    def null_thread(self, a, direction, color):
        a = np.array(a, dtype=float)
        direction = np.array(direction, dtype=float)
        direction = direction / np.linalg.norm(direction)
        start = a + direction * self.NODE_R
        end = a + direction * (self.NODE_R + 0.5)
        ar = Arrow(start, end, color=color, stroke_width=2.5, tip_length=0.14, buff=0)
        dashed = DashedVMobject(ar, num_dashes=4, dashed_ratio=0.55)
        nul = Text("∧", font_size=18, color=GRAY_B).move_to(end + direction * 0.16)
        return VGroup(dashed, nul)

    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("遍历中序线索二叉树 (Python版)", font_size=44, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        fit_tree_title(algo_title, logo, top_buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(
            text="本节我们学习遍历中序线索二叉树的Python实现。该算法是指中序遍历带线索的二叉树。",
            subcaption="本节我们学习遍历中序线索二叉树的Python实现。该算法是指中序遍历带线索的二叉树。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE B — CODE BLOCK CONFIG =====
        py_lines = [
            "def in_order_traverse_thr(t):",
            "    if t is None: return",
            "    p = t.lchild",
            "    while p != t:",
            "        while p.ltag == 0:",
            "            p = p.lchild",
            "        print(p.data, end='')",
            "        while p.rtag == 1 and p.rchild != t:",
            "            p = p.rchild",
            "            print(p.data, end='')",
            "        p = p.rchild",
        ]

        IDX_INIT = 2
        IDX_OUTER_WHILE = 3
        IDX_INNER_LEFT_WHILE = 4
        IDX_INNER_LEFT_MOVE = 5
        IDX_VISIT_LEFTMOST = 6
        IDX_INNER_RIGHT_WHILE = 7
        IDX_INNER_RIGHT_MOVE = 8
        IDX_VISIT_THREAD = 9
        IDX_RIGHT_SUBTREE = 10

        self.py_texts = []
        for line in py_lines:
            t = Text(line.lstrip(" "), font_size=13, font="Consolas", color=WHITE)
            self.py_texts.append(t)

        code_group = VGroup(*self.py_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        SPACE_WIDTH = 0.10
        for i, line in enumerate(py_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.py_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 5.5:
            code_group.scale_to_fit_width(5.5)
        if code_group.height > 3.8:
            code_group.scale_to_fit_height(3.8)

        code_bg = RoundedRectangle(
            corner_radius=0.14,
            height=code_group.get_height() + 0.35,
            width=code_group.get_width() + 0.6,
            color=GRAY, fill_opacity=0.1, stroke_width=1
        )
        code_bg.move_to(code_group.get_center() + LEFT * 0.12)
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.25).to_edge(RIGHT, buff=0.35)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line:
                if new_idx is None:
                    return [Wait(0.001)]
                return [self.py_texts[new_idx].animate.set_color(YELLOW)]
            anims = []
            if self.current_line is not None:
                anims.append(self.py_texts[self.current_line].animate.set_color(WHITE).scale(1 / 1.12, about_edge=LEFT))
            if new_idx is not None:
                anims.append(self.py_texts[new_idx].animate.set_color(YELLOW).scale(1.12, about_edge=LEFT))
                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.12).rotate(-PI / 2)
                    self.code_pointer.next_to(self.py_texts[new_idx], LEFT, buff=0.12)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.py_texts[new_idx], LEFT, buff=0.12)
                    anims.append(MoveToTarget(self.code_pointer))
                self.current_line = new_idx
            else:
                if hasattr(self, 'code_pointer'):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, 'code_pointer')
                self.current_line = None
            if not anims:
                anims.append(Wait(0.001))
            return anims

        # ===== PHASE C — 树与输出面板 =====
        pos = {
            'A': np.array([-2.5, 1.8, 0]),
            'B': np.array([-4.0, 0.6, 0]), 'C': np.array([-1.0, 0.6, 0]),
            'D': np.array([-4.8, -0.6, 0]), 'E': np.array([-3.2, -0.6, 0]), 'F': np.array([-0.2, -0.6, 0])
        }
        head_pos = np.array([-5.7, 1.8, 0])
        head_node = self.make_head_node(head_pos)
        head_name = Text("头结点", font_size=15, font="Microsoft YaHei", color=PURPLE).next_to(head_node, DOWN, buff=0.12)
        head_lchild = Arrow(head_pos + RIGHT * self.NODE_R, pos['A'] + LEFT * self.NODE_R,
                            color=PURPLE, buff=0, stroke_width=2.5, tip_length=0.16)
        # 从 F 沿树图右侧、上侧绕回 T，避开树结点和输出表。
        f_head_points = [pos['F'] + RIGHT * self.NODE_R,
                         np.array([0.65, -0.6, 0]), np.array([0.65, 2.4, 0]),
                         np.array([-5.7, 2.4, 0]), head_pos + UP * self.NODE_R]
        f_head_path = VMobject(color=self.TEAL, stroke_width=2.5).set_points_as_corners(f_head_points)
        f_head_thread = VGroup(DashedVMobject(f_head_path, num_dashes=36, dashed_ratio=0.55),
                               Arrow(f_head_points[-2], f_head_points[-1], color=self.TEAL,
                                     buff=0, stroke_width=2.5, tip_length=0.14,
                                     max_tip_length_to_length_ratio=0.5))

        edges = VGroup(
            self.edge(pos['A'], pos['B']),
            self.edge(pos['A'], pos['C']),
            self.edge(pos['B'], pos['D']),
            self.edge(pos['B'], pos['E']),
            self.edge(pos['C'], pos['F'])
        )

        threads = VGroup(
            self.thread_edge(pos['D'], head_pos, angle=-0.5, color=self.ORANGE),
            self.thread_edge(pos['D'], pos['B'], angle=-TAU/3, color=self.TEAL),
            self.thread_edge(pos['E'], pos['B'], angle=TAU/4, color=self.ORANGE),
            self.thread_edge(pos['E'], pos['A'], angle=-TAU/3, color=self.TEAL),
            self.thread_edge(pos['C'], pos['A'], angle=TAU/4, color=self.ORANGE),
            self.thread_edge(pos['F'], pos['C'], angle=TAU/4, color=self.ORANGE),
            f_head_thread
        )

        circles = {}
        labels = {}
        node_group = VGroup()
        for k, p in pos.items():
            nd = self.make_node(k, p)
            circles[k] = nd.circle
            labels[k] = nd.label
            node_group.add(nd)

        tree_group = VGroup(edges, threads, node_group, head_node, head_name, head_lchild)

        ring = Circle(radius=self.NODE_R + 0.1, color=YELLOW, stroke_width=4).move_to(pos['A'])

        def make_cell(content, w, h, fs, txt_color=WHITE, box_color=GRAY_B):
            rect = Rectangle(width=w, height=h, color=box_color, stroke_width=1.5)
            t = Text(str(content), font_size=fs, color=txt_color, font="Microsoft YaHei")
            t.move_to(rect.get_center())
            return VGroup(rect, t)

        HEAD_W, CELL_W, CELL_H = 1.0, 0.55, 0.5
        N_OUT = 6
        row_idx = VGroup(make_cell("序号", HEAD_W, CELL_H, 16, txt_color=YELLOW))
        row_node = VGroup(make_cell("结点", HEAD_W, CELL_H, 16, txt_color=GREEN))
        out_cells = {}
        for k in range(N_OUT):
            row_idx.add(make_cell(k + 1, CELL_W, CELL_H, 18, txt_color=YELLOW))
            cell = make_cell("", CELL_W, CELL_H, 18)
            row_node.add(cell)
            out_cells[k] = cell[0]
        for r in (row_idx, row_node):
            r.arrange(RIGHT, buff=0)
        out_table = VGroup(row_idx, row_node).arrange(DOWN, buff=0)
        out_table_title = Text("中序输出序列", font_size=18, font="Microsoft YaHei", color=WHITE)
        out_block = VGroup(out_table_title, out_table).arrange(DOWN, buff=0.15)
        out_block.move_to([-2.5, -1.7, 0])

        with self.voiceover(
            text="这是一棵已经建立好中序线索的二叉树。在正式演示算法前，我们先来了解一下本算法的核心思想。",
            subcaption="这是一棵已经建立好中序线索的二叉树。在正式演示算法前，我们先来了解一下本算法的核心思想。"
        ) as tracker:
            self.play(FadeIn(code_block), FadeIn(tree_group), FadeIn(out_block), run_time=tracker.duration)

        with self.voiceover(
            text="遍历线索二叉树的核心思想是利用原本为空的左右孩子指针，将它们改造成 指向遍历序列中前驱或后继的线索。这使得二叉树 在逻辑上被串联成了一个线性结构。",
            subcaption="遍历线索二叉树的核心思想是利用原本为空的左右孩子指针，将它们改造成指向遍历序列中前驱或后继的线索。这使得二叉树在逻辑上被串联成了一个线性结构。"
        ) as tracker:
            self.wait(tracker.duration)

        with self.voiceover(
            text="在普通二叉树的遍历中，我们必须依赖栈来进行回溯。而有了线索之后，我们可以直接顺着线索找到下一个结点，或者通过右子树自然地过渡，从而彻底摆脱了对栈的依赖。",
            subcaption="在普通二叉树的遍历中，我们必须依赖栈来进行回溯。而有了线索之后，我们可以直接顺着线索找到下一个结点，或者通过右子树自然地过渡，从而彻底摆脱了对栈的依赖。"
        ) as tracker:
            self.wait(tracker.duration)

        with self.voiceover(
            text="在这棵树中，橙色虚线代表前驱线索，青色虚线代表后继线索。正是这些青色的后继线索，赋予了我们像遍历单链表一样，顺藤摸瓜遍历整棵树的能力。",
            subcaption="在这棵树中，橙色虚线代表前驱线索，青色虚线代表后继线索。正是这些青色的后继线索，赋予了我们像遍历单链表一样，顺藤摸瓜遍历整棵树的能力。"
        ) as tracker:
            self.wait(tracker.duration)

        with self.voiceover(
            text="那么具体是如何遍历的呢？规则非常简单：首先不断向左，找到整棵树最左侧的结点作为起点；",
            subcaption="那么具体是如何遍历的呢？规则非常简单：首先不断向左，找到整棵树最左侧的结点作为起点；"
        ) as tracker:
            self.wait(tracker.duration)

        with self.voiceover(
            text="在访问当前结点后，如果它有后继线索，就直接顺着线索找到下一个结点；",
            subcaption="在访问当前结点后，如果它有后继线索，就直接顺着线索找到下一个结点；"
        ) as tracker:
            self.wait(tracker.duration)

        with self.voiceover(
            text="如果没有后继线索，说明它有右子树，那么下一个要访问的结点就是它右子树中最左侧的结点。不断重复这个过程，直到遍历完成。",
            subcaption="如果没有后继线索，说明它有右子树，那么下一个要访问的结点就是它右子树中最左侧的结点。不断重复这个过程，直到遍历完成。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE D — 算法演示 =====
        order = {'n': 0}
        flyers_group = VGroup()

        def visit(node_key):
            k = order['n']
            order['n'] += 1
            flyer = labels[node_key].copy()
            self.play(circles[node_key].animate.set_fill(GREEN, opacity=0.5).set_stroke(GREEN, width=4), run_time=0.2)
            self.play(flyer.animate.move_to(out_cells[k].get_center()).set_color(GREEN),
                      Indicate(out_cells[k], color=GREEN, scale_factor=1.2), run_time=0.4)
            self.add(flyer)
            flyers_group.add(flyer)

        with self.voiceover(
            text="第一步，初始化指针 p 指向二叉树的根结点 A。",
            subcaption="第一步，初始化指针 p 指向二叉树的根结点 A。"
        ) as tracker:
            self.play(*get_track_anims(IDX_INIT), run_time=0.4)
            ring.move_to(pos['A'])
            p_text = Text("p", font_size=20, color=YELLOW).next_to(ring, UP, buff=0.1)
            self.play(FadeIn(ring), FadeIn(p_text), run_time=max(0.2, tracker.duration - 0.4))

        with self.voiceover(
            text="当 p 不等于头结点 T 时，遍历继续进行。",
            subcaption="当 p 不等于头结点 T 时，遍历继续进行。"
        ) as tracker:
            self.play(*get_track_anims(IDX_OUTER_WHILE), run_time=tracker.duration)

        with self.voiceover(
            text="沿左孩子不断向下，找到中序遍历的第一个结点。",
            subcaption="沿左孩子不断向下，找到中序遍历的第一个结点。"
        ) as tracker:
            self.play(*get_track_anims(IDX_INNER_LEFT_WHILE), run_time=0.4)
            self.play(*get_track_anims(IDX_INNER_LEFT_MOVE), run_time=0.2)
            self.play(ring.animate.move_to(pos['B']), p_text.animate.next_to(pos['B'], UP, buff=0.1), run_time=0.4)
            self.play(*get_track_anims(IDX_INNER_LEFT_WHILE), run_time=0.2)
            self.play(*get_track_anims(IDX_INNER_LEFT_MOVE), run_time=0.2)
            self.play(ring.animate.move_to(pos['D']), p_text.animate.next_to(pos['D'], UP, buff=0.1), run_time=0.4)
            self.play(*get_track_anims(IDX_INNER_LEFT_WHILE), run_time=0.2)
            self.wait(max(0.1, tracker.duration - 2.0))

        with self.voiceover(
            text="结点 D 没有左孩子，直接访问 D。",
            subcaption="结点 D 没有左孩子，直接访问 D。"
        ) as tracker:
            self.play(*get_track_anims(IDX_VISIT_LEFTMOST), run_time=0.2)
            visit('D')
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
            text="D 的右线索指向 B，访问后继结点 B。",
            subcaption="D 的右线索指向 B，访问后继结点 B。"
        ) as tracker:
            self.play(*get_track_anims(IDX_INNER_RIGHT_WHILE), run_time=0.4)
            self.play(*get_track_anims(IDX_INNER_RIGHT_MOVE), run_time=0.2)
            self.play(ring.animate.move_to(pos['B']), p_text.animate.next_to(pos['B'], UP, buff=0.1), run_time=0.4)
            self.play(*get_track_anims(IDX_VISIT_THREAD), run_time=0.2)
            visit('B')
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
            text="B 有右子树，退出寻找线索的循环，转向 p 的右子树，来到 E。",
            subcaption="B 有右子树，退出寻找线索的循环，转向 p 的右子树，来到 E。"
        ) as tracker:
            self.play(*get_track_anims(IDX_INNER_RIGHT_WHILE), run_time=0.3)
            self.play(*get_track_anims(IDX_RIGHT_SUBTREE), run_time=0.3)
            self.play(ring.animate.move_to(pos['E']), p_text.animate.next_to(pos['E'], UP, buff=0.1), run_time=0.5)

        with self.voiceover(
            text="继续外层循环，E 没有左孩子，访问 E。",
            subcaption="继续外层循环，E 没有左孩子，访问 E。"
        ) as tracker:
            self.play(*get_track_anims(IDX_OUTER_WHILE), run_time=0.2)
            self.play(*get_track_anims(IDX_INNER_LEFT_WHILE), run_time=0.2)
            self.play(*get_track_anims(IDX_VISIT_LEFTMOST), run_time=0.2)
            visit('E')
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(
            text="E 的右线索指向根结点 A，访问后继结点 A。",
            subcaption="E 的右线索指向根结点 A，访问后继结点 A。"
        ) as tracker:
            self.play(*get_track_anims(IDX_INNER_RIGHT_WHILE), run_time=0.3)
            self.play(*get_track_anims(IDX_INNER_RIGHT_MOVE), run_time=0.2)
            self.play(ring.animate.move_to(pos['A']), p_text.animate.next_to(pos['A'], UP, buff=0.1), run_time=0.4)
            self.play(*get_track_anims(IDX_VISIT_THREAD), run_time=0.2)
            visit('A')
            self.wait(max(0.1, tracker.duration - 1.1))

        with self.voiceover(
            text="A 退出线索查找循环，转向它的右子树，来到 C。",
            subcaption="A 退出线索查找循环，转向它的右子树，来到 C。"
        ) as tracker:
            self.play(*get_track_anims(IDX_INNER_RIGHT_WHILE), run_time=0.3)
            self.play(*get_track_anims(IDX_RIGHT_SUBTREE), run_time=0.3)
            self.play(ring.animate.move_to(pos['C']), p_text.animate.next_to(pos['C'], UP, buff=0.1), run_time=0.5)

        with self.voiceover(
            text="C 同样没有左孩子，访问 C。",
            subcaption="C 同样没有左孩子，访问 C。"
        ) as tracker:
            self.play(*get_track_anims(IDX_OUTER_WHILE), run_time=0.2)
            self.play(*get_track_anims(IDX_INNER_LEFT_WHILE), run_time=0.2)
            self.play(*get_track_anims(IDX_VISIT_LEFTMOST), run_time=0.2)
            visit('C')
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(
            text="C 有右子树，退出寻找线索的循环，转向 p 的右子树，来到 F。",
            subcaption="C 有右子树，退出寻找线索的循环，转向 p 的右子树，来到 F。"
        ) as tracker:
            self.play(*get_track_anims(IDX_INNER_RIGHT_WHILE), run_time=0.3)
            self.play(*get_track_anims(IDX_RIGHT_SUBTREE), run_time=0.3)
            self.play(ring.animate.move_to(pos['F']), p_text.animate.next_to(pos['F'], UP, buff=0.1), run_time=0.5)

        with self.voiceover(
            text="继续外层循环，F 没有左孩子，访问 F。",
            subcaption="继续外层循环，F 没有左孩子，访问 F。"
        ) as tracker:
            self.play(*get_track_anims(IDX_OUTER_WHILE), run_time=0.2)
            self.play(*get_track_anims(IDX_INNER_LEFT_WHILE), run_time=0.2)
            self.play(*get_track_anims(IDX_VISIT_LEFTMOST), run_time=0.2)
            visit('F')
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(
            text="F 的右线索指向头结点 T。这里的循环条件 p 的右孩子不等于 T 变为假，跳出循环。",
            subcaption="F 的右线索指向头结点 T。这里的循环条件 p 的右孩子不等于 T 变为假，跳出循环。"
        ) as tracker:
            self.play(*get_track_anims(IDX_INNER_RIGHT_WHILE), run_time=0.4)
            self.play(Indicate(f_head_thread, color=YELLOW), Indicate(head_node, color=YELLOW), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(
            text="转向右子树后，p 回到头结点 T。",
            subcaption="转向右子树后，p 回到头结点 T。"
        ) as tracker:
            self.play(*get_track_anims(IDX_RIGHT_SUBTREE), run_time=0.3)
            self.play(ring.animate.move_to(head_pos),
                      p_text.animate.become(Text("p=T", font_size=20, color=YELLOW).next_to(head_node, LEFT, buff=0.1)), run_time=0.5)

        with self.voiceover(
            text="此时 p 等于头结点 T，外层循环结束，整个中序遍历完成。",
            subcaption="此时 p 等于头结点 T，外层循环结束，整个中序遍历完成。"
        ) as tracker:
            self.play(*get_track_anims(IDX_OUTER_WHILE), run_time=0.4)
            self.play(*get_track_anims(None), FadeOut(ring), FadeOut(p_text), run_time=0.5)

        # ===== PHASE E — COMPLEXITY =====
        self.play(FadeOut(out_block), FadeOut(flyers_group), run_time=0.5)

        result_label = Text("线索遍历序列：D B E A C F", font_size=24, font="Microsoft YaHei", color=GREEN)
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          Text("O(n)", font_size=24, font="Consolas", color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           Text("O(1)", font_size=24, font="Consolas", color=YELLOW)).arrange(RIGHT, buff=0.1)
        summary = VGroup(result_label, time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        summary.move_to([-2.5, -1.7, 0])

        with self.voiceover(
            text="在遍历中序线索二叉树时，每个结点仅被访问一次，并且没有多余的回溯，时间复杂度为 O(n)。",
            subcaption="在遍历中序线索二叉树时，每个结点仅被访问一次，并且没有多余的回溯，时间复杂度为 O(n)。"
        ) as tracker:
            self.play(Write(result_label), run_time=0.5)
            self.play(FadeIn(time_box), run_time=max(0.5, tracker.duration - 0.5))

        with self.voiceover(
            text="由于我们只使用了少量指针变量，不再需要递归调用栈或辅助栈，因此空间复杂度为 O(1)。",
            subcaption="由于我们只使用了少量指针变量，不再需要递归调用栈或辅助栈，因此空间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(
            text="以上就是遍历中序线索二叉树算法的完整演示。",
            subcaption="以上就是遍历中序线索二叉树算法的完整演示。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)


ContinuousTraverseInOrderThreadedTreePythonVideo = TraverseInOrderThreadedTreePythonVideo
