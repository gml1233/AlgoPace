# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import numpy as np
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
class NodeCountVideo(VoiceoverScene):
    # ===== 统一的结点 / 连线样式（与复制二叉树、中序遍历视频保持一致，保证全章视觉统一、美观）=====
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
        # 初始化语音服务（与复制二叉树视频完全一致的中文男声配置）
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE（标题，与复制二叉树视频保持完全一致的版式）=====
        algo_title = Text("统计二叉树的结点个数", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        subtitle = Text("通过递归遍历，统计一棵二叉树中全部结点的总个数",
                        font_size=22, font="Microsoft YaHei", color=GRAY_A).next_to(algo_title, DOWN, buff=0.25)

        with self.voiceover(
            text="本节我们学习统计二叉树的结点个数。它的含义是：通过递归遍历一棵二叉树，把所有结点数一遍，得到结点的总个数。",
            subcaption="本节我们学习统计二叉树的结点个数。它的含义是：通过递归遍历一棵二叉树，把所有结点数一遍，得到结点的总个数。"
        ) as tracker:
            self.play(FadeIn(subtitle), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        self.play(FadeOut(subtitle), run_time=0.4)

        # ===== PHASE B — 例子引入（生活类比：统计公司总人数，每位主管上报"我这条线共有几人"）=====
        # 一棵 3 结点的小组织架构：总(甲, 乙)
        epos = {'总': np.array([-0.2, 1.0, 0]), '甲': np.array([-1.35, -0.15, 0]), '乙': np.array([0.95, -0.15, 0])}

        board = RoundedRectangle(corner_radius=0.12, width=3.9, height=2.9, color=GRAY_B,
                                 fill_color=GRAY_E, fill_opacity=0.25, stroke_width=2).move_to([-0.2, 0.35, 0])
        board_title = Text("公司组织架构（统计总人数）", font_size=20, font="Microsoft YaHei",
                           color=BLUE_B).next_to(board, UP, buff=0.12)

        e_edges = VGroup(self.edge(epos['总'], epos['甲']), self.edge(epos['总'], epos['乙']))
        e_nodes = {k: self.make_node(k, p) for k, p in epos.items()}
        e_tree = VGroup(e_edges, *e_nodes.values())

        with self.voiceover(
            text="先用一个生活中的例子来理解。想象要统计一家公司一共有多少人：每位主管只负责上报一件事——我这条线上，一共有多少人。",
            subcaption="先用一个生活中的例子来理解。想象要统计一家公司一共有多少人：每位主管只负责上报一件事——我这条线上，一共有多少人。"
        ) as tracker:
            self.play(FadeIn(board), FadeIn(board_title), run_time=0.6)
            self.play(FadeIn(e_tree), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 1.2))

        # 统计规则提示
        rule = Text("这条线的人数 = 左边下属人数 + 右边下属人数 + 我自己 1 人",
                    font_size=20, font="Microsoft YaHei", color=YELLOW).next_to(board, DOWN, buff=0.35)

        bubble_jia = Text("1 人", font_size=20, font="Microsoft YaHei", color=GREEN).next_to(e_nodes['甲'], DOWN, buff=0.15)
        bubble_yi = Text("1 人", font_size=20, font="Microsoft YaHei", color=GREEN).next_to(e_nodes['乙'], DOWN, buff=0.15)
        arrow_sum = Arrow(start=epos['总'] + RIGHT * 0.4, end=[2.4, 1.0, 0], color=YELLOW, stroke_width=4, buff=0.1)
        bubble_zong = Text("1 + 1 + 1 = 3 人", font_size=22, font="Microsoft YaHei",
                           color=YELLOW).move_to([3.7, 1.0, 0])

        with self.voiceover(
            text="统计的规则是：我这条线的人数，等于左边下属那条线的人数，加上右边下属那条线的人数，再加上我自己一个人。",
            subcaption="统计的规则是：我这条线的人数，等于左边下属那条线的人数，加上右边下属那条线的人数，再加上我自己一个人。"
        ) as tracker:
            self.play(FadeIn(rule), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
            text="甲和乙是最底层的员工，手下没有下属，所以他们各自只算自己一人。总经理把两边上报的人数加起来，再加上自己：一加一再加一，等于三，这就是全公司的总人数。",
            subcaption="甲和乙是最底层的员工，手下没有下属，所以他们各自只算自己一人。总经理把两边上报的人数加起来，再加上自己：一加一再加一，等于三，这就是全公司的总人数。"
        ) as tracker:
            self.play(FadeIn(bubble_jia, shift=UP * 0.1), FadeIn(bubble_yi, shift=UP * 0.1), run_time=0.6)
            self.play(GrowArrow(arrow_sum), FadeIn(bubble_zong), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 1.2))

        with self.voiceover(
            text="这种由下往上、层层汇总的思路，正是统计二叉树结点个数的递归思想：结点总数等于左子树的结点数加上右子树的结点数，再加根结点这一个。空树里没有结点，就返回零。下面来看代码实现。",
            subcaption="这种由下往上、层层汇总的思路，正是统计二叉树结点个数的递归思想：结点总数等于左子树的结点数加上右子树的结点数，再加根结点这一个。空树里没有结点，就返回零。下面来看代码实现。"
        ) as tracker:
            self.wait(tracker.duration)

        self.play(*[FadeOut(m) for m in self.mobjects if m is not logo and m is not algo_title], run_time=0.6)

        # ===== PHASE C — CODE BLOCK CONFIG（与复制二叉树视频完全相同的代码板样式）=====
        c_lines = [
            "int NodeCount(BiTree T) {",
            "    if (T == NULL)",
            "        return 0;",
            "    else",
            "        return NodeCount(T->lchild)",
            "             + NodeCount(T->rchild)",
            "             + 1;",
            "}"
        ]
        # 代码行索引常量（便于追踪高亮）
        IDX_IF = 1     # if (T == NULL)                —— 第①步：判空
        IDX_RET0 = 2   # return 0;                     —— 第①步：空树返回 0，递归结束
        IDX_ELSE = 3   # else
        IDX_LEFT = 4   # return NodeCount(T->lchild)   —— 第②步：递归统计左子树
        IDX_RIGHT = 5  #      + NodeCount(T->rchild)   —— 第②步：递归统计右子树
        IDX_PLUS1 = 6  #      + 1;                     —— 第②步：再加根结点这一个

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

        # ===== PHASE C2 — 二叉树 T、计数徽章、调用栈面板 =====
        # 一棵 5 结点二叉树：A(B(D,E), C)，先序输入 A B D # # E # # C # #
        # 每个结点旁的金色徽章表示"以该结点为根的子树的结点个数"，由下往上逐层算出
        opos = {
            'A': np.array([-1.9, 1.45, 0]),
            'B': np.array([-3.0, 0.35, 0]), 'C': np.array([-0.8, 0.35, 0]),
            'D': np.array([-3.6, -0.75, 0]), 'E': np.array([-2.4, -0.75, 0]),
        }
        children = {'A': ('B', 'C'), 'B': ('D', 'E'),
                    'C': (None, None), 'D': (None, None), 'E': (None, None)}

        # ----- 二叉树 T（蓝色，开局即完整绘制）-----
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
        otree_title = Text("二叉树 T", font_size=20, font="Microsoft YaHei", color=BLUE_B).move_to([-1.9, 2.35, 0])

        # “当前结点”活动指示环（始终套在正在处理的结点上）
        ring = Circle(radius=self.NODE_R + 0.1, color=YELLOW, stroke_width=4).move_to(opos['A'])

        # ----- 计数徽章（金色小圆 + 数字，表示子树结点个数）-----
        badges = {}

        def make_badge(node_key, count):
            p = opos[node_key] + RIGHT * 0.44 + UP * 0.34
            circ = Circle(radius=0.18, color=GOLD, fill_color=GOLD, fill_opacity=1.0, stroke_width=1.5).move_to(p)
            num = Text(str(count), font_size=17, color=BLACK, weight=BOLD).move_to(p)
            return VGroup(circ, num)

        # ----- 底部“递归计算区”：把 左+右+1 的算式实时显示出来 -----
        calc_pos = np.array([-1.1, -2.0, 0])
        calc_hint = Text("结点总数 = 左子树结点数 + 右子树结点数 + 1",
                         font_size=20, font="Microsoft YaHei", color=GRAY_A).move_to([-1.1, -1.5, 0])
        self.calc_line = Text("开始递归统计……", font_size=20, font="Microsoft YaHei",
                              color=GRAY_A).move_to(calc_pos)

        # ----- 调用栈面板（左侧）-----
        STACK_X = -5.8
        STACK_BASE_Y = -0.9
        FRAME_H = 0.6
        stack_title = Text("调用栈", font_size=22, font="Microsoft YaHei", color=YELLOW).move_to([STACK_X, 1.9, 0])
        stack_hint = Text("（递归深度=树高）", font_size=12, font="Microsoft YaHei", color=GRAY).next_to(
            stack_title, DOWN, buff=0.12)

        def make_frame(node_key):
            box = RoundedRectangle(corner_radius=0.08, width=1.9, height=0.5, color=BLUE_D, fill_color=BLUE_D,
                                   fill_opacity=0.18, stroke_width=2)
            t = Text("NodeCount(%s)" % node_key, font_size=14, color=WHITE).move_to(box.get_center())
            return VGroup(box, t)

        with self.voiceover(
            text="屏幕中间蓝色的是一棵二叉树 T：根结点是 A，左子树由 B、D、E 组成，右子树是 C，一共五个结点。我们要用递归把它们数出来。",
            subcaption="屏幕中间蓝色的是一棵二叉树 T：根结点是 A，左子树由 B、D、E 组成，右子树是 C，一共五个结点。我们要用递归把它们数出来。"
        ) as tracker:
            self.play(FadeIn(code_block), FadeIn(otree), FadeIn(otree_title), run_time=tracker.duration)

        with self.voiceover(
            text="最左侧的调用栈展示递归的层层调用，黄色圆环表示当前正在统计的结点，结点右上角的金色徽章记录以它为根的子树一共有多少个结点。统计按先左、后右、最后加根的顺序进行。",
            subcaption="最左侧的调用栈展示递归的层层调用，黄色圆环表示当前正在统计的结点，结点右上角的金色徽章记录以它为根的子树一共有多少个结点。统计按先左、后右、最后加根的顺序进行。"
        ) as tracker:
            self.play(FadeIn(stack_title), FadeIn(stack_hint), FadeIn(calc_hint), FadeIn(self.calc_line),
                      run_time=tracker.duration)

        # ===== PHASE D — 递归统计的辅助动画函数 =====
        path = []          # 当前调用链（结点 key）
        stack_mobs = []    # 调用栈中的帧 Mobject

        def push_frame(node_key):
            y = STACK_BASE_Y + len(stack_mobs) * FRAME_H
            fr = make_frame(node_key).move_to([STACK_X, y, 0])
            stack_mobs.append(fr)
            return fr

        def enter_root():
            # 主函数调用 NodeCount(A)，压栈，T 指向 A，判空为非空
            path.append('A')
            fr = push_frame('A')
            self.play(FadeIn(ring), FadeIn(fr, shift=UP * 0.2), run_time=0.5)
            self.play(*get_track_anims(IDX_IF), run_time=0.35)

        def go_child(parent, child, side):
            # 第②步：递归进入左/右孩子，压栈，环移动到孩子，判空为非空
            self.play(*get_track_anims(IDX_LEFT if side == 'L' else IDX_RIGHT), run_time=0.35)
            path.append(child)
            fr = push_frame(child)
            self.play(ring.animate.move_to(opos[child]), FadeIn(fr, shift=UP * 0.2), run_time=0.45)
            self.play(*get_track_anims(IDX_IF), run_time=0.3)

        def null_child(parent, side):
            # 第①步：递归进入空指针，if(T==NULL) 为真，return 0（不压栈、不产生徽章）
            self.play(*get_track_anims(IDX_LEFT if side == 'L' else IDX_RIGHT), run_time=0.3)
            self.play(*get_track_anims(IDX_IF), run_time=0.3)
            self.play(*get_track_anims(IDX_RET0), run_time=0.3)
            off = (LEFT * 0.5 if side == 'L' else RIGHT * 0.5) + DOWN * 0.62
            tag = Text("空，返回 0", font_size=14, font="Microsoft YaHei", color=GRAY).move_to(opos[parent] + off)
            self.play(FadeIn(tag, shift=DOWN * 0.1), run_time=0.3)
            self.play(FadeOut(tag), run_time=0.25)

        def settle(node, lc, rc, total):
            # 左右子树都已统计完毕，执行 + 1 并返回：更新算式、长出徽章、弹栈、环退回父结点
            # （B、A 等内部结点在其子结点返回时指针已停在 +1 行，此时高亮无变化，跳过空动画）
            plus_anims = get_track_anims(IDX_PLUS1)
            if plus_anims:
                self.play(*plus_anims, run_time=0.3)
            new_calc = Text("NodeCount(%s) = %d + %d + 1 = %d" % (node, lc, rc, total),
                            font_size=21, font="Consolas", color=YELLOW).move_to(calc_pos)
            self.play(FadeTransform(self.calc_line, new_calc), run_time=0.5)
            self.calc_line = new_calc
            bdg = make_badge(node, total)
            badges[node] = bdg
            self.play(GrowFromCenter(bdg), Indicate(ocircles[node], color=GOLD, scale_factor=1.2), run_time=0.5)
            path.pop()
            fr = stack_mobs.pop()
            self.play(FadeOut(fr, shift=UP * 0.2), run_time=0.3)
            if path:
                self.play(ring.animate.move_to(opos[path[-1]]), run_time=0.35)
            else:
                self.play(FadeOut(ring), run_time=0.3)

        # ===== PHASE D2 — 递归统计过程（场景化讲解，对应算法步骤 ①②）=====
        with self.voiceover(
            text="主函数调用 NodeCount，传入根结点 A。A 被压入调用栈。判断 T 不为空，说明不是空树，于是转到 else 分支，准备统计以 A 为根的整棵树的结点个数。",
            subcaption="主函数调用 NodeCount，传入根结点 A。A 被压入调用栈。判断 T 不为空，说明不是空树，于是转到 else 分支，准备统计以 A 为根的整棵树的结点个数。"
        ) as tracker:
            enter_root()

        with self.voiceover(
            text="要算 A 的结点数，得先统计它的左子树。递归进入左孩子 B，B 不为空；再从 B 递归进入它的左孩子 D，D 也不为空。",
            subcaption="要算 A 的结点数，得先统计它的左子树。递归进入左孩子 B，B 不为空；再从 B 递归进入它的左孩子 D，D 也不为空。"
        ) as tracker:
            go_child('A', 'B', 'L')
            go_child('B', 'D', 'L')

        with self.voiceover(
            text="D 是叶子结点。它的左孩子为空，返回 0；右孩子也为空，返回 0。于是 D 的结点数等于 0 加 0 再加 1，也就是 1。D 统计完毕，返回 1 并从栈中弹出。",
            subcaption="D 是叶子结点。它的左孩子为空，返回 0；右孩子也为空，返回 0。于是 D 的结点数等于 0 加 0 再加 1，也就是 1。D 统计完毕，返回 1 并从栈中弹出。"
        ) as tracker:
            null_child('D', 'L')
            null_child('D', 'R')
            settle('D', 0, 0, 1)

        with self.voiceover(
            text="回到 B，接着统计它的右子树，递归进入右孩子 E。E 同样是叶子，左右孩子都为空各返回 0，所以 E 的结点数是 0 加 0 加 1，等于 1。E 返回 1 并出栈。",
            subcaption="回到 B，接着统计它的右子树，递归进入右孩子 E。E 同样是叶子，左右孩子都为空各返回 0，所以 E 的结点数是 0 加 0 加 1，等于 1。E 返回 1 并出栈。"
        ) as tracker:
            go_child('B', 'E', 'R')
            null_child('E', 'L')
            null_child('E', 'R')
            settle('E', 0, 0, 1)

        with self.voiceover(
            text="现在 B 的左子树返回 1，右子树返回 1，再加上 B 自己这一个结点。B 的结点数等于 1 加 1 加 1，等于 3。B 统计完毕，返回 3 并出栈。",
            subcaption="现在 B 的左子树返回 1，右子树返回 1，再加上 B 自己这一个结点。B 的结点数等于 1 加 1 加 1，等于 3。B 统计完毕，返回 3 并出栈。"
        ) as tracker:
            settle('B', 1, 1, 3)

        with self.voiceover(
            text="回到根结点 A，开始统计它的右子树，递归进入右孩子 C。C 是叶子，左右孩子都为空返回 0，C 的结点数为 0 加 0 加 1，等于 1，返回 1 并出栈。",
            subcaption="回到根结点 A，开始统计它的右子树，递归进入右孩子 C。C 是叶子，左右孩子都为空返回 0，C 的结点数为 0 加 0 加 1，等于 1，返回 1 并出栈。"
        ) as tracker:
            go_child('A', 'C', 'R')
            null_child('C', 'L')
            null_child('C', 'R')
            settle('C', 0, 0, 1)

        with self.voiceover(
            text="最后回到 A。左子树 B 返回 3，右子树 C 返回 1，再加上 A 自己一个结点。A 的结点数等于 3 加 1 加 1，等于 5。A 返回 5，调用栈清空，递归结束。",
            subcaption="最后回到 A。左子树 B 返回 3，右子树 C 返回 1，再加上 A 自己一个结点。A 的结点数等于 3 加 1 加 1，等于 5。A 返回 5，调用栈清空，递归结束。"
        ) as tracker:
            settle('A', 3, 1, 5)

        # ===== PHASE D3 — 结果展示：结点总数 = 5 =====
        end_anims = get_track_anims(None)
        if end_anims:
            self.play(*end_anims, run_time=0.4)
        all_badges = VGroup(*[badges[k] for k in badges])
        with self.voiceover(
            text="根结点 A 返回的 5，就是整棵二叉树的结点总数。我们数一下：A、B、C、D、E，正好五个结点，结果完全正确。",
            subcaption="根结点 A 返回的 5，就是整棵二叉树的结点总数。我们数一下：A、B、C、D、E，正好五个结点，结果完全正确。"
        ) as tracker:
            self.play(Indicate(otree, color=YELLOW, scale_factor=1.05),
                      Indicate(all_badges, color=YELLOW, scale_factor=1.15), run_time=1.0)
            self.wait(max(0.3, tracker.duration - 1.0))

        # ===== PHASE E — COMPLEXITY（复杂度看板）=====
        self.play(FadeOut(stack_title), FadeOut(stack_hint), FadeOut(calc_hint), FadeOut(self.calc_line), run_time=0.4)

        visit_label = Text("每个结点恰好被访问一次（共 5 个）", font_size=22, font="Microsoft YaHei", color=GREEN)
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(h)", font_size=24, color=YELLOW),
                           Text("（树高 h，最坏退化成单链时为 ", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(n)", font_size=24, color=YELLOW),
                           Text("）", font_size=22, font="Microsoft YaHei", color=YELLOW)).arrange(RIGHT, buff=0.08)
        summary = VGroup(visit_label, time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        summary.move_to(DOWN * 1.85 + LEFT * 0.3)

        with self.voiceover(
            text="来分析一下复杂度。递归会访问到每一个结点，并且每个结点都恰好被访问一次，所以时间复杂度为 O n。",
            subcaption="来分析一下复杂度。递归会访问到每一个结点，并且每个结点都恰好被访问一次，所以时间复杂度为 O(n)。"
        ) as tracker:
            self.play(Write(visit_label), run_time=max(0.5, tracker.duration - 0.3))
            self.play(FadeIn(time_box), run_time=0.3)

        with self.voiceover(
            text="空间复杂度主要由递归调用栈决定，栈的最大深度等于树的高度 h，因此空间复杂度为 O h。最坏情况下，二叉树退化成一条单链，高度 h 等于 n，此时空间复杂度为 O n。",
            subcaption="空间复杂度主要由递归调用栈决定，栈的最大深度等于树的高度 h，因此空间复杂度为 O(h)。最坏情况下，二叉树退化成一条单链，高度 h 等于 n，此时空间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(
            text="以上就是统计二叉树结点个数算法的完整过程。",
            subcaption="以上就是统计二叉树结点个数算法的完整过程。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)