# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
from codetest.tree_video_support import TreeVideoScene, fit_tree_title, place_tree_summary


# =========================================================================
# Python 版链栈、二叉树与表达式树创建算法逻辑
# =========================================================================
class StackNode:
    def __init__(self, data=None):
        self.data = data
        self.next = None

    def __str__(self):
        return str(self.data)


class LinkStack:
    def __init__(self):
        # 初始化链栈
        self.top = None  # 构造一个空栈，栈顶指针top置空

    def push(self, e):
        # 在栈顶插入元素e
        p = StackNode(data=e)  # 生成新结点，将新结点数据域置为e
        p.next = self.top  # 将新结点插入栈顶
        self.top = p  # 修改栈顶指针为p

    def pop(self):
        # 将栈顶元素弹出
        if self.top is None:
            raise Exception('栈已空')
        e = self.top.data  # 将栈顶元素赋给e
        self.top = self.top.next  # 修改栈顶指针
        return e

    def get_top(self):
        # 返回栈顶元素，不修改栈顶指针
        if self.top is not None:  # 栈非空
            return self.top.data
        else:
            raise Exception('栈已空')

    def __len__(self):
        p = self.top
        count = 0
        while p is not None:
            p = p.next
            count += 1
        return count

    def stack_empty(self):
        # 判断栈是否为空
        return self.top is None


class BinaryTree:
    def __init__(self, data=None):
        self.data = data  # 数据域data默认为None，data为None时表示一颗空树
        self.lchild = None
        self.rchild = None

    def create_exptree(self, data, lchild=None, rchild=None):
        # 创建二叉链表表示的二叉树
        self.data = data  # 根结点的数据域赋值为data
        self.lchild = lchild
        self.rchild = rchild

    def post_order(self):
        # 后序遍历二叉树的递归算法
        if self.data is not None:  # 若二叉树非空
            if self.lchild:
                self.lchild.post_order()  # 后序遍历左子树
            if self.rchild:
                self.rchild.post_order()  # 后序遍历右子树
            print(self.data, end='')  # 访问根结点


def is_optr(ch):
    # 判断ch是否为合法的运算符
    return ch in '+-*/()#'


def precede(theta1, theta2):
    # 判断运算符优先级
    if (theta1 == '(' and theta2 == ')') or (theta1 == '#' and theta2 == '#'):
        return '='
    elif theta1 == '(' or theta1 == '#' or theta2 == '(' or (
            (theta1 == '+' or theta1 == '-') and (theta2 == '*' or theta2 == '/')):
        return '<'
    else:
        return '>'


def get_value(a, b, theta):
    # 加减乘除运算
    if theta == '+':
        return a + b
    elif theta == '-':
        return a - b
    elif theta == '*':
        return a * b
    elif theta == '/':
        return a / b


def init_exptree(e):
    i = 0
    optr = LinkStack()  # 初始化optr栈
    expr = LinkStack()  # 初始化expr栈
    optr.push('#')  # 将表达式起始符“#”压入optr栈
    b_t = None
    while i < len(e) and (e[i] != '#' or optr.get_top() != '#'):  # 表达式没有扫描完毕或optr栈顶不为“#”
        ch = e[i]
        if not is_optr(ch):  # ch不是运算符
            b_t = BinaryTree()
            b_t.create_exptree(ch, None, None)  # 以ch为根创建一棵只有根结点的二叉树
            expr.push(b_t)  # 将二叉树根结点进expr栈
            i += 1
        else:
            character = precede(optr.get_top(), ch)  # 比较optr的栈顶元素和ch的优先级
            if '<' == character:
                optr.push(ch)  # 当前字符ch压入optr栈
                i += 1
            elif '>' == character:
                theta = optr.pop()  # 弹出optr栈顶的运算符
                b = expr.pop()  # 弹出expr栈顶的两个运算数
                a = expr.pop()
                b_t = BinaryTree()
                b_t.create_exptree(theta, a, b)  # 以theta为根，a为左子树，b为右子树创建二叉树
                expr.push(b_t)  # 将二叉树根结点进expr栈
            elif '=' == character:  # optr的栈顶元素是“(”且ch是“)”
                optr.pop()  # 弹出optr栈顶的“(”
                i += 1
    return expr.get_top() if expr.top is not None else b_t  # 返回树的根结点


