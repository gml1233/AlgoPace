# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import numpy as np
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class InOrderTraverseVideo(VoiceoverScene):
    # ===== 统一的结点 / 连线样式（供例子与主演示共用，保证全片视觉一致、美观）=====
    NODE_R = 0.36

    def make_node(self, label, center, r=None, color=BLUE):
        """工厂方法：绘制一个二叉树结点（圆形 + 居中字母），并挂载属性便于后续高亮。"""
        r = self.NODE_R if r is None else r
        c = Circle(radius=r, color=color, fill_color=color, fill_opacity=0.15, stroke_width=2.5).move_to(center)
        t = Text(str(label), font_size=24, color=WHITE).move_to(center)
        g = VGroup(c, t)
        g.circle = c
        g.label = t
        g.radius = r
        return g

    def edge(self, p1, p2, r1=None, r2=None, color=GRAY, sw=2.5):
        """在两结点圆心之间连线，但两端各留出半径长度，使连线只画到圆的边缘、不插入结点内部。"""
        r1 = self.NODE_R if r1 is None else r1
        r2 = self.NODE_R if r2 is None else r2
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        return Line(p1 + u * r1, p2 - u * r2, color=color, stroke_width=sw)

    def construct(self):
        # 初始化语音服务（与 KMP 算法视频完全一致的中文男声配置）
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE（标题，与 KMP 算法保持完全一致的版式）=====
        algo_title = Text("中序遍历的递归算法", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(
                text="本节我们学习二叉树的中序遍历递归算法"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE B — 例子引入（直观类比：把结点投影到地面，从左往右读，揭示“中序”名字的由来）=====
        with self.voiceover(text="先用一个例子建立直观印象。这里有一棵普通的二叉树。") as tracker:
            # 一棵 4 结点小树（与主演示不同的例子）：C(E(_, A), B)
            ipos = {'C': np.array([0.0, 1.6, 0]), 'E': np.array([-1.7, 0.3, 0]),
                    'B': np.array([1.7, 0.3, 0]), 'A': np.array([-0.7, -0.9, 0])}
            iedges = VGroup(self.edge(ipos['C'], ipos['E']), self.edge(ipos['C'], ipos['B']),
                            self.edge(ipos['E'], ipos['A']))
            inodes = {k: self.make_node(k, p) for k, p in ipos.items()}
            intro_tree = VGroup(iedges, *inodes.values())
            self.play(FadeIn(intro_tree), run_time=tracker.duration)

        GROUND_Y = -2.0  # 地面横线高度
        LABEL_Y = GROUND_Y - 0.38  # 投影字母落在横线下方（类似坐标轴刻度标注），不与横线重叠
        ground = Line(LEFT * 3.2, RIGHT * 3.2, color=GRAY_B, stroke_width=2).move_to(DOWN * (-GROUND_Y))
        proj_group = VGroup()  # 投影出的字母与虚线，便于稍后统一淡出
        with self.voiceover(
                text="如果把每个结点都竖直投影到下面这条横线上，就可以得到一个从左往右的序列，这就是以中序遍历二叉树的结果。",
                subcaption="如果把每个结点都竖直投影到下面这条横线上，就可以得到一个从左往右的序列，这就是以中序遍历二叉树的结果。"
        ) as tracker:
            self.play(Create(ground), run_time=0.5)
            for key in ('E', 'A', 'C', 'B'):  # 按从左到右（即中序）的次序逐个投影
                x = ipos[key][0]
                node = inodes[key]
                guide = DashedLine(node.circle.get_bottom(), np.array([x, GROUND_Y, 0]),
                                   color=GRAY, stroke_width=1.5, dash_length=0.09)
                drop = node.label.copy()
                self.play(node.circle.animate.set_fill(GREEN, opacity=0.5).set_stroke(GREEN),
                          Create(guide), run_time=0.3)
                self.play(drop.animate.move_to([x, LABEL_Y, 0]).set_color(GREEN), run_time=0.35)
                proj_group.add(guide, drop)

        with self.voiceover(
                text="中序遍历的递归算法是先递归遍历左子树，然后访问根结点，最后递归遍历右子树。",
                subcaption="中序遍历的递归算法是先递归遍历左子树，然后访问根结点，最后递归遍历右子树。"
        ) as tracker:
            self.play(Indicate(inodes['C'], color=YELLOW, scale_factor=1.25), run_time=0.8)
            self.wait(max(0.2, tracker.duration - 0.8))

        with self.voiceover(
                text="这种“先左、再根、后右”的顺序，会对每一棵子树递归地执行，下面学习该算法的代码实现。"
        ) as tracker:
            self.wait(tracker.duration)

        self.play(FadeOut(intro_tree), FadeOut(ground), FadeOut(proj_group), run_time=0.6)

        # ===== PHASE C — CODE BLOCK CONFIG（与 KMP 算法完全相同的代码板样式）=====
        c_lines = [
            "void InOrderTraverse(BiTree T) {",
            "    if (T) {",
            "        InOrderTraverse(T->lchild);",
            "        cout << T->data;",
            "        InOrderTraverse(T->rchild);",
            "    }",
            "}"
        ]
        # 代码行索引常量（便于追踪高亮）
        IDX_IF = 1  # if (T)                       —— 第①步：判空
        IDX_LEFT = 2  # InOrderTraverse(T->lchild);  —— 第②(a)步：中序遍历左子树
        IDX_VISIT = 3  # cout << T->data;             —— 第②(b)步：访问根结点
        IDX_RIGHT = 4  # InOrderTraverse(T->rchild);  —— 第②(c)步：中序遍历右子树

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            # 代码字号 13，与单链表插入的代码追踪区保持一致
            t = Text(stripped_line, font_size=13, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        # 纵向堆叠并左对齐所有代码文本行（行距与单链表插入一致）
        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        # 高精度手工模拟等宽字体的空格缩进对齐位移（与单链表插入一致）
        SPACE_WIDTH = 0.105
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        # 勾勒精美的代码板半透明磨砂背景（buff/圆角与单链表插入一致）
        buff_val = 0.25
        radius_val = 0.2
        code_bg = RoundedRectangle(
            corner_radius=radius_val,
            height=code_group.get_height() + 2 * buff_val,
            width=code_group.get_width() + 2 * buff_val,
            color=GRAY, fill_opacity=0.1, stroke_width=1
        )
        code_bg.move_to(code_group)

        # 布局挂载在 logo 下方，杜绝与标题和 logo 遮挡
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

        # ===== PHASE C2 — 二叉树、调用栈面板、中序序列表（表样式与 KMP 完全一致）=====
        # 一棵 5 结点二叉树：A(B(D,E), C)，先序输入 A B D # # E # # C # #
        pos = {
            'A': np.array([0.0, 2.0, 0]),
            'B': np.array([-1.7, 0.55, 0]), 'C': np.array([1.7, 0.55, 0]),
            'D': np.array([-2.6, -0.85, 0]), 'E': np.array([-0.8, -0.85, 0]),
        }
        children = {'A': ('B', 'C'), 'B': ('D', 'E'),
                    'C': (None, None), 'D': (None, None), 'E': (None, None)}

        # 连线只画到圆的边缘（不插入结点内部），叶子结点不再绘制任何空指针子结点
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

        # 调用栈面板（左侧）：展示递归层层调用
        STACK_X = -5.4
        STACK_BASE_Y = -0.85
        FRAME_H = 0.56
        stack_title = Text("调用栈", font_size=22, font="Microsoft YaHei", color=YELLOW).move_to([STACK_X, 1.45, 0])
        stack_hint = Text("（递归深度 = 树高）", font_size=14, font="Microsoft YaHei", color=GRAY).next_to(
            stack_title, DOWN, buff=0.12)

        def make_frame(node_key):
            box = RoundedRectangle(corner_radius=0.08, width=1.95, height=0.5, color=BLUE_D, fill_color=BLUE_D,
                                   fill_opacity=0.18, stroke_width=2)
            t = Text("InOrder(%s)" % node_key, font_size=15, color=WHITE).move_to(box.get_center())
            return VGroup(box, t)

        # ----- 中序序列结果表（make_cell 与表格样式与 KMP 算法完全一致）-----
        def make_cell(content, w, h, fs, txt_color=WHITE, box_color=GRAY_B):
            rect = Rectangle(width=w, height=h, color=box_color, stroke_width=1.5)
            t = Text(str(content), font_size=fs, color=txt_color, font="Microsoft YaHei")
            t.move_to(rect.get_center())
            return VGroup(rect, t)

        HEAD_W, CELL_W, CELL_H = 1.0, 0.55, 0.5
        N_OUT = 5
        row_idx = VGroup(make_cell("序号", HEAD_W, CELL_H, 16, txt_color=YELLOW))
        row_node = VGroup(make_cell("结点", HEAD_W, CELL_H, 16, txt_color=GREEN))
        out_cells = {}
        for k in range(N_OUT):
            row_idx.add(make_cell(k + 1, CELL_W, CELL_H, 18, txt_color=YELLOW))
            cell = make_cell("", CELL_W, CELL_H, 18)  # 数据单元格初始为空，访问到结点时再填入
            row_node.add(cell)
            out_cells[k] = cell[0]  # 记录单元格矩形，便于把字母飞入其中
        for r in (row_idx, row_node):
            r.arrange(RIGHT, buff=0)
        out_table = VGroup(row_idx, row_node).arrange(DOWN, buff=0)
        out_table_title = Text("中序输出序列", font_size=18, font="Microsoft YaHei", color=WHITE)
        out_block = VGroup(out_table_title, out_table).arrange(DOWN, buff=0.15)
        out_block.move_to(RIGHT * 1.65 + DOWN * 1.85)

        with self.voiceover(
                text="这是一棵已建好的二叉树：根结点是 A，它的左子树由 B、D、E 组成，右子树是 C。",
                subcaption="这是一棵已建好的二叉树：根结点是 A，它的左子树由 B、D、E 组成，右子树是 C。"
        ) as tracker:
            self.play(FadeIn(code_block), FadeIn(tree_group), run_time=tracker.duration)

        with self.voiceover(
                text="左侧用一个调用栈展示递归的调用，底部的表格记录中序遍历输出的结点序列，黄色圆环表示当前正在处理的结点。",
                subcaption="左侧用一个调用栈展示递归的调用，底部的表格记录中序遍历输出的结点序列，黄色圆环表示当前正在处理的结点。"
        ) as tracker:
            self.play(FadeIn(stack_title), FadeIn(stack_hint), FadeIn(out_block), run_time=tracker.duration)

        # ===== PHASE D — 递归遍历的辅助动画函数 =====
        path = []  # 当前调用链（结点 key），用于返回时把环移回父结点
        stack_mobs = []  # 调用栈中的帧 Mobject
        order = {'n': 0}  # 已输出的结点个数

        def push_frame(node_key):
            y = STACK_BASE_Y + len(stack_mobs) * FRAME_H
            fr = make_frame(node_key).move_to([STACK_X, y, 0])
            stack_mobs.append(fr)
            return fr

        def enter_root():
            # 主函数调用 InOrderTraverse(A)，压栈，T 指向 A，判空为非空
            path.append('A')
            fr = push_frame('A')
            ring.move_to(pos['A'])
            self.play(FadeIn(ring), FadeIn(fr, shift=UP * 0.2), run_time=0.5)
            self.play(*get_track_anims(IDX_IF), run_time=0.4)

        def go_child(parent, child, side):
            # 第②(a)/(c)步：递归进入左/右孩子，压栈，环移动到孩子，再判空
            self.play(*get_track_anims(IDX_LEFT if side == 'L' else IDX_RIGHT), run_time=0.35)
            path.append(child)
            fr = push_frame(child)
            self.play(ring.animate.move_to(pos[child]), FadeIn(fr, shift=UP * 0.2), run_time=0.5)
            self.play(*get_track_anims(IDX_IF), run_time=0.35)

        def null_child(node, side):
            # 第①步：递归进入空指针，if(T) 为假，直接返回（不压栈）。
            # 空子树不在树上绘制任何子结点，只用一个“空，返回”提示一闪而过，保证叶子结点干净美观。
            self.play(*get_track_anims(IDX_LEFT if side == 'L' else IDX_RIGHT), run_time=0.3)
            self.play(*get_track_anims(IDX_IF), run_time=0.3)
            off = (LEFT * 0.5 if side == 'L' else RIGHT * 0.5) + DOWN * 0.72
            tag = Text("空，返回", font_size=15, font="Microsoft YaHei", color=GRAY).move_to(pos[node] + off)
            self.play(FadeIn(tag, shift=DOWN * 0.1), run_time=0.35)
            self.play(FadeOut(tag), run_time=0.3)

        def visit(node):
            # 第②(b)步：访问根结点，结点变绿，字母复制一份飞入输出表
            self.play(*get_track_anims(IDX_VISIT), run_time=0.3)
            self.play(circles[node].animate.set_fill(GREEN, opacity=0.5).set_stroke(GREEN, width=4), run_time=0.4)
            k = order['n']
            order['n'] += 1
            flyer = labels[node].copy()
            self.play(flyer.animate.move_to(out_cells[k].get_center()).set_color(GREEN),
                      Indicate(out_cells[k], color=GREEN, scale_factor=1.2), run_time=0.6)
            self.add(flyer)

        def leave():
            # 当前结点的左、根、右全部处理完毕，函数返回，从调用栈弹出，环退回父结点
            path.pop()
            fr = stack_mobs.pop()
            self.play(FadeOut(fr, shift=UP * 0.2), run_time=0.3)
            if path:
                self.play(ring.animate.move_to(pos[path[-1]]), run_time=0.4)
            else:
                self.play(FadeOut(ring), run_time=0.3)

        # ===== PHASE D2 — 递归遍历过程（场景化讲解，对应算法步骤 ①②(a)(b)(c)）=====
        with self.voiceover(
                text="主函数调用中序遍历的递归函数，传入根结点 A。这次调用被压入调用栈，T 指向 A，判断非空。",
                subcaption="主函数调用中序遍历的递归函数，传入根结点 A。这次调用被压入调用栈，T 指向 A，判断非空。"
        ) as tracker:
            enter_root()

        with self.voiceover(
                text="先递归遍历左子树：从 A 进入左孩子 B，再从 B 进入左孩子 D。每深入一层，调用栈就多压入一层。",
                subcaption="先递归遍历左子树：从 A 进入左孩子 B，再从 B 进入左孩子 D。每深入一层，调用栈就多压入一层"
        ) as tracker:
            go_child('A', 'B', 'L')
            go_child('B', 'D', 'L')

        with self.voiceover(
                text="D 的左孩子为空，if 判断为假，递归立即返回。D 的左子树处理完毕，于是访问 D，输出第一个结点 D。",
                subcaption="D 的左孩子为空，if 判断为假，递归立即返回。D 的左子树处理完毕，于是访问 D，输出第一个结点 D。"
        ) as tracker:
            null_child('D', 'L')
            visit('D')

        with self.voiceover(
                text="再看 D 的右子树，同样为空并返回。D 这一层全部完成，从调用栈弹出，返回到 B。此时 B 的左子树已处理完，访问 B，输出 B。",
                subcaption="再看 D 的右子树，同样为空并返回。D 这一层全部完成，从调用栈弹出，返回到 B。此时 B 的左子树已处理完，访问 B，输出 B。"
        ) as tracker:
            null_child('D', 'R')
            leave()
            visit('B')

        with self.voiceover(
                text="接着递归遍历 B 的右子树，进入 E。E 的左子树为空并返回，于是访问 E，输出 E。",
                subcaption="接着递归遍历 B 的右子树，进入 E。E 的左子树为空并返回，于是访问 E，输出 E。"
        ) as tracker:
            go_child('B', 'E', 'R')
            null_child('E', 'L')
            visit('E')

        with self.voiceover(
                text="E 的右子树为空并返回，E 出栈；B 的右子树也处理完，B 出栈。至此 A 的整棵左子树全部完成，现在访问根结点 A，输出 A。",
                subcaption="E 的右子树为空并返回，E 出栈；B 的右子树也处理完，B 出栈。至此 A 的整棵左子树全部完成，现在访问根结点 A，输出 A。"
        ) as tracker:
            null_child('E', 'R')
            leave()
            leave()
            visit('A')

        with self.voiceover(
                text="最后递归遍历 A 的右子树，进入 C。C 的左子树为空并返回，访问 C，输出 C。",
                subcaption="最后递归遍历 A 的右子树，进入 C。C 的左子树为空并返回，访问 C，输出 C。"
        ) as tracker:
            go_child('A', 'C', 'R')
            null_child('C', 'L')
            visit('C')

        with self.voiceover(
                text="C 的右子树为空并返回，C 出栈；最后 A 也返回出栈。调用栈清空，整棵树的中序遍历全部结束。",
                subcaption="C 的右子树为空并返回，C 出栈；最后 A 也返回出栈。调用栈清空，整棵树的中序遍历全部结束。"
        ) as tracker:
            null_child('C', 'R')
            leave()
            leave()

        # ===== PHASE D3 — 结果展示 =====
        self.play(*get_track_anims(None), run_time=0.4)
        with self.voiceover(
                text="中序遍历的最终结果是：D B E A C。",
                subcaption="中序遍历的最终结果是：D B E A C。"
        ) as tracker:
            self.play(*[out_cells[k].animate.set_color(GREEN) for k in range(N_OUT)], run_time=0.6)
            self.wait(max(0.3, tracker.duration - 0.6))

        # ===== PHASE E — COMPLEXITY（复杂度看板）=====
        # 调用栈与代码追踪已无需保留，淡出左侧调用栈以腾出空间放结论
        self.play(FadeOut(stack_title), FadeOut(stack_hint), run_time=0.4)

        result_label = Text("中序序列：D B E A C", font_size=24, font="Microsoft YaHei", color=GREEN)
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        summary = VGroup(result_label, time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        summary.move_to(LEFT * 4.3 + UP * 0.4)

        with self.voiceover(text="至此，整棵二叉树的中序遍历完成。") as tracker:
            self.play(Write(result_label), run_time=max(0.5, tracker.duration))

        with self.voiceover(
                text="每个结点都恰好被访问一次，因此时间复杂度为O恩",
                subcaption="每个结点恰好被访问一次，时间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
                text="所需的辅助空间是调用栈的最大容量，也就是树的深度。最坏情况下二叉树退化成一条单链，深度为 n，因此空间复杂度为 O恩。",
                subcaption="所需的辅助空间是调用栈的最大容量，也就是树的深度。最坏情况下二叉树退化成一条单链，深度为 n，因此空间复杂度为O(n)"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是中序遍历递归算法的完整过程。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)