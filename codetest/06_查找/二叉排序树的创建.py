# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class BSTNode:
    def __init__(self, val, pos):
        self.val = val
        self.pos = pos
        self.left = None
        self.right = None
        self.mobject = None
        self.edge_left = None
        self.edge_right = None


class CreateBSTVideo(VoiceoverScene):
    NODE_R = 0.35

    def make_node(self, label, center, r=None, color=BLUE):
        r = self.NODE_R if r is None else r
        c = Circle(radius=r, color=color, fill_color=color, fill_opacity=0.15, stroke_width=2.5).move_to(center)
        t = Text(str(label), font="Arial", font_size=20, color=WHITE).move_to(center)
        g = VGroup(c, t)
        g.circle = c
        g.label = t
        return g

    def edge(self, p1, p2, r1=None, r2=None, color=GRAY, sw=2.5):
        r1 = self.NODE_R if r1 is None else r1
        r2 = self.NODE_R if r2 is None else r2
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        return Line(p1 + u * r1, p2 - u * r2, color=color, stroke_width=sw)

    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE & INTRO =====
        algo_title = Text("二叉排序树的创建", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(
            text="本节我们学习二叉排序树的创建算法，该算法是通过依次读入关键字为key的结点，将相应结点插入到二叉排序树中。",
            subcaption="本节我们学习二叉排序树的创建算法，该算法是通过依次读入关键字为key的结点，将相应结点插入到二叉排序树中。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE A0 — 生活实例 (家族树) =====
        self.play(FadeOut(algo_title))

        with self.voiceover(
            text="在学习具体的创建算法之前，我们先来看一个生活实例：从零开始，建立一个按年龄大小组织的家族树。",
            subcaption="在学习具体的创建算法之前，我们先来看一个生活实例：从零开始，建立一个按年龄大小组织的家族树。"
        ) as tracker:
            example_title = Text("生活实例：从零创建家族树", font_size=36, color=YELLOW).to_edge(UP, buff=0.6)
            rule_text = Text("规则：年龄较小的人放左边，年龄较大的人放右边", font_size=24, color=WHITE).next_to(example_title, DOWN, buff=0.4)
            self.play(FadeIn(example_title), FadeIn(rule_text))
            
        def make_family_node(name, age, center, r=0.5, color=BLUE):
            c = Circle(radius=r, color=color, fill_color=color, fill_opacity=0.15, stroke_width=2.5).move_to(center)
            t_name = Text(name, font="Microsoft YaHei", font_size=18, color=WHITE)
            t_age = Text(str(age), font="Arial", font_size=18, color=YELLOW)
            t_group = VGroup(t_name, t_age).arrange(DOWN, buff=0.05).move_to(center)
            g = VGroup(c, t_group)
            g.circle = c
            return g

        pos_f = {
            'N70': np.array([1.5, 0.8, 0]),
            'N45': np.array([0.0, -0.4, 0]),
            'N50': np.array([1.5, -1.6, 0]),
            'N20': np.array([-1.5, -1.6, 0]),
        }
        
        f_nodes = {
            'N70': make_family_node("爷爷", 70, pos_f['N70']),
            'N45': make_family_node("爸爸", 45, pos_f['N45']),
            'N50': make_family_node("大伯", 50, pos_f['N50']),
            'N20': make_family_node("我", 20, pos_f['N20']),
        }
        
        f_edges = {
            'E70_45': self.edge(pos_f['N70'], pos_f['N45'], r1=0.5, r2=0.5),
            'E45_20': self.edge(pos_f['N45'], pos_f['N20'], r1=0.5, r2=0.5),
            'E45_50': self.edge(pos_f['N45'], pos_f['N50'], r1=0.5, r2=0.5),
        }
        
        with self.voiceover(
            text="一开始，家族树是空的。第一位加入的是爷爷，70岁。由于树是空的，爷爷直接成为家族树的根结点。",
            subcaption="一开始，家族树是空的。第一位加入的是爷爷，70岁。由于树是空的，爷爷直接成为家族树的根结点。"
        ) as tracker:
            self.play(FadeIn(f_nodes['N70']))
            self.wait(max(0.1, tracker.duration - 1.0))
            
        with self.voiceover(
            text="第二位加入的是爸爸，45岁。因为 45岁 小于爷爷的 70岁，所以爸爸被安排在爷爷的左边。",
            subcaption="第二位加入的是爸爸，45岁。因为 45岁 小于爷爷的 70岁，所以爸爸被安排在爷爷的左边。"
        ) as tracker:
            self.play(f_nodes['N70'].circle.animate.set_color(RED).set_fill(RED, opacity=0.8), run_time=0.5)
            self.play(Create(f_edges['E70_45']), FadeIn(f_nodes['N45']), run_time=1.0)
            self.play(f_nodes['N70'].circle.animate.set_color(BLUE).set_fill(BLUE, opacity=0.15), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 2.0))
            
        with self.voiceover(
            text="第三位加入的是大伯，今年五十岁。五十小于七十，所以从爷爷这里往左走。",
            subcaption="第三位加入的是大伯，50 岁。50 < 70，所以从爷爷这里往左走。"
        ) as tracker:
            self.play(f_nodes['N70'].circle.animate.set_color(RED).set_fill(RED, opacity=0.8), run_time=0.4)
            self.play(f_nodes['N70'].circle.animate.set_color(BLUE).set_fill(BLUE, opacity=0.15),
                      f_nodes['N45'].circle.animate.set_color(RED).set_fill(RED, opacity=0.8), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
            text="接着比较爸爸的年龄。五十大于四十五，所以把大伯安排在爸爸的右边。",
            subcaption="接着与爸爸的 45 岁比较。50 > 45，所以把大伯安排在爸爸的右边。"
        ) as tracker:
            self.play(Create(f_edges['E45_50']), FadeIn(f_nodes['N50']), run_time=1.0)
            self.play(f_nodes['N45'].circle.animate.set_color(BLUE).set_fill(BLUE, opacity=0.15), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 1.4))
            
        with self.voiceover(
            text="最后加入的是我，20岁。20岁 小于爷爷的 70岁，去左边；20岁 也小于爸爸的 45岁，去左边。爸爸的左边是空位，于是我就安排在这里。",
            subcaption="最后加入的是我，20岁。20岁 小于爷爷的 70岁，去左边；20岁 也小于爸爸的 45岁，去左边。爸爸的左边是空位，于是我就安排在这里。"
        ) as tracker:
            self.play(f_nodes['N70'].circle.animate.set_color(RED).set_fill(RED, opacity=0.8), run_time=0.4)
            self.play(f_nodes['N70'].circle.animate.set_color(BLUE).set_fill(BLUE, opacity=0.15),
                      f_nodes['N45'].circle.animate.set_color(RED).set_fill(RED, opacity=0.8), run_time=0.4)
            self.play(Create(f_edges['E45_20']), FadeIn(f_nodes['N20']), run_time=1.0)
            self.play(f_nodes['N45'].circle.animate.set_color(BLUE).set_fill(BLUE, opacity=0.15), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 2.2))
            
        with self.voiceover(
            text="这就是创建家族树的过程：从一个空树开始，每来一个新成员，就从根部逐级比较，找到空位并放入。二叉排序树的创建也是同样的原理。",
            subcaption="这就是创建家族树的过程：从一个空树开始，每来一个新成员，就从根部逐级比较，找到空位并放入。二叉排序树的创建也是同样的原理。"
        ) as tracker:
            self.wait(tracker.duration)
            
        # Clean up Life Example
        self.play(
            FadeOut(VGroup(*f_nodes.values(), *f_edges.values())), 
            FadeOut(example_title), FadeOut(rule_text)
        )
        self.play(FadeIn(algo_title))

        # ===== PHASE A1 — 算法思想 =====
        logic_title = Text("二叉排序树创建核心逻辑", font_size=32, font="Microsoft YaHei", color=YELLOW)
        logic_1 = Text("1. 将二叉排序树 T 初始化为空树", font_size=20, font="Microsoft YaHei")
        logic_2 = Text("2. 依次读入序列中的关键字 key", font_size=20, font="Microsoft YaHei")
        logic_3 = Text("3. 将读入的 key 插入到二叉排序树 T 中", font_size=20, font="Microsoft YaHei")
        
        logic_group = VGroup(logic_title, logic_1, logic_2, logic_3).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        logic_box = RoundedRectangle(
            corner_radius=0.2,
            height=logic_group.get_height() + 0.8,
            width=logic_group.get_width() + 0.8,
            color=BLUE, fill_color=BLACK, fill_opacity=0.85, stroke_width=2
        )
        logic_box.move_to(logic_group)
        logic_panel = VGroup(logic_box, logic_group).next_to(algo_title, DOWN, buff=0.5)

        with self.voiceover(
            text="正如刚才生活实例所展示的，创建二叉排序树的过程就是从一棵空树开始，逐个插入的过程。",
            subcaption="正如刚才生活实例所展示的，创建二叉排序树的过程就是从一棵空树开始，逐个插入的过程。"
        ) as tracker:
            self.play(FadeIn(logic_box), FadeIn(logic_title), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))
            
        with self.voiceover(
            text="第一步，需要将二叉排序树 T 初始化为空树，这对应着最初没有任何元素的状态。",
            subcaption="第一步，需要将二叉排序树 T 初始化为空树，这对应着最初没有任何元素的状态。"
        ) as tracker:
            self.play(FadeIn(logic_1), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(
            text="第二步，依次按顺序读入数据序列中的每一个待插入的关键字 key。",
            subcaption="第二步，依次按顺序读入数据序列中的每一个待插入的关键字 key。"
        ) as tracker:
            self.play(FadeIn(logic_2), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))
            
        with self.voiceover(
            text="第三步，针对每个读入的 key 反复调用插入算法，从根结点开始比较，寻找属于它的空位并将其链接到树 T 中。",
            subcaption="第三步，针对每个读入的 key 反复调用插入算法，从根结点开始比较，寻找属于它的空位并将其链接到树 T 中。"
        ) as tracker:
            self.play(FadeIn(logic_3), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))
            
        with self.voiceover(
            text="不断循环上述读取和插入的操作，直到序列中所有的元素都被处理完，一棵完整的二叉排序树也就创建完成了。",
            subcaption="不断循环上述读取和插入的操作，直到序列中所有的元素都被处理完，一棵完整的二叉排序树也就创建完成了。"
        ) as tracker:
            self.wait(tracker.duration)

        self.play(FadeOut(logic_panel))

        # ===== PHASE B — CODE BLOCK CONFIG =====
        c_lines = [
            "void InsertBST(BSTree &T, ElemType e) {",
            "    if (!T) {",
            "        BSTree S = new BSTNode;",
            "        S->data = e;",
            "        S->lchild = S->rchild = NULL;",
            "        T = S;",
            "    }",
            "    else if (e.key < T->data.key)",
            "        InsertBST(T->lchild, e);",
            "    else if (e.key > T->data.key)",
            "        InsertBST(T->rchild, e);",
            "}"
        ]

        IDX_FUNC = 0
        IDX_IF_NULL = 1
        IDX_NEW_S = 2
        IDX_S_DATA = 3
        IDX_S_CHILD = 4
        IDX_T_EQ_S = 5
        IDX_LESS = 7
        IDX_INS_L = 8
        IDX_GREATER = 9
        IDX_INS_R = 10

        self.c_texts = []
        for line in c_lines:
            t = Text(line.lstrip(" "), font_size=15, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        SPACE_WIDTH = 0.11
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        code_bg = RoundedRectangle(
            corner_radius=0.2,
            height=code_group.get_height() + 0.5,
            width=code_group.get_width() + 0.5,
            color=GRAY, fill_opacity=0.1, stroke_width=1
        )
        code_bg.move_to(code_group)
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.2).to_edge(RIGHT, buff=0.2)

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

        def play_track(new_idx, run_time=0.3):
            anims = get_track_anims(new_idx)
            if anims:
                self.play(*anims, run_time=run_time)

        with self.voiceover(
            text="我们来看看单次插入的具体代码实现。",
            subcaption="我们来看看单次插入的具体代码实现。"
        ) as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # ===== PHASE C — 动画演示 =====
        with self.voiceover(
            text="初始时，将树 T 初始化为空树。现在开始按顺序读入关键字。",
            subcaption="初始时，将树 T 初始化为空树。现在开始按顺序读入关键字。"
        ) as tracker:
            self.wait(max(0.1, tracker.duration))

        # Input array
        input_vals = [45, 24, 53, 12, 37, 93]
        array_group = VGroup()
        squares = VGroup()
        texts = VGroup()
        for i, val in enumerate(input_vals):
            sq = Square(side_length=0.6, color=WHITE)
            t = Text(str(val), font_size=24)
            sq_t = VGroup(sq, t).arrange(ORIGIN)
            array_group.add(sq_t)
            squares.add(sq)
            texts.add(t)
        
        array_group.arrange(RIGHT, buff=0).to_edge(UP, buff=1.8).shift(LEFT * 2)

        with self.voiceover(
            text="假设我们需要按照顺序插入这些关键字来构建二叉排序树。",
            subcaption="假设我们需要按照顺序插入这些关键字来构建二叉排序树。"
        ) as tracker:
            self.play(FadeIn(array_group), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        root = None
        tree_nodes = []
        tree_edges = []
        # Keep a visible gap below the input cells, even while a cell is highlighted.
        root_pos = np.array([-3.0, array_group.get_bottom()[1] - 0.8 - self.NODE_R, 0])

        for i, val in enumerate(input_vals):
            with self.voiceover(
                text=f"现在准备插入关键字 {val}。",
                subcaption=f"现在准备插入关键字 {val}。"
            ) as tracker:
                self.play(squares[i].animate.set_color(YELLOW), run_time=0.3)
                self.wait(max(0.1, tracker.duration - 0.3))
                
            # Insert logic
            if root is None:
                with self.voiceover(
                    text="当前树为空，因此直接作为根结点插入。",
                    subcaption="当前树为空，因此直接作为根结点插入。"
                ) as tracker2:
                    play_track(IDX_FUNC, run_time=0.3)
                    play_track(IDX_IF_NULL, run_time=0.3)
                    play_track(IDX_NEW_S, run_time=0.3)

                    root = BSTNode(val, root_pos)
                    root.mobject = self.make_node(val, root_pos, color=YELLOW)
                    tree_nodes.append(root)
                    self.play(FadeIn(root.mobject), run_time=0.5)

                    play_track(IDX_S_DATA, run_time=0.2)
                    play_track(IDX_S_CHILD, run_time=0.2)
                    play_track(IDX_T_EQ_S, run_time=0.2)

                    self.play(root.mobject.circle.animate.set_color(BLUE).set_fill(BLUE, opacity=0.15), run_time=0.3)
            else:
                curr = root
                h_sep = 1.6
                v_sep = 1.0
                play_track(IDX_FUNC, run_time=0.3)
                
                while curr is not None:
                    self.play(curr.mobject.circle.animate.set_color(RED).set_fill(RED, opacity=0.8), run_time=0.3)
                    if val < curr.val:
                        with self.voiceover(
                            text=f"由于 {val} 小于当前结点 {curr.val}，因此进入左子树。",
                            subcaption=f"由于 {val} 小于当前结点 {curr.val}，因此进入左子树。"
                        ) as tracker3:
                            play_track(IDX_LESS, run_time=0.3)
                            play_track(IDX_INS_L, run_time=0.3)
                            self.wait(max(0.1, tracker3.duration - 0.6))
                            
                        if curr.left is None:
                            with self.voiceover(
                                text="发现左子树为空，所以在这里新建结点并插入。",
                                subcaption="发现左子树为空，所以在这里新建结点并插入。"
                            ) as tracker4:
                                play_track(IDX_FUNC, run_time=0.3)
                                play_track(IDX_IF_NULL, run_time=0.3)
                                play_track(IDX_NEW_S, run_time=0.3)
                                
                                new_pos = curr.pos + np.array([-h_sep, -v_sep, 0])
                                new_node = BSTNode(val, new_pos)
                                new_node.mobject = self.make_node(val, new_pos, color=YELLOW)
                                tree_nodes.append(new_node)
                                edge = self.edge(curr.pos, new_pos, color=YELLOW)
                                curr.left = new_node
                                curr.edge_left = edge
                                tree_edges.append(edge)
                                self.play(Create(edge), FadeIn(new_node.mobject), run_time=0.5)
                                
                                play_track(IDX_S_DATA, run_time=0.2)
                                play_track(IDX_S_CHILD, run_time=0.2)
                                play_track(IDX_T_EQ_S, run_time=0.2)
                                
                                self.play(new_node.mobject.circle.animate.set_color(BLUE).set_fill(BLUE, opacity=0.15),
                                          edge.animate.set_color(GRAY), run_time=0.3)
                            break
                        else:
                            self.play(curr.mobject.circle.animate.set_color(GREEN).set_fill(GREEN, opacity=0.8), run_time=0.2)
                            curr = curr.left
                            h_sep *= 0.6
                            play_track(IDX_FUNC, run_time=0.2)
                    else:
                        with self.voiceover(
                            text=f"由于 {val} 大于当前结点 {curr.val}，因此进入右子树。",
                            subcaption=f"由于 {val} 大于当前结点 {curr.val}，因此进入右子树。"
                        ) as tracker3:
                            play_track(IDX_LESS, run_time=0.2)
                            play_track(IDX_GREATER, run_time=0.3)
                            play_track(IDX_INS_R, run_time=0.3)
                            self.wait(max(0.1, tracker3.duration - 0.8))
                            
                        if curr.right is None:
                            with self.voiceover(
                                text="发现右子树为空，所以在这里新建结点并插入。",
                                subcaption="发现右子树为空，所以在这里新建结点并插入。"
                            ) as tracker4:
                                play_track(IDX_FUNC, run_time=0.3)
                                play_track(IDX_IF_NULL, run_time=0.3)
                                play_track(IDX_NEW_S, run_time=0.3)
                                
                                new_pos = curr.pos + np.array([h_sep, -v_sep, 0])
                                new_node = BSTNode(val, new_pos)
                                new_node.mobject = self.make_node(val, new_pos, color=YELLOW)
                                tree_nodes.append(new_node)
                                edge = self.edge(curr.pos, new_pos, color=YELLOW)
                                curr.right = new_node
                                curr.edge_right = edge
                                tree_edges.append(edge)
                                self.play(Create(edge), FadeIn(new_node.mobject), run_time=0.5)
                                
                                play_track(IDX_S_DATA, run_time=0.2)
                                play_track(IDX_S_CHILD, run_time=0.2)
                                play_track(IDX_T_EQ_S, run_time=0.2)
                                
                                self.play(new_node.mobject.circle.animate.set_color(BLUE).set_fill(BLUE, opacity=0.15),
                                          edge.animate.set_color(GRAY), run_time=0.3)
                            break
                        else:
                            self.play(curr.mobject.circle.animate.set_color(GREEN).set_fill(GREEN, opacity=0.8), run_time=0.2)
                            curr = curr.right
                            h_sep *= 0.6
                            play_track(IDX_FUNC, run_time=0.2)
                
                # Reset colors
                reset_anims = [node.mobject.circle.animate.set_color(BLUE).set_fill(BLUE, opacity=0.15) for node in tree_nodes]
                if reset_anims:
                    self.play(*reset_anims, run_time=0.3)
            
            self.play(squares[i].animate.set_color(GRAY), run_time=0.2)
            play_track(None, run_time=0.2)

        with self.voiceover(
            text="循环结束，一棵二叉排序树就创建完成了。",
            subcaption="循环结束，一棵二叉排序树就创建完成了。"
        ) as tracker:
            play_track(None, run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.5))

        # ===== PHASE D — 复杂度分析 =====
        time_box = VGroup(Text("时间复杂度：", font_size=28, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(N \\log N)", font_size=32, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=28, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(N)", font_size=32, color=YELLOW)).arrange(RIGHT, buff=0.1)
        summary = VGroup(time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        summary.to_edge(RIGHT, buff=2.0).shift(DOWN * 1.5)
        
        self.play(FadeOut(code_block), run_time=0.5)
        
        with self.voiceover(
            text="分析一下时空复杂度。创建二叉排序树需要依次插入 N 个结点，每次插入平均需要 O(log N) 的时间。",
            subcaption="分析一下时空复杂度。创建二叉排序树需要依次插入 N 个结点，每次插入平均需要 O(log N) 的时间。"
        ) as tracker:
            self.wait(tracker.duration)
            
        with self.voiceover(
            text="因此创建二叉排序树的平均时间复杂度为 O(N log N)。",
            subcaption="因此创建二叉排序树的平均时间复杂度为 O(N log N)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))
            
        with self.voiceover(
            text="空间复杂度方面，N 个结点本身的存储空间为 O(N)，这也是其整体的空间复杂度。此外，递归调用的辅助栈空间平均为 O(log N)。",
            subcaption="空间复杂度方面，N 个结点本身的存储空间为 O(N)，这也是其整体的空间复杂度。此外，递归调用的辅助栈空间平均为 O(log N)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))
            
        with self.voiceover(
            text="以上就是二叉排序树创建算法的演示。",
            subcaption="以上就是二叉排序树创建算法的演示。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)
