# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import numpy as np
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
from codetest.tree_video_support import TreeVideoScene, fit_tree_title


# =========================================================================
# Python 版二叉树定义与带头结点的二叉树中序线索化算法逻辑
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
        in_threading(p.lchild)  # 左子树递归线索化
        if p.lchild is None:  # p的左孩子为空
            p.ltag = 1  # 给p加上左线索
            p.lchild = pre  # p的左孩子指针指向pre（前驱）
        else:
            p.ltag = 0
        if pre:
            if pre.rchild is None:  # pre的右孩子为空
                pre.rtag = 1  # 给pre加上右线索
                pre.rchild = p  # pre的右孩子指针指向p（后继）
            else:
                pre.rtag = 0
        pre = p  # 保持pre指向p的前驱
        in_threading(p.rchild)  # 右子树递归线索化


def in_order_threading(t):
    # 带头结点的二叉树中序线索化
    global pre
    thrt = BinaryTree()  # 建头结点
    thrt.ltag = 0  # 头结点有左孩子，若树非空，则其左孩子为树根；
    thrt.rtag = 1  # 头结点的右孩子指针为右线索
    thrt.rchild = thrt  # 初始化时右指针指向自己
    if t is None:  # 若树为空，则左指针也指向自己
        thrt.lchild = thrt
    else:
        thrt.lchild = t  # 头结点的左孩子指向根
        pre = thrt  # pre初值指向头结点
        in_threading(t)  # 调用算法，对以T为根的二叉树进行中序线索化
        pre.rchild = thrt  # 算法结束后，pre为最右结点，pre的右线索指向头结点
        pre.rtag = 1
        thrt.rchild = pre  # 头结点的右线索指向pre
    return thrt


def in_order_traverse_thr(t):
    # 中序遍历二叉线索树T的非递归算法，对每个数据元素直接输出
    if t is None:
        return
    p = t.lchild  # p指向根结点
    while p != t:  # 空树或遍历结束时，p==t
        while p.ltag == 0:
            p = p.lchild  # 沿左孩子向下
        print(p.data, end='')  # 访问其左子树为空的结点
        while p.rtag == 1 and p.rchild != t:
            p = p.rchild  # 沿右线索访问后继结点
            print(p.data, end='')
        p = p.rchild  # 转向p的右子树


