# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import numpy as np
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class InOrderNonRecursiveVideo(VoiceoverScene):
    # ===== 统一的结点 / 连线样式（与本章中序遍历递归、线索化视频保持一致，保证全章视觉统一、美观）=====
    NODE_R = 0.34
    Q_COLOR = "#FF8C1A"  # q 暂存槽专用橙色，与线索化视频的 pre 指针配色一致

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

    def make_cell(self, content, w, h, fs, txt_color=WHITE, box_color=GRAY_B):
        """表格单元格（样式与本章其它算法视频的表格完全一致）。"""
        rect = Rectangle(width=w, height=h, color=box_color, stroke_width=1.5)
        t = Text(str(content), font_size=fs, color=txt_color, font="Microsoft YaHei")
        t.move_to(rect.get_center())
        return VGroup(rect, t)

    def construct(self):
        # 初始化语音服务（与本章其它视频完全一致的中文男声配置）
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ============================================================
        # PHASE A — 算法标题 + 一句话算法描述（版式与本章其它视频完全一致）
        # ============================================================
        algo_title = Text("中序遍历的非递归算法", font_size=48, font="Microsoft YaHei",
                          weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(
                text="本节学习中序遍历的非递归算法",
                subcaption="本节学习中序遍历的非递归算法"
        ) as tracker:
            self.wait(tracker.duration)

        subtitle = Text("该算法借助栈实现二叉树的中序遍历", font_size=22, font="Microsoft YaHei",
                        color=GRAY_A).next_to(algo_title, DOWN, buff=0.25)
        with self.voiceover(
                text="该算法借助栈实现二叉树的中序遍历",
                subcaption="该算法借助栈实现二叉树的中序遍历"
        ) as tracker:
            self.play(FadeIn(subtitle), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        self.play(FadeOut(subtitle), run_time=0.4)

        # ============================================================
        # PHASE C — CODE BLOCK CONFIG（代码板样式与本章其它视频完全相同，只跟踪核心函数）
        # ============================================================
        c_lines = [
            "void InOrderTraverse(BiTree T) {",
            "    LinkStack S; BiTree p;",
            "    BiTree q = new BiTNode;",
            "    InitStack(S); p = T;",
            "    while (p || !StackEmpty(S)) {",
            "        if (p) {",
            "            Push(S, p);",
            "            p = p->lchild;",
            "        } else {",
            "            Pop(S, q);",
            "            cout << q->data;",
            "            p = q->rchild;",
            "        }",
            "    }",
            "}"
        ]
        # 代码行索引常量（便于追踪高亮，对应算法步骤 ①②③(a)(b)）
        IDX_Q = 2  # BiTree q = new BiTNode;      —— ② 申请结点空间 q
        IDX_INIT = 3  # InitStack(S); p = T;         —— ① 初始化空栈，p 指向根
        IDX_WHILE = 4  # while (p || !StackEmpty(S))  —— ③ 循环条件判断
        IDX_IF = 5  # if (p)                       —— ③(a) p 非空
        IDX_PUSH = 6  # Push(S, p);                  —— ③(a) p 进栈
        IDX_LEFT = 7  # p = p->lchild;               —— ③(a) p 指向左孩子
        IDX_ELSE = 8  # } else {                     —— ③(b) p 为空
        IDX_POP = 9  # Pop(S, q);                   —— ③(b) 栈顶弹出至 q
        IDX_OUT = 10  # cout << q->data;             —— ③(b) 访问（输出）根结点
        IDX_RIGHT = 11  # p = q->rchild;               —— ③(b) p 指向右孩子

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=13, font="Consolas", color=WHITE)
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

        def track(new_idx, run_time=0.35):
            """安全地播放代码行高亮切换：若目标行已高亮（无动画可播），则以等长等待代替，避免空 play 报错。"""
            anims = get_track_anims(new_idx)
            if anims:
                self.play(*anims, run_time=run_time)
            else:
                self.wait(run_time)

        # ============================================================
        # PHASE C2 — 二叉树、栈 S 容器、指针 p、暂存槽 q、输出序列表
        # ============================================================
        # 一棵 5 结点二叉树：A(B(C,D), E)，先序输入 A B C # # D # # E # #，中序输出 C B D A E
        pos = {
            'A': np.array([-1.2, 1.95, 0]),
            'B': np.array([-2.6, 0.7, 0]), 'E': np.array([0.2, 0.7, 0]),
            'C': np.array([-3.6, -0.55, 0]), 'D': np.array([-1.6, -0.55, 0]),
        }
        children = {'A': ('B', 'E'), 'B': ('C', 'D'),
                    'C': (None, None), 'D': (None, None), 'E': (None, None)}
        # 空孩子（∧）标记的出现位置：结点斜下方，游标 p 走到空指针时落在这里
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

        # “指针 p”活动指示环（黄色圆环 + 上方的 p 字标签，二者始终同步移动）
        P_OFF = np.array([0, 0.72, 0])
        ring = Circle(radius=self.NODE_R + 0.12, color=YELLOW, stroke_width=4).move_to(pos['A'])
        p_tag = Text("p", font_size=22, font="Consolas", weight=BOLD,
                     color=YELLOW).move_to(pos['A'] + P_OFF)

        # ----- 栈 S 容器（左侧，开口向上的“U”形，支持压入 / 弹出动画）-----
        STACK_X, STACK_BASE_Y, SLOT_H = -5.6, -1.55, 0.68
        stack_box = VGroup(
            Line([-6.35, 0.75, 0], [-6.35, -1.95, 0], color=GRAY_A, stroke_width=3),
            Line([-6.35, -1.95, 0], [-4.85, -1.95, 0], color=GRAY_A, stroke_width=3),
            Line([-4.85, -1.95, 0], [-4.85, 0.75, 0], color=GRAY_A, stroke_width=3),
        )
        stack_title = Text("栈 S", font_size=20, font="Microsoft YaHei",
                           color=YELLOW).move_to([STACK_X, 1.05, 0])

        # ----- 暂存槽 q（栈底部附近，接收出栈的结点）-----
        q_box = RoundedRectangle(corner_radius=0.1, width=0.95, height=0.8, color=self.Q_COLOR,
                                 fill_color=self.Q_COLOR, fill_opacity=0.12,
                                 stroke_width=2).move_to([STACK_X, -2.85, 0])
        q_label = Text("q", font_size=20, font="Consolas", weight=BOLD,
                       color=self.Q_COLOR).next_to(q_box, LEFT, buff=0.15)

        # ----- 中序输出序列表（底部；单元格样式与本章其它视频完全一致）-----
        HEAD_W, CELL_W, CELL_H = 1.0, 0.55, 0.5
        N_OUT = 5
        row_idx = VGroup(self.make_cell("序号", HEAD_W, CELL_H, 16, txt_color=YELLOW))
        row_node = VGroup(self.make_cell("结点", HEAD_W, CELL_H, 16, txt_color=GREEN))
        out_cells = {}
        for k in range(N_OUT):
            row_idx.add(self.make_cell(k + 1, CELL_W, CELL_H, 18, txt_color=YELLOW))
            cell = self.make_cell("", CELL_W, CELL_H, 18)  # 数据单元格初始为空，访问到结点时再填入
            row_node.add(cell)
            out_cells[k] = cell[0]  # 记录单元格矩形，便于把字母飞入其中
        for r in (row_idx, row_node):
            r.arrange(RIGHT, buff=0)
        out_table = VGroup(row_idx, row_node).arrange(DOWN, buff=0)
        out_table_title = Text("中序输出序列", font_size=18, font="Microsoft YaHei", color=WHITE)
        out_block = VGroup(out_table_title, out_table).arrange(DOWN, buff=0.15)
        out_block.move_to([-0.7, -2.35, 0])

        # ----- 场景铺设 -----
        with self.voiceover(
                text="这是该算法的核心代码",
                subcaption="这是该算法的核心代码"
        ) as tracker:
            self.play(FadeIn(code_block), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        with self.voiceover(
                text="这是一棵已建好的二叉树",
                subcaption="这是一棵已建好的二叉树"
        ) as tracker:
            self.play(FadeIn(tree_group), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        with self.voiceover(
                text="根是A，左子树有B、C、D，右孩子是E",
                subcaption="根是A，左子树有B、C、D，右孩子是E"
        ) as tracker:
            self.play(Indicate(nodes['A'], color=YELLOW, scale_factor=1.2), run_time=0.4)
            for k in ('B', 'C', 'D'):
                self.play(Indicate(nodes[k], color=GREEN, scale_factor=1.2), run_time=0.4)
            self.play(Indicate(nodes['E'], color=GREEN, scale_factor=1.2), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 2.0))

        with self.voiceover(
                text="左边是栈S，用来暂存访问过的的结点",
                subcaption="左边是栈S，用来暂存访问过的的结点"
        ) as tracker:
            self.play(Create(stack_box), FadeIn(stack_title), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        # ============================================================
        # PHASE C4 — 算法步骤（把非递归中序遍历的完整步骤 ①②③(a)(b) 逐条列出并讲解）
        # 暂时淡出二叉树腾出版面，保留右侧代码板与左侧栈 S；讲完后再淡回二叉树进入逐行跟踪。
        # 讲解文本 text 与字幕 subcaption 完全一致。
        # ============================================================
        self.play(FadeOut(tree_group), run_time=0.5)

        steps_title = Text("算法步骤", font_size=26, font="Microsoft YaHei", color=YELLOW, weight=BOLD)
        s1 = Text("① 初始化一个空栈S，指针p指向根结点。", font_size=19, font="Microsoft YaHei", color=WHITE)
        s2 = Text("② 申请一个结点空间q，用来存放栈顶弹出的元素。", font_size=19, font="Microsoft YaHei", color=WHITE)
        s3 = Text("③ 当p非空或者栈S非空时，循环执行以下操作：", font_size=19, font="Microsoft YaHei", color=WHITE)
        sa = Text("(a) 如果p非空，则使p进栈，p指向该结点的左孩子；", font_size=18, font="Microsoft YaHei", color=GRAY_A)
        # (b) 步骤较长，拆成两行显示，避免挤到左侧栈 S 与右侧代码板
        sb = VGroup(
            Text("(b) 如果p为空，则弹出栈顶元素并访问根结点，", font_size=18, font="Microsoft YaHei", color=GRAY_A),
            Text("将p指向该结点的右孩子。", font_size=18, font="Microsoft YaHei", color=GRAY_A),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        steps_body = VGroup(s1, s2, s3, sa, sb).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        sa.shift(RIGHT * 0.45)  # (a)(b) 作为 ③ 的子步骤，缩进对齐
        sb.shift(RIGHT * 0.45)
        steps_panel = VGroup(steps_title, steps_body).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        steps_panel.move_to([-0.95, 0.15, 0])

        with self.voiceover(
                text="接下来，把该算法的基本步骤梳理一遍。"
        ) as tracker:
            self.play(FadeIn(steps_title, shift=DOWN * 0.15), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
                text="初始化一个空栈S，指针p指向根结点。",
                subcaption="初始化一个空栈S，指针p指向根结点。"
        ) as tracker:
            self.play(FadeIn(s1, shift=RIGHT * 0.15), run_time=0.5)
            self.wait(max(0.2, tracker.duration - 0.5))

        with self.voiceover(
                text="申请一个结点空间q，用来存放栈顶弹出的元素。",
                subcaption="申请一个结点空间q，用来存放栈顶弹出的元素。"
        ) as tracker:
            self.play(FadeIn(s2, shift=RIGHT * 0.15), run_time=0.5)
            self.wait(max(0.2, tracker.duration - 0.5))

        with self.voiceover(
                text="当p非空或者栈S非空时，循环执行以下操作。",
                subcaption="当p非空或者栈S非空时，循环执行以下操作。"
        ) as tracker:
            self.play(FadeIn(s3, shift=RIGHT * 0.15), run_time=0.5)
            self.wait(max(0.2, tracker.duration - 0.5))

        with self.voiceover(
                text="如果p非空，则使p进栈，p指向该结点的左孩子。",
                subcaption="如果p非空，则使p进栈，p指向该结点的左孩子。"
        ) as tracker:
            self.play(FadeIn(sa, shift=RIGHT * 0.15), run_time=0.5)
            self.wait(max(0.2, tracker.duration - 0.5))

        with self.voiceover(
                text="如果p为空，则弹出栈顶元素并访问根结点，将p指向该结点的右孩子。",
                subcaption="如果p为空，则弹出栈顶元素并访问根结点，将p指向该结点的右孩子。"
        ) as tracker:
            self.play(FadeIn(sb, shift=RIGHT * 0.15), run_time=0.5)
            self.wait(max(0.2, tracker.duration - 0.5))

        # 步骤讲解结束：淡出步骤面板，淡回二叉树，进入正式的逐行代码跟踪
        self.play(FadeOut(steps_panel), FadeIn(tree_group), run_time=0.6)

        with self.voiceover(
                text="下方表格记录输出的中序序列",
                subcaption="下方表格记录输出的中序序列"
        ) as tracker:
            self.play(FadeIn(out_block), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        # ============================================================
        # PHASE D — 遍历过程的辅助动画函数（进栈 / 出栈 / 访问 / 移动 p）
        # ============================================================
        stack_items = []  # 栈中的微缩结点 Mobject（自底向上）
        order = {'n': 0}  # 已输出的结点个数
        self.q_item = None  # 当前停在 q 槽中的微缩结点
        self.cur_null = None  # 当前显示的空指针（∧）标记

        def make_null(pt):
            circ = DashedVMobject(Circle(radius=0.2, color=GRAY_B, stroke_width=2).move_to(pt), num_dashes=12)
            t = Text("∧", font_size=15, color=GRAY_B).move_to(pt)
            return VGroup(circ, t)

        def move_p_node(key, rt=0.45):
            # 游标 p 移动到一个真实结点；若此前停在空指针上，顺带淡出 ∧ 标记
            anims = [ring.animate.move_to(pos[key]), p_tag.animate.move_to(pos[key] + P_OFF)]
            if self.cur_null is not None:
                anims.append(FadeOut(self.cur_null))
                self.cur_null = None
            self.play(*anims, run_time=rt)

        def move_p_null(nkey, rt=0.45):
            # 游标 p 移动到空指针处：原地生成一个灰色虚线 ∧ 标记，环套在它外面
            pt = NULL_POS[nkey]
            nm = make_null(pt)
            anims = [ring.animate.move_to(pt), p_tag.animate.move_to(pt + P_OFF), FadeIn(nm)]
            if self.cur_null is not None:
                anims.append(FadeOut(self.cur_null))
            self.play(*anims, run_time=rt)
            self.cur_null = nm

        def push_to_stack(key, rt=0.5):
            # ③(a)：从树结点复制一个微缩图标，飞入栈顶空槽
            mini = nodes[key].copy()
            mini.generate_target()
            mini.target.scale(0.8).move_to([STACK_X, STACK_BASE_Y + len(stack_items) * SLOT_H, 0])
            self.play(MoveToTarget(mini), run_time=rt)
            stack_items.append(mini)

        def pop_to_q(rt=0.5):
            # ③(b)：栈顶元素飞出，落入 q 槽位（q 中原有内容被覆盖）
            mini = stack_items.pop()
            anims = [mini.animate.move_to(q_box.get_center())]
            if self.q_item is not None:
                anims.append(FadeOut(self.q_item))
            self.play(*anims, run_time=rt)
            self.q_item = mini

        def visit_output(key):
            # ③(b)：访问 q 指向的结点——树中该结点变绿，字母从 q 槽飞入输出表
            self.play(circles[key].animate.set_fill(GREEN, opacity=0.5).set_stroke(GREEN, width=4), run_time=0.35)
            k = order['n']
            order['n'] += 1
            flyer = self.q_item[1].copy()
            self.play(flyer.animate.move_to(out_cells[k].get_center()).set_color(GREEN).scale(1.2),
                      Indicate(out_cells[k], color=GREEN, scale_factor=1.2), run_time=0.5)
            self.add(flyer)

        def push_step(key, w=0.22, rt=0.5):
            # 一轮完整的“进栈”迭代：while → if → Push
            track(IDX_WHILE, w)
            track(IDX_IF, w)
            track(IDX_PUSH, w)
            push_to_stack(key, rt)

        def pop_step(w=0.22, rt=0.5):
            # 一轮完整的“出栈”迭代：while → else → Pop
            track(IDX_WHILE, w)
            track(IDX_ELSE, w)
            track(IDX_POP, w)
            pop_to_q(rt)

        def out_step(key):
            # cout << q->data：访问并输出
            track(IDX_OUT, 0.28)
            visit_output(key)

        def left_step(child, parent, rt=0.45):
            # p = p->lchild：p 移向左孩子（child 为 None 时移向空指针标记）
            track(IDX_LEFT, 0.28)
            if child is not None:
                move_p_node(child, rt)
            else:
                move_p_null((parent, 'L'), rt)

        def right_step(child, parent, rt=0.45):
            # p = q->rchild：p 移向右孩子（child 为 None 时移向空指针标记）
            track(IDX_RIGHT, 0.28)
            if child is not None:
                move_p_node(child, rt)
            else:
                move_p_null((parent, 'R'), rt)

        # ============================================================
        # PHASE D2 — 初始化（对应算法步骤 ①②）
        # ============================================================
        with self.voiceover(
                text="申请结点空间q，暂存出栈的元素",
                subcaption="申请结点空间q，暂存出栈的元素"
        ) as tracker:
            track(IDX_Q, 0.4)
            self.play(FadeIn(q_box), FadeIn(q_label), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(
                text="初始化空栈S，指针p指向根结点A",
                subcaption="初始化空栈S，指针p指向根结点A"
        ) as tracker:
            track(IDX_INIT, 0.4)
            self.play(FadeIn(ring), FadeIn(p_tag), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 1.0))

        # ============================================================
        # PHASE D3 — 循环遍历过程（对应算法步骤 ③(a)(b)）
        # 深入左子树：A、B、C 依次进栈
        # ============================================================
        with self.voiceover(
                text="p非空，满足循环条件",
                subcaption="p非空，满足循环条件"
        ) as tracker:
            track(IDX_WHILE, 0.4)
            self.wait(max(0.1, tracker.duration - 0.4))

        with self.voiceover(
                text="执行if分支，A进栈",
                subcaption="执行if分支，A进栈"
        ) as tracker:
            track(IDX_IF, 0.3)
            track(IDX_PUSH, 0.3)
            push_to_stack('A', 0.6)
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="p指向A的左孩子B",
                subcaption="p指向A的左孩子B"
        ) as tracker:
            left_step('B', 'A')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(
                text="B非空，B也进栈",
                subcaption="B非空，B也进栈"
        ) as tracker:
            push_step('B')
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="p指向B的左孩子C",
                subcaption="p指向B的左孩子C"
        ) as tracker:
            left_step('C', 'B')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(
                text="C非空，C也进栈",
                subcaption="C非空，C也进栈"
        ) as tracker:
            push_step('C')
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="p指向C的左孩子，左孩子为空",
                subcaption="p指向C的左孩子，左孩子为空"
        ) as tracker:
            left_step(None, 'C')
            self.wait(max(0.1, tracker.duration - 0.75))

        # ----- 退栈与访问：C、B 依次出栈输出 -----
        with self.voiceover(
                text="p为空，但栈非空，继续循环",
                subcaption="p为空，但栈非空，继续循环"
        ) as tracker:
            track(IDX_WHILE, 0.4)
            self.wait(max(0.1, tracker.duration - 0.4))

        with self.voiceover(
                text="执行else分支，弹出栈顶C，存入q",
                subcaption="执行else分支，弹出栈顶C，存入q"
        ) as tracker:
            track(IDX_ELSE, 0.3)
            track(IDX_POP, 0.3)
            pop_to_q(0.6)
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="访问q指向的结点，输出C",
                subcaption="访问q指向的结点，输出C"
        ) as tracker:
            out_step('C')
            self.wait(max(0.1, tracker.duration - 1.15))

        with self.voiceover(
                text="p指向C的右孩子，右孩子为空",
                subcaption="p指向C的右孩子，右孩子为空"
        ) as tracker:
            right_step(None, 'C')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(
                text="栈非空，再弹出栈顶B，存入q",
                subcaption="栈非空，再弹出栈顶B，存入q"
        ) as tracker:
            pop_step()
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="访问B，输出B",
                subcaption="访问B，输出B"
        ) as tracker:
            out_step('B')
            self.wait(max(0.1, tracker.duration - 1.15))

        with self.voiceover(
                text="p指向B的右孩子D",
                subcaption="p指向B的右孩子D"
        ) as tracker:
            right_step('D', 'B')
            self.wait(max(0.1, tracker.duration - 0.75))

        # ----- 处理 D：进栈 → 左空 → 出栈输出 -----
        with self.voiceover(
                text="D非空，D进栈",
                subcaption="D非空，D进栈"
        ) as tracker:
            push_step('D')
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="p指向D的左孩子，为空",
                subcaption="p指向D的左孩子，为空"
        ) as tracker:
            left_step(None, 'D')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(
                text="弹出栈顶D并访问，输出D",
                subcaption="弹出栈顶D并访问，输出D"
        ) as tracker:
            pop_step()
            out_step('D')
            self.wait(max(0.1, tracker.duration - 2.35))

        with self.voiceover(
                text="p指向D的右孩子，仍为空",
                subcaption="p指向D的右孩子，仍为空"
        ) as tracker:
            right_step(None, 'D')
            self.wait(max(0.1, tracker.duration - 0.75))

        # ----- 弹出 A，转向右子树 E -----
        with self.voiceover(
                text="弹出栈顶A并访问，输出A",
                subcaption="弹出栈顶A并访问，输出A"
        ) as tracker:
            pop_step()
            out_step('A')
            self.wait(max(0.1, tracker.duration - 2.35))

        with self.voiceover(
                text="p指向A的右孩子E",
                subcaption="p指向A的右孩子E"
        ) as tracker:
            right_step('E', 'A')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(
                text="E非空，E进栈",
                subcaption="E非空，E进栈"
        ) as tracker:
            push_step('E')
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="p指向E的左孩子，为空",
                subcaption="p指向E的左孩子，为空"
        ) as tracker:
            left_step(None, 'E')
            self.wait(max(0.1, tracker.duration - 0.75))

        with self.voiceover(
                text="弹出栈顶E并访问，输出E",
                subcaption="弹出栈顶E并访问，输出E"
        ) as tracker:
            pop_step()
            out_step('E')
            self.wait(max(0.1, tracker.duration - 2.35))

        with self.voiceover(
                text="p指向E的右孩子，为空",
                subcaption="p指向E的右孩子，为空"
        ) as tracker:
            right_step(None, 'E')
            self.wait(max(0.1, tracker.duration - 0.75))

        # ----- 循环结束 -----
        with self.voiceover(
                text="此时p为空，栈也为空",
                subcaption="此时p为空，栈也为空"
        ) as tracker:
            track(IDX_WHILE, 0.4)
            self.play(Indicate(stack_box, color=GRAY_A, scale_factor=1.05), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(
                text="循环条件不成立，遍历结束",
                subcaption="循环条件不成立，遍历结束"
        ) as tracker:
            end_anims = [FadeOut(ring), FadeOut(p_tag)]
            if self.cur_null is not None:
                end_anims.append(FadeOut(self.cur_null))
                self.cur_null = None
            self.play(*get_track_anims(None), *end_anims, run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.5))

        with self.voiceover(
                text="中序遍历结果是：C、B、D、A、E",
                subcaption="中序遍历结果是：C、B、D、A、E"
        ) as tracker:
            self.play(*[out_cells[k].animate.set_color(GREEN) for k in range(N_OUT)], run_time=0.6)
            self.wait(max(0.3, tracker.duration - 0.6))

        # ============================================================
        # PHASE E — COMPLEXITY（复杂度看板）
        # ============================================================
        # 栈 S 与暂存槽 q 已完成使命，淡出左侧区域腾出空间放结论
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
                text="每个结点进栈和出栈各一次",
                subcaption="每个结点进栈和出栈各一次"
        ) as tracker:
            self.play(FadeIn(note1), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
                text="时间复杂度为O恩",
                subcaption="时间复杂度为O(n)"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
                text="栈的最大容量是树的深度",
                subcaption="栈的最大容量是树的深度"
        ) as tracker:
            self.play(FadeIn(note2), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
                text="最坏情况下，空间复杂度为O恩",
                subcaption="最坏情况下，空间复杂度为O(n)"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
                text="以上就是中序遍历的非递归算法",
                subcaption="以上就是中序遍历的非递归算法"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)