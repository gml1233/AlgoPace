# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import numpy as np
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
class TreeDepthVideo(VoiceoverScene):
    # ===== 统一的结点 / 连线样式（与中序遍历、复制二叉树等视频保持一致，保证全章视觉统一、美观）=====
    NODE_R = 0.34

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
        # 初始化语音服务（与本章其它视频完全一致的中文男声配置）
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE（标题，与本章其它视频保持一致的版式）=====
        algo_title = Text("计算二叉树的深度", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        subtitle = Text("通过后序遍历，比较左右子树的深度，取较大者加一",
                        font_size=22, font="Microsoft YaHei", color=GRAY_A).next_to(algo_title, DOWN, buff=0.22)

        with self.voiceover(
            text="本节我们学习如何计算二叉树的深度，该算法通过后序遍历，比较左右子树的深度，取较大者再加1，来确定树中结点的最大层次。"
        ) as tracker:
            self.play(FadeIn(subtitle), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        self.play(FadeOut(subtitle), run_time=0.4)

        # ===== PHASE B — 例子引入（直观类比：深度就是“层数”，等于较深子树的层数再加根结点这一层）=====
        # 一棵 4 结点小树（与主演示不同的例子）：甲(乙(丁), 丙)
        spos = {'甲': np.array([-0.3, 1.7, 0]), '乙': np.array([-1.7, 0.35, 0]),
                '丙': np.array([1.1, 0.35, 0]), '丁': np.array([-2.5, -1.0, 0])}
        sedges = VGroup(self.edge(spos['甲'], spos['乙']), self.edge(spos['甲'], spos['丙']),
                        self.edge(spos['乙'], spos['丁']))
        snodes = {k: self.make_node(k, p) for k, p in spos.items()}
        stree = VGroup(sedges, *snodes.values())

        with self.voiceover(text="先用一个例子建立直观印象。这里有一棵二叉树。",
                            subcaption="先用一个例子建立直观印象。这里有一棵二叉树。") as tracker:
            self.play(FadeIn(stree), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        # 三条“层次”横线，揭示深度就是最大层数
        level_ys = [1.7, 0.35, -1.0]
        level_lines = VGroup()
        level_tags = VGroup()
        for idx, y in enumerate(level_ys):
            ln = DashedLine(np.array([-3.4, y, 0]), np.array([2.2, y, 0]), color=GRAY_B,
                            stroke_width=1.5, dash_length=0.1)
            tag = Text("第%d层" % (idx + 1), font_size=16, font="Microsoft YaHei", color=GRAY_A).next_to(
                ln, RIGHT, buff=0.15)
            level_lines.add(ln)
            level_tags.add(tag)

        with self.voiceover(
            text="所谓深度，就是把结点分层。根结点在第1层，它的孩子在第2层，一层一层往下数。"
        ) as tracker:
            for ln, tag in zip(level_lines, level_tags):
                self.play(Create(ln), FadeIn(tag), run_time=0.35)
            self.wait(max(0.1, tracker.duration - 3 * 0.35))

        with self.voiceover(
            text="这棵树最深的一条路径经过3层，所以它的深度就是3。"
        ) as tracker:
            self.play(Indicate(VGroup(snodes['甲'], snodes['乙'], snodes['丁']), color=YELLOW, scale_factor=1.12),
                      run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))

        self.play(FadeOut(level_lines), FadeOut(level_tags), run_time=0.4)

        with self.voiceover(
            text="怎么用递归求深度呢？关键在于：一棵树的深度，等于它左右两棵子树里较深的那一个，再加上根结点自己这一层。"
        ) as tracker:
            left_box = SurroundingRectangle(VGroup(snodes['乙'], snodes['丁']), color=BLUE, buff=0.12)
            right_box = SurroundingRectangle(snodes['丙'], color=GREEN, buff=0.12)
            left_lab = Text("左子树深度 2", font_size=16, font="Microsoft YaHei", color=BLUE_B).next_to(
                left_box, DOWN, buff=0.12)
            right_lab = Text("右子树深度 1", font_size=16, font="Microsoft YaHei", color=GREEN_B).next_to(
                right_box, UP, buff=0.12)
            self.play(Create(left_box), FadeIn(left_lab), run_time=0.6)
            self.play(Create(right_box), FadeIn(right_lab), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
            text="这里左子树深度是2，右子树深度是1，取较大的2，再加1，正好得到整棵树的深度3。"
        ) as tracker:
            formula0 = Text("max(2, 1) + 1 = 3", font_size=26, font="Consolas", color=GOLD).move_to([0.2, -2.4, 0])
            self.play(Write(formula0), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(text="下面来看代码如何实现。", subcaption="下面来看代码如何实现。") as tracker:
            self.wait(tracker.duration)

        self.play(FadeOut(stree), FadeOut(left_box), FadeOut(right_box),
                  FadeOut(left_lab), FadeOut(right_lab), FadeOut(formula0), run_time=0.6)

        # ===== PHASE C — CODE BLOCK CONFIG（与本章其它视频完全相同的代码板样式）=====
        c_lines = [
            "int Depth(BiTree T) {",
            "    if (T == NULL)",
            "        return 0;",
            "    int m = Depth(T->lchild);",
            "    int n = Depth(T->rchild);",
            "    if (m > n)",
            "        return m + 1;",
            "    else",
            "        return n + 1;",
            "}"
        ]
        # 代码行索引常量（便于追踪高亮）
        IDX_IF0 = 1    # if (T == NULL)              —— 第①步：判空
        IDX_RET0 = 2   # return 0;                   —— 第①步：空树深度为 0，递归结束
        IDX_LEFT = 3   # int m = Depth(T->lchild);   —— 第②(a)步：递归求左子树深度 m
        IDX_RIGHT = 4  # int n = Depth(T->rchild);   —— 第②(b)步：递归求右子树深度 n
        IDX_CMP = 5    # if (m > n)                  —— 第②(c)步：比较 m 与 n
        IDX_RETM = 6   # return m + 1;               —— m 较大，深度 = m + 1
        IDX_RETN = 8   # return n + 1;               —— n 较大（或相等），深度 = n + 1

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

        def hl(idx, rt=0.35):
            """把代码追踪高亮切换到第 idx 行。"""
            a = get_track_anims(idx)
            if a:
                self.play(*a, run_time=rt)

        # ===== PHASE C2 — 二叉树、调用栈面板 =====
        # 主演示二叉树（对应本节 md 指定示例）：A(B, C(D))，期望深度 3
        #        A
        #       / \
        #      B   C
        #         /
        #        D
        pos = {
            'A': np.array([-0.5, 2.0, 0]),
            'B': np.array([-2.2, 0.5, 0]),
            'C': np.array([1.2, 0.5, 0]),
            'D': np.array([0.3, -0.9, 0]),
        }
        children = {'A': ('B', 'C'), 'B': (None, None), 'C': ('D', None), 'D': (None, None)}
        parent_of = {'B': 'A', 'C': 'A', 'D': 'C'}
        # 每个结点的深度徽标位置（放在不与连线、兄弟结点冲突的一侧）
        badge_off = {
            'A': np.array([0.5, 0.35, 0]),
            'B': np.array([-0.55, 0.1, 0]),
            'C': np.array([0.55, 0.15, 0]),
            'D': np.array([-0.62, 0.02, 0]),
        }

        # 连线只画到圆的边缘（不插入结点内部），空子树不在树上绘制任何结点
        edges = VGroup()
        for k, (lc, rc) in children.items():
            for ch in (lc, rc):
                if ch is not None:
                    edges.add(self.edge(pos[k], pos[ch]))

        circles = {}
        labels = {}
        node_group = VGroup()
        for k, p in pos.items():
            nd = self.make_node(k, p)
            circles[k] = nd.circle
            labels[k] = nd.label
            node_group.add(nd)
        tree_group = VGroup(edges, node_group)

        # “当前结点”活动指示环
        ring = Circle(radius=self.NODE_R + 0.1, color=YELLOW, stroke_width=4).move_to(pos['A'])

        # ----- 调用栈面板（左侧）：每个栈帧实时显示 结点名 + 局部变量 m、n -----
        STACK_X = -5.6
        STACK_BASE_Y = -1.3
        FRAME_H = 0.85
        stack_title = Text("递归调用栈", font_size=22, font="Microsoft YaHei", color=YELLOW).move_to([STACK_X, 1.55, 0])
        stack_hint = Text("（栈帧记录 m、n）", font_size=13, font="Microsoft YaHei", color=GRAY).next_to(
            stack_title, DOWN, buff=0.12)

        frame_of = {}   # node -> 栈帧 VGroup
        mn_mob = {}     # node -> 该栈帧中 "m=? n=?" 文本（可被更新）
        mval = {}       # node -> 当前 m 值（None 表示尚未算出）
        nval = {}       # node -> 当前 n 值
        stack_mobs = []  # 栈中活动帧（用于计算入栈高度）
        path = []        # 当前调用链

        def make_frame(node, center):
            box = RoundedRectangle(corner_radius=0.08, width=1.9, height=0.72, color=BLUE_D, fill_color=BLUE_D,
                                   fill_opacity=0.18, stroke_width=2)
            title = Text("Depth(%s)" % node, font_size=15, color=WHITE)
            mn = Text("m=?  n=?", font_size=14, font="Consolas", color=GRAY_A)
            inner = VGroup(title, mn).arrange(DOWN, buff=0.06)
            grp = VGroup(box, inner).move_to(center)
            mn_mob[node] = mn
            mval[node] = None
            nval[node] = None
            return grp

        def push_frame(node):
            y = STACK_BASE_Y + len(stack_mobs) * FRAME_H
            fr = make_frame(node, [STACK_X, y, 0])
            stack_mobs.append(fr)
            frame_of[node] = fr
            return fr

        def set_mn(node, which, val):
            """更新某栈帧中局部变量 m 或 n 的显示。"""
            if which == 'm':
                mval[node] = val
            else:
                nval[node] = val
            ms = str(mval[node]) if mval[node] is not None else "?"
            ns = str(nval[node]) if nval[node] is not None else "?"
            new = Text("m=%s  n=%s" % (ms, ns), font_size=14, font="Consolas", color=WHITE).move_to(mn_mob[node])
            self.play(Transform(mn_mob[node], new), run_time=0.3)

        def make_badge(v, center):
            c = Circle(radius=0.17, color=GOLD, fill_color=GOLD, fill_opacity=0.22, stroke_width=2).move_to(center)
            t = Text(str(v), font_size=18, font="Consolas", color=GOLD, weight=BOLD).move_to(center)
            return VGroup(c, t)

        badge = {}
        depth_val = {}

        # 结果看板（最终把根结点返回值显示于此）
        result_head = Text("二叉树的深度", font_size=20, font="Microsoft YaHei", color=GREEN_B)
        result_num = Text("?", font_size=40, font="Consolas", color=GREEN, weight=BOLD)
        result_box = VGroup(result_head, result_num).arrange(DOWN, buff=0.15).move_to([-5.5, -2.6, 0])

        with self.voiceover(
            text="我们用这棵二叉树来演示：根结点是 A，左孩子是 B，右孩子是 C，C 又有一个左孩子 D。"
        ) as tracker:
            self.play(FadeIn(code_block), FadeIn(tree_group), run_time=tracker.duration)

        with self.voiceover(
            text="左侧的递归调用栈展示层层调用，每个栈帧都记录着局部变量m和n。黄色圆环表示当前正在计算深度的结点。"
        ) as tracker:
            self.play(FadeIn(stack_title), FadeIn(stack_hint), FadeIn(result_box), run_time=tracker.duration)

        with self.voiceover(
            text="算法采用后序遍历：先递归求出左右子树的深度，再回过头来确定当前结点的深度。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE D — 递归求深度的辅助动画函数 =====
        def enter_root():
            # 主函数调用 Depth(A)，压栈，T 指向 A，判空为非空
            path.append('A')
            fr = push_frame('A')
            ring.move_to(pos['A'])
            self.play(FadeIn(ring), FadeIn(fr, shift=UP * 0.2), run_time=0.5)
            self.play(*get_track_anims(IDX_IF0), run_time=0.4)

        def go_child(parent, child, side):
            # 第②(a)/(b)步：递归进入左/右孩子，压栈，环移动到孩子，再判空为非空
            self.play(*get_track_anims(IDX_LEFT if side == 'L' else IDX_RIGHT), run_time=0.35)
            path.append(child)
            fr = push_frame(child)
            self.play(ring.animate.move_to(pos[child]), FadeIn(fr, shift=UP * 0.2), run_time=0.5)
            self.play(*get_track_anims(IDX_IF0), run_time=0.35)

        def null_call(parent, side):
            # 第①步：递归进入空指针，if(T==NULL) 为真，返回 0（指针变红，0 飞向上一层栈帧的 m 或 n）
            self.play(*get_track_anims(IDX_LEFT if side == 'L' else IDX_RIGHT), run_time=0.3)
            self.play(*get_track_anims(IDX_IF0), run_time=0.3)
            self.play(*get_track_anims(IDX_RET0), run_time=0.3)
            slot = pos[parent] + DOWN * 0.95 + (LEFT * 0.6 if side == 'L' else RIGHT * 0.6)
            null_ring = Circle(radius=0.26, color=RED, fill_opacity=0, stroke_width=2.5).move_to(slot)
            zero = Text("0", font_size=18, font="Consolas", color=RED).move_to(slot)
            self.play(FadeIn(null_ring, scale=0.7), FadeIn(zero), run_time=0.3)
            which = 'm' if side == 'L' else 'n'
            flyer = zero.copy()
            dest = mn_mob[parent].get_center() + (LEFT * 0.42 if which == 'm' else RIGHT * 0.42)
            self.play(flyer.animate.move_to(dest).set_color(GREEN), run_time=0.45)
            self.play(FadeOut(flyer), FadeOut(null_ring), FadeOut(zero), run_time=0.2)
            set_mn(parent, which, 0)

        def combine(node):
            # 第②(c)步：左右子树深度均已求出，比较 m、n，取较大者加 1 作为返回值，弹出栈帧
            lc, rc = children[node]
            mv = depth_val.get(lc, 0)
            nv = depth_val.get(rc, 0)
            res = max(mv, nv) + 1
            self.play(*get_track_anims(IDX_CMP), run_time=0.35)
            self.play(Indicate(mn_mob[node], color=YELLOW, scale_factor=1.25), run_time=0.5)
            self.play(*get_track_anims(IDX_RETM if mv > nv else IDX_RETN), run_time=0.35)
            formula = Text("max(%d, %d) + 1 = %d" % (mv, nv, res), font_size=18, font="Consolas",
                           color=GOLD).move_to(pos[node] + DOWN * 0.72)
            self.play(FadeIn(formula, shift=DOWN * 0.1), run_time=0.4)
            # 给结点挂上深度徽标
            b = make_badge(res, pos[node] + badge_off[node])
            badge[node] = b
            depth_val[node] = res
            self.play(GrowFromCenter(b), Indicate(circles[node], color=GOLD, scale_factor=1.12), run_time=0.5)
            # 弹栈：返回值飞向上一层栈帧的 m/n（或飞向结果看板）
            fr = frame_of.pop(node)
            stack_mobs.pop()
            path.pop()
            parent = parent_of.get(node)
            if parent is not None:
                which = 'm' if children[parent][0] == node else 'n'
                flyer = Text(str(res), font_size=20, font="Consolas", color=GREEN).move_to(pos[node] + badge_off[node])
                self.play(FadeIn(flyer, scale=0.6), FadeOut(formula), run_time=0.25)
                dest = mn_mob[parent].get_center() + (LEFT * 0.42 if which == 'm' else RIGHT * 0.42)
                self.play(FadeOut(fr, shift=UP * 0.2), flyer.animate.move_to(dest),
                          ring.animate.move_to(pos[parent]), run_time=0.5)
                self.play(FadeOut(flyer), run_time=0.12)
                set_mn(parent, which, res)
            else:
                # 根结点：返回值即为整棵树的深度，飞入结果看板
                flyer = Text(str(res), font_size=20, font="Consolas", color=GREEN).move_to(pos[node] + badge_off[node])
                self.play(FadeIn(flyer, scale=0.6), FadeOut(formula), run_time=0.25)
                new_num = Text(str(res), font_size=40, font="Consolas", color=GREEN, weight=BOLD).move_to(result_num)
                self.play(FadeOut(fr, shift=UP * 0.2), flyer.animate.move_to(result_num.get_center()).scale(2.0),
                          FadeOut(ring), run_time=0.6)
                self.play(FadeOut(flyer), Transform(result_num, new_num), run_time=0.25)

        # ===== PHASE D2 — 场景2：递归左子树（A → B），叶子的空子树返回 0 =====
        with self.voiceover(
            text="主函数调用 Depth，传入根结点 A。这次调用被压入栈中，T 指向 A，判断非空，需要先求它左右子树的深度。"
        ) as tracker:
            enter_root()

        with self.voiceover(
            text="先求左子树：进入 A 的左孩子 B，再次压栈。B 也非空。"
        ) as tracker:
            go_child('A', 'B', 'L')

        with self.voiceover(
            text="B 的左孩子为空，判空为真，返回深度 0，这个 0 飞回 B 栈帧的 m。它的右孩子也为空，返回 0，赋给 n。"
        ) as tracker:
            null_call('B', 'L')
            null_call('B', 'R')

        with self.voiceover(
            text="现在 B 的 m 和 n 都是 0，比较后取较大的 0 加 1，B 的深度是 1。B 返回，弹出栈帧，1返回A栈帧的 m。"
        ) as tracker:
            combine('B')

        # ===== PHASE D3 — 场景3：右子树与回溯计算（A → C → D） =====
        with self.voiceover(
            text="接着求右子树：进入 A 的右孩子 C，压栈，C 非空。"
        ) as tracker:
            go_child('A', 'C', 'R')

        with self.voiceover(
            text="C 有一个左孩子 D，先进入 D，再次压栈，D 非空。"
        ) as tracker:
            go_child('C', 'D', 'L')

        with self.voiceover(
            text="D 的左右孩子都为空，各返回 0，赋给 D 栈帧的 m 和 n。取较大的 0 加 1，D 的深度是 1，返回并弹栈，1 返回 C 栈帧的 m。"
        ) as tracker:
            null_call('D', 'L')
            null_call('D', 'R')
            combine('D')

        with self.voiceover(
            text="C 的右孩子为空，返回 0，赋给 C 栈帧的 n。"
        ) as tracker:
            null_call('C', 'R')

        with self.voiceover(
            text="现在 C 的 m 是 1，n 是 0，比较后取较大的 1 加 1，C 的深度是 2。C 返回并弹栈，2 返回 A 栈帧的 n。"
        ) as tracker:
            combine('C')

        with self.voiceover(
            text="最后回到根结点 A。它的左子树深度 m 是 1，右子树深度 n 是 2，比较后取较大的 2 加 1，整棵二叉树的深度就是 3。"
        ) as tracker:
            combine('A')

        # ===== 结果强调 =====
        self.play(*get_track_anims(None), run_time=0.4)
        with self.voiceover(
            text="递归全部结束，调用栈清空。最深的一条路径是 A 到 C 再到 D，一共三层，这棵二叉树的深度就是 3。"
        ) as tracker:
            deep_path = VGroup(circles['A'], circles['C'], circles['D'], labels['A'], labels['C'], labels['D'])
            self.play(Indicate(deep_path, color=GREEN, scale_factor=1.12),
                      Indicate(result_box, color=GREEN, scale_factor=1.1), run_time=1.2)
            self.wait(max(0.2, tracker.duration - 1.2))

        # ===== PHASE E — COMPLEXITY（复杂度看板）=====
        self.play(FadeOut(code_block), FadeOut(stack_title), FadeOut(stack_hint), run_time=0.5)

        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(h)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_note = Text("（h 为树高，最坏退化为单链时 O(n)）", font_size=15, font="Microsoft YaHei", color=GRAY)
        summary = VGroup(time_box, space_box, space_note).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        summary.move_to(RIGHT * 4.0 + UP * 0.2)

        with self.voiceover(
            text="每个结点都恰好被访问一次，因此时间复杂度为 O恩。",
            subcaption="每个结点恰好被访问一次，时间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
            text="所需的辅助空间是递归调用栈的最大容量，也就是树的高度 h。最坏情况下二叉树退化成一条单链，高度为 n，因此空间复杂度为 O恩。",
            subcaption="所需的辅助空间是递归调用栈的最大容量，也就是树的高度h。最坏情况下二叉树退化成一条单链，高度为n，因此空间复杂度为O(n)。"
        ) as tracker:
            self.play(FadeIn(space_box), FadeIn(space_note), run_time=tracker.duration)

        with self.voiceover(
            text="以上就是计算二叉树深度算法的完整过程。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)