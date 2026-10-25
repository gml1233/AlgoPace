# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService

class EvaluateExpTreeVideo(VoiceoverScene):
    NODE_R = 0.35

    def make_node(self, label, center, color=BLUE):
        c = Circle(radius=self.NODE_R, color=color, fill_color=color, fill_opacity=0.15, stroke_width=2.5).move_to(center)
        t = Text(label, font_size=24, font="Consolas", color=WHITE).move_to(center)
        g = VGroup(c, t)
        g.circle = c
        g.label = t
        return g

    def make_edge(self, p1, p2, color=WHITE):
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        start_pt = p1 + u * self.NODE_R
        end_pt = p2 - u * self.NODE_R
        line = Line(start_pt, end_pt, color=color, stroke_width=2.2)
        return line

    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(UP * 0.1)
        self.add(logo)

        # ===== 标题 =====
        algo_title = Text("表达式树的求值算法", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.3)
        self.play(FadeIn(algo_title), run_time=0.8)

        # ===== 生活实例：快餐店流水线 =====
        title_analogy = Text("生活实例：快餐店流水线", font_size=32, color=BLUE).next_to(algo_title, DOWN, buff=0.3)
        
        box_raw1 = RoundedRectangle(corner_radius=0.1, width=2.8, height=0.9, color=GREEN).shift(DOWN*2.2 + LEFT*2.5)
        txt_raw1 = Text("生鲜原料\n(叶子结点/操作数)", font_size=20, font="Microsoft YaHei").move_to(box_raw1)
        raw1 = VGroup(box_raw1, txt_raw1)

        box_raw2 = RoundedRectangle(corner_radius=0.1, width=2.8, height=0.9, color=GREEN).shift(DOWN*2.2 + RIGHT*2.5)
        txt_raw2 = Text("生鲜原料\n(叶子结点/操作数)", font_size=20, font="Microsoft YaHei").move_to(box_raw2)
        raw2 = VGroup(box_raw2, txt_raw2)

        box_mid = RoundedRectangle(corner_radius=0.1, width=3.2, height=0.9, color=YELLOW).shift(DOWN*0.5)
        txt_mid = Text("操作台加工\n(内部结点/运算符)", font_size=20, font="Microsoft YaHei").move_to(box_mid)
        mid = VGroup(box_mid, txt_mid)

        box_top = RoundedRectangle(corner_radius=0.1, width=3.2, height=0.9, color=RED).shift(UP*1.2)
        txt_top = Text("最终成品\n(根结点/最终结果)", font_size=20, font="Microsoft YaHei").move_to(box_top)
        top_grp = VGroup(box_top, txt_top)

        arrow_kwargs = {"color": WHITE, "max_tip_length_to_length_ratio": 1.0, "max_stroke_width_to_length_ratio": 1.0}
        arrow_l = Arrow(box_raw1.get_top(), box_mid.get_bottom(), **arrow_kwargs)
        arrow_r = Arrow(box_raw2.get_top(), box_mid.get_bottom(), **arrow_kwargs)
        arrow_up = Arrow(box_mid.get_top(), box_top.get_bottom(), **arrow_kwargs)

        # 运动的小物件，表示原料运输
        dot_l = Dot(color=GREEN).move_to(box_raw1.get_top())
        dot_r = Dot(color=GREEN).move_to(box_raw2.get_top())
        dot_up = Dot(color=YELLOW).move_to(box_mid.get_top())

        analogy_bg = VGroup(title_analogy, raw1, raw2, mid, top_grp)

        with self.voiceover(text="本节我们来学习表达式树的求值算法。改算法是指通过后序遍历表达式树进行表达式求值") as tracker:
            self.play(FadeIn(analogy_bg), run_time=tracker.duration)
            
        with self.voiceover(text="表达式树的求值，就像是快餐店流水线的加工过程。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="底层的生鲜原料，必须全部通过传送带送达上层操作台，相当于递归计算左右子树。") as tracker:
            self.play(GrowArrow(arrow_l), GrowArrow(arrow_r), FadeIn(dot_l), FadeIn(dot_r), run_time=max(0.1, tracker.duration*0.3))
            self.play(dot_l.animate.move_to(box_mid.get_bottom()), dot_r.animate.move_to(box_mid.get_bottom()), run_time=max(0.1, tracker.duration*0.7))

        with self.voiceover(text="原料凑齐后，操作台加工得出半成品，也就得出了当前结点的结果。") as tracker:
            self.play(FadeOut(dot_l), FadeOut(dot_r), run_time=0.2)
            self.play(Indicate(box_mid, color=ORANGE, scale_factor=1.1), FadeIn(dot_up), run_time=max(0.1, tracker.duration-0.2))

        with self.voiceover(text="随后半成品送往顶层总操作台，最终加工出成品，即整个表达式的结果。") as tracker:
            self.play(GrowArrow(arrow_up), run_time=max(0.1, tracker.duration*0.2))
            self.play(dot_up.animate.move_to(box_top.get_bottom()), run_time=max(0.1, tracker.duration*0.4))
            self.play(FadeOut(dot_up), run_time=0.2)
            self.play(Indicate(box_top, color=RED, scale_factor=1.15), run_time=max(0.1, tracker.duration-0.4))

        self.wait(0.5)
        analogy_group = VGroup(analogy_bg, arrow_l, arrow_r, arrow_up)
        self.play(FadeOut(analogy_group))

        # ===== 核心思想总结 =====
        summary_title = Text("核心思想", font_size=36, color=YELLOW).shift(UP*1.5)
        summary_body = Text(
            "表达式树的求值本质上是一个 自底向上 的 后序遍历 过程：\n\n"
            "1. 先递归求解 左子树\n"
            "2. 再递归求解 右子树\n"
            "3. 最后根据 根结点 的运算符进行最终计算",
            font_size=28, font="Microsoft YaHei", line_spacing=1.5,
            t2c={
                "自底向上": RED,
                "后序遍历": RED,
                "左子树": GREEN,
                "右子树": GREEN,
                "根结点": BLUE
            }
        ).next_to(summary_title, DOWN, buff=0.8)
        
        summary_box = SurroundingRectangle(summary_body, color=WHITE, buff=0.5, corner_radius=0.2)
        summary_group = VGroup(summary_title, summary_body, summary_box)

        with self.voiceover(text="通过这个实例我们可以看出，表达式树求值的核心思想，本质上就是一个自底向上的后序遍历过程。") as tracker:
            self.play(FadeIn(summary_title, shift=DOWN), run_time=max(0.1, tracker.duration*0.3))
            self.play(Create(summary_box), run_time=max(0.1, tracker.duration*0.3))
            self.play(Write(summary_body), run_time=max(0.1, tracker.duration*0.4))

        with self.voiceover(text="算法总是先递归求出左子树的值，再求出右子树的值，最后利用根结点的运算符，将左右两边的结果合并计算。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="理解了这个自底向上的核心流程后，接下来我们通过具体的代码和一棵实际的二叉树，来看看它是如何工作的。") as tracker:
            self.play(FadeOut(summary_group), run_time=tracker.duration)

        # ===== 准备代码块 =====
        c_lines = [
            "int EvaluateExpTree(BiTree T)",
            "{//遍历表达式树进行表达式求值",
            "    lvalue=rvalue=0;   //初始为0",
            "    if(T->lchild==NULL && T->rchild==NULL)",
            "        return T->data-'0';           //操作数则返回数值",
            "    else",
            "    {",
            "        lvalue=EvaluateExpTree(T->lchild); //递归计算左子树值",
            "        rvalue=EvaluateExpTree(T->rchild); //递归计算右子树值",
            "        return GetValue(T->data,lvalue,rvalue);",
            "        //运算符则根据类型进行相应运算",
            "    }",
            "}"
        ]

        L_FUNCTION = 0
        L_LEAF_IF = 3
        L_LEAF_RETURN = 4
        L_ELSE = 5
        L_LEFT_RECURSE = 7
        L_RIGHT_RECURSE = 8
        L_GET_VALUE = 9

        self.c_texts = []
        for line in c_lines:
            t = Text(line.lstrip(" "), font_size=11.0, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.09)
        SPACE_WIDTH = 0.05
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 6.0:
            code_group.scale_to_fit_width(6.0)
        if code_group.height > 4.2:
            code_group.scale_to_fit_height(4.2)

        code_bg = RoundedRectangle(corner_radius=0.15, height=code_group.get_height() + 0.38,
                                   width=code_group.get_width() + 0.6, color=GRAY, fill_opacity=0.1, stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT*0.25)
        code_bg.match_y(code_group)
        code_block = VGroup(code_bg, code_group)

        self.current_lines = []

        def get_track_anims(new_idx):
            if isinstance(new_idx, int):
                new_idx = [new_idx]
            elif new_idx is None:
                new_idx = []
                
            if set(new_idx) == set(self.current_lines):
                if not new_idx:
                    return [Wait(0.001)]
                return [self.c_texts[new_idx[0]].animate.set_color(YELLOW)]
            anims = []
            for idx in self.current_lines:
                if idx not in new_idx:
                    anims.append(self.c_texts[idx].animate.set_color(WHITE).scale(1 / 1.08, about_edge=LEFT))
            
            first_idx = None
            for idx in new_idx:
                if idx not in self.current_lines:
                    anims.append(self.c_texts[idx].animate.set_color(YELLOW).scale(1.08, about_edge=LEFT))
                if first_idx is None or idx < first_idx:
                    first_idx = idx

            if first_idx is not None:
                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.14).rotate(-PI / 2)
                    self.code_pointer.next_to(self.c_texts[first_idx], LEFT, buff=0.15)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.c_texts[first_idx], LEFT, buff=0.15)
                    anims.append(MoveToTarget(self.code_pointer))
            else:
                if hasattr(self, 'code_pointer'):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, 'code_pointer')
                    
            self.current_lines = new_idx
            return anims

        # 布局右侧代码块
        top_y_limit = algo_title.get_bottom()[1] - 0.2
        code_block.to_edge(RIGHT, buff=0.2).set_y(0)

        # 布局左侧二叉树 3+4*5
        arena_center = np.array([-3.5, 0.5, 0])
        node_pos = {
            '+': arena_center + np.array([0, 1.2, 0]),
            '3': arena_center + np.array([-1.5, -0.2, 0]),
            '*': arena_center + np.array([1.5, -0.2, 0]),
            '4': arena_center + np.array([0.3, -1.6, 0]),
            '5': arena_center + np.array([2.7, -1.6, 0]),
        }
        
        n_plus = self.make_node('+', node_pos['+'], BLUE)
        n_3 = self.make_node('3', node_pos['3'], GREEN)
        n_mul = self.make_node('*', node_pos['*'], BLUE)
        n_4 = self.make_node('4', node_pos['4'], GREEN)
        n_5 = self.make_node('5', node_pos['5'], GREEN)
        
        e_plus_3 = self.make_edge(node_pos['+'], node_pos['3'])
        e_plus_mul = self.make_edge(node_pos['+'], node_pos['*'])
        e_mul_4 = self.make_edge(node_pos['*'], node_pos['4'])
        e_mul_5 = self.make_edge(node_pos['*'], node_pos['5'])
        
        tree_group = VGroup(e_plus_3, e_plus_mul, e_mul_4, e_mul_5, n_plus, n_3, n_mul, n_4, n_5)
        
        # 准备指针
        ptr = Arrow(start=UP, end=DOWN, color=YELLOW, buff=0).scale(0.8)
        ptr.next_to(n_plus, UP, buff=0.1)
        
        # 开始动画
        with self.voiceover(text="假设我们有一棵对应表达式 3加4乘5 的二叉树。") as tracker:
            self.play(FadeIn(code_block), FadeIn(tree_group), run_time=tracker.duration)

        with self.voiceover(text="求值过程实际上是一个后序遍历。我们从根结点加号开始，对其进行递归求值。") as tracker:
            self.play(*get_track_anims(L_FUNCTION))
            self.play(FadeIn(ptr), run_time=tracker.duration - 0.5)

        with self.voiceover(text="当前结点是加号，属于运算符，因此我们要先递归计算它的左子树的值。") as tracker:
            self.play(*get_track_anims(L_LEAF_IF), run_time=0.4)
            self.play(*get_track_anims(L_LEFT_RECURSE), run_time=0.4)
            self.play(ptr.animate.next_to(n_3, UP, buff=0.1), run_time=max(0.1, tracker.duration - 0.8))
            
        with self.voiceover(text="来到左子结点 3，由于它是叶子结点，也就是操作数。") as tracker:
            self.play(*get_track_anims(L_LEAF_IF), run_time=0.4)
            self.play(*get_track_anims(L_LEAF_RETURN), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 0.8))
            
        with self.voiceover(text="我们直接返回该结点的数值 3。") as tracker:
            self.play(*get_track_anims(L_LEAF_RETURN))
            val_3 = Text("3", font_size=20, font="Consolas", color=YELLOW).next_to(n_3, LEFT, buff=0.2)
            self.play(FadeIn(val_3, shift=UP), run_time=max(0.1, tracker.duration - 0.5))
            
        with self.voiceover(text="于是根结点的左子树求值结果记录为 3。接下来递归计算根结点的右子树。") as tracker:
            self.play(*get_track_anims(L_ELSE))
            self.play(val_3.animate.next_to(n_plus, LEFT, buff=0.2))
            self.play(ptr.animate.next_to(n_mul, UP, buff=0.1), run_time=max(0.1, tracker.duration - 1.0))
            
        with self.voiceover(text="来到右子结点乘号，它同样是运算符。于是再次递归计算它的左子树。") as tracker:
            self.play(*get_track_anims(L_LEAF_IF), run_time=0.4)
            self.play(*get_track_anims(L_LEFT_RECURSE), run_time=0.4)
            self.play(ptr.animate.next_to(n_4, UP, buff=0.1), run_time=max(0.1, tracker.duration - 1.2))
            
        with self.voiceover(text="左子结点 4 是叶子结点，所以返回其数值 4。") as tracker:
            self.play(*get_track_anims(L_LEAF_IF), run_time=0.4)
            self.play(*get_track_anims(L_LEAF_RETURN), run_time=0.4)
            self.play(*get_track_anims(L_LEAF_RETURN), run_time=0.4)
            val_4 = Text("4", font_size=20, font="Consolas", color=YELLOW).next_to(n_4, LEFT, buff=0.2)
            self.play(FadeIn(val_4, shift=UP), run_time=max(0.1, tracker.duration - 1.2))

        with self.voiceover(text="乘号结点的左子树结果记录为 4。接着递归计算乘号的右子树。") as tracker:
            self.play(*get_track_anims(L_ELSE))
            self.play(val_4.animate.next_to(n_mul, LEFT, buff=0.2))
            self.play(ptr.animate.next_to(n_5, UP, buff=0.1), run_time=max(0.1, tracker.duration - 1.0))

        with self.voiceover(text="右子结点 5 也是叶子结点，直接返回数值 5。") as tracker:
            self.play(*get_track_anims(L_LEAF_IF), run_time=0.4)
            self.play(*get_track_anims(L_LEAF_RETURN), run_time=0.4)
            self.play(*get_track_anims(L_LEAF_RETURN), run_time=0.4)
            val_5 = Text("5", font_size=20, font="Consolas", color=YELLOW).next_to(n_5, RIGHT, buff=0.2)
            self.play(FadeIn(val_5, shift=UP), run_time=max(0.1, tracker.duration - 1.2))
            
        with self.voiceover(text="此时乘号的左右子树都已经求值完毕，右子树值记录为 5。") as tracker:
            self.play(*get_track_anims(L_RIGHT_RECURSE))
            self.play(val_5.animate.next_to(n_mul, RIGHT, buff=0.2), ptr.animate.next_to(n_mul, UP, buff=0.1), run_time=max(0.1, tracker.duration - 0.5))
            
        with self.voiceover(text="根据当前结点运算符为乘号，我们将左右子树的结果进行相乘。") as tracker:
            self.play(*get_track_anims(L_GET_VALUE))
            self.wait(max(0.1, tracker.duration - 0.5))
            
        with self.voiceover(text="计算得到 20，作为该子树的求值结果返回给上一层。") as tracker:
            res_20 = Text("20", font_size=24, font="Consolas", color=YELLOW).next_to(n_mul, RIGHT, buff=0.2)
            self.play(FadeIn(res_20, shift=UP))
            self.play(res_20.animate.next_to(n_plus, RIGHT, buff=0.2), ptr.animate.next_to(n_plus, UP, buff=0.1), run_time=max(0.1, tracker.duration - 1.0))

        with self.voiceover(text="回到根结点加号，它的左右子树结果分别为 3 和 20。根据加号运算符，将它们相加。") as tracker:
            self.play(*get_track_anims(L_GET_VALUE))
            self.wait(max(0.1, tracker.duration - 0.5))

        with self.voiceover(text="最终得到整个表达式的值为 23。") as tracker:
            res_23 = Text("23", font_size=36, font="Consolas", color=YELLOW).next_to(n_plus, UP, buff=0.6)
            self.play(FadeIn(res_23, shift=UP))
            self.play(FadeOut(ptr), res_23.animate.scale(1.2), run_time=max(0.1, tracker.duration - 1.0))

        self.play(*get_track_anims(None))
        self.wait(1)

        # ===== 复杂度分析 =====
        time_box = VGroup(Text("时间复杂度: ", font_size=20, color=YELLOW), MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度: ", font_size=20, color=YELLOW), MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        complexity_text = VGroup(time_box, space_box).arrange(RIGHT, buff=0.8)
        complexity_text.to_edge(DOWN, buff=0.5).shift(LEFT * 1.5)

        with self.voiceover(text="该算法递归遍历了表达式树的所有结点，每个结点访问一次，因此时间复杂度为O(n)。") as tracker:
            self.play(FadeIn(time_box, shift=UP), run_time=tracker.duration)
            
        with self.voiceover(text="递归调用所需的栈空间与树的深度成正比，空间复杂度为O(n)。") as tracker:
            self.play(FadeIn(space_box, shift=UP), run_time=tracker.duration)

        with self.voiceover(text="以上就是表达式树求值算法的完整演示。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)