class InOrderThreadingPythonVideo(TreeVideoScene):
    # ===== 与「以结点p为根的子树中序线索化」视频完全一致的结点 / 线索样式 =====
    NODE_R = 0.32
    ORANGE = "#FF8C1A"   # 前驱线索 —— ltag = 1
    TEAL = "#1AC7C7"     # 后继线索 —— rtag = 1
    HEADC = "#B15CFF"    # 头结点专用配色（紫色），头结点及其 rchild 指针

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

    def thread_arrow(self, a, b, angle, color):
        """线索弧线：从结点 a 指向结点 b 的一条虚线弯箭头（两端各留出半径，避开圆内部）。"""
        a, b = np.array(a, dtype=float), np.array(b, dtype=float)
        u = (b - a) / np.linalg.norm(b - a)
        start = a + u * self.NODE_R
        end = b - u * self.NODE_R
        ca = CurvedArrow(start, end, angle=angle, color=color, stroke_width=2.5, tip_length=0.16)
        return DashedVMobject(ca, num_dashes=9, dashed_ratio=0.55)

    def ptr_arrow(self, p1, p2, color=GRAY, sw=2.5):
        """结点间的实心指针箭头：头结点的 lchild / rchild 指向真实结点时使用。"""
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        return Arrow(p1 + u * self.NODE_R, p2 - u * self.NODE_R, color=color,
                     stroke_width=sw, tip_length=0.16, buff=0)

    def self_loop(self, center, color):
        """结点右上角的一个小自环虚线箭头：表示 thrt.rchild = thrt（头结点右指针初始指向自己）。"""
        c = np.array(center, dtype=float)
        start = c + np.array([self.NODE_R * 0.55, self.NODE_R * 0.85, 0])
        end = c + np.array([self.NODE_R * 1.02, -self.NODE_R * 0.15, 0])
        ca = CurvedArrow(start, end, angle=-4.2, color=color, stroke_width=2.5, tip_length=0.12)
        return DashedVMobject(ca, num_dashes=7, dashed_ratio=0.5)

    def null_mark(self, center, direction, color):
        """指向空的短虚线箭头 + 末端 ∧ 标记：表示某个指针此刻悬空（无前驱 / 无后继）。"""
        c = np.array(center, dtype=float)
        d = np.array(direction, dtype=float)
        d = d / np.linalg.norm(d)
        start = c + d * self.NODE_R
        end = c + d * (self.NODE_R + 0.5)
        ar = DashedVMobject(Arrow(start, end, color=color, stroke_width=2.5, tip_length=0.14, buff=0), num_dashes=4)
        nul = Text("∧", font_size=18, color=GRAY_B).move_to(end + d * 0.16)
        return VGroup(ar, nul)

    def construct(self):
        # 初始化语音服务（中文男声配置）
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ============================================================
        # PHASE A — TITLE
        # ============================================================
        algo_title = Text("带头结点的二叉树中序线索化（Python版）", font_size=36, font="Microsoft YaHei",
                          weight=BOLD).to_edge(UP, buff=0.55).shift(LEFT * 0.4)
        fit_tree_title(algo_title, logo)
        self.play(FadeIn(algo_title), run_time=0.8)

        subtitle = Text("为二叉树建立带头结点的中序线索链表，可从两端双向遍历",
                        font_size=20, font="Microsoft YaHei", color=GRAY_A).next_to(algo_title, DOWN, buff=0.22)

        with self.voiceover(
            text="本视频讲解使用 Python 语言，实现带头结点的二叉树中序线索化的代码实现与逐行跟踪。",
            subcaption="本视频讲解使用 Python 语言，实现带头结点的二叉树中序线索化的代码实现与逐行跟踪。"
        ) as tracker:
            self.play(FadeIn(subtitle), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        with self.voiceover(
            text="该算法通过调用以结点 p 为根的子树中序线索化，对整棵二叉树完成中序线索化，并为它建立一个带头结点的双向线索链表。",
            subcaption="该算法通过调用以结点 p 为根的子树中序线索化，对整棵二叉树完成中序线索化，并为它建立一个带头结点的双向线索链表。"
        ) as tracker:
            self.wait(tracker.duration)

        self.play(FadeOut(subtitle), run_time=0.4)

        # ============================================================
        # PHASE B — 例子引入：头结点把线索链表的首尾接成一个环
        # ============================================================
        ipos = {'H': np.array([-3.4, 1.7, 0]), 'G': np.array([-4.5, 0.4, 0]),
                'J': np.array([-2.3, 0.4, 0]), 'I': np.array([-3.6, -0.8, 0])}
        ichildren = {'H': ('G', 'J'), 'G': (None, 'I'), 'J': (None, None), 'I': (None, None)}
        iedges = VGroup()
        for k, (lc, rc) in ichildren.items():
            for ch in (lc, rc):
                if ch is not None:
                    iedges.add(self.edge(ipos[k], ipos[ch]))
        inodes = {k: self.make_node(k, p) for k, p in ipos.items()}
        intro_tree = VGroup(iedges, *inodes.values())

        with self.voiceover(
            text="先看一个小例子。这棵二叉树的中序序列是 G、I、H、J。中序线索化，会把每个结点空着的指针，改造成指向前驱和后继的线索。",
            subcaption="先看一个小例子。这棵二叉树的中序序列是 G、I、H、J。中序线索化把空指针改造成指向前驱和后继的线索。"
        ) as tracker:
            self.play(FadeIn(intro_tree), run_time=tracker.duration)

        # 中序序列铺成一条横向的“链”
        seq_keys = ['G', 'I', 'H', 'J']
        chain = VGroup()
        for i, k in enumerate(seq_keys):
            cc = self.make_node(k, np.array([0.2 + i * 1.4, -1.6, 0]), color=GREEN)
            chain.add(cc)
        chain_pos = {k: chain[i].circle.get_center() for i, k in enumerate(seq_keys)}

        succ_arrows = VGroup()
        pred_arrows = VGroup()
        for i in range(len(seq_keys) - 1):
            a = chain_pos[seq_keys[i]]
            b = chain_pos[seq_keys[i + 1]]
            succ_arrows.add(self.thread_arrow(a, b, -0.6, self.TEAL))
            pred_arrows.add(self.thread_arrow(b, a, -0.6, self.ORANGE))

        with self.voiceover(
            text="把中序序列拉成一条链，相邻结点之间，用青色的后继线索和橙色的前驱线索连接起来。",
            subcaption="把中序序列拉成一条链，相邻结点之间，用青色的后继线索和橙色的前驱线索连接起来。"
        ) as tracker:
            for i, k in enumerate(seq_keys):
                self.play(TransformFromCopy(inodes[k], chain[i]), run_time=0.35)
            self.play(Create(succ_arrows), Create(pred_arrows), run_time=1.0)
            self.wait(max(0.2, tracker.duration - len(seq_keys) * 0.35 - 1.0))

        # 两个“断头”：G 无前驱、J 无后继
        g_null = self.null_mark(chain_pos['G'], LEFT + DOWN * 0.4, self.ORANGE)
        j_null = self.null_mark(chain_pos['J'], RIGHT + DOWN * 0.4, self.TEAL)
        with self.voiceover(
            text="但这条链有两个断头：第一个结点 G 没有前驱，最后一个结点 J 没有后继，它们的这两个指针悬空着。",
            subcaption="但这条链有两个断头：第一个结点 G 没有前驱，最后一个结点 J 没有后继，这两个指针悬空。"
        ) as tracker:
            self.play(Create(g_null), Create(j_null), run_time=1.0)
            self.play(Indicate(VGroup(g_null, j_null), color=YELLOW, scale_factor=1.15), run_time=1.0)
            self.wait(max(0.2, tracker.duration - 2.0))

        # 头结点：把两个断头接到它上面，形成一个环
        hi_pos = np.array([-2.5, -1.6, 0])
        hi_c = Circle(radius=self.NODE_R, color=self.HEADC, fill_color=self.HEADC,
                      fill_opacity=0.18, stroke_width=2.5).move_to(hi_pos)
        hi_t = Text("头", font_size=20, color=WHITE, font="Microsoft YaHei").move_to(hi_pos)
        head_intro = VGroup(hi_c, hi_t)
        g_to_head = self.thread_arrow(chain_pos['G'], hi_pos, 0.7, self.ORANGE)
        j_to_head = self.thread_arrow(chain_pos['J'], hi_pos, 2.9, self.TEAL)

        with self.voiceover(
            text="于是，我们增加一个头结点，把这两个断头都接到它身上：让 G 的前驱指向头结点，也让 J 的后继指向头结点。这样，整条链就接成了一个环，而头结点，就是这个环唯一的入口。",
            subcaption="增加头结点连接两个断头：G 的前驱指向头结点，J 的后继也指向头结点，整条链连成双向循环环路。"
        ) as tracker:
            self.play(FadeOut(g_null), FadeOut(j_null), FadeIn(head_intro, shift=UP * 0.15), run_time=0.7)
            self.play(Create(g_to_head), run_time=0.7)
            self.play(Create(j_to_head), run_time=0.9)
            self.wait(max(0.2, tracker.duration - 2.3))

        with self.voiceover(
            text="从头结点出发，既能顺着后继正向遍历，也能顺着前驱反向遍历，最后都回到头结点。带头结点的二叉树中序线索化，做的正是这件事。",
            subcaption="从头结点出发，既能顺后继正向遍历，也能顺前驱反向遍历。带头结点的中序线索化正是实现这一闭环。"
        ) as tracker:
            self.play(Indicate(VGroup(head_intro, g_to_head, j_to_head), color=YELLOW, scale_factor=1.08),
                      run_time=1.2)
            self.wait(max(0.2, tracker.duration - 1.2))

        with self.voiceover(text="下面来看它的 Python 代码实现。", subcaption="下面来看它的 Python 代码实现。") as tracker:
            self.wait(tracker.duration)

        self.play(*[FadeOut(m) for m in self.mobjects if m is not logo], run_time=0.6)

        # ============================================================
        # PHASE C — CODE BLOCK（跟踪 in_order_threading 函数）
        # ============================================================
        c_lines = [
            "def in_order_threading(t):",
            "    global pre",
            "    thrt = BinaryTree()",
            "    thrt.ltag = 0",
            "    thrt.rtag = 1",
            "    thrt.rchild = thrt",
            "    if t is None:",
            "        thrt.lchild = thrt",
            "    else:",
            "        thrt.lchild = t",
            "        pre = thrt",
            "        in_threading(t)",
            "        pre.rchild = thrt",
            "        pre.rtag = 1",
            "        thrt.rchild = pre",
            "    return thrt",
        ]
        # 代码行索引常量
        IDX_NEW = 2        # thrt = BinaryTree()     —— ① 创建头结点
        IDX_HLTAG = 3      # thrt.ltag = 0           —— 头结点有左孩子，ltag=0
        IDX_HRTAG = 4      # thrt.rtag = 1           —— 头结点右指针是线索，rtag=1
        IDX_HRSELF = 5     # thrt.rchild = thrt      —— ① 右指针初始指向自己
        IDX_IFT = 6        # if t is None:           —— ② 判断树是否为空
        IDX_EMPTY = 7      # thrt.lchild = thrt      —— 空树分支（本例不走）
        IDX_ELSE = 8       # else:                   —— 树非空
        IDX_HLROOT = 9     # thrt.lchild = t         —— ③ 头结点左孩子指向树根
        IDX_PREHEAD = 10   # pre = thrt              —— ③ pre 初值指向头结点
        IDX_CALL = 11      # in_threading(t)         —— ④ 对整棵树中序线索化
        IDX_LASTRCH = 12   # pre.rchild = thrt       —— ⑤ 最后结点后继指向头结点
        IDX_LASTRTAG = 13  # pre.rtag = 1            —— ⑤ 最后结点 rtag=1
        IDX_HRLAST = 14    # thrt.rchild = pre       —— ⑥ 头结点右指针指向最后结点

        self.c_texts = []
        for line in c_lines:
            t = Text(line.lstrip(" "), font_size=12, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        SPACE_WIDTH = 0.097
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        buff_val = 0.22
        code_bg = RoundedRectangle(
            corner_radius=0.2,
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
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.12).rotate(-PI / 2)
                    self.code_pointer.next_to(self.c_texts[new_idx], LEFT, buff=0.15)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.c_texts[new_idx], LEFT, buff=0.15)
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
        # PHASE C2 — 二叉树、标志位、线索图例
        # ============================================================
        pos = {
            'A': np.array([-0.7, 2.3, 0]),
            'B': np.array([-2.7, 0.9, 0]), 'C': np.array([1.3, 0.9, 0]),
            'D': np.array([-3.7, -0.5, 0]), 'E': np.array([-1.7, -0.5, 0]), 'F': np.array([2.3, -0.5, 0]),
        }
        children = {'A': ('B', 'C'), 'B': ('D', 'E'), 'C': (None, 'F'),
                    'D': (None, None), 'E': (None, None), 'F': (None, None)}

        edges = VGroup()
        for k, (lc, rc) in children.items():
            for ch in (lc, rc):
                if ch is not None:
                    edges.add(self.edge(pos[k], pos[ch]))

        node_group = VGroup()
        for k, p in pos.items():
            node_group.add(self.make_node(k, p))
        tree_group = VGroup(edges, node_group)

        tag_mobs = {}
        tag_group = VGroup()
        for k, p in pos.items():
            lt = Text("0", font_size=15, color=GRAY_B).move_to(p + LEFT * 0.5)
            rt = Text("0", font_size=15, color=GRAY_B).move_to(p + RIGHT * 0.5)
            tag_mobs[(k, 'L')] = lt
            tag_mobs[(k, 'R')] = rt
            tag_group.add(lt, rt)

        def leg_row(color, dashed, txt):
            if dashed:
                seg = DashedVMobject(Line(ORIGIN, RIGHT * 0.5, color=color, stroke_width=2.5), num_dashes=4)
            else:
                seg = Line(ORIGIN, RIGHT * 0.5, color=color, stroke_width=2.5)
            return VGroup(seg, Text(txt, font_size=14, font="Microsoft YaHei", color=color if dashed else GRAY_A)
                          ).arrange(RIGHT, buff=0.12)

        legend = VGroup(
            leg_row(GRAY, False, "孩子指针"),
            leg_row(self.ORANGE, True, "前驱线索 (ltag=1)"),
            leg_row(self.TEAL, True, "后继线索 (rtag=1)"),
            leg_row(self.HEADC, True, "头结点 rchild"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.14).to_corner(DL, buff=0.3).shift(UP * 1.1)

        with self.voiceover(
            text="这是一棵已经建好的二叉树。根是 A，A 的左子树由 B、D、E 组成，右子树是 C，C 又有一个右孩子 F。它的中序序列是 D、B、E、A、C、F。每个结点旁的两个数字，是它的 ltag 和 rtag，现在都是 0。",
            subcaption="已有二叉树：中序序列为 D、B、E、A、C、F；结点旁两个数字为 ltag 和 rtag（初始为 0）。"
        ) as tracker:
            self.play(FadeIn(code_block), FadeIn(tree_group), FadeIn(tag_group), FadeIn(legend),
                      run_time=tracker.duration)

        # ============================================================
        # PHASE D — 动画辅助函数
        # ============================================================
        pos['HEAD'] = np.array([-0.7, 3.35, 0])
        drawn_threads = VGroup()
        self.pre_key = None
        self.pre_ptr = None

        ring = Circle(radius=self.NODE_R + 0.1, color=YELLOW, stroke_width=4)

        def flip_tag(node, side, color):
            new = Text("1", font_size=16, color=color, weight=BOLD).move_to(tag_mobs[(node, side)].get_center())
            self.play(Transform(tag_mobs[(node, side)], new), run_time=0.35)

        def set_pre(node, beside=False):
            target = (pos[node] + LEFT * 0.75) if beside else (pos[node] + DOWN * 0.66)
            if self.pre_ptr is None:
                tri = Triangle(color=GREEN, fill_opacity=1).scale(0.11)
                lbl = Text("pre", font_size=15, color=GREEN)
                self.pre_ptr = VGroup(tri, lbl).arrange(DOWN, buff=0.04).move_to(target)
                self.play(FadeIn(self.pre_ptr, shift=UP * 0.15), run_time=0.4)
            else:
                self.pre_ptr.generate_target()
                self.pre_ptr.target.move_to(target)
                self.play(MoveToTarget(self.pre_ptr), run_time=0.5)
            self.pre_key = node

        def m_ring(node):
            self.play(ring.animate.move_to(pos[node]), run_time=0.4)

        def m_left(node, angle):
            flip_tag(node, 'L', self.ORANGE)
            thr = self.thread_arrow(pos[node], pos[self.pre_key], angle, self.ORANGE)
            drawn_threads.add(thr)
            self.play(Create(thr), run_time=0.55)

        def m_right(node, angle):
            flip_tag(self.pre_key, 'R', self.TEAL)
            thr = self.thread_arrow(pos[self.pre_key], pos[node], angle, self.TEAL)
            drawn_threads.add(thr)
            self.play(Create(thr), run_time=0.55)

        # ============================================================
        # PHASE D2 — 逐行跟踪 in_order_threading
        # ============================================================
        head_circle = Circle(radius=self.NODE_R, color=self.HEADC, fill_color=self.HEADC,
                             fill_opacity=0.18, stroke_width=2.5).move_to(pos['HEAD'])
        head_label = Text("头", font_size=20, color=WHITE, font="Microsoft YaHei").move_to(pos['HEAD'])
        head_node = VGroup(head_circle, head_label)
        head_name = Text("头结点 thrt", font_size=15, color=self.HEADC, font="Microsoft YaHei").next_to(
            head_node, RIGHT, buff=0.15)

        with self.voiceover(
            text="算法开始。第一步，创建一个新结点 thrt，作为头结点。",
            subcaption="算法开始。第一步：thrt = BinaryTree()，创建新结点作为头结点。"
        ) as tracker:
            track(IDX_NEW)
            self.play(FadeIn(head_node, shift=DOWN * 0.15), FadeIn(head_name), run_time=0.7)
            self.wait(max(0.2, tracker.duration - 1.05))

        with self.voiceover(
            text="把头结点的 ltag 置为 0，因为如果树非空，头结点就有一个左孩子，也就是树根；再把 rtag 置为 1，表示头结点的右指针是一条线索。",
            subcaption="thrt.ltag 置 0（左孩子为树根）；thrt.rtag 置 1（右指针为线索）。"
        ) as tracker:
            track(IDX_HLTAG)
            self.play(Indicate(head_node, color=self.ORANGE, scale_factor=1.12), run_time=0.6)
            track(IDX_HRTAG)
            self.play(Indicate(head_node, color=self.TEAL, scale_factor=1.12), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 1.9))

        head_selfloop = self.self_loop(pos['HEAD'], self.HEADC)
        with self.voiceover(
            text="接着，把头结点的右指针，初始化为指向它自己。",
            subcaption="thrt.rchild = thrt，头结点右指针初始化指向自己。"
        ) as tracker:
            track(IDX_HRSELF)
            self.play(Create(head_selfloop), run_time=0.7)
            self.wait(max(0.2, tracker.duration - 1.05))

        with self.voiceover(
            text="然后判断这棵树是否为空。本例中树 t 非空，因此跳过空树的处理，进入 else 分支。",
            subcaption="判断树是否为空：t 非空，跳过空树分支，进入 else 分支。"
        ) as tracker:
            track(IDX_IFT)
            self.play(Indicate(node_group, color=YELLOW, scale_factor=1.06), run_time=0.7)
            track(IDX_ELSE)
            self.wait(max(0.2, tracker.duration - 1.05))

        head_lchild = self.ptr_arrow(pos['HEAD'], pos['A'], color=GRAY)
        with self.voiceover(
            text="在 else 分支里，先让头结点的左孩子指向树根 A。",
            subcaption="thrt.lchild = t，头结点左孩子指向树根 A。"
        ) as tracker:
            track(IDX_HLROOT)
            self.play(Create(head_lchild), run_time=0.7)
            self.wait(max(0.2, tracker.duration - 1.05))

        with self.voiceover(
            text="再让全局指针 pre 指向头结点，作为中序线索化的起点。这样 pre 一开始就不是空指针。",
            subcaption="pre = thrt，pre 初值指向头结点，作为线索化起点。"
        ) as tracker:
            track(IDX_PREHEAD)
            set_pre('HEAD', beside=True)
            self.wait(max(0.2, tracker.duration - 0.9))

        # ---- 调用 in_threading(t) ----
        with self.voiceover(
            text="现在调用以结点 p 为根的子树中序线索化，传入树根 A，对整棵树进行中序线索化。它会按中序顺序，从最左的 D 开始，逐个处理每一个结点。",
            subcaption="调用 in_threading(t)，从最左结点 D 开始按中序次序建立线索。"
        ) as tracker:
            track(IDX_CALL)
            ring.move_to(pos['D'])
            self.play(FadeIn(ring), run_time=0.3)
            m_left('D', -2.2)
            set_pre('D')
            self.wait(max(0.2, tracker.duration - 1.6))

        with self.voiceover(
            text="处理 B 时，为它的前驱 D 补上一条指向 B 的后继线索；处理 E 时，为 E 建立一条指向前驱 B 的前驱线索。",
            subcaption="处理 B：补齐 D 到 B 的后继线索；处理 E：建立 E 到 B 的前驱线索。"
        ) as tracker:
            m_ring('B')
            m_right('B', 1.2)
            set_pre('B')
            m_ring('E')
            m_left('E', -1.0)
            set_pre('E')
            self.wait(max(0.2, tracker.duration - 2.1))

        with self.voiceover(
            text="回到根 A 时，为它的前驱 E 补上指向 A 的后继线索；接着进入右子树，处理 C 和 F，分别为它们建立指向前驱 A、指向前驱 C 的前驱线索。",
            subcaption="回到 A：补齐 E 到 A 的后继线索；进入右子树分别建立 C 到 A、F 到 C 的前驱线索。"
        ) as tracker:
            m_ring('A')
            m_right('A', -0.55)
            set_pre('A')
            m_ring('C')
            m_left('C', -1.1)
            set_pre('C')
            m_ring('F')
            m_left('F', -1.1)
            set_pre('F')
            self.wait(max(0.2, tracker.duration - 3.1))

        with self.voiceover(
            text="至此，in_threading 把树内部所有前驱、后继线索都建好了。中序序列 D、B、E、A、C、F 全部处理完毕，pre 正好停在最后一个结点 F 上。这一步的详细递归过程，可以参考上一个视频。",
            subcaption="内部线索建立完毕，中序处理结束，pre 指向中序最后一个结点 F。"
        ) as tracker:
            self.play(FadeOut(ring), run_time=0.3)
            self.play(Indicate(drawn_threads, color=YELLOW, scale_factor=1.05), run_time=1.2)
            self.wait(max(0.2, tracker.duration - 1.5))

        # ---- 收尾：最后结点 F 与头结点相互链接 ----
        with self.voiceover(
            text="调用返回后，pre 指向中序最后一个结点 F。让 F 的右指针指向头结点，作为它的后继线索。",
            subcaption="pre.rchild = thrt，最后结点 F 的右指针指向头结点。"
        ) as tracker:
            track(IDX_LASTRCH)
            f_succ = self.thread_arrow(pos['F'], pos['HEAD'], -2.4, self.TEAL)
            drawn_threads.add(f_succ)
            self.play(Create(f_succ), run_time=0.7)
            self.wait(max(0.2, tracker.duration - 1.05))

        with self.voiceover(
            text="并把 F 的 rtag 置为 1，表示这是一条线索。",
            subcaption="pre.rtag = 1，置 F 的 rtag 为 1。"
        ) as tracker:
            track(IDX_LASTRTAG)
            flip_tag('F', 'R', self.TEAL)
            self.wait(max(0.2, tracker.duration - 0.7))

        with self.voiceover(
            text="最后，把头结点的右指针，从原来指向自己，改为指向这个最后结点 F。至此，一个带头结点的双向线索链表就建好了。",
            subcaption="thrt.rchild = pre，头结点右指针指向最后结点 F，形成完整闭环。"
        ) as tracker:
            track(IDX_HRLAST)
            head_rchild = self.thread_arrow(pos['HEAD'], pos['F'], -1.5, self.HEADC)
            drawn_threads.add(head_rchild)
            self.play(FadeOut(head_selfloop), Create(head_rchild), run_time=0.8)
            if self.pre_ptr is not None:
                self.play(FadeOut(self.pre_ptr), run_time=0.3)
            self.wait(max(0.2, tracker.duration - 1.4))

        track(None)

        # ============================================================
        # PHASE E — 结果与复杂度分析
        # ============================================================
        self.play(FadeOut(code_block), run_time=0.5)

        with self.voiceover(
            text="现在，整棵二叉树的中序线索化就完成了。所有空指针都变成了前驱或后继线索，并通过头结点首尾相连，构成一个双向线索链表。从头结点出发，既能顺着后继按中序顺序 D B E A C F 正向遍历，也能顺着前驱反向遍历。",
            subcaption="所有空指针均转化为线索，并由头结点连成双向循环线索链表，支持顺畅双向遍历。"
        ) as tracker:
            self.play(Indicate(drawn_threads, color=YELLOW, scale_factor=1.05), run_time=1.2)
            self.wait(max(0.2, tracker.duration - 1.2))

        result_label = Text("中序序列：D B E A C F", font_size=22, font="Microsoft YaHei", color=GREEN)
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          Text("O(n)", font_size=24, font="Consolas", color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           Text("O(h)", font_size=24, font="Consolas", color=YELLOW)).arrange(RIGHT, buff=0.1)
        summary = VGroup(result_label, time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        summary.move_to([3.6, -1.85, 0])

        with self.voiceover(
            text="算法对二叉树做一次中序遍历，每个结点都恰好被访问、处理一次，因此时间复杂度为O恩。",
            subcaption="算法对二叉树做一次中序遍历，每个结点都恰好被访问、处理一次，因此时间复杂度为 O(n)。"
        ) as tracker:
            self.play(Write(result_label), run_time=0.6)
            self.play(FadeIn(time_box), run_time=max(0.4, tracker.duration - 0.6))

        with self.voiceover(
            text="线索化采用递归实现，空间主要花在递归栈上，栈的深度等于树的高度h；最坏情况退化成一条单链时，h 等于 n，空间复杂度为O恩。",
            subcaption="线索化采用递归实现，空间主要花在递归栈上，栈的深度等于树的高度h；最坏退化为单链时 h=n，空间复杂度 O(n)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(
            text="以上就是带头结点的二叉树中序线索化算法 Python 版的完整过程。",
            subcaption="以上就是带头结点的二叉树中序线索化算法 Python 版的完整过程。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)


# Alias
ContinuousInOrderThreadingPythonVideo = InOrderThreadingPythonVideo
