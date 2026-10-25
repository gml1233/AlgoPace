# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class BSTInsertionVideo(VoiceoverScene):
    NODE_R = 0.35

    def make_node(self, label, center, r=None, color=BLUE):
        r = self.NODE_R if r is None else r
        c = Circle(radius=r, color=color, fill_color=color, fill_opacity=0.15, stroke_width=2.5).move_to(center)
        t = Text(str(label), font="Arial", font_size=20, color=WHITE).move_to(center)
        g = VGroup(c, t)
        g.circle = c
        g.label = t
        g.radius = r
        return g

    def edge(self, p1, p2, r1=None, r2=None, color=GRAY, sw=2.5):
        r1 = self.NODE_R if r1 is None else r1
        r2 = self.NODE_R if r2 is None else r2
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        return Line(p1 + u * r1, p2 - u * r2, color=color, stroke_width=sw)

    def null_edge(self, p1, direction, r1=None, color=GRAY, sw=2.5):
        r1 = self.NODE_R if r1 is None else r1
        p1 = np.array(p1, dtype=float)
        direction = np.array(direction, dtype=float)
        direction = direction / np.linalg.norm(direction)
        start = p1 + direction * r1
        end = start + direction * 0.5
        l = Line(start, end, color=color, stroke_width=sw)
        nul = Text("NULL", font_size=16, color=GRAY_B).move_to(end + direction * 0.25)
        g = VGroup(l, nul)
        g.line = l
        g.nul = nul
        return g

    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE & INTRO =====
        algo_title = Text("二叉排序树的插入", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(
            text="本节我们学习二叉排序树的插入算法。该算法是在二叉排序树中插入一个不存在的新元素",
            subcaption="本节我们学习二叉排序树的插入算法。该算法是在二叉排序树中插入一个不存在的新元素"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE A1 — 生活实例 (家族树) =====
        self.play(FadeOut(algo_title))

        with self.voiceover(
            text="在学习具体的插入算法之前，我们先来看一个生活实例：建立一个按年龄大小组织的家族树。",
            subcaption="在学习具体的插入算法之前，我们先来看一个生活实例：建立一个按年龄大小组织的家族树。"
        ) as tracker:
            example_title = Text("生活实例：按年龄组织的家族树", font_size=36, color=YELLOW).to_edge(UP, buff=0.6)
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
        
        f_edges = VGroup(
            self.edge(pos_f['N70'], pos_f['N45'], r1=0.5, r2=0.5),
            self.edge(pos_f['N45'], pos_f['N20'], r1=0.5, r2=0.5),
            self.edge(pos_f['N45'], pos_f['N50'], r1=0.5, r2=0.5),
        )
        
        family_group = VGroup(f_edges, *f_nodes.values())
        
        with self.voiceover(
            text="假设现在已经有这样一棵家族树：爷爷 70 岁是根结点；爸爸 45 岁比爷爷小在左边，大伯 50 岁比爸爸大，在爸爸的右边；我 20 岁在爸爸左边。",
            subcaption="假设现在已经有这样一棵家族树：爷爷 70 岁是根结点；爸爸 45 岁比爷爷小在左边，大伯 50 岁比爸爸大，在爸爸的右边；我 20 岁在爸爸左边。"
        ) as tracker:
            self.play(FadeIn(family_group), run_time=tracker.duration)
            
        with self.voiceover(
            text="现在新增一个家庭成员：弟弟 15 岁。我们需要找到他应该待的位置。",
            subcaption="现在新增一个家庭成员：弟弟 15 岁。我们需要找到他应该待的位置。"
        ) as tracker:
            target_text = Text("新增成员：弟弟 (15)", font_size=28, color=GREEN).next_to(rule_text, DOWN, buff=0.4)
            self.play(FadeIn(target_text))
            
        def set_f_node(node_key, run_time=0.5):
            anims = []
            if getattr(self, 'cur_f_node', None) is not None:
                anims.append(f_nodes[self.cur_f_node].circle.animate.set_color(GREEN).set_fill(GREEN, opacity=0.8))
            if node_key is not None:
                anims.append(f_nodes[node_key].circle.animate.set_color(RED).set_fill(RED, opacity=0.8))
            self.cur_f_node = node_key
            if anims:
                return AnimationGroup(*anims, run_time=run_time)
            return AnimationGroup(run_time=run_time)

        self.cur_f_node = None
        
        with self.voiceover(
            text="第一步比较根结点爷爷的 70 岁，15 小于 70，所以去左边找。",
            subcaption="第一步比较根结点爷爷的 70 岁，15 小于 70，所以去左边找。"
        ) as tracker:
            self.play(set_f_node('N70'))
            
        with self.voiceover(
            text="第二步遇到爸爸的 45 岁，15 依然小于 45，继续去左边。",
            subcaption="第二步遇到爸爸的 45 岁，15 依然小于 45，继续去左边。"
        ) as tracker:
            self.play(set_f_node('N45'))
            
        with self.voiceover(
            text="第三步遇到我的 20 岁，15 还是小于 20，因此去我的左边。",
            subcaption="第三步遇到我的 20 岁，15 还是小于 20，因此去我的左边。"
        ) as tracker:
            self.play(set_f_node('N20'))
            
        with self.voiceover(
            text="发现我的左边已经是空位了，这就是弟弟的最终插入位置。",
            subcaption="发现我的左边已经是空位了，这就是弟弟的最终插入位置。"
        ) as tracker:
            self.play(set_f_node(None))
            pos_f['N15'] = np.array([-3.0, -2.8, 0])
            f_nodes['N15'] = make_family_node("弟弟", 15, pos_f['N15'], color=YELLOW)
            e_20_15 = self.edge(pos_f['N20'], pos_f['N15'], r1=0.5, r2=0.5, color=YELLOW)
            self.play(FadeIn(f_nodes['N15']), Create(e_20_15))
            
        with self.voiceover(
            text="通过这个简单直观的比较过程，我们就能把新的结点安置在正确的位置。",
            subcaption="通过这个简单直观的比较过程，我们就能把新的结点安置在正确的位置。"
        ) as tracker:
            self.wait(tracker.duration)
            
        # Clean up Life Example
        self.play(FadeOut(family_group), FadeOut(example_title), FadeOut(rule_text), FadeOut(target_text), FadeOut(f_nodes['N15']), FadeOut(e_20_15))
        self.play(FadeIn(algo_title))

        # ===== PHASE C — 场景初始化 (绘制初始 BST) =====
        # Sequence: 45, 24, 53, 12, 37, 93
        pos = {
            'N45': np.array([-3.0, 1.55, 0]),
            'N24': np.array([-4.45, 0.20, 0]),
            'N53': np.array([-1.55, 0.20, 0]),
            'N12': np.array([-5.25, -1.20, 0]),
            'N37': np.array([-3.65, -1.20, 0]),
            'N93': np.array([-1.10, -1.20, 0]),
        }

        nodes = {}
        for k, p in pos.items():
            val = int(k[1:])
            nodes[k] = self.make_node(val, p)

        edges = VGroup(
            self.edge(pos['N45'], pos['N24']),
            self.edge(pos['N45'], pos['N53']),
            self.edge(pos['N24'], pos['N12']),
            self.edge(pos['N24'], pos['N37']),
            self.edge(pos['N53'], pos['N93']),
        )
        
        tree_group = VGroup(edges, *nodes.values())
        
        with self.voiceover(
            text="这里有一棵已经构建好的二叉排序树，我们在左侧展示出来。",
            subcaption="这里有一棵已经构建好的二叉排序树，我们在左侧展示出来。"
        ) as tracker:
            self.play(FadeIn(tree_group), run_time=tracker.duration)

        with self.voiceover(
            text="在接下来的演示中，我们将当前正在比较的结点标记为红色，而已经经过的路径结点将标记为绿色。",
            subcaption="在接下来的演示中，我们将当前正在比较的结点标记为红色，而已经经过的路径结点将标记为绿色。"
        ) as tracker:
            self.wait(tracker.duration)

        self.current_node = None
        
        def set_current_node(node_key, run_time=0.6):
            anims = []
            if self.current_node is not None and self.current_node in nodes:
                anims.append(nodes[self.current_node].circle.animate.set_color(GREEN).set_fill(GREEN, opacity=0.8))
            if node_key is not None and node_key in nodes:
                anims.append(nodes[node_key].circle.animate.set_color(RED).set_fill(RED, opacity=0.8))
            self.current_node = node_key
            if anims:
                return AnimationGroup(*anims, run_time=run_time)
            return AnimationGroup(run_time=run_time)

        # ===== PHASE A2 — 思想讲解 (Logic Panel) =====
        logic_title = Text("二叉排序树插入核心逻辑", font_size=32, font="Microsoft YaHei", color=YELLOW)
        logic_1 = Text("1. 若树为空，则将待插入结点作为根结点插入", font_size=20, font="Microsoft YaHei")
        logic_2 = Text("2. 若树非空，比较目标值与当前结点关键字", font_size=20, font="Microsoft YaHei")
        logic_3 = Text("3. 若较小，则向左子树递归寻找插入位置", font_size=20, font="Microsoft YaHei")
        logic_4 = Text("4. 若较大，则向右子树递归寻找插入位置", font_size=20, font="Microsoft YaHei")
        logic_5 = Text("5. 找到空位（NULL）后，新建结点并链接", font_size=20, font="Microsoft YaHei")

        logic_group = VGroup(logic_title, logic_1, logic_2, logic_3, logic_4, logic_5).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        logic_box = RoundedRectangle(
            corner_radius=0.2,
            height=logic_group.get_height() + 0.8,
            width=logic_group.get_width() + 0.8,
            color=BLUE, fill_color=BLACK, fill_opacity=0.85, stroke_width=2
        )
        logic_box.move_to(logic_group)
        logic_panel = VGroup(logic_box, logic_group).to_edge(RIGHT, buff=0.5)

        with self.voiceover(
            text="插入操作的核心思想是：首先沿着树查找合适的插入位置，就像我们查找结点一样。",
            subcaption="插入操作的核心思想是：首先沿着树查找合适的插入位置，就像我们查找结点一样。"
        ) as tracker:
            self.play(FadeIn(logic_box), FadeIn(logic_title), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))
            
        with self.voiceover(
            text="若遇到空树则直接插入；若非空，较小就往左走，较大就往右走。当找到空指针时，即可新建结点并链接上去。",
            subcaption="若遇到空树则直接插入；若非空，较小就往左走，较大就往右走。当找到空指针时，即可新建结点并链接上去。"
        ) as tracker:
            self.play(FadeIn(logic_1), FadeIn(logic_2), FadeIn(logic_3), FadeIn(logic_4), FadeIn(logic_5), run_time=2.0)
            self.wait(max(0.1, tracker.duration - 2.0))

        self.play(FadeOut(logic_panel))
        
        with self.voiceover(
            text="接下来，我们看看具体的算法代码。",
            subcaption="接下来，我们看看具体的算法代码。"
        ) as tracker:
            self.wait(tracker.duration)

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

        self.play(FadeIn(code_block), run_time=0.8)

        # ===== PHASE D — 插入演示 (50) =====
        with self.voiceover(
            text="我们来演示插入一个新关键字 50。",
            subcaption="我们来演示插入一个新关键字 50。"
        ) as tracker:
            t_label = Text("待插入值 ", font_size=26, color=YELLOW)
            t_val = Text("key = 50", font="Arial", font_size=26, color=YELLOW)
            search_text = VGroup(t_label, t_val).arrange(RIGHT, buff=0.1).to_edge(UP, buff=1.5).shift(LEFT * 3)
            self.play(FadeIn(search_text))
            
        with self.voiceover(
            text="首次调用插入函数，传入根结点指针和值 50。树非空，触发比较判断。",
            subcaption="首次调用插入函数，传入根结点指针和值 50。树非空，触发比较判断。"
        ) as tracker:
            self.play(*get_track_anims(IDX_FUNC), run_time=0.3)
            self.play(set_current_node('N45', run_time=0.5))
            self.play(*get_track_anims(IDX_GREATER), run_time=0.5)

        with self.voiceover(
            text="因为 50 大于根结点 45，所以我们将向右子树递归插入。",
            subcaption="因为 50 大于根结点 45，所以我们将向右子树递归插入。"
        ) as tracker:
            self.play(*get_track_anims(IDX_INS_R), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.5))
            
        with self.voiceover(
            text="进入第二层递归，当前结点来到 53。树非空，继续比较。",
            subcaption="进入第二层递归，当前结点来到 53。树非空，继续比较。"
        ) as tracker:
            self.play(*get_track_anims(IDX_FUNC), run_time=0.3)
            self.play(set_current_node('N53', run_time=0.5))
            self.play(*get_track_anims(IDX_LESS), run_time=0.5)
            
        with self.voiceover(
            text="因为 50 小于 53，所以我们将向左子树递归插入。",
            subcaption="因为 50 小于 53，所以我们将向左子树递归插入。"
        ) as tracker:
            self.play(*get_track_anims(IDX_INS_L), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.5))

        with self.voiceover(
            text="进入第三层递归，由于 53 没有左孩子，此时传入的指针 T 为 NULL。",
            subcaption="进入第三层递归，由于 53 没有左孩子，此时传入的指针 T 为 NULL。"
        ) as tracker:
            self.play(*get_track_anims(IDX_FUNC), run_time=0.3)
            self.play(set_current_node(None, run_time=0.5))
            null_e = self.null_edge(pos['N53'], LEFT + DOWN * 0.8)
            self.play(FadeIn(null_e), run_time=0.5)
            self.play(*get_track_anims(IDX_IF_NULL), run_time=0.5)
            self.play(Indicate(null_e.nul, color=RED, scale_factor=1.2), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 2.3))

        with self.voiceover(
            text="符合空树条件，这说明我们找到了合适的插入位置。开始创建新结点 S。",
            subcaption="符合空树条件，这说明我们找到了合适的插入位置。开始创建新结点 S。"
        ) as tracker:
            self.play(*get_track_anims(IDX_NEW_S), run_time=0.5)
            pos['N50'] = np.array([-2.15, -1.20, 0])
            nodes['N50'] = self.make_node(50, pos['N50'], color=YELLOW)
            self.play(FadeOut(null_e), FadeIn(nodes['N50'].circle), run_time=0.5)
            
        with self.voiceover(
            text="将新结点的数据域置为 50，左右孩子置为空。",
            subcaption="将新结点的数据域置为 50，左右孩子置为空。"
        ) as tracker:
            self.play(*get_track_anims(IDX_S_DATA), run_time=0.3)
            self.play(FadeIn(nodes['N50'].label), run_time=0.5)
            self.play(*get_track_anims(IDX_S_CHILD), run_time=0.3)
            
        with self.voiceover(
            text="最后，将 T 指向新结点 S。由于 T 是引用传递，这也相当于把新结点链接到了父结点 53 的左孩子指针上。",
            subcaption="最后，将 T 指向新结点 S。由于 T 是引用传递，这也相当于把新结点链接到了父结点 53 的左孩子指针上。"
        ) as tracker:
            self.play(*get_track_anims(IDX_T_EQ_S), run_time=0.5)
            e53_50 = self.edge(pos['N53'], pos['N50'], color=YELLOW)
            edges.add(e53_50)
            self.play(Create(e53_50), nodes['N50'].circle.animate.set_color(BLUE).set_fill(BLUE, opacity=0.15), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 1.3))

        with self.voiceover(
            text="至此，插入 50 成功完成，递归逐层返回。",
            subcaption="至此，插入 50 成功完成，递归逐层返回。"
        ) as tracker:
            self.play(*get_track_anims(None), FadeOut(search_text), run_time=0.5)
            reset_anims = [n.circle.animate.set_color(BLUE).set_fill(BLUE, opacity=0.15) for n in nodes.values()]
            self.play(*reset_anims, run_time=0.8)

        # ===== PHASE E — 复杂度分析 =====
        time_box = VGroup(Text("时间复杂度：", font_size=28, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(\\log N)", font_size=32, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=28, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(h)", font_size=32, color=YELLOW)).arrange(RIGHT, buff=0.1)
        summary = VGroup(time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        summary.to_edge(RIGHT, buff=2.0)
        
        self.play(FadeOut(code_block), run_time=0.5)
        
        with self.voiceover(
            text="总结一下，二叉排序树插入操作需要先沿树查找插入位置，因此时间复杂度与查找操作相同。",
            subcaption="总结一下，二叉排序树插入操作需要先沿树查找插入位置，因此时间复杂度与查找操作相同。"
        ) as tracker:
            self.wait(tracker.duration)
            
        with self.voiceover(
            text="如果树较为平衡，插入一个结点的时间复杂度为 O(log N)；若树退化成单链表，则为 O(N)。",
            subcaption="如果树较为平衡，插入一个结点的时间复杂度为 O(log N)；若树退化成单链表，则为 O(N)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))
            
        with self.voiceover(
            text="由于采用递归方式，空间复杂度主要来自递归调用栈，大小为树高 O(h)。",
            subcaption="由于采用递归方式，空间复杂度主要来自递归调用栈，大小为树高 O(h)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))
            
        with self.voiceover(
            text="以上就是二叉排序树的插入算法演示。",
            subcaption="以上就是二叉排序树的插入算法演示。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)
