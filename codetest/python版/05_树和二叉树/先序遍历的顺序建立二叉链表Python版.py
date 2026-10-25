# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import numpy as np
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


# =========================================================================
# Python 版二叉树二叉链表定义与先序建立二叉树算法逻辑
# =========================================================================
class BinaryTree:
    def __init__(self, data=None):
        self.data = data  # 数据域data默认为None，data为None时表示一颗空树
        self.lchild = None
        self.rchild = None


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


def in_order_traverse(t):
    # 中序遍历二叉树的递归算法
    if t is not None:  # 若二叉树非空
        in_order_traverse(t.lchild)  # 中序遍历左子树
        print(t.data, end='')  # 访问根结点
        in_order_traverse(t.rchild)  # 中序遍历右子树


class CreateBiTreePythonVideo(VoiceoverScene):
    # ===== 统一的结点 / 连线样式（与中序遍历保持一致，保证全章视觉统一、美观）=====
    NODE_R = 0.32

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
        """在两结点圆心之间连线，两端各留出半径长度，使连线只画到圆的边缘、不插入结点内部。"""
        r1 = self.NODE_R if r1 is None else r1
        r2 = self.NODE_R if r2 is None else r2
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        return Line(p1 + u * r1, p2 - u * r2, color=color, stroke_width=sw)

    def construct(self):
        # 初始化语音服务（中文男声配置）
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE（标题）=====
        algo_title = Text("先序遍历的顺序建立二叉链表（Python版）", font_size=34, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.55).shift(LEFT * 0.5)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(
            text="本节我们使用 Python 语言，学习先序建立二叉链表。",
            subcaption="本节我们使用 Python 语言，学习先序建立二叉链表。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE B — 例子引入（直观类比：一串“先序字符序列”与一棵树一一对应，# 表示空子树）=====
        spos = {'甲': np.array([-0.2, 1.3, 0]), '乙': np.array([-1.5, 0.0, 0]), '丙': np.array([1.1, 0.0, 0])}
        sedges = VGroup(self.edge(spos['甲'], spos['乙']), self.edge(spos['甲'], spos['丙']))
        snodes = {k: self.make_node(k, p) for k, p in spos.items()}
        stree = VGroup(sedges, *snodes.values())

        # 小示例的先序字符序列：甲 乙 # # 丙 # #
        sseq = ['甲', '乙', '#', '#', '丙', '#', '#']
        scells = []
        stape = VGroup()
        for ch in sseq:
            rect = Rectangle(width=0.5, height=0.56, color=GRAY_B, stroke_width=1.5)
            col = GRAY if ch == '#' else WHITE
            fnt = "Consolas" if ch == '#' else "Microsoft YaHei"
            t = Text(ch, font_size=22, color=col, font=fnt).move_to(rect.get_center())
            cell = VGroup(rect, t)
            scells.append(cell)
            stape.add(cell)
        stape.arrange(RIGHT, buff=0).move_to([-0.2, -2.0, 0])
        stape_title = Text("先序字符序列", font_size=18, font="Microsoft YaHei", color=GRAY_A).next_to(stape, UP, buff=0.2)

        with self.voiceover(text="先看一个直观的例子。", subcaption="先看一个直观的例子。") as tracker:
            self.play(FadeIn(stree), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(text="这是它的先序字符序列。", subcaption="这是它的先序字符序列。") as tracker:
            self.play(FadeIn(stape), FadeIn(stape_title), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(text="井号表示空的子树。", subcaption="井号表示空的子树。") as tracker:
            self.play(Indicate(VGroup(scells[2], scells[3], scells[5], scells[6]), color=GRAY_A, scale_factor=1.15),
                      run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(text="先序先访问根结点甲。", subcaption="先序先访问根结点甲。") as tracker:
            self.play(Indicate(scells[0], color=YELLOW, scale_factor=1.2),
                      Indicate(snodes['甲'], color=YELLOW, scale_factor=1.2), run_time=0.9)
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="接着访问左孩子乙。", subcaption="接着访问左孩子乙。") as tracker:
            self.play(Indicate(scells[1], color=YELLOW, scale_factor=1.2),
                      Indicate(snodes['乙'], color=YELLOW, scale_factor=1.2), run_time=0.9)
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="乙没有孩子，记两个井号。", subcaption="乙没有孩子，记两个井号。") as tracker:
            self.play(Indicate(VGroup(scells[2], scells[3]), color=GRAY_A, scale_factor=1.2), run_time=0.9)
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="最后访问右孩子丙。", subcaption="最后访问右孩子丙。") as tracker:
            self.play(Indicate(scells[4], color=YELLOW, scale_factor=1.2),
                      Indicate(snodes['丙'], color=YELLOW, scale_factor=1.2), run_time=0.9)
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="丙也没有孩子，两个井号。", subcaption="丙也没有孩子，两个井号。") as tracker:
            self.play(Indicate(VGroup(scells[5], scells[6]), color=GRAY_A, scale_factor=1.2), run_time=0.9)
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="反过来读这串序列，就能唯一还原这棵树。", subcaption="反过来读这串序列，就能唯一还原这棵树。") as tracker:
            self.play(Indicate(stape, color=BLUE, scale_factor=1.05), run_time=0.9)
            self.play(Indicate(stree, color=GREEN, scale_factor=1.08), run_time=0.9)
            self.wait(max(0.1, tracker.duration - 1.8))

        self.play(FadeOut(stree), FadeOut(stape), FadeOut(stape_title), run_time=0.6)

        # ===== PHASE B2 — 算法基本思路（先讲清“边读边建”的核心策略，再进入代码）=====
        idea_title = Text("算法基本思路", font_size=30, font="Microsoft YaHei", weight=BOLD, color=YELLOW).move_to(UP * 2.3)
        idea_src = [
            "① 按先序次序，逐个弹出字符 ch",
            "② 读到 # ：当前子树为空，返回 None",
            "③ 读到其它字符：创建新节点，存入 ch",
            "④ 先递归建立左子树，再递归建立右子树",
        ]
        idea_lines = VGroup(*[Text(s, font_size=24, font="Microsoft YaHei", color=WHITE) for s in idea_src])
        idea_lines.arrange(DOWN, aligned_edge=LEFT, buff=0.32).move_to(UP * 0.35)
        idea_flow = Text("读入 → 判空 → 建根 → 建左子树 → 建右子树",
                         font_size=22, font="Microsoft YaHei", color=GREEN).move_to(DOWN * 1.9)

        with self.voiceover(text="在动手写代码之前，先理清算法的基本思路。", subcaption="在动手写代码之前，先理清算法的基本思路。") as tracker:
            self.play(FadeIn(idea_title, shift=DOWN * 0.15), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(text="算法按先序次序，逐个弹出字符。", subcaption="算法按先序次序，逐个弹出字符。") as tracker:
            self.play(FadeIn(idea_lines[0], shift=RIGHT * 0.2), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(text="如果读到井号，说明这棵子树为空，返回空指针。", subcaption="如果读到井号，说明这棵子树为空，返回 None。") as tracker:
            self.play(FadeIn(idea_lines[1], shift=RIGHT * 0.2), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(text="否则就新建一个结点，把这个字符存进去。", subcaption="否则就新建一个结点，把这个字符存进去。") as tracker:
            self.play(FadeIn(idea_lines[2], shift=RIGHT * 0.2), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(text="然后递归地建立它的左子树，再建立右子树。", subcaption="然后递归地建立它的左子树，再建立右子树。") as tracker:
            self.play(FadeIn(idea_lines[3], shift=RIGHT * 0.2), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(text="读入、判空、建根、建左、建右，每个结点都重复这一过程。",
                            subcaption="读入、判空、建根、建左、建右，每个结点都重复这一过程。") as tracker:
            self.play(Write(idea_flow), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(text="下面对照 Python 代码看具体实现。", subcaption="下面对照 Python 代码看具体实现。") as tracker:
            self.wait(tracker.duration)

        self.play(FadeOut(idea_title), FadeOut(idea_lines), FadeOut(idea_flow), run_time=0.5)

        # ===== PHASE C — CODE BLOCK CONFIG（Python 代码板样式）=====
        c_lines = [
            "def create_bitree(preorder):",
            "    if not preorder: return None",
            "    ch = preorder.pop(0)",
            "    if ch == '#':",
            "        return None",
            "    else:",
            "        node = BinaryTree(ch)",
            "        node.lchild = create_bitree(preorder)",
            "        node.rchild = create_bitree(preorder)",
            "        return node",
        ]
        # 代码行索引常量（便于追踪高亮）
        IDX_READ = 2    # ch = preorder.pop(0)                 —— 第①步：弹出当前字符存入 ch
        IDX_IF = 3      # if ch == '#':                        —— 第②步：判空
        IDX_RET_NONE = 4 # return None                         —— 为井号则返回 None
        IDX_NEW = 6     # node = BinaryTree(ch)                —— 第③步：创建新节点并保存 ch
        IDX_DATA = 6    # 同上，Python 初始化时直接传入 ch
        IDX_LEFT = 7    # node.lchild = create_bitree(...)     —— 递归建立左子树
        IDX_RIGHT = 8   # node.rchild = create_bitree(...)     —— 递归建立右子树
        IDX_RET = 9     # return node                          —— 返回新建立的子树根结点

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=12, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        SPACE_WIDTH = 0.095
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
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.2).to_edge(RIGHT, buff=0.25)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line:
                return []
            anims = []
            if self.current_line is not None:
                anims.append(self.c_texts[self.current_line].animate.set_color(WHITE).scale(1 / 1.2, about_edge=LEFT))
            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW).scale(1.2, about_edge=LEFT))
                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.15).rotate(-PI / 2)
                    self.code_pointer.next_to(self.c_texts[new_idx], LEFT, buff=0.2)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.c_texts[new_idx], LEFT, buff=0.2)
                    anims.append(MoveToTarget(self.code_pointer))
                self.current_line = new_idx
            else:
                if hasattr(self, 'code_pointer'):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, 'code_pointer')
                self.current_line = None
            return anims

        # ===== PHASE C2 — 二叉树区、变量 ch、调用栈面板、输入字符带 =====
        # 目标二叉树：A(B(D,E), C)，其先序输入序列为 A B D # # E # # C # #
        pos = {
            'A': np.array([-2.0, 2.0, 0]),
            'B': np.array([-3.5, 0.7, 0]), 'C': np.array([-0.5, 0.7, 0]),
            'D': np.array([-4.3, -0.6, 0]), 'E': np.array([-2.7, -0.6, 0]),
        }
        circles = {}
        labels = {}
        edges_dyn = VGroup()

        # “当前结点”活动指示环（套在当前正在创建的结点上）
        ring = Circle(radius=self.NODE_R + 0.1, color=YELLOW, stroke_width=4)

        # ----- 变量 ch（左上角）：preorder.pop(0) 读入这里，node = BinaryTree(ch) 再从这里存入结点 -----
        ch_cap = Text("当前字符", font_size=14, font="Microsoft YaHei", color=GRAY_A)
        ch_name = Text("ch", font_size=20, font="Consolas", color=YELLOW)
        ch_eq = Text("=", font_size=20, font="Consolas", color=GRAY_A)
        ch_cell = Square(side_length=0.52, color=YELLOW, stroke_width=2.5, fill_color=YELLOW, fill_opacity=0.08)
        ch_row = VGroup(ch_name, ch_eq, ch_cell).arrange(RIGHT, buff=0.12)
        ch_group = VGroup(ch_cap, ch_row).arrange(DOWN, buff=0.12).move_to([-5.35, 2.15, 0])
        ch_holder = {'mob': None}   # 当前显示在 ch 框内的字符 Mobject

        # ----- 调用栈面板（左侧）：展示递归层层调用 -----
        STACK_X = -6.05
        STACK_BASE_Y = -1.5
        FRAME_H = 0.56
        stack_title = Text("调用栈", font_size=22, font="Microsoft YaHei", color=YELLOW).move_to([STACK_X, 1.0, 0])
        stack_hint = Text("（递归深度=树高）", font_size=12, font="Microsoft YaHei", color=GRAY).next_to(
            stack_title, DOWN, buff=0.12)

        def make_frame(node_key):
            box = RoundedRectangle(corner_radius=0.08, width=1.5, height=0.5, color=BLUE_D, fill_color=BLUE_D,
                                   fill_opacity=0.18, stroke_width=2)
            t = Text("create %s" % node_key, font_size=14, color=WHITE).move_to(box.get_center())
            return VGroup(box, t)

        path = []          # 当前调用链（结点 key）
        stack_mobs = []    # 调用栈中的帧 Mobject

        def push_frame(node_key):
            y = STACK_BASE_Y + len(stack_mobs) * FRAME_H
            fr = make_frame(node_key).move_to([STACK_X, y, 0])
            stack_mobs.append(fr)
            return fr

        # ----- 输入字符带（底部）：先序输入 A B D # # E # # C # #，三角标记指向下一个待读字符 -----
        seq = ['A', 'B', 'D', '#', '#', 'E', '#', '#', 'C', '#', '#']
        CELL_W, CELL_H = 0.46, 0.56
        cells = []
        tape = VGroup()
        for ch in seq:
            rect = Rectangle(width=CELL_W, height=CELL_H, color=GRAY_B, stroke_width=1.5)
            col = GRAY if ch == '#' else WHITE
            t = Text(ch, font_size=20, font="Consolas", color=col).move_to(rect.get_center())
            cell = VGroup(rect, t)
            cells.append(cell)
            tape.add(cell)
        tape.arrange(RIGHT, buff=0).move_to([-2.1, -3.0, 0])
        tape_title = Text("preorder 列表", font_size=16, font="Microsoft YaHei", color=GRAY_A).next_to(
            tape, LEFT, buff=0.2)

        # 读取位置标记：黄色方框套住下一个待读单元 + 上方一个向下的小三角
        i_box = Rectangle(width=CELL_W + 0.06, height=CELL_H + 0.06, color=YELLOW, stroke_width=3).move_to(
            cells[0].get_center())
        i_tag = Triangle(fill_opacity=1, color=YELLOW).scale(0.12).rotate(PI).next_to(i_box, UP, buff=0.06)
        i_marker = VGroup(i_box, i_tag)

        st = {'i': 0, 'ring': False}

        # ===== PHASE D — 递归建立的辅助动画函数 =====
        def advance_i():
            """消耗当前字符：当前单元变灰，读取标记后移一格（越界则淡出）。"""
            k = st['i']
            anims = [cells[k][0].animate.set_stroke(GRAY_D, opacity=0.5),
                     cells[k][1].animate.set_color(GRAY_D)]
            st['i'] += 1
            if st['i'] < len(seq):
                delta = cells[st['i']].get_center() - cells[k].get_center()
                anims.append(i_marker.animate.shift(delta))
            else:
                anims.append(FadeOut(i_marker))
            self.play(*anims, run_time=0.4)

        def hl(idx, rt=0.35):
            """把代码追踪高亮切换到第 idx 行。"""
            a = get_track_anims(idx)
            if a:
                self.play(*a, run_time=rt)

        def read():
            """第①步：ch = preorder.pop(0); 从列表弹出下一个字符，飞入变量 ch，读取标记后移。"""
            hl(IDX_READ)
            k = st['i']
            self.play(Indicate(cells[k], color=YELLOW, scale_factor=1.15), run_time=0.3)
            flyer = cells[k][1].copy()
            anims = [flyer.animate.move_to(ch_cell.get_center()).set_color(WHITE)]
            if ch_holder['mob'] is not None:
                anims.append(FadeOut(ch_holder['mob']))
            self.play(*anims, run_time=0.5)
            self.add(flyer)
            ch_holder['mob'] = flyer
            advance_i()

        def grow(key, parent):
            """第③步：node = BinaryTree(ch); 创建新节点（空心圆长出、连到父结点、压栈、圆环就位）。"""
            hl(IDX_NEW)
            c = Circle(radius=self.NODE_R, color=BLUE, fill_color=BLUE, fill_opacity=0.15,
                       stroke_width=2.5).move_to(pos[key])
            circles[key] = c
            anims = [GrowFromCenter(c)]
            if parent is not None:
                e = self.edge(pos[parent], pos[key], color=GRAY)
                edges_dyn.add(e)
                anims.append(Create(e))
            path.append(key)
            fr = push_frame(key)
            anims.append(FadeIn(fr, shift=UP * 0.2))
            if not st['ring']:
                ring.move_to(pos[key])
                anims.append(FadeIn(ring))
                st['ring'] = True
            else:
                anims.append(ring.animate.move_to(pos[key]))
            self.play(*anims, run_time=0.55)

        def put_data(key):
            """把 ch 里的字符飞入结点，完成数据域赋值。"""
            hl(IDX_DATA)
            flyer = ch_holder['mob'].copy()
            self.play(flyer.animate.move_to(pos[key]).set_color(WHITE),
                      Indicate(circles[key], color=TEAL, scale_factor=1.15), run_time=0.5)
            self.add(flyer)
            labels[key] = flyer

        def null_leaf(parent, side):
            """第②步：ch=='#' 时 return None; 空子树返回空指针（不压栈、树上不画空结点）。"""
            hl(IDX_IF)
            off = (LEFT * 0.5 if side == 'L' else RIGHT * 0.5) + DOWN * 0.85
            tag = Text("None", font_size=16, font="Consolas", color=GRAY).move_to(pos[parent] + off)
            self.play(FadeIn(tag, shift=DOWN * 0.12), run_time=0.35)
            self.wait(0.15)
            self.play(FadeOut(tag), run_time=0.25)

        def ret(key):
            """当前结点左右子树全部建完，函数返回 node，弹出栈顶，圆环退回父结点。"""
            self.play(Indicate(circles[key], color=YELLOW, scale_factor=1.15), run_time=0.4)
            path.pop()
            fr = stack_mobs.pop()
            if path:
                self.play(FadeOut(fr, shift=UP * 0.2), ring.animate.move_to(pos[path[-1]]), run_time=0.4)
            else:
                self.play(FadeOut(fr, shift=UP * 0.2), FadeOut(ring), run_time=0.4)

        # ===== PHASE D1 — 场景搭建（代码 / 变量 / 输入列表 / 调用栈依次登场）=====
        with self.voiceover(text="这是 Python 算法的核心代码。", subcaption="这是 Python 算法的核心代码。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        with self.voiceover(text="用变量 ch 保存当前读入的字符。",
                            subcaption="用变量 ch 保存当前读入的字符。") as tracker:
            self.play(FadeIn(ch_group), run_time=tracker.duration)

        with self.voiceover(text="这是先序输入序列列表。", subcaption="这是先序输入序列列表。") as tracker:
            self.play(FadeIn(tape), FadeIn(tape_title), run_time=tracker.duration)

        with self.voiceover(text="井号代表空的子树。", subcaption="井号代表空的子树。") as tracker:
            self.play(Indicate(VGroup(cells[3], cells[4], cells[6], cells[7], cells[9], cells[10]),
                               color=GRAY_A, scale_factor=1.15), run_time=0.9)
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="三角标记指向下一个待读入的字符。", subcaption="三角标记指向下一个待读入的字符。") as tracker:
            self.play(FadeIn(i_marker), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(text="左侧是递归调用栈。", subcaption="左侧是递归调用栈。") as tracker:
            self.play(FadeIn(stack_title), FadeIn(stack_hint), run_time=tracker.duration)

        with self.voiceover(text="下面开始建立二叉树。", subcaption="下面开始建立二叉树。") as tracker:
            self.wait(tracker.duration)

        # ===== PHASE D2 — 递归建立过程 =====
        # ---- 结点 A（根）----
        with self.voiceover(text="进入递归，读入首字符 A，存入 ch。", subcaption="进入递归，读入首字符 A，存入 ch。") as tracker:
            read()
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(text="ch 不是井号，新建根结点 A。", subcaption="ch 不是井号，新建根结点 A。") as tracker:
            hl(IDX_IF)
            grow('A', None)
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="把 ch 里的 A 存入结点。", subcaption="把 ch 里的 A 存入结点。") as tracker:
            put_data('A')
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="然后递归建立 A 的左子树。", subcaption="然后递归建立 A 的左子树。") as tracker:
            hl(IDX_LEFT)
            self.wait(max(0.1, tracker.duration - 0.35))

        # ---- 结点 B ----
        with self.voiceover(text="读入 B，存入 ch。", subcaption="读入 B，存入 ch。") as tracker:
            read()
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(text="不是井号，新建 B，接到 A 左边。", subcaption="不是井号，新建 B，接到 A 左边。") as tracker:
            hl(IDX_IF)
            grow('B', 'A')
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="把 B 存入结点。", subcaption="把 B 存入结点。") as tracker:
            put_data('B')
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="继续递归建立 B 的左子树。", subcaption="继续递归建立 B 的左子树。") as tracker:
            hl(IDX_LEFT)
            self.wait(max(0.1, tracker.duration - 0.35))

        # ---- 结点 D ----
        with self.voiceover(text="读入 D，存入 ch。", subcaption="读入 D，存入 ch。") as tracker:
            read()
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(text="不是井号，新建 D，接到 B 左边。", subcaption="不是井号，新建 D，接到 B 左边。") as tracker:
            hl(IDX_IF)
            grow('D', 'B')
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="把 D 存入结点，此时调用栈已有三层。", subcaption="把 D 存入结点，此时调用栈已有三层。") as tracker:
            put_data('D')
            self.play(Indicate(VGroup(*stack_mobs), color=YELLOW, scale_factor=1.08), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 1.7))

        with self.voiceover(text="递归建立 D 的左子树。", subcaption="递归建立 D 的左子树。") as tracker:
            hl(IDX_LEFT)
            self.wait(max(0.1, tracker.duration - 0.35))

        with self.voiceover(text="读入井号，存入 ch。", subcaption="读入井号，存入 ch。") as tracker:
            read()
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(text="ch 是井号，返回空指针 None。", subcaption="ch 是井号，返回 None。") as tracker:
            null_leaf('D', 'L')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(text="再递归建立 D 的右子树。", subcaption="再递归建立 D 的右子树。") as tracker:
            hl(IDX_RIGHT)
            self.wait(max(0.1, tracker.duration - 0.35))

        with self.voiceover(text="又读入井号。", subcaption="又读入井号。") as tracker:
            read()
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(text="把 D 的右指针也置空。", subcaption="把 D 的右指针也置空。") as tracker:
            null_leaf('D', 'R')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(text="D 的左右子树都建好，返回并弹栈。", subcaption="D 的左右子树都建好，返回并弹栈。") as tracker:
            ret('D')
            self.wait(max(0.1, tracker.duration - 0.9))

        # ---- 结点 E（B 的右孩子）----
        with self.voiceover(text="回到 B，递归建立它的右子树。", subcaption="回到 B，递归建立它的右子树。") as tracker:
            hl(IDX_RIGHT)
            self.wait(max(0.1, tracker.duration - 0.35))

        with self.voiceover(text="读入 E，存入 ch。", subcaption="读入 E，存入 ch。") as tracker:
            read()
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(text="不是井号，新建 E，接到 B 右边。", subcaption="不是井号，新建 E，接到 B 右边。") as tracker:
            hl(IDX_IF)
            grow('E', 'B')
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="把 E 存入结点。", subcaption="把 E 存入结点。") as tracker:
            put_data('E')
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="建立 E 的左子树。", subcaption="建立 E 的左子树。") as tracker:
            hl(IDX_LEFT)
            self.wait(max(0.1, tracker.duration - 0.35))

        with self.voiceover(text="读入井号。", subcaption="读入井号。") as tracker:
            read()
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(text="置空 E 的左指针。", subcaption="置空 E 的左指针。") as tracker:
            null_leaf('E', 'L')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(text="再建立 E 的右子树。", subcaption="再建立 E 的右子树。") as tracker:
            hl(IDX_RIGHT)
            self.wait(max(0.1, tracker.duration - 0.35))

        with self.voiceover(text="还是井号。", subcaption="还是井号。") as tracker:
            read()
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(text="置空 E 的右指针。", subcaption="置空 E 的右指针。") as tracker:
            null_leaf('E', 'R')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(text="E 建好，返回弹栈。", subcaption="E 建好，返回弹栈。") as tracker:
            ret('E')
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="B 的左右也建好，返回弹栈。", subcaption="B 的左右也建好，返回弹栈。") as tracker:
            ret('B')
            self.wait(max(0.1, tracker.duration - 0.9))

        # ---- 结点 C（A 的右孩子）----
        with self.voiceover(text="回到 A，递归建立它的右子树。", subcaption="回到 A，递归建立它的右子树。") as tracker:
            hl(IDX_RIGHT)
            self.wait(max(0.1, tracker.duration - 0.35))

        with self.voiceover(text="读入 C，存入 ch。", subcaption="读入 C，存入 ch。") as tracker:
            read()
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(text="不是井号，新建 C，接到 A 右边。", subcaption="不是井号，新建 C，接到 A 右边。") as tracker:
            hl(IDX_IF)
            grow('C', 'A')
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="把 C 存入结点。", subcaption="把 C 存入结点。") as tracker:
            put_data('C')
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="建立 C 的左子树。", subcaption="建立 C 的左子树。") as tracker:
            hl(IDX_LEFT)
            self.wait(max(0.1, tracker.duration - 0.35))

        with self.voiceover(text="读入井号。", subcaption="读入井号。") as tracker:
            read()
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(text="置空 C 的左指针。", subcaption="置空 C 的左指针。") as tracker:
            null_leaf('C', 'L')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(text="再建立 C 的右子树。", subcaption="再建立 C 的右子树。") as tracker:
            hl(IDX_RIGHT)
            self.wait(max(0.1, tracker.duration - 0.35))

        with self.voiceover(text="读入最后一个井号。", subcaption="读入最后一个井号。") as tracker:
            read()
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(text="置空 C 的右指针。", subcaption="置空 C 的右指针。") as tracker:
            null_leaf('C', 'R')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(text="C 建好，返回弹栈。", subcaption="C 建好，返回弹栈。") as tracker:
            ret('C')
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="A 的左右都建好，返回，调用栈清空。", subcaption="A 的左右都建好，返回，调用栈清空。") as tracker:
            ret('A')
            self.wait(max(0.1, tracker.duration - 0.9))

        # ===== PHASE D3 — 结果展示 =====
        tree_all = VGroup(edges_dyn, *[circles[k] for k in pos], *[labels[k] for k in pos])
        with self.voiceover(text="整棵二叉链表建立完成。", subcaption="整棵二叉链表建立完成。") as tracker:
            anims = get_track_anims(None)
            if anims:
                self.play(*anims, run_time=0.35)
            self.play(Indicate(tree_all, color=GREEN, scale_factor=1.05), run_time=0.9)
            self.wait(max(0.1, tracker.duration - 1.25))

        with self.voiceover(text="输入序列也已全部读入。", subcaption="输入序列也已全部读入。") as tracker:
            self.play(Indicate(tape, color=BLUE, scale_factor=1.03), run_time=0.9)
            self.wait(max(0.1, tracker.duration - 0.9))

        # ===== PHASE E — COMPLEXITY（复杂度看板）=====
        fade_targets = [FadeOut(code_block), FadeOut(tape), FadeOut(tape_title),
                        FadeOut(stack_title), FadeOut(stack_hint), FadeOut(ch_group)]
        if ch_holder['mob'] is not None:
            fade_targets.append(FadeOut(ch_holder['mob']))
        self.play(*fade_targets, run_time=0.5)

        order_label = Text("生成顺序（先序）：A B D E C", font_size=22, font="Microsoft YaHei", color=GREEN)
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        summary = VGroup(order_label, time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        # 靠右摆放，与仍留在中左侧的二叉树（右端结点 C 在 x≈-0.18）保持充足间距
        summary.move_to(RIGHT * 3.3 + DOWN * 0.2)

        with self.voiceover(text="结点生成顺序就是先序遍历。", subcaption="结点生成顺序就是先序遍历。") as tracker:
            self.play(Write(order_label), run_time=max(0.5, tracker.duration))

        with self.voiceover(text="依次是 A B D E C。", subcaption="依次是 A B D E C。") as tracker:
            self.play(Indicate(order_label, color=YELLOW, scale_factor=1.05), run_time=0.9)
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(text="每个结点只被创建一次。", subcaption="每个结点只被创建一次。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="所以时间复杂度为 O恩。", subcaption="所以时间复杂度为 O(n)。") as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(text="辅助空间取决于递归深度，也就是二叉树的高度。",
                            subcaption="辅助空间取决于递归深度，也就是二叉树的高度。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="最坏退化为单链，深度为 n，空间复杂度也是 O恩。",
                            subcaption="最坏退化为单链，深度为 n，空间复杂度也是 O(n)。") as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是先序建立二叉链表的 Python 实现。", subcaption="以上就是先序建立二叉链表的 Python 实现。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)


# Alias
ContinuousCreateBiTreePythonVideo = CreateBiTreePythonVideo
PreOrderCreateBiTreePythonVideo = CreateBiTreePythonVideo
