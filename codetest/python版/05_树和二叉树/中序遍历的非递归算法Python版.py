# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import numpy as np
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService

# =========================================================================
# Python 版二叉树定义与中序遍历非递归算法逻辑
# =========================================================================
class BinaryTree:
    def __init__(self, data=None):
        self.data = data  # 数据域data默认为None，data为None时表示一颗空树
        self.lchild = None
        self.rchild = None

    def create_bitree(self, it):
        # 按先序次序输入二叉树中结点的值（一个字符），创建二叉链表表示的二叉树
        ch = next(it)
        if ch == '#':
            self.data = None
        else:
            self.data = ch  # 根结点的数据域赋值为ch
            self.lchild = BinaryTree()  # 为当前结点创建一个空的左子树
            self.lchild.create_bitree(it)  # 递归创建左子树
            self.rchild = BinaryTree()  # 为当前结点创建一个空的右子树
            self.rchild.create_bitree(it)  # 递归创建右子树

    def in_order_traverse(self):
        # 中序遍历二叉树的递归算法
        if self.data is not None:  # 若二叉树非空
            self.lchild.in_order_traverse()  # 中序遍历左子树
            print(self.data)  # 访问根结点
            self.rchild.in_order_traverse()  # 中序遍历右子树

    def in_order_traverse_nonre(self):
        # 中序遍历二叉树的非递归算法
        stack = []
        p = self
        while p.data is not None or stack:
            if p.data is not None:  # p非空
                stack.append(p)  # 根指针进栈
                p = p.lchild  # 遍历左子树
            else:  # p为空
                q = stack.pop()  # 退栈
                print(q.data, end='')  # 不换行、不加空格
                p = q.rchild  # 遍历右子树