# =========================================================================
# Manim 动画场景
# =========================================================================
class ExpressionTreeCreatePythonVideo(TreeVideoScene):
    NODE_R = 0.35

    def make_node(self, label, center, color=BLUE):
        c = Circle(radius=self.NODE_R, color=color, fill_color=color, fill_opacity=0.15, stroke_width=2.5).move_to(center)
        t = Text(label, font_size=24, color=WHITE).move_to(center)
        g = VGroup(c, t)
        g.circle = c
        g.label = t
        return g

    def make_edge(self, p1, p2, color=WHITE):
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        start_pt = p1 + u * self.NODE_R
        end_pt = p2 - u * self.NODE_R
        return Line(start_pt, end_pt, color=color, stroke_width=2.2)

    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(UP * 0.1)
        self.add(logo)

        # ===== 标题 =====
        algo_title = Text("表达式树的创建算法 (Python版)", font_size=46, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.3)
        fit_tree_title(algo_title, logo, top_buff=0.3)
        self.play(FadeIn(algo_title), run_time=0.8)

        # ===== 生活实例：工厂流水线组装 =====
        title_analogy = Text("生活实例：工厂流水线快速演示 (以 a+b 为例)", font_size=32, color=BLUE).next_to(algo_title, DOWN, buff=0.3)

        # 零件仓库
        box_expt = RoundedRectangle(corner_radius=0.1, width=3.0, height=1.5, color=GREEN).shift(DOWN * 1.8 + LEFT * 2.8)
        txt_expt = Text("零件仓库", font_size=20, font="Microsoft YaHei").next_to(box_expt, DOWN, buff=0.1)
        grp_expt = VGroup(box_expt, txt_expt)

        # 指令图纸
        box_optr = RoundedRectangle(corner_radius=0.1, width=3.0, height=1.5, color=BLUE).shift(DOWN * 1.8 + RIGHT * 2.8)
        txt_optr = Text("指令图纸", font_size=20, font="Microsoft YaHei").next_to(box_optr, DOWN, buff=0.1)
        grp_optr = VGroup(box_optr, txt_optr)

        # 组装台
        box_asm = RoundedRectangle(corner_radius=0.1, width=3.6, height=2.0, color=YELLOW)
        txt_asm = Text("自动化组装台", font_size=20, font="Microsoft YaHei").next_to(box_asm, UP, buff=0.1)
        grp_asm = VGroup(box_asm, txt_asm).next_to(title_analogy, DOWN, buff=0.5)

        arrow_kwargs = {"color": WHITE, "max_tip_length_to_length_ratio": 1.0, "max_stroke_width_to_length_ratio": 1.0}

        arrow_expt = Arrow(box_expt.get_top(), box_asm.get_bottom(), **arrow_kwargs)
        arrow_optr = Arrow(box_optr.get_top(), box_asm.get_bottom(), **arrow_kwargs)

        arrow_in_expt = Arrow(box_expt.get_left() + LEFT * 1.5, box_expt.get_left(), **arrow_kwargs)
        arrow_in_optr = Arrow(box_optr.get_right() + RIGHT * 1.5, box_optr.get_right(), **arrow_kwargs)

        analogy_bg = VGroup(
            title_analogy, grp_expt, grp_optr, grp_asm,
            arrow_expt, arrow_optr, arrow_in_expt, arrow_in_optr
        )

        with self.voiceover(
            text="本节我们来学习表达式树创建算法的Python实现，该算法是指利用双栈来创建中缀表达式对应的表达式树。"
        ) as tracker:
            self.play(FadeIn(analogy_bg), run_time=tracker.duration)

        with self.voiceover(
            text="表达式树的创建，就像是一个自动化工厂的流水线组装过程。我们以 a加b 为例，快速浏览一遍。"
        ) as tracker:
            self.wait(tracker.duration)

        n_a = self.make_node('a', arrow_in_expt.get_start())
        n_plus = self.make_node('+', arrow_in_optr.get_start(), BLUE)
        n_b = self.make_node('b', arrow_in_expt.get_start())

        with self.voiceover(text="当流水线运来基础零件 a 时，机器会直接将其送入左侧的零件仓库暂存。") as tracker:
            self.play(FadeIn(n_a, shift=RIGHT), run_time=max(0.1, tracker.duration * 0.3))
            self.play(n_a.animate.move_to(box_expt.get_center() + LEFT * 0.6), run_time=max(0.1, tracker.duration * 0.7))

        with self.voiceover(text="随后运来了一张加号组装图纸，它会被送入右侧的图纸栈中等待。") as tracker:
            self.play(FadeIn(n_plus, shift=LEFT), run_time=max(0.1, tracker.duration * 0.3))
            self.play(n_plus.animate.move_to(box_optr.get_center()), run_time=max(0.1, tracker.duration * 0.7))

        with self.voiceover(text="紧接着又运来了基础零件 b，同样也被送入左侧的零件仓库。") as tracker:
            self.play(FadeIn(n_b, shift=RIGHT), run_time=max(0.1, tracker.duration * 0.3))
            self.play(n_b.animate.move_to(box_expt.get_center() + RIGHT * 0.6), run_time=max(0.1, tracker.duration * 0.7))

        with self.voiceover(text="此时触发了组装作业，机器会从图纸栈取出一张图纸，并从零件仓库取出对应的两个零件，一起送上组装台。") as tracker:
            self.play(
                n_plus.animate.move_to(box_asm.get_center() + UP * 0.3),
                n_a.animate.move_to(box_asm.get_center() + DOWN * 0.3 + LEFT * 0.7),
                n_b.animate.move_to(box_asm.get_center() + DOWN * 0.3 + RIGHT * 0.7),
                run_time=tracker.duration
            )

        with self.voiceover(text="在组装台上，它们被牢牢地拼装在一起，形成了一个更大的半成品组件。") as tracker:
            e1 = self.make_edge(n_plus.circle.get_center(), n_a.circle.get_center())
            e2 = self.make_edge(n_plus.circle.get_center(), n_b.circle.get_center())
            self.play(Create(e1), Create(e2), run_time=tracker.duration)

        with self.voiceover(text="随后，这个新组装的半成品作为一个整体，被重新送回零件仓库，等待下一次更大规模的组装。") as tracker:
            subtree = VGroup(n_plus, n_a, n_b, e1, e2)
            self.play(subtree.animate.scale(0.7).move_to(box_expt.get_center()), run_time=tracker.duration)

        with self.voiceover(text="当所有图纸执行完毕，仓库中剩下的最后这件终极成品，就是我们需要的完整表达式树结构。") as tracker:
            self.play(Indicate(subtree, color=RED, scale_factor=1.1), run_time=tracker.duration)

        self.wait(0.5)
        self.play(FadeOut(analogy_bg), FadeOut(subtree))

        # ===== 核心思想总结 =====
        summary_title = Text("核心思想", font_size=36, color=YELLOW).shift(UP * 1.5)
        summary_body = Text(
            "表达式树的创建本质上是一个 算符优先分析 过程：\n\n"
            "1. 遇到操作数：直接入 结点栈(expr)\n"
            "2. 遇到运算符：与 符号栈(optr) 栈顶比较优先级\n"
            "3. 栈顶运算符优先级更高时，先弹栈组装\n"
            "   弹出1个运算符、2棵子树，建树后压回结点栈\n"
            "4. 读入运算符优先级更高时，压入符号栈",
            font_size=28, font="Microsoft YaHei", line_spacing=1.5,
            t2c={
                "算符优先分析": RED,
                "结点栈(expr)": GREEN,
                "符号栈(optr)": BLUE,
                "组装": ORANGE
            }
        ).next_to(summary_title, DOWN, buff=0.8)

        summary_box = SurroundingRectangle(summary_body, color=WHITE, buff=0.5, corner_radius=0.2)
        summary_group = VGroup(summary_title, summary_body, summary_box)
        place_tree_summary(summary_group, algo_title)

        with self.voiceover(text="通过这个实例我们可以看出，表达式树的创建本质上是一个算符优先分析过程。") as tracker:
            self.play(FadeIn(summary_title, shift=DOWN), run_time=max(0.1, tracker.duration * 0.3))
            self.play(Create(summary_box), run_time=max(0.1, tracker.duration * 0.3))
            self.play(Write(summary_body), run_time=max(0.1, tracker.duration * 0.4))

        with self.voiceover(text="遇到操作数直接压入结点栈。比较运算符时，如果栈顶运算符的优先级更高，就先弹栈组装子树；如果读入运算符的优先级更高，就将它压入符号栈。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="接下来我们结合具体代码，看看程序中是如何借助两个栈完成建树的。") as tracker:
            self.play(FadeOut(summary_group), run_time=tracker.duration)

        # ===== 准备代码块 =====
        py_lines = [
            "def init_exptree(e):",                               # 0
            "    optr = LinkStack(); expr = LinkStack()",         # 1  L_INIT
            "    optr.push('#')  # 起始符'#'压入optr栈",            # 2  L_PUSH_OPTR
            "    i = 0",                                          # 3
            "    while i < len(e) and (e[i]!='#' or optr.get_top()!='#'):", # 4 L_WHILE
            "        ch = e[i]",                                  # 5
            "        if not is_optr(ch):  # ch是操作数",           # 6  L_IF_NOT_OP
            "            t = BinaryTree()",                       # 7  L_NEW_NODE
            "            t.create_exptree(ch, None, None)",       # 8
            "            expr.push(t); i += 1",                   # 9  L_PUSH_EXPT
            "        else:  # 比较优先级",                         # 10 L_ELSE
            "            char = precede(optr.get_top(), ch)",     # 11 L_PRECEDE
            "            if '<' == char:",                        # 12 L_CASE_LESS
            "                optr.push(ch); i += 1",              # 13
            "            elif '>' == char:",                      # 14 L_CASE_GREATER
            "                theta = optr.pop()",                 # 15 L_MERGE_POP
            "                b = expr.pop(); a = expr.pop()",     # 16 L_MERGE_POP2
            "                t = BinaryTree()",                   # 17 L_MERGE_NEW
            "                t.create_exptree(theta, a, b)",      # 18 L_MERGE_LINK
            "                expr.push(t)",                       # 19 L_MERGE_PUSH
            "            elif '=' == char:",                      # 20 L_CASE_EQUAL
            "                optr.pop(); i += 1",                 # 21
        ]

        L_INIT = 1
        L_PUSH_OPTR = 2
        L_WHILE = 4
        L_IF_NOT_OP = 6
        L_NEW_NODE = 7
        L_PUSH_EXPT = 9
        L_ELSE = 10
        L_PRECEDE = 11
        L_CASE_LESS = 12
        L_CASE_GREATER = 14
        L_MERGE_POP = 15
        L_MERGE_POP2 = 16
        L_MERGE_NEW = 17
        L_MERGE_LINK = 18
        L_MERGE_PUSH = 19
        L_CASE_EQUAL = 20

        self.py_texts = []
        for line in py_lines:
            display_line = line.lstrip(" ")
            code_font = "Microsoft YaHei" if any("\u4e00" <= char <= "\u9fff" for char in display_line) else "Consolas"
            t = Text(display_line, font_size=9.5, font=code_font, color=WHITE)
            self.py_texts.append(t)

        code_group = VGroup(*self.py_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.07)
        SPACE_WIDTH = 0.06
        for i, line in enumerate(py_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.py_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 5.6:
            code_group.scale_to_fit_width(5.6)
        if code_group.height > 4.7:
            code_group.scale_to_fit_height(4.7)

        code_bg = RoundedRectangle(corner_radius=0.15, height=code_group.get_height() + 0.35,
                                   width=code_group.get_width() + 0.5, color=GRAY, fill_opacity=0.1, stroke_width=1)
        code_bg.move_to(code_group)
        code_block = VGroup(code_bg, code_group)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line:
                if new_idx is None:
                    return [Wait(0.001)]
                return [self.py_texts[new_idx].animate.set_color(YELLOW)]
            anims = []
            if self.current_line is not None:
                anims.append(self.py_texts[self.current_line].animate.set_color(WHITE).scale(1 / 1.08, about_edge=LEFT))
            if new_idx is not None:
                anims.append(self.py_texts[new_idx].animate.set_color(YELLOW).scale(1.08, about_edge=LEFT))
                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.14).rotate(-PI / 2)
                    self.code_pointer.next_to(self.py_texts[new_idx], LEFT, buff=0.15)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.py_texts[new_idx], LEFT, buff=0.15)
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

        # ===== 布局核心区域 =====
        SCREEN_BOTTOM = -config.frame_y_radius
        MARGIN = 0.3

        top_y_limit = algo_title.get_bottom()[1] - 0.2
        max_height = top_y_limit - SCREEN_BOTTOM - MARGIN * 2

        # [右侧代码块]
        if code_block.height > max_height:
            code_block.scale_to_fit_height(max_height)
        if code_block.width > 5.15:
            code_block.scale_to_fit_width(5.15)
        code_block.to_edge(RIGHT, buff=0.2).set_y((top_y_limit + SCREEN_BOTTOM) / 2)

        # [输入字符串流]
        expr_str = "a+b*c#"
        str_boxes = VGroup()
        for i, ch in enumerate(expr_str):
            box = Square(side_length=0.6, color=GRAY_B)
            txt = Text(ch, font_size=24, color=WHITE).move_to(box.get_center())
            str_boxes.add(VGroup(box, txt))
        str_boxes.arrange(RIGHT, buff=0)
        str_title = Text("表达式:", font_size=18, color=YELLOW).next_to(str_boxes, LEFT, buff=0.3)
        expr_group = VGroup(str_title, str_boxes)

        expr_group.to_edge(LEFT, buff=0.5).set_y(top_y_limit - 0.5)

        # [双栈区]
        stack_width = 1.0
        stack_height = 0.5

        # optr 栈
        optr_title = Text("optr栈", font_size=18, color=ORANGE)
        optr_stack = VGroup()
        optr_base_line = Line(LEFT * 0.6, RIGHT * 0.6, color=ORANGE, stroke_width=3)
        optr_group = VGroup(VGroup(optr_base_line), optr_title).arrange(DOWN, buff=0.2)

        # expr 栈
        expt_title = Text("expr栈(树指针)", font_size=18, color=GREEN)
        expt_stack = VGroup()
        expt_base_line = Line(LEFT * 0.8, RIGHT * 0.8, color=GREEN, stroke_width=3)
        expt_group = VGroup(VGroup(expt_base_line), expt_title).arrange(DOWN, buff=0.2)

        stacks_group = VGroup(optr_group, expt_group).arrange(RIGHT, buff=2.0)
        stacks_group.to_edge(LEFT, buff=0.8).to_edge(DOWN, buff=0.8)

        def push_stack(stack_vgroup, base_line, label_str, color):
            box = Rectangle(width=stack_width, height=stack_height, color=color, fill_opacity=0.2)
            txt = Text(label_str, font_size=18, color=WHITE).move_to(box.get_center())
            item = VGroup(box, txt)
            if len(stack_vgroup) == 0:
                item.next_to(base_line, UP, buff=0)
            else:
                item.next_to(stack_vgroup[-1], UP, buff=0)
            stack_vgroup.add(item)
            return item

        def pop_stack(stack_vgroup):
            if len(stack_vgroup) > 0:
                item = stack_vgroup[-1]
                stack_vgroup.remove(item)
                return item
            return None

        # [树的构建区域]
        arena_center = np.array([-2.5, 0.5, 0])
        node_pos = {
            '+': arena_center + np.array([0, 1.2, 0]),
            'a': arena_center + np.array([-2, 0, 0]),
            '*': arena_center + np.array([2, 0, 0]),
            'b': arena_center + np.array([0.8, -1.2, 0]),
            'c': arena_center + np.array([3.2, -1.2, 0]),
        }

        created_nodes = {}

        # ==================== 正式动画开始 ====================
        with self.voiceover(text="我们将通过经典的算符优先法，使用optr操作符栈和expr树指针栈，来构建表达式树。") as tracker:
            self.play(FadeIn(code_block), FadeIn(expr_group), FadeIn(optr_title), FadeIn(optr_base_line), FadeIn(expt_title), FadeIn(expt_base_line), run_time=tracker.duration)

        with self.voiceover(text="初始化阶段，我们将一个结束符井号，压入optr栈中，作为表达式结束的比对标识。") as tracker:
            self.play(*get_track_anims(L_INIT), run_time=0.4)
            self.play(*get_track_anims(L_PUSH_OPTR), run_time=0.4)

            item = push_stack(optr_stack, optr_base_line, '#', ORANGE)
            self.play(FadeIn(item, shift=UP), run_time=max(0.2, tracker.duration - 0.8))

        ch_pointer = Arrow(start=UP, end=DOWN, color=RED).scale(0.5).next_to(str_boxes[0], UP, buff=0.1)
        self.play(FadeIn(ch_pointer))

        steps = [
            ('a', 'operand'),
            ('+', 'push_op'),
            ('b', 'operand'),
            ('*', 'push_op'),
            ('c', 'operand'),
            ('#', 'pop_op_merge1'),
            ('#', 'pop_op_merge2'),
            ('#', 'end')
        ]

        step_idx = 0
        while step_idx < len(steps):
            ch, step_type = steps[step_idx]
            ch_idx = min(step_idx, len(str_boxes) - 1)

            self.play(*get_track_anims(L_WHILE))
            self.play(ch_pointer.animate.next_to(str_boxes[ch_idx], UP, buff=0.1), run_time=0.4)

            if step_type == 'operand':
                with self.voiceover(text=f"读入字符 {ch}，它不是运算符，所以我们以它为根创建一棵树。") as tracker:
                    self.play(*get_track_anims(L_IF_NOT_OP))
                    self.play(*get_track_anims(L_NEW_NODE))

                    n = self.make_node(ch, node_pos[ch], GREEN)
                    created_nodes[ch] = n
                    self.play(FadeIn(n, scale=0.5), run_time=max(0.2, tracker.duration - 0.8))

                with self.voiceover(text=f"然后，将这棵树结点的指针压入 expr 栈中。") as tracker:
                    self.play(*get_track_anims(L_PUSH_EXPT))

                    item = push_stack(expt_stack, expt_base_line, f"ptr({ch})", GREEN)
                    self.play(FadeIn(item, shift=UP), run_time=tracker.duration)

            elif step_type == 'push_op':
                with self.voiceover(text=f"读入运算符 {ch}，它与optr栈顶元素比较，优先级更高，所以直接压入optr栈。") as tracker:
                    self.play(*get_track_anims(L_ELSE))
                    self.play(*get_track_anims(L_PRECEDE))
                    self.play(*get_track_anims(L_CASE_LESS))

                    item = push_stack(optr_stack, optr_base_line, ch, ORANGE)
                    self.play(FadeIn(item, shift=UP), run_time=max(0.2, tracker.duration - 0.8))

            elif step_type == 'pop_op_merge1':
                with self.voiceover(text="读入井号，它的优先级低于栈顶的乘号。说明乘法已经可以组装了。") as tracker:
                    self.play(*get_track_anims(L_PRECEDE))
                    self.play(*get_track_anims(L_CASE_GREATER))

                with self.voiceover(text="我们从optr栈弹出乘号作为新的根结点。") as tracker:
                    self.play(*get_track_anims(L_MERGE_POP))
                    op_item = pop_stack(optr_stack)

                    n_theta = self.make_node('*', node_pos['*'], BLUE)
                    created_nodes['*'] = n_theta
                    self.play(FadeOut(op_item, shift=DOWN), FadeIn(n_theta, scale=0.5), run_time=max(0.2, tracker.duration - 0.5))

                with self.voiceover(text="再从expr栈依次弹出两个树指针，分别作为它的右子树和左子树。") as tracker:
                    self.play(*get_track_anims(L_MERGE_POP2))
                    right_item = pop_stack(expt_stack)
                    self.play(FadeOut(right_item, shift=DOWN), run_time=0.3)

                    left_item = pop_stack(expt_stack)
                    self.play(FadeOut(left_item, shift=DOWN), run_time=0.3)

                    self.play(*get_track_anims(L_MERGE_NEW), run_time=0.2)
                    self.play(*get_track_anims(L_MERGE_LINK), run_time=0.2)

                    e_right = self.make_edge(node_pos['*'], node_pos['c'])
                    e_left = self.make_edge(node_pos['*'], node_pos['b'])
                    self.play(Create(e_right), Create(e_left))

                with self.voiceover(text="最后，将合并生成的新树根结点的指针重新压回 expr 栈。") as tracker:
                    self.play(*get_track_anims(L_MERGE_PUSH))
                    item = push_stack(expt_stack, expt_base_line, "ptr(*)", GREEN)
                    self.play(FadeIn(item, shift=UP), run_time=tracker.duration)

            elif step_type == 'pop_op_merge2':
                with self.voiceover(text="当前输入依然是井号，继续与栈顶比较，优先级仍低于加号，继续进行弹栈合并。") as tracker:
                    self.play(*get_track_anims(L_PRECEDE))
                    self.play(*get_track_anims(L_CASE_GREATER))

                with self.voiceover(text="弹出加号作为新的根结点，并从expr弹出两棵子树。") as tracker:
                    self.play(*get_track_anims(L_MERGE_POP))
                    op_item = pop_stack(optr_stack)
                    n_theta = self.make_node('+', node_pos['+'], BLUE)
                    created_nodes['+'] = n_theta
                    self.play(FadeOut(op_item, shift=DOWN), FadeIn(n_theta, scale=0.5))

                    self.play(*get_track_anims(L_MERGE_POP2))
                    right_item = pop_stack(expt_stack)
                    self.play(FadeOut(right_item, shift=DOWN), run_time=0.3)

                    left_item = pop_stack(expt_stack)
                    self.play(FadeOut(left_item, shift=DOWN), run_time=0.3)

                    self.play(*get_track_anims(L_MERGE_LINK))
                    e_right = self.make_edge(node_pos['+'], node_pos['*'])
                    e_left = self.make_edge(node_pos['+'], node_pos['a'])
                    self.play(Create(e_right), Create(e_left))

                with self.voiceover(text="再次将生成的新树压回 expr 栈。此时，栈中存放的就是完整的表达式树的根指针了。") as tracker:
                    self.play(*get_track_anims(L_MERGE_PUSH))
                    item = push_stack(expt_stack, expt_base_line, "ptr(+)", GREEN)
                    self.play(FadeIn(item, shift=UP), run_time=tracker.duration)

            elif step_type == 'end':
                with self.voiceover(text="最后，当前输入井号与栈顶井号相遇，循环结束，返回完整表达式树即可。") as tracker:
                    self.play(*get_track_anims(L_CASE_EQUAL))
                    self.play(FadeOut(ch_pointer), run_time=tracker.duration)

            step_idx += 1

        self.play(*get_track_anims(None))
        self.wait(1)

        # ===== 复杂度分析 =====
        time_box = VGroup(Text("时间复杂度: ", font_size=20, font="Microsoft YaHei", color=YELLOW), MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度: ", font_size=20, font="Microsoft YaHei", color=YELLOW), MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        complexity_text = VGroup(time_box, space_box).arrange(RIGHT, buff=0.8)
        complexity_text.to_edge(DOWN, buff=0.5)

        with self.voiceover(text="至此，表达式树创建完成。该算法每个字符最多进出栈各一次，因此时间复杂度和空间复杂度均为O(n)。") as tracker:
            self.play(FadeIn(complexity_text, shift=UP), run_time=tracker.duration)

        self.wait(2)


ContinuousExpressionTreeCreatePythonVideo = ExpressionTreeCreatePythonVideo
