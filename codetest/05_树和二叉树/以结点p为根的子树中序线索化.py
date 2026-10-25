# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import numpy as np
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class InThreadingVideo(VoiceoverScene):
    # ===== 统一的结点 / 连线样式（与本章中序遍历、复制二叉树视频保持一致，保证全章视觉统一、美观）=====
    NODE_R = 0.32
    # 线索专用配色：前驱线索（左线索）用橙色，后继线索（右线索）用青色，与灰色的“孩子指针”实线区分开
    ORANGE = "#FF8C1A"  # 前驱线索 —— LTag = 1
    TEAL = "#1AC7C7"  # 后继线索 —— RTag = 1
    HEADC = "#B15CFF"  # 头结点专用配色（紫色），头结点及其 rchild 指针

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
        """结点间的实心指针箭头：头结点的 lchild / rchild 指向真实结点（LTag/RTag=0 的真指针）时使用。"""
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        return Arrow(p1 + u * self.NODE_R, p2 - u * self.NODE_R, color=color,
                     stroke_width=sw, tip_length=0.16, buff=0)

    def construct(self):
        # 初始化语音服务（与本章其它视频完全一致的中文男声配置）
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ============================================================
        # PHASE A — TITLE（标题，与本章其它视频保持完全一致的版式）
        # ============================================================
        algo_title = Text("以结点p为根的子树中序线索化（有代码跟踪版）", font_size=38, font="Microsoft YaHei",
                          weight=BOLD).to_edge(UP, buff=0.55)
        self.play(FadeIn(algo_title), run_time=0.8)

        subtitle = Text("按中序遍历顺序，把结点空着的指针改造成指向前驱、后继的“线索”",
                        font_size=21, font="Microsoft YaHei", color=GRAY_A).next_to(algo_title, DOWN, buff=0.22)

        with self.voiceover(
                text="本视频讲解以结点p为根的子树中序线索化的代码实现与逐行跟踪，如尚未掌握该算法的设计思路，建议首先观看学习该算法的无代码跟踪版讲解视频。",
        ) as tracker:
            self.play(FadeIn(subtitle), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        with self.voiceover(text="该算法是对树中任意一个以结点p为根的子树进行中序线索化。") as tracker:
            self.wait(tracker.duration)

        self.play(FadeOut(subtitle), run_time=0.4)

        # ============================================================
        # PHASE B — 例子引入（直观类比：中序序列是一条“链”，用空指针存下相邻关系）
        # ============================================================
        # 一棵 4 结点小树（与主演示不同的例子）：H(G(_, I), J)，中序序列 G I H J
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
                text="先建立一个直观印象。这里有一棵普通的二叉树，它的中序遍历序列是 G、I、H、J。"
        ) as tracker:
            self.play(FadeIn(intro_tree), run_time=tracker.duration)

        # 把中序序列铺成一条横向的“链”
        seq_keys = ['G', 'I', 'H', 'J']
        chain = VGroup()
        for i, k in enumerate(seq_keys):
            cc = self.make_node(k, np.array([-0.4 + i * 1.4, -1.6, 0]), color=GREEN)
            chain.add(cc)
        chain_pos = {k: chain[i].circle.get_center() for i, k in enumerate(seq_keys)}

        with self.voiceover(
                text="把这个中序序列拉成一条横向的链。可以看到，链上的每个结点，都有它的直接前驱和直接后继。"
        ) as tracker:
            for i, k in enumerate(seq_keys):
                self.play(TransformFromCopy(inodes[k], chain[i]), run_time=0.4)
            self.wait(max(0.2, tracker.duration - len(seq_keys) * 0.4))

        # 画出链上相邻结点之间的前驱/后继关系箭头
        succ_arrows = VGroup()
        pred_arrows = VGroup()
        for i in range(len(seq_keys) - 1):
            a = chain_pos[seq_keys[i]]
            b = chain_pos[seq_keys[i + 1]]
            succ_arrows.add(self.thread_arrow(a, b, -0.6, self.TEAL))  # 后继：i -> i+1
            pred_arrows.add(self.thread_arrow(b, a, -0.6, self.ORANGE))  # 前驱：i+1 -> i

        with self.voiceover(
                text="向后指的青色箭头，表示后继；向前指的橙色箭头，表示前驱。中序线索化，就是要把这些前驱后继关系，记录在树里。"
        ) as tracker:
            self.play(Create(succ_arrows), run_time=1.0)
            self.play(Create(pred_arrows), run_time=1.0)
            self.wait(max(0.2, tracker.duration - 2.0))

        with self.voiceover(
                text="一棵有 n 个结点的二叉树，恰好有 n 加 1 个空指针被白白浪费，中序线索化正是利用这些空指针来存放前驱和后继。",
                subcaption="一棵有 n 个结点的二叉树，恰好有n+1个空指针被白白浪费，中序线索化正是利用这些空指针来存放前驱和后继。"
        ) as tracker:
            self.play(Indicate(VGroup(inodes['I'].circle, inodes['J'].circle, inodes['G'].circle),
                               color=YELLOW, scale_factor=1.15), run_time=1.0)
            self.wait(max(0.2, tracker.duration - 1.0))

        # ----- 结点结构讲解：新增 LTag / RTag 两个标志位 -----
        node_pic = VGroup(
            *[Rectangle(width=w, height=0.6, stroke_width=2, color=GRAY_B)
              for w in (0.7, 1.1, 0.9, 1.1, 0.7)]
        ).arrange(RIGHT, buff=0)
        node_fields = ['LTag', 'lchild', 'data', 'rchild', 'RTag']
        node_labels = VGroup(*[Text(f, font_size=15, color=WHITE).move_to(node_pic[i].get_center())
                               for i, f in enumerate(node_fields)])
        node_struct = VGroup(node_pic, node_labels).move_to([2.9, 0.9, 0])
        node_hint = Text("Tag = 0 → 指向孩子      Tag = 1 → 指向线索",
                         font_size=17, font="Microsoft YaHei", color=YELLOW).next_to(node_struct, DOWN, buff=0.3)

        with self.voiceover(
                text="为此，给每个结点增加两个标志位：LTag 和 RTag。标志位为 0，表示对应的指针指向真正的孩子；标志位为 1，就表示它是一条线索，分别指向前驱和后继。"
        ) as tracker:
            self.play(FadeIn(node_struct, shift=UP * 0.2), run_time=0.8)
            self.play(Indicate(VGroup(node_pic[0], node_labels[0]), color=self.ORANGE, scale_factor=1.1),
                      Indicate(VGroup(node_pic[4], node_labels[4]), color=self.TEAL, scale_factor=1.1), run_time=0.8)
            self.play(FadeIn(node_hint), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 2.2))

        with self.voiceover(
                text="下面来看该算法的代码实现。"
        ) as tracker:
            self.wait(tracker.duration)

        # 淡出标题：接下来要在树根正上方绘制头结点，需要腾出顶部空间
        self.play(*[FadeOut(m) for m in self.mobjects if m is not logo], run_time=0.6)

        # ============================================================
        # PHASE C — CODE BLOCK CONFIG（与本章其它视频完全相同的代码板样式）
        # ============================================================
        c_lines = [
            "void InThreading(BiThrTree p) {",
            "  if (p) {",
            "    InThreading(p->lchild);",
            "    if (!p->lchild) {",
            "      p->LTag = 1;",
            "      p->lchild = pre;",
            "    }",
            "    else p->LTag = 0;",
            "    if (!pre->rchild) {",
            "      pre->RTag = 1;",
            "      pre->rchild = p;",
            "    }",
            "    else pre->RTag = 0;",
            "    pre = p;",
            "    InThreading(p->rchild);",
            "  }",
            "}",
        ]
        # 代码行索引常量（严格对应用户给定的 InThreading 函数）
        IDX_IF = 1  # if (p)                  —— 判空
        IDX_LEFT = 2  # InThreading(p->lchild); —— 左子树递归线索化
        IDX_CHKL = 3  # if (!p->lchild)         —— 判断 p 左孩子是否为空
        IDX_SETLTAG = 4  # p->LTag = 1;            —— 给 p 加左线索标志
        IDX_SETLTHR = 5  # p->lchild = pre;        —— 左孩子指向前驱 pre
        IDX_ELSE_LTAG = 7  # else p->LTag = 0;       —— p 有左孩子，LTag 置 0
        IDX_CHKR = 8  # if (!pre->rchild)       —— 判断 pre 右孩子是否为空
        IDX_SETRTAG = 9  # pre->RTag = 1;          —— 给 pre 加右线索标志
        IDX_SETRTHR = 10  # pre->rchild = p;        —— 右孩子指向后继 p
        IDX_ELSE_RTAG = 12  # else pre->RTag = 0;     —— pre 有右孩子，RTag 置 0
        IDX_PRE = 13  # pre = p;                —— pre 指向刚访问的 p
        IDX_RIGHT = 14  # InThreading(p->rchild); —— 右子树递归线索化

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=12, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        SPACE_WIDTH = 0.097
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        buff_val = 0.22
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

        def track(new_idx, run_time=0.3):
            """安全地播放代码行高亮切换：若目标行已高亮（无动画），则以等长等待代替，避免空 play 报错。"""
            anims = get_track_anims(new_idx)
            if anims:
                self.play(*anims, run_time=run_time)
            else:
                self.wait(run_time)

        # ============================================================
        # PHASE C2 — 二叉树、调用栈、pre 指针、线索图例
        # ============================================================
        # 一棵 6 结点二叉树：A(B(D,E), C(_, F))，先序输入 A B D # # E # # C # F # #
        # 中序序列为 D B E A C F —— 也正是线索化时结点被处理的顺序
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

        circles, labels = {}, {}
        node_group = VGroup()
        for k, p in pos.items():
            nd = self.make_node(k, p)
            circles[k] = nd.circle
            labels[k] = nd.label
            node_group.add(nd)
        tree_group = VGroup(edges, node_group)

        # 每个结点的 LTag（左）/ RTag（右）标志位，初始都是 0（建树时已置 0）
        tag_mobs = {}
        tag_group = VGroup()
        for k, p in pos.items():
            lt = Text("0", font_size=15, color=GRAY_B).move_to(p + LEFT * 0.5)
            rt = Text("0", font_size=15, color=GRAY_B).move_to(p + RIGHT * 0.5)
            tag_mobs[(k, 'L')] = lt
            tag_mobs[(k, 'R')] = rt
            tag_group.add(lt, rt)

        # “当前结点 p”活动指示环（黄色）
        ring = Circle(radius=self.NODE_R + 0.1, color=YELLOW, stroke_width=4).move_to(pos['A'])

        # 线索图例（左下角）
        def leg_row(color, dashed, txt):
            if dashed:
                seg = DashedVMobject(Line(ORIGIN, RIGHT * 0.5, color=color, stroke_width=2.5), num_dashes=4)
            else:
                seg = Line(ORIGIN, RIGHT * 0.5, color=color, stroke_width=2.5)
            return VGroup(seg, Text(txt, font_size=14, font="Microsoft YaHei", color=color if dashed else GRAY_A)
                          ).arrange(RIGHT, buff=0.12)

        legend = VGroup(
            leg_row(GRAY, False, "孩子指针"),
            leg_row(self.ORANGE, True, "前驱线索 (LTag=1)"),
            leg_row(self.TEAL, True, "后继线索 (RTag=1)"),
            leg_row(self.HEADC, True, "头结点 rchild"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.14).to_corner(DL, buff=0.3).shift(UP * 1.1)

        # 调用栈面板（左侧）
        STACK_X = -6.0
        STACK_BASE_Y = 0.35
        FRAME_H = 0.5
        stack_title = Text("调用栈", font_size=20, font="Microsoft YaHei", color=YELLOW).move_to([STACK_X, 2.15, 0])
        stack_hint = Text("（递归深度=树高）", font_size=12, font="Microsoft YaHei", color=GRAY).next_to(
            stack_title, DOWN, buff=0.1)

        def make_frame(node_key):
            box = RoundedRectangle(corner_radius=0.08, width=1.5, height=0.44, color=BLUE_D, fill_color=BLUE_D,
                                   fill_opacity=0.18, stroke_width=2)
            t = Text("InThr(%s)" % node_key, font_size=14, color=WHITE).move_to(box.get_center())
            return VGroup(box, t)

        with self.voiceover(
                text="这是一棵已经建好的二叉树。根是 A，A 的左子树由 B、D、E 组成，右子树是 C，C 又有一个右孩子 F。它的中序序列是 D、B、E、A、C、F。"
        ) as tracker:
            self.play(FadeIn(code_block), FadeIn(tree_group), FadeIn(tag_group), run_time=tracker.duration)

        with self.voiceover(
                text="每个结点旁的两个数字是它的 LTag 和 RTag，现在都是 0。左侧是递归调用栈，黄色圆环表示当前正在处理的结点 p，左下角是线索的图例。",
                subcaption="结点旁的数字是 LTag、RTag（初始为 0）；黄环表示当前结点 p；左侧为调用栈，左下为图例。"
        ) as tracker:
            self.play(FadeIn(stack_title), FadeIn(stack_hint), FadeIn(legend), run_time=tracker.duration)

        # ============================================================
        # PHASE D — 线索化过程的辅助动画函数
        # ============================================================
        path = []  # 当前调用链（结点 key）
        stack_mobs = []  # 调用栈中的帧
        self.pre_key = None  # 全局 pre 当前指向的结点
        self.pre_ptr = None  # pre 指针的 Mobject

        def push_frame(node_key):
            y = STACK_BASE_Y + len(stack_mobs) * FRAME_H
            fr = make_frame(node_key).move_to([STACK_X, y, 0])
            stack_mobs.append(fr)
            return fr

        def enter_root():
            path.append('A')
            fr = push_frame('A')
            ring.move_to(pos['A'])
            self.play(FadeIn(ring), FadeIn(fr, shift=UP * 0.2), run_time=0.5)
            track(IDX_IF, 0.4)

        def go_child(child, side):
            # ①/⑤：递归进入左/右孩子，压栈，环移动到孩子，再判空
            track(IDX_LEFT if side == 'L' else IDX_RIGHT, 0.35)
            path.append(child)
            fr = push_frame(child)
            self.play(ring.animate.move_to(pos[child]), FadeIn(fr, shift=UP * 0.2), run_time=0.5)
            track(IDX_IF, 0.35)

        def null_child(node, side):
            # 递归进入空指针，if(p) 为假，直接返回（不压栈）
            track(IDX_LEFT if side == 'L' else IDX_RIGHT, 0.3)
            track(IDX_IF, 0.3)
            off = (LEFT * 0.55 if side == 'L' else RIGHT * 0.55) + DOWN * 0.7
            tag = Text("空，返回", font_size=14, font="Microsoft YaHei", color=GRAY).move_to(pos[node] + off)
            self.play(FadeIn(tag, shift=DOWN * 0.1), run_time=0.3)
            self.play(FadeOut(tag), run_time=0.25)

        def flip_tag(node, side, color):
            new = Text("1", font_size=16, color=color, weight=BOLD).move_to(tag_mobs[(node, side)].get_center())
            self.play(Transform(tag_mobs[(node, side)], new), run_time=0.35)

        def set_pre(node):
            # ④ pre = p：pre 指针移动到刚处理完的结点 node 下方
            target = pos[node] + DOWN * 0.66
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

        # 建好的线索留在画面上
        drawn_threads = VGroup()

        def make_left_thread(node, angle):
            # if (!p->lchild) 为真：p->LTag=1，p->lchild 指向前驱 pre（有头结点后 pre 一定非空）
            track(IDX_CHKL)
            track(IDX_SETLTAG)
            flip_tag(node, 'L', self.ORANGE)
            track(IDX_SETLTHR)
            thr = self.thread_arrow(pos[node], pos[self.pre_key], angle, self.ORANGE)
            drawn_threads.add(thr)
            self.play(Create(thr), run_time=0.6)

        def else_left(node):
            # if (!p->lchild) 为假 → else p->LTag = 0（p 有左孩子，保持 0）
            track(IDX_CHKL)
            track(IDX_ELSE_LTAG)
            self.play(Indicate(tag_mobs[(node, 'L')], color=GRAY_A, scale_factor=1.4), run_time=0.4)

        def make_right_thread(node, angle):
            # if (!pre->rchild) 为真：pre->RTag=1，pre->rchild 指向后继 node
            track(IDX_CHKR)
            track(IDX_SETRTAG)
            flip_tag(self.pre_key, 'R', self.TEAL)
            track(IDX_SETRTHR)
            thr = self.thread_arrow(pos[self.pre_key], pos[node], angle, self.TEAL)
            drawn_threads.add(thr)
            self.play(Create(thr), run_time=0.6)

        def else_right():
            # if (!pre->rchild) 为假 → else pre->RTag = 0（pre 已有右孩子/指向自己，保持 0）
            track(IDX_CHKR)
            track(IDX_ELSE_RTAG)
            if self.pre_key == 'HEAD':
                # pre 是头结点，其右指针指向自己、不为空
                self.play(Indicate(head_node, color=GRAY_A, scale_factor=1.1), run_time=0.4)
            else:
                self.play(Indicate(tag_mobs[(self.pre_key, 'R')], color=GRAY_A, scale_factor=1.4), run_time=0.4)

        def leave():
            path.pop()
            fr = stack_mobs.pop()
            self.play(FadeOut(fr, shift=UP * 0.2), run_time=0.3)
            if path:
                self.play(ring.animate.move_to(pos[path[-1]]), run_time=0.4)
            else:
                self.play(FadeOut(ring), run_time=0.3)

        # ============================================================
        # PHASE D2 — 线索化过程（严格跟踪用户给定的 InThreading 函数）
        # ============================================================
        # ---- 先增加头结点，并令 pre 指向它（这样 pre 从一开始就不为空）----
        pos['HEAD'] = np.array([-0.7, 3.35, 0])
        head_circle = Circle(radius=self.NODE_R, color=self.HEADC, fill_color=self.HEADC,
                             fill_opacity=0.18, stroke_width=2.5).move_to(pos['HEAD'])
        head_label = Text("头", font_size=20, color=WHITE, font="Microsoft YaHei").move_to(pos['HEAD'])
        head_node = VGroup(head_circle, head_label)
        head_name = Text("头结点 Thrt", font_size=15, color=self.HEADC, font="Microsoft YaHei").next_to(
            head_node, RIGHT, buff=0.15)
        head_lchild = self.ptr_arrow(pos['HEAD'], pos['A'], color=GRAY)  # 头结点左指针指向树根 A

        with self.voiceover(
                text="在正式线索化之前，先在线索链表上增加一个头结点Thrt。线索化开始时，把全局指针pre指向头结点。这样，pre从一开始就不是空指针，后面判断前驱、后继时都不必再担心pre为空。",
        ) as tracker:
            self.play(FadeIn(head_node, shift=DOWN * 0.15), FadeIn(head_name), run_time=0.8)
            self.play(Create(head_lchild), run_time=0.6)
            tri = Triangle(color=GREEN, fill_opacity=1).scale(0.11)
            lbl = Text("pre", font_size=15, color=GREEN)
            self.pre_ptr = VGroup(tri, lbl).arrange(DOWN, buff=0.04).next_to(head_node, LEFT, buff=0.18)
            self.pre_key = 'HEAD'
            self.play(FadeIn(self.pre_ptr, shift=RIGHT * 0.15), run_time=0.5)
            self.wait(max(0.2, tracker.duration - 1.9))

        with self.voiceover(
                text="现在，主函数调用线索化函数 InThreading，传入根结点 A。这次调用被压入调用栈，判断 A 非空。"
        ) as tracker:
            enter_root()

        with self.voiceover(
                text="先递归线索化左子树：从 A 深入到左孩子 B，再从 B 深入到左孩子 D。每深入一层，调用栈就多压一层。到达 D 后，D 的左孩子为空，递归立即返回。"
        ) as tracker:
            go_child('B', 'L')
            go_child('D', 'L')
            null_child('D', 'L')

        with self.voiceover(
                text="现在处理 D。D 的左孩子为空，于是把 D 的 LTag 置为 1，让它的左指针指向前驱 pre。此刻 pre 正是头结点，所以作为中序第一个结点，D 的前驱线索指向头结点。"
        ) as tracker:
            make_left_thread('D', -2.2)

        with self.voiceover(
                text="接着检查 pre 的右孩子。pre 是头结点，它的右指针指向自己、不为空，于是走 else 分支，不建立右线索。然后让 pre 指向刚刚处理完的 D。"
        ) as tracker:
            else_right()
            track(IDX_PRE)
            set_pre('D')

        with self.voiceover(
                text="递归线索化 D 的右子树，也是空，返回。D 这一层全部完成，从调用栈弹出，返回到 B。"
        ) as tracker:
            null_child('D', 'R')
            leave()

        with self.voiceover(
                text="现在处理 B。B 的左孩子是 D，不为空，走 else 分支，B 的 LTag 保持 0。再看 pre，pre 是 D，D 的右孩子为空，于是给 D 建立后继线索：把 D 的 RTag 置为 1，让 D 的右指针指向它的后继，也就是 B。"
        ) as tracker:
            else_left('B')
            make_right_thread('B', 1.2)

        with self.voiceover(
                text="让 pre 指向 B。递归线索化 B 的右子树，进入 E。E 的左孩子为空，返回。",
        ) as tracker:
            track(IDX_PRE)
            set_pre('B')
            go_child('E', 'R')
            null_child('E', 'L')

        with self.voiceover(
                text="处理 E。E 的左孩子为空，给 E 建前驱线索：LTag 置 1，左指针指向前驱 pre，也就是 B。再看 pre 是 B，B 的右孩子是 E，不为空，走 else 分支，B 的 RTag 保持 0。然后 pre 指向 E。"
        ) as tracker:
            make_left_thread('E', -1.0)
            else_right()
            track(IDX_PRE)
            set_pre('E')

        with self.voiceover(
                text="E 的右子树为空，返回，E 出栈；B 的左右子树都处理完了，B 也返回出栈，回到根结点 A。"
        ) as tracker:
            null_child('E', 'R')
            leave()
            leave()

        with self.voiceover(
                text="现在处理 A。A 的左孩子是 B，不为空，走 else 分支，A 的 LTag 保持 0。pre 是 E，E 的右孩子为空，于是给 E 建后继线索：RTag 置 1，E 的右指针指向后继 A。然后 pre 指向 A。"
        ) as tracker:
            else_left('A')
            make_right_thread('A', -0.55)
            track(IDX_PRE)
            set_pre('A')

        with self.voiceover(
                text="递归线索化 A 的右子树，进入 C。C 的左孩子为空，给 C 建前驱线索：LTag 置 1，左指针指向前驱 pre，也就是 A。pre 是 A，A 的右孩子是 C，不为空，走 else 分支，A 的 RTag 保持 0。然后 pre 指向 C。"
        ) as tracker:
            go_child('C', 'R')
            null_child('C', 'L')
            make_left_thread('C', -1.1)
            else_right()
            track(IDX_PRE)
            set_pre('C')

        with self.voiceover(
                text="递归线索化 C 的右子树，进入 F。F 的左孩子为空，给 F 建前驱线索：LTag 置 1，左指针指向前驱 pre，也就是 C。pre 是 C，C 的右孩子是 F，不为空，走 else 分支，C 的 RTag 保持 0。然后 pre 指向 F。"
        ) as tracker:
            go_child('F', 'R')
            null_child('F', 'L')
            make_left_thread('F', -1.1)
            else_right()
            track(IDX_PRE)
            set_pre('F')

        with self.voiceover(
                text="F 的右子树为空，返回。接着 F、C、A 依次返回出栈，调用栈清空，递归全部结束。"
        ) as tracker:
            null_child('F', 'R')
            leave()
            leave()
            leave()

        track(None)

        # 主函数收尾（InOrderThreading）：把最后一个结点 F 与头结点相互链接
        with self.voiceover(
                text="最后，由主函数收尾。此时pre停在中序最后一个结点F上，它的右孩子为空，于是把F的RTag置为 1，让F的后继线索指向头结点；同时，把头结点的右指针，从原来指向自己，改为指向这个最后结点 F。至此，整棵子树的中序线索化全部完成。"
        ) as tracker:
            flip_tag('F', 'R', self.TEAL)
            f_succ = self.thread_arrow(pos['F'], pos['HEAD'], -2.4, self.TEAL)  # F 的后继线索 → 头结点
            head_rchild = self.thread_arrow(pos['HEAD'], pos['F'], -1.5, self.HEADC)  # 头结点 rchild → F
            drawn_threads.add(f_succ, head_rchild)
            self.play(Create(f_succ), run_time=0.6)
            self.play(Create(head_rchild), run_time=0.6)
            if self.pre_ptr is not None:
                self.play(FadeOut(self.pre_ptr), run_time=0.3)
            self.wait(max(0.2, tracker.duration - 2.1))

        # ============================================================
        # PHASE E — 结果与复杂度分析
        # ============================================================
        self.play(FadeOut(stack_title), FadeOut(stack_hint), FadeOut(code_block), run_time=0.5)

        with self.voiceover(
                text="现在，所有原本空着的指针，都变成了指向前驱或后继的线索，并通过头结点首尾相连，构成一个双向线索链表。沿着这些线索，既能从头结点顺着后继，按中序顺序 D B E A C F 正向遍历，也能从最后一个结点顺着前驱反向遍历。") as tracker:
            self.play(Indicate(drawn_threads, color=YELLOW, scale_factor=1.05), run_time=1.2)
            self.wait(max(0.2, tracker.duration - 1.2))

        result_label = Text("中序序列：D B E A C F", font_size=22, font="Microsoft YaHei", color=GREEN)
        # 复杂度用 Text 渲染（本机不支持 LaTeX/MathTex 的 dvi→svg 转换，用 Text 规避）
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          Text("O(n)", font_size=24, font="Consolas", color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           Text("O(h)", font_size=24, font="Consolas", color=YELLOW)).arrange(RIGHT, buff=0.1)
        summary = VGroup(result_label, time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        summary.move_to([3.6, -1.85, 0])  # 放到右下方空白处，避开头结点两侧的线索弧线

        with self.voiceover(
                text="整个过程本质是一次中序遍历，每个结点都恰好被访问、处理一次，因此时间复杂度为O恩。",
                subcaption="整个过程本质是一次中序遍历，每个结点都恰好被访问、处理一次，因此时间复杂度为O(n)。"
        ) as tracker:
            self.play(Write(result_label), run_time=0.6)
            self.play(FadeIn(time_box), run_time=max(0.4, tracker.duration - 0.6))

        with self.voiceover(
                text="算法使用了递归调用栈，栈的深度等于子树的高度h，子树退化成一条单链，空间复杂度就是O恩。",
                subcaption="算法使用了递归调用栈，栈的深度等于子树的高度h，子树退化成一条单链，空间复杂度就是O(n)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(
                text="以上就是以结点p为根的子树中序线索化算法的完整过程。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)