class ContinuousInOrderNonRecursivePythonVideo(VoiceoverScene):
    NODE_R = 0.34
    Q_COLOR = "#FF8C1A"  # q 暂存槽专用橙色

    def make_node(self, label, center, r=None, color=BLUE):
        """工厂方法：绘制一个二叉树结点（圆形 + 居中字母），并挂载属性便于后续高亮。"""
        r = self.NODE_R if r is None else r
        c = Circle(radius=r, color=color, fill_color=color, fill_opacity=0.15, stroke_width=2.5).move_to(center)
        t = Text(str(label), font_size=22, color=WHITE).move_to(center)
        g = VGroup(c, t)
        g.circle = c
        g.label = t
        g.radius = r
        return g

    def edge(self, p1, p2, r1=None, r2=None, color=GRAY, sw=2.5):
        """在两结点圆心之间连线，两端各留出半径长度。"""
        r1 = self.NODE_R if r1 is None else r1
        r2 = self.NODE_R if r2 is None else r2
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        return Line(p1 + u * r1, p2 - u * r2, color=color, stroke_width=sw)

    def make_cell(self, content, w, h, fs, txt_color=WHITE, box_color=GRAY_B):
        """表格单元格。"""
        rect = Rectangle(width=w, height=h, color=box_color, stroke_width=1.5)
        t = Text(str(content), font_size=fs, color=txt_color, font="Microsoft YaHei")
        t.move_to(rect.get_center())
        return VGroup(rect, t)

    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ============================================================
        # PHASE A — 标题
        # ============================================================
        algo_title = Text("中序遍历的非递归算法（Python版）", font_size=36, font="Microsoft YaHei",
                          weight=BOLD).to_edge(UP, buff=0.5).shift(LEFT * 0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(
                text="本节我们使用 Python 语言，学习二叉树中序遍历的非递归算法。",
                subcaption="本节我们使用 Python 语言，学习二叉树中序遍历的非递归算法。"
        ) as tracker:
            self.wait(tracker.duration)

        subtitle = Text("该算法借助栈模拟递归，实现二叉树的中序遍历", font_size=20, font="Microsoft YaHei",
                        color=GRAY_A).next_to(algo_title, DOWN, buff=0.25)
        with self.voiceover(
                text="该算法借助栈模拟递归过程，实现二叉树的中序遍历。",
                subcaption="该算法借助栈模拟递归，实现二叉树的中序遍历。"
        ) as tracker:
            self.play(FadeIn(subtitle), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        self.play(FadeOut(subtitle), run_time=0.4)

        # ============================================================
        # PHASE C — CODE BLOCK CONFIG
        # ============================================================
        c_lines = [
            "def in_order_traverse_nonre(self):",
            "    stack = []",
            "    p = self",
            "    while p.data is not None or stack:",
            "        if p.data is not None:",
            "            stack.append(p)",
            "            p = p.lchild",
            "        else:",
            "            q = stack.pop()",
            "            print(q.data, end='')",
            "            p = q.rchild"
        ]
        # 代码行索引常量
        IDX_INIT = 1       # stack = []
        IDX_P = 2          # p = self
        IDX_WHILE = 3      # while p.data is not None or stack:
        IDX_IF = 4         # if p.data is not None:
        IDX_PUSH = 5       # stack.append(p)
        IDX_LEFT = 6       # p = p.lchild
        IDX_ELSE = 7       # else:
        IDX_POP = 8        # q = stack.pop()
        IDX_OUT = 9        # print(q.data, end='')
        IDX_RIGHT = 10     # p = q.rchild

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=11.5, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        SPACE_WIDTH = 0.105
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        buff_val = 0.25
        radius_val = 0.2
        code_bg = RoundedRectangle(
            corner_radius=radius_val,
            height=code_group.get_height() + 2 * buff_val,
            width=code_group.get_width() + 2 * buff_val,
            color=GRAY, fill_opacity=0.1, stroke_width=1
        )
        code_bg.move_to(code_group)
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.2).to_edge(RIGHT, buff=0.3)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line:
                return []
            anims = []
            if self.current_line is not None:
                anims.append(self.c_texts[self.current_line].animate.set_color(WHITE).scale(1 / 1.15, about_edge=LEFT))
            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW).scale(1.15, about_edge=LEFT))
                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.14).rotate(-PI / 2)
                    self.code_pointer.next_to(self.c_texts[new_idx], LEFT, buff=0.18)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.c_texts[new_idx], LEFT, buff=0.18)
                    anims.append(MoveToTarget(self.code_pointer))
                self.current_line = new_idx
            else:
                if hasattr(self, 'code_pointer'):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, 'code_pointer')
                self.current_line = None
            return anims

        def track(new_idx, run_time=0.35):
            anims = get_track_anims(new_idx)
            if anims:
                self.play(*anims, run_time=run_time)
            else:
                self.wait(run_time)

        # ============================================================
        # PHASE C2 — 二叉树、栈容器、指针 p、暂存槽 q、输出序列表
        # ============================================================
        # 一棵 5 结点二叉树：A(B(C,D), E)，先序输入 A B C # # D # # E # #，中序输出 C B D A E
        pos = {
            'A': np.array([-1.2, 1.95, 0]),
            'B': np.array([-2.6, 0.7, 0]), 'E': np.array([0.2, 0.7, 0]),
            'C': np.array([-3.6, -0.55, 0]), 'D': np.array([-1.6, -0.55, 0]),
        }
        children = {'A': ('B', 'E'), 'B': ('C', 'D'),
                    'C': (None, None), 'D': (None, None), 'E': (None, None)}
        NULL_POS = {
            ('C', 'L'): pos['C'] + np.array([-0.6, -0.85, 0]),
            ('C', 'R'): pos['C'] + np.array([0.6, -0.85, 0]),
            ('D', 'L'): pos['D'] + np.array([-0.6, -0.85, 0]),
            ('D', 'R'): pos['D'] + np.array([0.6, -0.85, 0]),
            ('E', 'L'): pos['E'] + np.array([-0.6, -0.85, 0]),
            ('E', 'R'): pos['E'] + np.array([0.6, -0.85, 0]),
        }

        edges = VGroup()
        for k, (lc, rc) in children.items():
            for ch in (lc, rc):
                if ch is not None:
                    edges.add(self.edge(pos[k], pos[ch]))

        circles, labels, nodes = {}, {}, {}
        node_group = VGroup()
        for k, p in pos.items():
            nd = self.make_node(k, p)
            circles[k] = nd.circle
            labels[k] = nd.label
            nodes[k] = nd
            node_group.add(nd)
        tree_group = VGroup(edges, node_group)

        # 指针 p 活动指示环
        P_OFF = np.array([0, 0.72, 0])
        ring = Circle(radius=self.NODE_R + 0.12, color=YELLOW, stroke_width=4).move_to(pos['A'])
        p_tag = Text("p", font_size=22, font="Consolas", weight=BOLD,
                     color=YELLOW).move_to(pos['A'] + P_OFF)

        # 栈容器
        STACK_X, STACK_BASE_Y, SLOT_H = -5.6, -1.55, 0.68
        stack_box = VGroup(
            Line([-6.35, 0.75, 0], [-6.35, -1.95, 0], color=GRAY_A, stroke_width=3),
            Line([-6.35, -1.95, 0], [-4.85, -1.95, 0], color=GRAY_A, stroke_width=3),
            Line([-4.85, -1.95, 0], [-4.85, 0.75, 0], color=GRAY_A, stroke_width=3),
        )
        stack_title = Text("stack", font_size=20, font="Consolas",
                           color=YELLOW).move_to([STACK_X, 1.05, 0])

        # 暂存槽 q
        q_box = RoundedRectangle(corner_radius=0.1, width=0.95, height=0.8, color=self.Q_COLOR,
                                 fill_color=self.Q_COLOR, fill_opacity=0.12,
                                 stroke_width=2).move_to([STACK_X, -2.85, 0])
        q_label = Text("q", font_size=20, font="Consolas", weight=BOLD,
                       color=self.Q_COLOR).next_to(q_box, LEFT, buff=0.15)

        # 中序输出序列表
        HEAD_W, CELL_W, CELL_H = 1.0, 0.55, 0.5
        N_OUT = 5
        row_idx = VGroup(self.make_cell("序号", HEAD_W, CELL_H, 16, txt_color=YELLOW))
        row_node = VGroup(self.make_cell("结点", HEAD_W, CELL_H, 16, txt_color=GREEN))
        out_cells = {}
        for k in range(N_OUT):
            row_idx.add(self.make_cell(k + 1, CELL_W, CELL_H, 18, txt_color=YELLOW))
            cell = self.make_cell("", CELL_W, CELL_H, 18)
            row_node.add(cell)
            out_cells[k] = cell[0]
        for r in (row_idx, row_node):
            r.arrange(RIGHT, buff=0)
        out_table = VGroup(row_idx, row_node).arrange(DOWN, buff=0)
        out_table_title = Text("中序输出序列", font_size=18, font="Microsoft YaHei", color=WHITE)
        out_block = VGroup(out_table_title, out_table).arrange(DOWN, buff=0.15)
        out_block.move_to([-0.7, -2.35, 0])

        with self.voiceover(
                text="右侧是该算法在 Python 中的核心实现代码。",
                subcaption="右侧是该算法在 Python 中的核心实现代码。"
        ) as tracker:
            self.play(FadeIn(code_block), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        with self.voiceover(
                text="这是一棵已建好的二叉树。",
                subcaption="这是一棵已建好的二叉树。"
        ) as tracker:
            self.play(FadeIn(tree_group), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        with self.voiceover(
                text="根结点是A，左子树有B、C、D，右孩子是E。",
                subcaption="根结点是A，左子树有B、C、D，右孩子是E。"
        ) as tracker:
            self.play(Indicate(nodes['A'], color=YELLOW, scale_factor=1.2), run_time=0.4)
            for k in ('B', 'C', 'D'):
                self.play(Indicate(nodes[k], color=GREEN, scale_factor=1.2), run_time=0.4)
            self.play(Indicate(nodes['E'], color=GREEN, scale_factor=1.2), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 2.0))

        with self.voiceover(
                text="左边是栈 stack，用来暂存遍历路径上的结点引用。",
                subcaption="左边是栈 stack，用来暂存遍历路径上的结点引用。"
        ) as tracker:
            self.play(Create(stack_box), FadeIn(stack_title), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        # ============================================================
        # PHASE C4 — 算法步骤
        # ============================================================
        self.play(FadeOut(tree_group), run_time=0.5)

        steps_title = Text("算法步骤", font_size=26, font="Microsoft YaHei", color=YELLOW, weight=BOLD)
        s1 = Text("① 初始化一个空列表作为栈 stack，指针 p 指向根结点。", font_size=18, font="Microsoft YaHei", color=WHITE)
        s2 = Text("② 当 p 非空或者栈 stack 非空时，循环执行以下操作：", font_size=18, font="Microsoft YaHei", color=WHITE)
        sa = Text("(a) 如果 p 非空，则使 p 进栈，p 指向该结点的左孩子；", font_size=17, font="Microsoft YaHei", color=GRAY_A)
        sb = VGroup(
            Text("(b) 如果 p 为空，则弹出栈顶元素 q 并访问输出，", font_size=17, font="Microsoft YaHei", color=GRAY_A),
            Text("将 p 指向 q 的右孩子。", font_size=17, font="Microsoft YaHei", color=GRAY_A),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        steps_body = VGroup(s1, s2, sa, sb).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        sa.shift(RIGHT * 0.45)
        sb.shift(RIGHT * 0.45)
        steps_panel = VGroup(steps_title, steps_body).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        steps_panel.move_to([-0.95, 0.15, 0])

        with self.voiceover(
                text="接下来，我们把该算法的基本步骤梳理一遍。"
        ) as tracker:
            self.play(FadeIn(steps_title, shift=DOWN * 0.15), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
                text="初始化空列表作为栈，指针 p 指向根结点。",
                subcaption="初始化空列表作为栈，指针 p 指向根结点。"
        ) as tracker:
            self.play(FadeIn(s1, shift=RIGHT * 0.15), run_time=0.5)
            self.wait(max(0.2, tracker.duration - 0.5))

        with self.voiceover(
                text="当 p 非空或者栈非空时，循环执行后续操作。",
                subcaption="当 p 非空或者栈非空时，循环执行后续操作。"
        ) as tracker:
            self.play(FadeIn(s2, shift=RIGHT * 0.15), run_time=0.5)
            self.wait(max(0.2, tracker.duration - 0.5))

        with self.voiceover(
                text="如果 p 非空，则使 p 进栈，p 指向该结点的左孩子。",
                subcaption="如果 p 非空，则使 p 进栈，p 指向该结点的左孩子。"
        ) as tracker:
            self.play(FadeIn(sa, shift=RIGHT * 0.15), run_time=0.5)
            self.wait(max(0.2, tracker.duration - 0.5))

        with self.voiceover(
                text="如果 p 为空，则从栈顶弹出结点 q 并访问输出，将 p 指向 q 的右孩子。",
                subcaption="如果 p 为空，则弹出栈顶元素 q 并访问输出，将 p 指向 q 的右孩子。"
        ) as tracker:
            self.play(FadeIn(sb, shift=RIGHT * 0.15), run_time=0.5)
            self.wait(max(0.2, tracker.duration - 0.5))

        self.play(FadeOut(steps_panel), FadeIn(tree_group), run_time=0.6)

        with self.voiceover(
                text="下方表格记录输出的中序序列。",
                subcaption="下方表格记录输出的中序序列。"
        ) as tracker:
            self.play(FadeIn(out_block), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        # ============================================================
        # PHASE D — 辅助函数
        # ============================================================
        stack_items = []
        order = {'n': 0}
        self.q_item = None
        self.cur_null = None

        def make_null(pt):
            circ = DashedVMobject(Circle(radius=0.2, color=GRAY_B, stroke_width=2).move_to(pt), num_dashes=12)
            t = Text("∧", font_size=15, color=GRAY_B).move_to(pt)
            return VGroup(circ, t)

        def move_p_node(key, rt=0.45):
            anims = [ring.animate.move_to(pos[key]), p_tag.animate.move_to(pos[key] + P_OFF)]
            if self.cur_null is not None:
                anims.append(FadeOut(self.cur_null))
                self.cur_null = None
            self.play(*anims, run_time=rt)

        def move_p_null(nkey, rt=0.45):
            pt = NULL_POS[nkey]
            nm = make_null(pt)
            anims = [ring.animate.move_to(pt), p_tag.animate.move_to(pt + P_OFF), FadeIn(nm)]
            if self.cur_null is not None:
                anims.append(FadeOut(self.cur_null))
            self.play(*anims, run_time=rt)
            self.cur_null = nm

        def push_to_stack(key, rt=0.5):
            mini = nodes[key].copy()
            mini.generate_target()
            mini.target.scale(0.8).move_to([STACK_X, STACK_BASE_Y + len(stack_items) * SLOT_H, 0])
            self.play(MoveToTarget(mini), run_time=rt)
            stack_items.append(mini)

        def pop_to_q(rt=0.5):
            mini = stack_items.pop()
            anims = [mini.animate.move_to(q_box.get_center())]
            if self.q_item is not None:
                anims.append(FadeOut(self.q_item))
            self.play(*anims, run_time=rt)
            self.q_item = mini

        def visit_output(key):
            self.play(circles[key].animate.set_fill(GREEN, opacity=0.5).set_stroke(GREEN, width=4), run_time=0.35)
            k = order['n']
            order['n'] += 1
            flyer = self.q_item[1].copy()
            self.play(flyer.animate.move_to(out_cells[k].get_center()).set_color(GREEN).scale(1.2),
                      Indicate(out_cells[k], color=GREEN, scale_factor=1.2), run_time=0.5)
            self.add(flyer)

        def push_step(key, w=0.22, rt=0.5):
            track(IDX_WHILE, w)
            track(IDX_IF, w)
            track(IDX_PUSH, w)
            push_to_stack(key, rt)

        def pop_step(w=0.22, rt=0.5):
            track(IDX_WHILE, w)
            track(IDX_ELSE, w)
            track(IDX_POP, w)
            pop_to_q(rt)

        def out_step(key):
            track(IDX_OUT, 0.28)
            visit_output(key)

        def left_step(child, parent, rt=0.45):
            track(IDX_LEFT, 0.28)
            if child is not None:
                move_p_node(child, rt)
            else:
                move_p_null((parent, 'L'), rt)

        def right_step(child, parent, rt=0.45):
            track(IDX_RIGHT, 0.28)
            if child is not None:
                move_p_node(child, rt)
            else:
                move_p_null((parent, 'R'), rt)

        # ============================================================
        # PHASE D2 — 初始化
        # ============================================================
        with self.voiceover(
                text="首先初始化一个空列表作为栈，并设置变量 q 暂存出栈的元素。",
                subcaption="初始化空列表作为栈，变量 q 暂存出栈的元素。"
        ) as tracker:
            track(IDX_INIT, 0.4)
            self.play(FadeIn(q_box), FadeIn(q_label), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(
                text="指针 p 指向根结点 A。",
                subcaption="指针 p 指向根结点 A。"
        ) as tracker:
            track(IDX_P, 0.4)
            self.play(FadeIn(ring), FadeIn(p_tag), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 1.0))

        # ============================================================
        # PHASE D3 — 遍历过程
        # ============================================================
        with self.voiceover(
                text="p非空，满足循环条件。",
                subcaption="p非空，满足循环条件。"
        ) as tracker:
            track(IDX_WHILE, 0.4)
            self.wait(max(0.1, tracker.duration - 0.4))

        with self.voiceover(
                text="执行if分支，A进栈。",
                subcaption="执行if分支，A进栈。"
        ) as tracker:
            track(IDX_IF, 0.3)
            track(IDX_PUSH, 0.3)
            push_to_stack('A', 0.6)
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="p指向A的左孩子B。",
                subcaption="p指向A的左孩子B。"
        ) as tracker:
            left_step('B', 'A')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(
                text="B非空，B也进栈。",
                subcaption="B非空，B也进栈。"
        ) as tracker:
            push_step('B')
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="p指向B的左孩子C。",
                subcaption="p指向B的左孩子C。"
        ) as tracker:
            left_step('C', 'B')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(
                text="C非空，C也进栈。",
                subcaption="C非空，C也进栈。"
        ) as tracker:
            push_step('C')
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="p指向C的左孩子，左孩子为空。",
                subcaption="p指向C的左孩子，左孩子为空。"
        ) as tracker:
            left_step(None, 'C')
            self.wait(max(0.1, tracker.duration - 0.75))

        # ----- 退栈与访问：C、B 依次出栈输出 -----
        with self.voiceover(
                text="p为空，但栈非空，继续循环。",
                subcaption="p为空，但栈非空，继续循环。"
        ) as tracker:
            track(IDX_WHILE, 0.4)
            self.wait(max(0.1, tracker.duration - 0.4))

        with self.voiceover(
                text="执行else分支，弹出栈顶C，存入q。",
                subcaption="执行else分支，弹出栈顶C，存入q。"
        ) as tracker:
            track(IDX_ELSE, 0.3)
            track(IDX_POP, 0.3)
            pop_to_q(0.6)
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="访问q指向的结点，输出C。",
                subcaption="访问q指向的结点，输出C。"
        ) as tracker:
            out_step('C')
            self.wait(max(0.1, tracker.duration - 1.15))

        with self.voiceover(
                text="p指向C的右孩子，右孩子为空。",
                subcaption="p指向C的右孩子，右孩子为空。"
        ) as tracker:
            right_step(None, 'C')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(
                text="栈非空，再弹出栈顶B，存入q。",
                subcaption="栈非空，再弹出栈顶B，存入q。"
        ) as tracker:
            pop_step()
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="访问B，输出B。",
                subcaption="访问B，输出B。"
        ) as tracker:
            out_step('B')
            self.wait(max(0.1, tracker.duration - 1.15))

        with self.voiceover(
                text="p指向B的右孩子D。",
                subcaption="p指向B的右孩子D。"
        ) as tracker:
            right_step('D', 'B')
            self.wait(max(0.1, tracker.duration - 0.75))

        # ----- 处理 D：进栈 → 左空 → 出栈输出 -----
        with self.voiceover(
                text="D非空，D进栈。",
                subcaption="D非空，D进栈。"
        ) as tracker:
            push_step('D')
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="p指向D的左孩子，为空。",
                subcaption="p指向D的左孩子，为空。"
        ) as tracker:
            left_step(None, 'D')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(
                text="弹出栈顶D并访问，输出D。",
                subcaption="弹出栈顶D并访问，输出D。"
        ) as tracker:
            pop_step()
            out_step('D')
            self.wait(max(0.1, tracker.duration - 2.35))

        with self.voiceover(
                text="p指向D的右孩子，仍为空。",
                subcaption="p指向D的右孩子，仍为空。"
        ) as tracker:
            right_step(None, 'D')
            self.wait(max(0.1, tracker.duration - 0.75))

        # ----- 弹出 A，转向右子树 E -----
        with self.voiceover(
                text="弹出栈顶A并访问，输出A。",
                subcaption="弹出栈顶A并访问，输出A。"
        ) as tracker:
            pop_step()
            out_step('A')
            self.wait(max(0.1, tracker.duration - 2.35))

        with self.voiceover(
                text="p指向A的右孩子E。",
                subcaption="p指向A的右孩子E。"
        ) as tracker:
            right_step('E', 'A')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(
                text="E非空，E进栈。",
                subcaption="E非空，E进栈。"
        ) as tracker:
            push_step('E')
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="p指向E的左孩子，为空。",
                subcaption="p指向E的左孩子，为空。"
        ) as tracker:
            left_step(None, 'E')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(
                text="弹出栈顶E并访问，输出E。",
                subcaption="弹出栈顶E并访问，输出E。"
        ) as tracker:
            pop_step()
            out_step('E')
            self.wait(max(0.1, tracker.duration - 2.35))

        with self.voiceover(
                text="p指向E的右孩子，为空。",
                subcaption="p指向E的右孩子，为空。"
        ) as tracker:
            right_step(None, 'E')
            self.wait(max(0.1, tracker.duration - 0.75))

        # ----- 循环结束 -----
        with self.voiceover(
                text="此时p为空，栈也为空。",
                subcaption="此时p为空，栈也为空。"
        ) as tracker:
            track(IDX_WHILE, 0.4)
            self.play(Indicate(stack_box, color=GRAY_A, scale_factor=1.05), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(
                text="循环条件不成立，遍历结束。",
                subcaption="循环条件不成立，遍历结束。"
        ) as tracker:
            end_anims = [FadeOut(ring), FadeOut(p_tag)]
            if self.cur_null is not None:
                end_anims.append(FadeOut(self.cur_null))
                self.cur_null = None
            self.play(*get_track_anims(None), *end_anims, run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.5))

        with self.voiceover(
                text="中序遍历结果是：C、B、D、A、E。",
                subcaption="中序遍历结果是：C、B、D、A、E。"
        ) as tracker:
            self.play(*[out_cells[k].animate.set_color(GREEN) for k in range(N_OUT)], run_time=0.6)
            self.wait(max(0.3, tracker.duration - 0.6))

        # ============================================================
        # PHASE E — COMPLEXITY
        # ============================================================
        fade_e = [FadeOut(stack_box), FadeOut(stack_title), FadeOut(q_box), FadeOut(q_label)]
        if self.q_item is not None:
            fade_e.append(FadeOut(self.q_item))
        self.play(*fade_e, run_time=0.5)

        note1 = Text("每个结点进栈和出栈各一次", font_size=20, font="Microsoft YaHei", color=WHITE)
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        note2 = Text("栈的最大容量是树的深度", font_size=20, font="Microsoft YaHei", color=WHITE)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        summary = VGroup(note1, time_box, note2, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.26)
        summary.move_to([-5.0, 1.0, 0])

        with self.voiceover(
                text="每个结点进栈和出栈各一次。",
                subcaption="每个结点进栈和出栈各一次。"
        ) as tracker:
            self.play(FadeIn(note1), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
                text="时间复杂度为 O n。",
                subcaption="时间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
                text="栈的最大容量是树的深度。",
                subcaption="栈的最大容量是树的深度。"
        ) as tracker:
            self.play(FadeIn(note2), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
                text="最坏情况下，二叉树退化成单支树，空间复杂度为 O n。",
                subcaption="最坏情况下，二叉树退化为单支树，空间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(text="以上就是中序遍历非递归算法 Python 版的完整演示。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)


# Alias
InOrderNonRecursivePythonVideo = ContinuousInOrderNonRecursivePythonVideo
