# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import numpy as np
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
class CopyBiTreeVideo(VoiceoverScene):
    # ===== 统一的结点 / 连线样式（与中序遍历视频保持一致，保证全章视觉统一、美观）=====
    NODE_R = 0.30

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
        # 初始化语音服务（与中序遍历递归算法视频完全一致的中文男声配置）
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE（标题，与中序遍历视频保持完全一致的版式）=====
        algo_title = Text("复制二叉树", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        subtitle = Text("通过先序遍历，复制得到一棵与原树完全相同的二叉树",
                        font_size=22, font="Microsoft YaHei", color=GRAY_A).next_to(algo_title, DOWN, buff=0.25)

        with self.voiceover(
            text="本节我们学习复制二叉树。它的含义是：通过先序遍历，利用一棵已有的二叉树，复制得到另外一棵与它完全相同的二叉树。",
            subcaption="本节我们学习复制二叉树。它的含义是：通过先序遍历，利用一棵已有的二叉树，复制得到另外一棵与它完全相同的二叉树。"
        ) as tracker:
            self.play(FadeIn(subtitle), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        self.play(FadeOut(subtitle), run_time=0.4)

        # ===== PHASE B — 例子引入（生活类比：照着一份“家谱”誊抄出一模一样的副本，揭示“先序复制”的含义）=====
        # 一棵 3 结点的小树（与主演示不同的例子）：甲(乙, 丙)
        epos = {'甲': np.array([-3.5, 0.6, 0]), '乙': np.array([-4.15, -0.35, 0]), '丙': np.array([-2.85, -0.35, 0])}
        cpos = {'甲': np.array([3.0, 0.6, 0]), '乙': np.array([2.35, -0.35, 0]), '丙': np.array([3.65, -0.35, 0])}

        paper_L = RoundedRectangle(corner_radius=0.12, width=2.9, height=3.0, color=GRAY_B,
                                   fill_color=GRAY_E, fill_opacity=0.25, stroke_width=2).move_to([-3.5, -0.1, 0])
        paper_R = RoundedRectangle(corner_radius=0.12, width=2.9, height=3.0, color=GRAY_B,
                                   fill_color=GRAY_E, fill_opacity=0.25, stroke_width=2).move_to([3.0, -0.1, 0])
        label_L = Text("原件（家谱）", font_size=20, font="Microsoft YaHei", color=BLUE_B).next_to(paper_L, UP, buff=0.12)
        label_R = Text("副本", font_size=20, font="Microsoft YaHei", color=GREEN_B).next_to(paper_R, UP, buff=0.12)

        e_edges = VGroup(self.edge(epos['甲'], epos['乙']), self.edge(epos['甲'], epos['丙']))
        e_nodes = {k: self.make_node(k, p) for k, p in epos.items()}
        e_tree = VGroup(e_edges, *e_nodes.values())

        with self.voiceover(
            text="先用一个生活中的例子来理解。把一棵二叉树想象成一份家谱，复制二叉树，就像照着这份家谱，重新誊抄出一份一模一样的副本。",
            subcaption="先用一个生活中的例子来理解。把一棵二叉树想象成一份家谱，复制二叉树，就像照着这份家谱，重新誊抄出一份一模一样的副本。"
        ) as tracker:
            self.play(FadeIn(paper_L), FadeIn(label_L), run_time=0.6)
            self.play(FadeIn(e_tree), run_time=0.6)
            self.play(FadeIn(paper_R), FadeIn(label_R), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 1.8))

        arrow = Arrow(start=[-1.9, -0.1, 0], end=[1.4, -0.1, 0], color=YELLOW, stroke_width=4, buff=0.1)
        arrow_tip = Text("先序复制", font_size=20, font="Microsoft YaHei", color=YELLOW).next_to(arrow, UP, buff=0.12)

        with self.voiceover(
            text="誊抄的顺序很关键，它遵循先序：先写下最上面的祖先，也就是根结点；再誊抄它的左边分支；最后誊抄右边分支。",
            subcaption="誊抄的顺序很关键，它遵循先序：先写下最上面的祖先，也就是根结点；再誊抄它的左边分支；最后誊抄右边分支。"
        ) as tracker:
            self.play(GrowArrow(arrow), FadeIn(arrow_tip), run_time=0.6)
            # 按先序 甲 → 乙 → 丙 把字母“誊抄”到右侧副本，并随之长出连线
            c_circles = {}
            order_keys = ['甲', '乙', '丙']
            for i, k in enumerate(order_keys):
                nc = Circle(radius=self.NODE_R, color=GREEN, fill_color=GREEN, fill_opacity=0.15,
                            stroke_width=2.5).move_to(cpos[k])
                c_circles[k] = nc
                flyer = e_nodes[k].label.copy()
                anims = [GrowFromCenter(nc)]
                if k != '甲':
                    anims.append(Create(self.edge(cpos['甲'], cpos[k], color=GRAY)))
                self.play(*anims, run_time=0.4)
                self.play(flyer.animate.move_to(cpos[k]).set_color(WHITE), run_time=0.4)
                self.add(flyer)
            self.wait(max(0.2, tracker.duration - 0.6 - len(order_keys) * 0.8))

        with self.voiceover(
            text="这种先根、再左、后右的顺序，正是先序遍历。复制二叉树就是借助先序遍历，一边遍历原树，一边新建结点。下面来看代码实现。",
            subcaption="这种先根、再左、后右的顺序，正是先序遍历。复制二叉树就是借助先序遍历，一边遍历原树，一边新建结点。下面来看代码实现。"
        ) as tracker:
            self.wait(tracker.duration)

        self.play(*[FadeOut(m) for m in self.mobjects if m is not logo and m is not algo_title], run_time=0.6)

        # ===== PHASE C — CODE BLOCK CONFIG（与中序遍历视频完全相同的代码板样式）=====
        c_lines = [
            "void Copy(BiTree T, BiTree &NewT) {",
            "    if (T == NULL) {",
            "        NewT = NULL; return;",
            "    } else {",
            "        NewT = new BiTNode;",
            "        NewT->data = T->data;",
            "        Copy(T->lchild, NewT->lchild);",
            "        Copy(T->rchild, NewT->rchild);",
            "    }",
            "}"
        ]
        # 代码行索引常量（便于追踪高亮）
        IDX_IF = 1     # if (T == NULL)              —— 第①步：判空
        IDX_NULL = 2   # NewT = NULL; return;        —— 第①步：空树，递归结束
        IDX_NEW = 4    # NewT = new BiTNode;         —— 第②(a)步：申请新结点空间
        IDX_DATA = 5   # NewT->data = T->data;       —— 第②(a)步：复制根结点
        IDX_LEFT = 6   # Copy(T->lchild, ...);       —— 第②(b)步：递归复制左子树
        IDX_RIGHT = 7  # Copy(T->rchild, ...);       —— 第②(c)步：递归复制右子树

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=13, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
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

        # ===== PHASE C2 — 原树 T、新树 NewT、调用栈面板 =====
        # 同一棵 5 结点二叉树：A(B(D,E), C)，先序输入 A B D # # E # # C # #
        # 先序遍历序列为 A B D E C —— 也正是复制结点的生成顺序
        opos = {
            'A': np.array([-3.15, 1.4, 0]),
            'B': np.array([-4.10, 0.3, 0]), 'C': np.array([-2.20, 0.3, 0]),
            'D': np.array([-4.60, -0.7, 0]), 'E': np.array([-3.65, -0.7, 0]),
        }
        npos = {
            'A': np.array([0.85, 1.4, 0]),
            'B': np.array([-0.10, 0.3, 0]), 'C': np.array([1.80, 0.3, 0]),
            'D': np.array([-0.60, -0.7, 0]), 'E': np.array([0.35, -0.7, 0]),
        }
        children = {'A': ('B', 'C'), 'B': ('D', 'E'),
                    'C': (None, None), 'D': (None, None), 'E': (None, None)}

        # ----- 原树 T（蓝色，开局即完整绘制）-----
        oedges = VGroup()
        for k, (lc, rc) in children.items():
            for ch in (lc, rc):
                if ch is not None:
                    oedges.add(self.edge(opos[k], opos[ch]))
        ocircles, olabels = {}, {}
        onode_group = VGroup()
        for k, p in opos.items():
            nd = self.make_node(k, p, color=BLUE)
            ocircles[k] = nd.circle
            olabels[k] = nd.label
            onode_group.add(nd)
        otree = VGroup(oedges, onode_group)
        otree_title = Text("原树 T", font_size=20, font="Microsoft YaHei", color=BLUE_B).move_to([-3.15, 2.2, 0])

        # ----- 新树 NewT（绿色，递归过程中逐个长出）-----
        ncircles, nlabels = {}, {}
        nedges = VGroup()
        ntree_title = Text("新树 NewT", font_size=20, font="Microsoft YaHei", color=GREEN_B).move_to([0.85, 2.2, 0])

        # “当前结点”活动指示环（始终套在原树正在处理的结点上）
        ring = Circle(radius=self.NODE_R + 0.1, color=YELLOW, stroke_width=4).move_to(opos['A'])

        # ----- 调用栈面板（左侧；相对上一版略向右移，避免贴近屏幕左边缘）-----
        STACK_X = -5.95
        STACK_BASE_Y = -1.0
        FRAME_H = 0.55
        stack_title = Text("调用栈", font_size=22, font="Microsoft YaHei", color=YELLOW).move_to([STACK_X, 1.9, 0])
        stack_hint = Text("（递归深度=树高）", font_size=12, font="Microsoft YaHei", color=GRAY).next_to(
            stack_title, DOWN, buff=0.12)

        def make_frame(node_key):
            box = RoundedRectangle(corner_radius=0.08, width=1.35, height=0.5, color=BLUE_D, fill_color=BLUE_D,
                                   fill_opacity=0.18, stroke_width=2)
            t = Text("Copy(%s)" % node_key, font_size=15, color=WHITE).move_to(box.get_center())
            return VGroup(box, t)

        with self.voiceover(
            text="左边蓝色的是已有的原树 T：根结点是 A，左子树由 B、D、E 组成，右子树是 C。右边绿色区域用来存放即将复制出的新树 NewT。",
            subcaption="左边蓝色的是已有的原树 T：根结点是 A，左子树由 B、D、E 组成，右子树是 C。右边绿色区域用来存放即将复制出的新树 NewT。"
        ) as tracker:
            self.play(FadeIn(code_block), FadeIn(otree), FadeIn(otree_title), FadeIn(ntree_title),
                      run_time=tracker.duration)

        with self.voiceover(
            text="最左侧的调用栈展示递归的层层调用，黄色圆环表示当前正在复制的结点。复制时按先序遍历的顺序：先根、再左、后右。",
            subcaption="最左侧的调用栈展示递归的层层调用，黄色圆环表示当前正在复制的结点。复制时按先序遍历的顺序：先根、再左、后右。"
        ) as tracker:
            self.play(FadeIn(stack_title), FadeIn(stack_hint), run_time=tracker.duration)

        # ===== PHASE D — 递归复制的辅助动画函数 =====
        path = []          # 当前调用链（结点 key）
        stack_mobs = []    # 调用栈中的帧 Mobject

        def push_frame(node_key):
            y = STACK_BASE_Y + len(stack_mobs) * FRAME_H
            fr = make_frame(node_key).move_to([STACK_X, y, 0])
            stack_mobs.append(fr)
            return fr

        def create_copy(node, parent):
            # 第②(a)步：NewT = new BiTNode; —— 申请新结点空间（空心圆先长出）
            self.play(*get_track_anims(IDX_NEW), run_time=0.3)
            nc = Circle(radius=self.NODE_R, color=GREEN, fill_color=GREEN, fill_opacity=0.15,
                        stroke_width=2.5).move_to(npos[node])
            ncircles[node] = nc
            anims = [GrowFromCenter(nc)]
            if parent is not None:   # 连到父结点对应的新结点上
                e = self.edge(npos[parent], npos[node], color=GRAY)
                nedges.add(e)
                anims.append(Create(e))
            self.play(*anims, run_time=0.4)
            # 第②(a)步：NewT->data = T->data; —— 复制根结点数据（字母从原树飞入新结点）
            self.play(*get_track_anims(IDX_DATA), run_time=0.3)
            flyer = olabels[node].copy()
            self.play(flyer.animate.move_to(npos[node]).set_color(WHITE),
                      Indicate(nc, color=GREEN, scale_factor=1.2), run_time=0.5)
            self.add(flyer)
            nlabels[node] = flyer

        def enter_root():
            # 主函数调用 Copy(A, NewT)，压栈，T 指向 A，判空为非空，复制根结点 A
            path.append('A')
            fr = push_frame('A')
            self.play(FadeIn(ring), FadeIn(fr, shift=UP * 0.2), run_time=0.5)
            self.play(*get_track_anims(IDX_IF), run_time=0.35)
            create_copy('A', None)

        def go_child(parent, child, side):
            # 第②(b)/(c)步：递归进入左/右孩子，压栈，环移动到孩子，判空为非空后复制该结点
            self.play(*get_track_anims(IDX_LEFT if side == 'L' else IDX_RIGHT), run_time=0.35)
            path.append(child)
            fr = push_frame(child)
            self.play(ring.animate.move_to(opos[child]), FadeIn(fr, shift=UP * 0.2), run_time=0.45)
            self.play(*get_track_anims(IDX_IF), run_time=0.3)
            create_copy(child, parent)

        def null_child(parent, side):
            # 第①步：递归进入空指针，if(T==NULL) 为真，NewT=NULL 后直接返回（不压栈、新树不长结点）
            self.play(*get_track_anims(IDX_LEFT if side == 'L' else IDX_RIGHT), run_time=0.3)
            self.play(*get_track_anims(IDX_IF), run_time=0.3)
            self.play(*get_track_anims(IDX_NULL), run_time=0.3)
            off = (LEFT * 0.45 if side == 'L' else RIGHT * 0.45) + DOWN * 0.62
            tag = Text("空，返回", font_size=14, font="Microsoft YaHei", color=GRAY).move_to(opos[parent] + off)
            self.play(FadeIn(tag, shift=DOWN * 0.1), run_time=0.3)
            self.play(FadeOut(tag), run_time=0.25)

        def leave():
            # 当前结点的根、左、右全部复制完毕，函数返回，从调用栈弹出，环退回父结点
            path.pop()
            fr = stack_mobs.pop()
            self.play(FadeOut(fr, shift=UP * 0.2), run_time=0.3)
            if path:
                self.play(ring.animate.move_to(opos[path[-1]]), run_time=0.35)
            else:
                self.play(FadeOut(ring), run_time=0.3)

        # ===== PHASE D2 — 递归复制过程（场景化讲解，对应算法步骤 ①②(a)(b)(c)）=====
        with self.voiceover(
            text="主函数调用 Copy，传入原树根结点 A。它被压入调用栈。判断 T 不为空，于是申请一个新结点，并把 A 的数据复制过去，这就是新树的根。",
            subcaption="主函数调用 Copy，传入原树根结点 A。它被压入调用栈。判断 T 不为空，于是申请一个新结点，并把 A 的数据复制过去，这就是新树的根。"
        ) as tracker:
            enter_root()

        with self.voiceover(
            text="接着递归复制左子树：从 A 进入左孩子 B，B 非空，新建结点并复制 B，作为新树根的左孩子；再从 B 进入左孩子 D，同样新建并复制 D。",
            subcaption="接着递归复制左子树：从 A 进入左孩子 B，B 非空，新建结点并复制 B，作为新树根的左孩子；再从 B 进入左孩子 D，同样新建并复制 D。"
        ) as tracker:
            go_child('A', 'B', 'L')
            go_child('B', 'D', 'L')

        with self.voiceover(
            text="D 的左孩子为空，判空为真，令新结点的左指针为空并立即返回；D 的右孩子也为空，同样返回。D 这一层全部复制完毕，函数返回，从栈中弹出。",
            subcaption="D 的左孩子为空，判空为真，令新结点的左指针为空并立即返回；D 的右孩子也为空，同样返回。D 这一层全部复制完毕，函数返回，从栈中弹出。"
        ) as tracker:
            null_child('D', 'L')
            null_child('D', 'R')
            leave()

        with self.voiceover(
            text="回到 B，递归复制它的右子树，进入 E，新建并复制 E；E 的左右孩子都为空并返回。E 复制完毕出栈，B 的左右子树都已复制完，B 也出栈。",
            subcaption="回到 B，递归复制它的右子树，进入 E，新建并复制 E；E 的左右孩子都为空并返回。E 复制完毕出栈，B 的左右子树都已复制完，B 也出栈。"
        ) as tracker:
            go_child('B', 'E', 'R')
            null_child('E', 'L')
            null_child('E', 'R')
            leave()
            leave()

        with self.voiceover(
            text="最后递归复制 A 的右子树，进入 C，新建并复制 C，作为新树根的右孩子；C 的左右孩子都为空并返回，C 出栈；最后 A 也返回出栈，调用栈清空。",
            subcaption="最后递归复制 A 的右子树，进入 C，新建并复制 C，作为新树根的右孩子；C 的左右孩子都为空并返回，C 出栈；最后 A 也返回出栈，调用栈清空。"
        ) as tracker:
            go_child('A', 'C', 'R')
            null_child('C', 'L')
            null_child('C', 'R')
            leave()
            leave()

        # ===== PHASE D3 — 结果展示：新树与原树完全相同 =====
        self.play(*get_track_anims(None), run_time=0.4)
        ntree_all = VGroup(nedges, *[ncircles[k] for k in npos], *[nlabels[k] for k in npos])
        with self.voiceover(
            text="现在，整棵新树 NewT 已经构造完成。可以看到，它和原树 T 的结构、数据完全一致，复制成功。",
            subcaption="现在，整棵新树 NewT 已经构造完成。可以看到，它和原树 T 的结构、数据完全一致，复制成功。"
        ) as tracker:
            self.play(Indicate(otree, color=YELLOW, scale_factor=1.05),
                      Indicate(ntree_all, color=YELLOW, scale_factor=1.05), run_time=1.0)
            self.wait(max(0.3, tracker.duration - 1.0))

        # ===== PHASE E — COMPLEXITY（复杂度看板）=====
        self.play(FadeOut(stack_title), FadeOut(stack_hint), run_time=0.4)

        order_label = Text("复制顺序（先序）：A B D E C", font_size=22, font="Microsoft YaHei", color=GREEN)
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        summary = VGroup(order_label, time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        summary.move_to(DOWN * 2.7 + LEFT * 1.0)

        with self.voiceover(
            text="结点的复制顺序，正是原树的先序遍历序列：A、B、D、E、C。",
            subcaption="结点的复制顺序，正是原树的先序遍历序列：A、B、D、E、C。"
        ) as tracker:
            self.play(Write(order_label), run_time=max(0.5, tracker.duration))

        with self.voiceover(
            text="复制过程中，每个结点都恰好被访问一次，所以时间复杂度为 O(n)。",
            subcaption="复制过程中，每个结点都恰好被访问一次，所以时间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
            text="所需的辅助空间是递归调用栈的最大容量，也就是树的深度。最坏情况下二叉树退化成一条单链，深度为 n，因此空间复杂度也是 O(n)。",
            subcaption="所需的辅助空间是递归调用栈的最大容量，也就是树的深度。最坏情况下二叉树退化成一条单链，深度为 n，因此空间复杂度也是 O(n)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(
            text="以上就是复制二叉树算法的完整过程。",
            subcaption="以上就是复制二叉树算法的完整过程。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)