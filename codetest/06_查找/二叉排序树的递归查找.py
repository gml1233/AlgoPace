# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class BSTRecursiveSearchVideo(VoiceoverScene):
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
        algo_title = Text("二叉排序树的递归查找", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(
            text="本节我们学习二叉排序树的递归查找算法。该算法是在二叉排序树中递归地查找某关键字等于key的数据元素。若查找成功，则返回指向该数据元素结点的指针，否则返回空指针。",
            subcaption="本节我们学习二叉排序树的递归查找算法。该算法是在二叉排序树中递归地查找某关键字等于key的数据元素。若查找成功，则返回指向该数据元素结点的指针，否则返回空指针。"
        ) as tracker:
            self.wait(tracker.duration)



        # ===== PHASE C — 场景初始化 (绘制 BST) =====
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
        
        # Add a null edge to N93 left child for the failed search demonstration
        null_e = self.null_edge(pos['N93'], LEFT + DOWN * 0.8)
        
        tree_group = VGroup(edges, *nodes.values())
        
        with self.voiceover(
            text="这里有一棵已经构建好的二叉排序树，我们在左侧展示出来。",
            subcaption="这里有一棵已经构建好的二叉排序树，我们在左侧展示出来。"
        ) as tracker:
            self.play(FadeIn(tree_group), run_time=tracker.duration)

        with self.voiceover(
            text="在接下来的查找演示中，我们将当前正在访问的结点标记为红色，而已经访问过的路径结点将标记为绿色。",
            subcaption="在接下来的查找演示中，我们将当前正在访问的结点标记为红色，而已经访问过的路径结点将标记为绿色。"
        ) as tracker:
            self.wait(tracker.duration)

        self.current_node = None
        
        def set_current_node(node_key, run_time=0.6):
            anims = []
            if self.current_node is not None:
                anims.append(nodes[self.current_node].circle.animate.set_color(GREEN).set_fill(GREEN, opacity=0.8))
            if node_key is not None:
                anims.append(nodes[node_key].circle.animate.set_color(RED).set_fill(RED, opacity=0.8))
            self.current_node = node_key
            if anims:
                return AnimationGroup(*anims, run_time=run_time)
            return AnimationGroup(run_time=run_time)

        # ===== PHASE C.5 — 生活实例：猜数字 =====
        with self.voiceover(
            text="在深入代码之前，我们以猜数字为例。假设一个人心里想了一个 1 到 100 之间的数字，你要猜出它是多少。",
            subcaption="在深入代码之前，我们以猜数字为例。假设一个人心里想了一个 1 到 100 之间的数字，你要猜出它是多少。"
        ) as tracker:
            example_title = Text("生活实例：猜数字 (1~100)", font_size=28, color=YELLOW).to_edge(UP, buff=1.5).shift(RIGHT * 3.5)
            self.play(FadeIn(example_title))
            
        with self.voiceover(
            text="现在已经建立了这棵二叉排序树，假设我们要查找的数字是 37。",
            subcaption="现在已经建立了这棵二叉排序树，假设我们要查找的数字是 37。"
        ) as tracker:
            target_text = Text("查找数字 37", font_size=26, color=GREEN).next_to(example_title, DOWN, buff=0.4)
            self.play(FadeIn(target_text))
            
        step_group = VGroup()
        
        with self.voiceover(
            text="第一步，比较根结点。当前结点是 45。因为 37 小于 45，所以去左边找。",
            subcaption="第一步，比较根结点。当前结点是 45。因为 37 小于 45，所以去左边找。"
        ) as tracker:
            self.play(set_current_node('N45', run_time=0.5))
            step_text = Text("第一步：当前 45，37 < 45，去左边", font_size=24).next_to(target_text, DOWN, buff=0.5)
            step_group.add(step_text)
            self.play(FadeIn(step_group))
            
        with self.voiceover(
            text="第二步，来到左孩子 24。比较发现 37 大于 24，所以去右边找。",
            subcaption="第二步，来到左孩子 24。比较发现 37 大于 24，所以去右边找。"
        ) as tracker:
            self.play(set_current_node('N24', run_time=0.6))
            new_step = Text("第二步：来到 24，37 > 24，去右边", font_size=24).next_to(target_text, DOWN, buff=0.5)
            self.play(ReplacementTransform(step_group, new_step))
            step_group = new_step
            
        with self.voiceover(
            text="第三步，来到右孩子 37，刚好找到！",
            subcaption="第三步，来到右孩子 37，刚好找到！"
        ) as tracker:
            self.play(set_current_node('N37', run_time=0.6))
            final_step = Text("第三步：来到 37，找到！", font_size=26, color=YELLOW).next_to(target_text, DOWN, buff=0.5)
            self.play(ReplacementTransform(step_group, final_step))
            self.play(Indicate(nodes['N37'].circle, color=YELLOW, scale_factor=1.2), run_time=0.6)
            
        # Clean up
        reset_anims = [n.circle.animate.set_color(BLUE).set_fill(BLUE, opacity=0.15) for n in nodes.values()]
        self.current_node = None
        self.play(
            FadeOut(example_title), FadeOut(target_text), FadeOut(final_step),
            *reset_anims,
            run_time=1.0
        )

        # ===== PHASE C.7 — 思想讲解 =====
        logic_title = Text("二叉排序树查找核心逻辑", font_size=32, font="Microsoft YaHei", color=YELLOW)
        logic_1 = Text("1. 若遇到空树（NULL），则查找失败", font_size=20, font="Microsoft YaHei")
        logic_2 = Text("2. 若目标值等于当前结点，则查找成功", font_size=20, font="Microsoft YaHei")
        logic_3 = Text("3. 若目标值较小，则在左子树中继续查找", font_size=20, font="Microsoft YaHei")
        logic_4 = Text("4. 若目标值较大，则在右子树中继续查找", font_size=20, font="Microsoft YaHei")

        logic_group = VGroup(logic_title, logic_1, logic_2, logic_3, logic_4).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        logic_box = RoundedRectangle(
            corner_radius=0.2,
            height=logic_group.get_height() + 1.0,
            width=logic_group.get_width() + 1.0,
            color=BLUE, fill_color=BLACK, fill_opacity=0.85, stroke_width=2
        )
        logic_box.move_to(logic_group)
        logic_panel = VGroup(logic_box, logic_group).to_edge(RIGHT, buff=0.5)

        with self.voiceover(
            text="刚才的过程体现了二叉排序树的一个重要性质：对于任何一个结点，它的左子树上所有结点的关键字都小于它，而右子树上所有结点的关键字都大于它。",
            subcaption="刚才的过程体现了二叉排序树的一个重要性质：对于任何一个结点，它的左子树上所有结点的关键字都小于它，而右子树上所有结点的关键字都大于它。"
        ) as tracker:
            self.play(FadeIn(logic_box), FadeIn(logic_title), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))
            
        with self.voiceover(
            text="利用这个性质，我们可以总结出递归查找的核心逻辑：比较目标值与当前结点，若相等则成功；若较小则向左，若较大则向右；直到遇到空树则失败。",
            subcaption="利用这个性质，我们可以总结出递归查找的核心逻辑：比较目标值与当前结点，若相等则成功；若较小则向左，若较大则向右；直到遇到空树则失败。"
        ) as tracker:
            self.play(FadeIn(logic_1), FadeIn(logic_2), FadeIn(logic_3), FadeIn(logic_4), run_time=1.5)
            self.wait(max(0.1, tracker.duration - 1.5))

        self.play(FadeOut(logic_panel))
        
        with self.voiceover(
            text="接下来，我们看看对应的算法代码。",
            subcaption="接下来，我们看看对应的算法代码。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE B — CODE BLOCK CONFIG =====
        c_lines = [
            "BSTree SearchBST(BSTree T, int key) {",
            "    if (!T) return NULL;",
            "    if (key == T->data.key)",
            "        return T;",
            "    else if (key < T->data.key)",
            "        return SearchBST(T->lchild, key);",
            "    else",
            "        return SearchBST(T->rchild, key);",
            "}"
        ]

        IDX_FUNC = 0
        IDX_NULL = 1
        IDX_EQUAL = 2
        IDX_RET_T = 3
        IDX_LESS = 4
        IDX_LEFT = 5
        IDX_ELSE = 6
        IDX_RIGHT = 7

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

        # ===== PHASE D — 成功查找演示 (37) =====
        with self.voiceover(
            text="我们先来演示查找成功的情况，例如查找关键字 37。",
            subcaption="我们先来演示查找成功的情况，例如查找关键字 37。"
        ) as tracker:
            t_label = Text("目标值 ", font_size=26, color=YELLOW)
            t_val = Text("key = 37", font="Arial", font_size=26, color=YELLOW)
            search_text = VGroup(t_label, t_val).arrange(RIGHT, buff=0.1).to_edge(UP, buff=1.5).shift(LEFT * 3)
            self.play(FadeIn(search_text))
            
        with self.voiceover(
            text="首次调用，传入根结点 45。",
            subcaption="首次调用，传入根结点 45。"
        ) as tracker:
            self.play(*get_track_anims(IDX_FUNC), run_time=0.5)
            self.play(set_current_node('N45', run_time=0.5))

        with self.voiceover(
            text="树不为空，并且 37 小于根结点的关键字 45，因此我们递归地在它的左子树中查找。",
            subcaption="树不为空，并且 37 小于根结点的关键字 45，因此我们递归地在它的左子树中查找。"
        ) as tracker:
            self.play(*get_track_anims(IDX_NULL), run_time=0.3)
            self.play(*get_track_anims(IDX_LESS), run_time=0.4)
            self.play(Indicate(nodes['N45'].circle, color=YELLOW), run_time=0.4)
            self.play(*get_track_anims(IDX_LEFT), run_time=0.4)
            self.play(set_current_node('N24', run_time=0.6))
            
        with self.voiceover(
            text="现在来到子树的根结点 24。因为 37 大于 24，所以继续递归进入右子树。",
            subcaption="现在来到子树的根结点 24。因为 37 大于 24，所以继续递归进入右子树。"
        ) as tracker:
            self.play(*get_track_anims(IDX_FUNC), run_time=0.3)
            self.play(*get_track_anims(IDX_NULL), run_time=0.3)
            self.play(*get_track_anims(IDX_ELSE), run_time=0.4)
            self.play(Indicate(nodes['N24'].circle, color=YELLOW), run_time=0.4)
            self.play(*get_track_anims(IDX_RIGHT), run_time=0.4)
            self.play(set_current_node('N37', run_time=0.6))

        with self.voiceover(
            text="在当前结点，目标值 37 正好等于结点的关键字。",
            subcaption="在当前结点，目标值 37 正好等于结点的关键字。"
        ) as tracker:
            self.play(*get_track_anims(IDX_FUNC), run_time=0.3)
            self.play(*get_track_anims(IDX_NULL), run_time=0.3)
            self.play(*get_track_anims(IDX_EQUAL), run_time=0.4)
            
        with self.voiceover(
            text="查找成功，返回该结点的指针。",
            subcaption="查找成功，返回该结点的指针。"
        ) as tracker:
            self.play(Indicate(nodes['N37'].circle, color=YELLOW, scale_factor=1.2), run_time=0.4)
            self.play(*get_track_anims(IDX_RET_T), run_time=0.5)
            
        reset_anims = [n.circle.animate.set_color(BLUE).set_fill(BLUE, opacity=0.15) for n in nodes.values()]
        self.current_node = None
        self.play(*reset_anims, FadeOut(search_text), run_time=1.0)


        # ===== PHASE E — 失败查找演示 (60) =====
        with self.voiceover(
            text="接下来，我们演示查找失败的情况，比如查找关键字 60。",
            subcaption="接下来，我们演示查找失败的情况，比如查找关键字 60。"
        ) as tracker:
            t_label = Text("目标值 ", font_size=26, color=YELLOW)
            t_val = Text("key = 60", font="Arial", font_size=26, color=YELLOW)
            search_text = VGroup(t_label, t_val).arrange(RIGHT, buff=0.1).to_edge(UP, buff=1.5).shift(LEFT * 3)
            self.play(FadeIn(search_text))
            
        with self.voiceover(
            text="同样从根结点开始搜索。因为 60 大于 45，进入右子树。",
            subcaption="同样从根结点开始搜索。因为 60 大于 45，进入右子树。"
        ) as tracker:
            self.play(*get_track_anims(IDX_FUNC), run_time=0.3)
            self.play(set_current_node('N45', run_time=0.4))
            self.play(*get_track_anims(IDX_ELSE), run_time=0.3)
            self.play(*get_track_anims(IDX_RIGHT), run_time=0.3)
            self.play(set_current_node('N53', run_time=0.6))

        with self.voiceover(
            text="目标 60 大于当前结点的 53，继续进入右子树。",
            subcaption="目标 60 大于当前结点的 53，继续进入右子树。"
        ) as tracker:
            self.play(*get_track_anims(IDX_FUNC), run_time=0.3)
            self.play(*get_track_anims(IDX_ELSE), run_time=0.3)
            self.play(*get_track_anims(IDX_RIGHT), run_time=0.3)
            self.play(set_current_node('N93', run_time=0.6))
                       
        with self.voiceover(
            text="在结点 93，60 小于 93，需要进入左子树，但这里的左孩子为空。",
            subcaption="在结点 93，60 小于 93，需要进入左子树，但这里的左孩子为空。"
        ) as tracker:
            self.play(*get_track_anims(IDX_FUNC), run_time=0.3)
            self.play(*get_track_anims(IDX_LESS), run_time=0.3)
            self.play(*get_track_anims(IDX_LEFT), run_time=0.3)
            
            self.play(
                set_current_node(None, run_time=0.8),
                FadeIn(null_e),
            )
            
        with self.voiceover(
            text="此时 T 为空指针，触发递归的第一层判断条件，查找结束并返回 NULL，代表查找失败。",
            subcaption="此时 T 为空指针，触发递归的第一层判断条件，查找结束并返回 NULL，代表查找失败。"
        ) as tracker:
            self.play(*get_track_anims(IDX_FUNC), run_time=0.3)
            self.play(*get_track_anims(IDX_NULL), run_time=0.5)
            self.play(Indicate(null_e.nul, color=RED, scale_factor=1.2), run_time=0.5)
            
        reset_anims = [n.circle.animate.set_color(BLUE).set_fill(BLUE, opacity=0.15) for n in nodes.values()]
        self.play(*reset_anims, FadeOut(search_text), FadeOut(null_e), run_time=1.0)

        # ===== PHASE F — 复杂度分析 =====
        self.play(*get_track_anims(None), FadeOut(code_block), run_time=0.5)
        
        time_box = VGroup(Text("时间复杂度：", font_size=28, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(\\log N)", font_size=32, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=28, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(h)", font_size=32, color=YELLOW)).arrange(RIGHT, buff=0.1)
        asl_box = VGroup(
            Text("平均查找长度：", font_size=25, font="Microsoft YaHei", color=GREEN),
            Text("取决于树形，通常为对数级", font_size=22, font="Microsoft YaHei", color=GREEN),
        ).arrange(RIGHT, buff=0.1)
        summary = VGroup(time_box, space_box, asl_box).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        summary.to_edge(RIGHT, buff=2.0)
        
        with self.voiceover(
            text="总结一下，二叉排序树查找的时间复杂度取决于树的高度。",
            subcaption="总结一下，二叉排序树查找的时间复杂度取决于树的高度。"
        ) as tracker:
            self.wait(tracker.duration)
            
        with self.voiceover(
            text="在最好和平均情况下，时间复杂度为 O(log N)；但在最坏情况，树退化成单链表时，则为 O(N)。",
            subcaption="在最好和平均情况下，时间复杂度为 O(log N)；但在最坏情况，树退化成单链表时，则为 O(N)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))
            
        with self.voiceover(
            text="由于使用了递归，空间开销为递归调用栈的深度 O(h)，h 为树高。",
            subcaption="由于使用了递归，空间开销为递归调用栈的深度 O(h)，h 为树高。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
            text="再看平均查找长度。二叉排序树的平均查找长度不只和结点个数有关，还和树的形态有关。",
            subcaption="再看平均查找长度。二叉排序树的平均查找长度不只和结点个数有关，还和树的形态有关。"
        ) as tracker:
            self.play(FadeIn(asl_box), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
            text="如果关键字按有序次序插入，树会退化成单支树，平均查找长度接近顺序查找，这是最差情况。",
            subcaption="如果关键字按有序次序插入，树会退化成单支树，平均查找长度接近顺序查找，这是最差情况。"
        ) as tracker:
            self.play(asl_box.animate.set_color(ORANGE), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
            text="如果树形接近折半查找的决策树，平均查找长度就和 log n 成正比。综合各种插入次序来看，它通常仍属于对数级。",
            subcaption="如果树形接近折半查找的决策树，平均查找长度就和 log n 成正比。综合各种插入次序来看，它通常仍属于对数级。"
        ) as tracker:
            self.play(asl_box.animate.set_color(GREEN), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
            text="以上就是二叉排序树递归查找算法的完整演示。",
            subcaption="以上就是二叉排序树递归查找算法的完整演示。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)
