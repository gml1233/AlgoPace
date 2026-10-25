# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class ExpressionTreeCreateVideo(VoiceoverScene):
    NODE_R = 0.35

    def make_node(self, label, center, color=BLUE):
        c = Circle(radius=self.NODE_R, color=color, fill_color=color, fill_opacity=0.15, stroke_width=2.5).move_to(center)
        t = Text(label, font_size=24, color=WHITE).move_to(center)
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
        algo_title = Text("表达式树的创建算法", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.3)
        self.play(FadeIn(algo_title), run_time=0.8)

        # ===== 生活实例：工厂流水线组装 =====
        title_analogy = Text("生活实例：工厂流水线快速演示 (以 a+b 为例)", font_size=32, color=BLUE).next_to(algo_title, DOWN, buff=0.3)
        
        # 零件仓库
        box_expt = RoundedRectangle(corner_radius=0.1, width=3.0, height=1.5, color=GREEN).shift(DOWN*1.8 + LEFT*2.8)
        txt_expt = Text("零件仓库", font_size=20, font="Microsoft YaHei").next_to(box_expt, DOWN, buff=0.1)
        grp_expt = VGroup(box_expt, txt_expt)

        # 指令图纸
        box_optr = RoundedRectangle(corner_radius=0.1, width=3.0, height=1.5, color=BLUE).shift(DOWN*1.8 + RIGHT*2.8)
        txt_optr = Text("指令图纸", font_size=20, font="Microsoft YaHei").next_to(box_optr, DOWN, buff=0.1)
        grp_optr = VGroup(box_optr, txt_optr)

        # 组装台
        box_asm = RoundedRectangle(corner_radius=0.1, width=3.6, height=2.0, color=YELLOW)
        txt_asm = Text("自动化组装台", font_size=20, font="Microsoft YaHei").next_to(box_asm, UP, buff=0.1)
        grp_asm = VGroup(box_asm, txt_asm).next_to(title_analogy, DOWN, buff=0.5)

        arrow_kwargs = {"color": WHITE, "max_tip_length_to_length_ratio": 1.0, "max_stroke_width_to_length_ratio": 1.0}
        
        arrow_expt = Arrow(box_expt.get_top(), box_asm.get_bottom(), **arrow_kwargs)
        arrow_optr = Arrow(box_optr.get_top(), box_asm.get_bottom(), **arrow_kwargs)
        
        arrow_in_expt = Arrow(box_expt.get_left() + LEFT*1.5, box_expt.get_left(), **arrow_kwargs)
        arrow_in_optr = Arrow(box_optr.get_right() + RIGHT*1.5, box_optr.get_right(), **arrow_kwargs)
        
        analogy_bg = VGroup(
            title_analogy, grp_expt, grp_optr, grp_asm,
            arrow_expt, arrow_optr, arrow_in_expt, arrow_in_optr
        )

        with self.voiceover(
                text="本节我们来学习表达式树的创建算法，该算法是指利用栈来创建中缀表达式对应的表达式树。") as tracker:
            self.play(FadeIn(analogy_bg), run_time=tracker.duration)
        with self.voiceover(
                text="表达式树的创建，就像是一个自动化工厂的流水线组装过程。我们以 a加b 为例，快速浏览一遍。") as tracker:
            self.wait(tracker.duration)

        n_a = self.make_node('a', arrow_in_expt.get_start())
        n_plus = self.make_node('+', arrow_in_optr.get_start(), BLUE)
        n_b = self.make_node('b', arrow_in_expt.get_start())

        with self.voiceover(text="当流水线运来基础零件 a 时，机器会直接将其送入左侧的零件仓库暂存。") as tracker:
            self.play(FadeIn(n_a, shift=RIGHT), run_time=max(0.1, tracker.duration*0.3))
            self.play(n_a.animate.move_to(box_expt.get_center() + LEFT*0.6), run_time=max(0.1, tracker.duration*0.7))

        with self.voiceover(text="随后运来了一张加号组装图纸，它会被送入右侧的图纸栈中等待。") as tracker:
            self.play(FadeIn(n_plus, shift=LEFT), run_time=max(0.1, tracker.duration*0.3))
            self.play(n_plus.animate.move_to(box_optr.get_center()), run_time=max(0.1, tracker.duration*0.7))

        with self.voiceover(text="紧接着又运来了基础零件 b，同样也被送入左侧的零件仓库。") as tracker:
            self.play(FadeIn(n_b, shift=RIGHT), run_time=max(0.1, tracker.duration*0.3))
            self.play(n_b.animate.move_to(box_expt.get_center() + RIGHT*0.6), run_time=max(0.1, tracker.duration*0.7))

        with self.voiceover(text="此时触发了组装作业，机器会从图纸栈取出一张图纸，并从零件仓库取出对应的两个零件，一起送上组装台。") as tracker:
            self.play(
                n_plus.animate.move_to(box_asm.get_center() + UP*0.3),
                n_a.animate.move_to(box_asm.get_center() + DOWN*0.3 + LEFT*0.7),
                n_b.animate.move_to(box_asm.get_center() + DOWN*0.3 + RIGHT*0.7),
                run_time=tracker.duration
            )

        with self.voiceover(text="在组装台上，它们被牢牢地拼装在一起，形成了一个更大的半成品组件。") as tracker:
            e1 = self.make_edge(n_plus.circle.get_center(), n_a.circle.get_center())
            e2 = self.make_edge(n_plus.circle.get_center(), n_b.circle.get_center())
            self.play(Create(e1), Create(e2), run_time=tracker.duration)

        with self.voiceover(text="随后，这个新组装的半成品作为一个整体，被重新送回零件仓库，等待下一次更大规模的组装。") as tracker:
            subtree = VGroup(n_plus, n_a, n_b, e1, e2)
            self.play(subtree.animate.scale(0.7).move_to(box_expt.get_center()), run_time=tracker.duration)

        with self.voiceover(text="当所有图纸执行完毕，仓库中剩下的最后这件终极成品，就是我们需要的完整结构。") as tracker:
            self.play(Indicate(subtree, color=RED, scale_factor=1.1), run_time=tracker.duration)

        self.wait(0.5)
        self.play(FadeOut(analogy_bg), FadeOut(subtree))

        # ===== 核心思想总结 =====
        summary_title = Text("核心思想", font_size=36, color=YELLOW).shift(UP*1.5)
        summary_body = Text(
            "表达式树的创建本质上是一个 算符优先分析 过程：\n\n"
            "1. 遇到操作数：直接入 结点栈(EXPT)\n"
            "2. 遇到运算符：与 符号栈(OPTR) 栈顶比较优先级\n"
            "3. 优先级高则 组装：弹1个运算符、2个操作数建树后重新入栈",
            font_size=28, font="Microsoft YaHei", line_spacing=1.5,
            t2c={
                "算符优先分析": RED,
                "结点栈(EXPT)": GREEN,
                "符号栈(OPTR)": BLUE,
                "组装": ORANGE
            }
        ).next_to(summary_title, DOWN, buff=0.8)
        
        summary_box = SurroundingRectangle(summary_body, color=WHITE, buff=0.5, corner_radius=0.2)
        summary_group = VGroup(summary_title, summary_body, summary_box)

        with self.voiceover(text="通过这个实例我们可以看出，表达式树的创建本质上是一个算符优先分析过程。") as tracker:
            self.play(FadeIn(summary_title, shift=DOWN), run_time=max(0.1, tracker.duration*0.3))
            self.play(Create(summary_box), run_time=max(0.1, tracker.duration*0.3))
            self.play(Write(summary_body), run_time=max(0.1, tracker.duration*0.4))

        with self.voiceover(text="它遇到操作数直接入栈，遇到运算符则通过优先级判断是否进行组装，组装后的新结点重新存回栈中。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="接下来我们结合具体代码，看看程序中是如何借助两个栈完成建树的。") as tracker:
            self.play(FadeOut(summary_group), run_time=tracker.duration)

        # ===== 准备代码块 =====
        c_lines = [
            "void InitExpTree()",
            "{//表达式树的创建算法",
            "    InitStack(EXPT);    //初始化EXPT栈",
            "    InitStack(OPTR);    //初始化OPTR栈",
            "    Push(OPTR,'#');     //将表达式起始符“#”压入OPTR栈",
            "    cin>>ch;",
            "    while(ch!='#'||GetTop(OPTR)!='#') //表达式未完或栈顶不为“#”",
            "    {",
            "        if(!In(ch))     //ch不是运算符",
            "        {",
            "            CreateExpTree(T,NULL,NULL,ch); //以ch为根建单结点树",
            "            Push(EXPT,T);   //根节点T进EXPT栈",
            "            cin>>ch;        //读入下一字符",
            "        }",
            "        else",
            "        switch(Precede(GetTop(OPTR),ch)) //比较栈顶和ch优先级",
            "        {",
            "            case '<':",
            "                Push(OPTR,ch);cin>>ch; //ch压入OPTR，读下一字符",
            "                break;",
            "            case '>':",
            "                Pop(OPTR,theta);       //弹出运算符",
            "                Pop(EXPT,b);Pop(EXPT,a); //弹出两个操作数",
            "                CreateExpTree(T,a,b,theta);",
            "                //以theta为根，a为左，b为右建树",
            "                Push(EXPT,T);          //根节点进EXPT栈",
            "                break;",
            "            case '=':    //栈顶为“(”且ch为“)”",
            "                Pop(OPTR,x);cin>>ch;   //弹出“(”，读下一字符",
            "                break;",
            "        }     //switch",
            "    }      //while",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            t = Text(line.lstrip(" "), font_size=9.5, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.07)
        SPACE_WIDTH = 0.05
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 5.9:
            code_group.scale_to_fit_width(5.9)
        if code_group.height > 4.7:
            code_group.scale_to_fit_height(4.7)

        code_bg = RoundedRectangle(corner_radius=0.15, height=code_group.get_height() + 0.35,
                                   width=code_group.get_width() + 0.5, color=GRAY, fill_opacity=0.1, stroke_width=1)
        code_bg.move_to(code_group)
        code_block = VGroup(code_bg, code_group)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line:
                if new_idx is None:
                    return [Wait(0.001)]
                return [self.c_texts[new_idx].animate.set_color(YELLOW)]
            anims = []
            if self.current_line is not None:
                anims.append(self.c_texts[self.current_line].animate.set_color(WHITE).scale(1 / 1.08, about_edge=LEFT))
            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW).scale(1.08, about_edge=LEFT))
                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.14).rotate(-PI / 2)
                    self.code_pointer.next_to(self.c_texts[new_idx], LEFT, buff=0.15)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.c_texts[new_idx], LEFT, buff=0.15)
                    anims.append(MoveToTarget(self.code_pointer))
                self.current_line = new_idx
            return anims

        # ===== 布局核心区域 =====
        SCREEN_TOP = config.frame_y_radius
        SCREEN_BOTTOM = -config.frame_y_radius
        SCREEN_RIGHT = config.frame_x_radius
        SCREEN_LEFT = -config.frame_x_radius
        MARGIN = 0.3
        
        top_y_limit = algo_title.get_bottom()[1] - 0.2
        max_height = top_y_limit - SCREEN_BOTTOM - MARGIN * 2

        # [右侧代码块]
        if code_block.height > max_height:
            code_block.scale_to_fit_height(max_height)
        if code_block.width > 5.15:
            code_block.scale_to_fit_width(5.15)
        code_block.to_edge(RIGHT, buff=0.2).set_y((top_y_limit + SCREEN_BOTTOM) / 2)

        # [输入字符串流]
        expr_str = "a+b*c#"
        str_boxes = VGroup()
        for i, ch in enumerate(expr_str):
            box = Square(side_length=0.6, color=GRAY_B)
            txt = Text(ch, font_size=24, color=WHITE).move_to(box.get_center())
            str_boxes.add(VGroup(box, txt))
        str_boxes.arrange(RIGHT, buff=0)
        str_title = Text("表达式:", font_size=18, color=YELLOW).next_to(str_boxes, LEFT, buff=0.3)
        expr_group = VGroup(str_title, str_boxes)
        
        expr_group.to_edge(LEFT, buff=0.5).set_y(top_y_limit - 0.5)

        # [双栈区]
        stack_width = 1.0
        stack_height = 0.5
        
        # OPTR 栈
        optr_title = Text("OPTR栈", font_size=18, color=ORANGE)
        optr_stack = VGroup()
        optr_base_line = Line(LEFT*0.6, RIGHT*0.6, color=ORANGE, stroke_width=3)
        optr_group = VGroup(VGroup(optr_base_line), optr_title).arrange(DOWN, buff=0.2)

        # EXPT 栈
        expt_title = Text("EXPT栈(树指针)", font_size=18, color=GREEN)
        expt_stack = VGroup()
        expt_base_line = Line(LEFT*0.8, RIGHT*0.8, color=GREEN, stroke_width=3)
        expt_group = VGroup(VGroup(expt_base_line), expt_title).arrange(DOWN, buff=0.2)
        
        stacks_group = VGroup(optr_group, expt_group).arrange(RIGHT, buff=2.0)
        stacks_group.to_edge(LEFT, buff=0.8).to_edge(DOWN, buff=0.8)

        def push_stack(stack_vgroup, base_line, label_str, color):
            box = Rectangle(width=stack_width, height=stack_height, color=color, fill_opacity=0.2)
            txt = Text(label_str, font_size=20, color=WHITE).move_to(box.get_center())
            item = VGroup(box, txt)
            if len(stack_vgroup) == 0:
                item.next_to(base_line, UP, buff=0)
            else:
                item.next_to(stack_vgroup[-1], UP, buff=0)
            stack_vgroup.add(item)
            return item

        def pop_stack(stack_vgroup):
            if len(stack_vgroup) > 0:
                item = stack_vgroup[-1]
                stack_vgroup.remove(item)
                return item
            return None

        # [竞技场预设坐标 (树的构建区域)]
        arena_center = np.array([-2.5, 0.5, 0])
        node_pos = {
            '+': arena_center + np.array([0, 1.2, 0]),
            'a': arena_center + np.array([-2, 0, 0]),
            '*': arena_center + np.array([2, 0, 0]),
            'b': arena_center + np.array([0.8, -1.2, 0]),
            'c': arena_center + np.array([3.2, -1.2, 0]),
        }
        
        created_nodes = {}

        L_INIT_EXPT = 2
        L_INIT_OPTR = 3
        L_PUSH_OPTR = 4
        L_WHILE = 6
        L_IF_NOT_OP = 8
        L_NEW_NODE = 10
        L_PUSH_EXPT = 11
        L_ELSE = 14
        L_SWITCH = 15
        L_CASE_LESS = 17
        L_CASE_GREATER = 20
        L_MERGE_POP = 21
        L_MERGE_POP2 = 22
        L_MERGE_POP3 = 22
        L_MERGE_NEW = 23
        L_MERGE_LINK = 24
        L_MERGE_PUSH = 25
        L_CASE_EQUAL = 27
        L_END = 32

        # ==================== 正式动画开始 ====================
        with self.voiceover(text="我们将通过经典的算符优先法，使用OPTR操作符栈和EXPT树指针栈，来构建表达式树。") as tracker:
            self.play(FadeIn(code_block), FadeIn(expr_group), FadeIn(optr_title), FadeIn(optr_base_line), FadeIn(expt_title), FadeIn(expt_base_line), run_time=tracker.duration)

        with self.voiceover(text="初始化阶段，我们将一个结束符井号，压入OPTR栈中。作为表达式结束的比对标识。") as tracker:
            self.play(*get_track_anims(L_INIT_EXPT))
            self.play(*get_track_anims(L_INIT_OPTR))
            self.play(*get_track_anims(L_PUSH_OPTR))
            
            item = push_stack(optr_stack, optr_base_line, '#', ORANGE)
            self.play(FadeIn(item, shift=UP), run_time=tracker.duration - 1.0)
            
        ch_pointer = Arrow(start=UP, end=DOWN, color=RED).scale(0.5).next_to(str_boxes[0], UP, buff=0.1)
        self.play(FadeIn(ch_pointer))

        steps = [
            ('a', 'operand'),
            ('+', 'push_op'),
            ('b', 'operand'),
            ('*', 'push_op'),
            ('c', 'operand'),
            ('#', 'pop_op_merge1'),
            ('#', 'pop_op_merge2'),
            ('#', 'end')
        ]

        step_idx = 0
        while step_idx < len(steps):
            ch, step_type = steps[step_idx]
            ch_idx = min(step_idx, len(str_boxes)-1)
            
            self.play(*get_track_anims(L_WHILE))
            self.play(ch_pointer.animate.next_to(str_boxes[ch_idx], UP, buff=0.1), run_time=0.4)
            
            if step_type == 'operand':
                with self.voiceover(text=f"读入字符 {ch}，它不是运算符，所以我们以它为根创建一棵树。") as tracker:
                    self.play(*get_track_anims(L_IF_NOT_OP))
                    self.play(*get_track_anims(L_NEW_NODE))
                    
                    n = self.make_node(ch, node_pos[ch], GREEN)
                    created_nodes[ch] = n
                    self.play(FadeIn(n, scale=0.5), run_time=tracker.duration - 1.0)
                    
                with self.voiceover(text=f"然后，将这棵树结点的指针压入 EXPT 栈中。") as tracker:
                    self.play(*get_track_anims(L_PUSH_EXPT))
                    
                    item = push_stack(expt_stack, expt_base_line, f"ptr({ch})", GREEN)
                    self.play(FadeIn(item, shift=UP), run_time=tracker.duration)
                    
            elif step_type == 'push_op':
                with self.voiceover(text=f"读入运算符 {ch}，它与OPTR栈顶元素比较，优先级更高，所以直接压入OPTR栈。") as tracker:
                    self.play(*get_track_anims(L_ELSE))
                    self.play(*get_track_anims(L_SWITCH))
                    self.play(*get_track_anims(L_CASE_LESS))
                    
                    item = push_stack(optr_stack, optr_base_line, ch, ORANGE)
                    self.play(FadeIn(item, shift=UP), run_time=tracker.duration - 1.0)
                    
            elif step_type == 'pop_op_merge1':
                with self.voiceover(text="读入井号，它的优先级低于栈顶的乘号。说明乘法已经可以计算了。") as tracker:
                    self.play(*get_track_anims(L_SWITCH))
                    self.play(*get_track_anims(L_CASE_GREATER))
                    
                with self.voiceover(text="我们从OPTR栈弹出乘号作为新的根结点。") as tracker:
                    self.play(*get_track_anims(L_MERGE_POP))
                    op_item = pop_stack(optr_stack)
                    
                    n_theta = self.make_node('*', node_pos['*'], BLUE)
                    created_nodes['*'] = n_theta
                    self.play(FadeOut(op_item, shift=DOWN), FadeIn(n_theta, scale=0.5), run_time=tracker.duration - 0.5)
                    
                with self.voiceover(text="再从EXPT栈依次弹出两个树指针，分别作为它的右子树和左子树。") as tracker:
                    self.play(*get_track_anims(L_MERGE_POP2))
                    right_item = pop_stack(expt_stack)
                    self.play(FadeOut(right_item, shift=DOWN))
                    
                    self.play(*get_track_anims(L_MERGE_POP3))
                    left_item = pop_stack(expt_stack)
                    self.play(FadeOut(left_item, shift=DOWN))
                    
                    self.play(*get_track_anims(L_MERGE_NEW))
                    
                    self.play(*get_track_anims(L_MERGE_LINK))
                    e_right = self.make_edge(node_pos['*'], node_pos['c'])
                    e_left = self.make_edge(node_pos['*'], node_pos['b'])
                    self.play(Create(e_right), Create(e_left))
                    
                with self.voiceover(text="最后，将合并生成的新树根结点的指针重新压回 EXPT 栈。") as tracker:
                    self.play(*get_track_anims(L_MERGE_PUSH))
                    item = push_stack(expt_stack, expt_base_line, "ptr(*)", GREEN)
                    self.play(FadeIn(item, shift=UP), run_time=tracker.duration)
                    
            elif step_type == 'pop_op_merge2':
                with self.voiceover(text="当前输入依然是井号，继续与栈顶比较，优先级仍低于加号，继续进行弹栈合并。") as tracker:
                    self.play(*get_track_anims(L_SWITCH))
                    self.play(*get_track_anims(L_CASE_GREATER))
                    
                with self.voiceover(text="弹出加号作为新的根结点，并从EXPT弹出两棵子树。") as tracker:
                    self.play(*get_track_anims(L_MERGE_POP))
                    op_item = pop_stack(optr_stack)
                    n_theta = self.make_node('+', node_pos['+'], BLUE)
                    created_nodes['+'] = n_theta
                    self.play(FadeOut(op_item, shift=DOWN), FadeIn(n_theta, scale=0.5))
                    
                    self.play(*get_track_anims(L_MERGE_POP2))
                    right_item = pop_stack(expt_stack)
                    self.play(FadeOut(right_item, shift=DOWN))
                    
                    self.play(*get_track_anims(L_MERGE_POP3))
                    left_item = pop_stack(expt_stack)
                    self.play(FadeOut(left_item, shift=DOWN))
                    
                    self.play(*get_track_anims(L_MERGE_LINK))
                    e_right = self.make_edge(node_pos['+'], node_pos['*'])
                    e_left = self.make_edge(node_pos['+'], node_pos['a'])
                    self.play(Create(e_right), Create(e_left))
                    
                with self.voiceover(text="再次将生成的新树压回 EXPT 栈。此时，栈中存放的就是完整的表达式树的根指针了。") as tracker:
                    self.play(*get_track_anims(L_MERGE_PUSH))
                    item = push_stack(expt_stack, expt_base_line, "ptr(+)", GREEN)
                    self.play(FadeIn(item, shift=UP), run_time=tracker.duration)
                    
            elif step_type == 'end':
                with self.voiceover(text="最后，当前输入井号与栈顶井号相遇，循环结束，弹出完整树即可完成创建。") as tracker:
                    self.play(*get_track_anims(L_CASE_EQUAL))
                    self.play(FadeOut(ch_pointer), run_time=tracker.duration)
                    
            step_idx += 1

        self.play(*get_track_anims(L_END))
        self.wait(1)

        # ===== 复杂度分析 =====
        time_box = VGroup(Text("时间复杂度: ", font_size=20, color=YELLOW), MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度: ", font_size=20, color=YELLOW), MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        complexity_text = VGroup(time_box, space_box).arrange(RIGHT, buff=0.8)
        complexity_text.to_edge(DOWN, buff=0.5)

        with self.voiceover(text="至此，表达式树创建完成。该算法每个字符最多进出栈各一次，因此时间复杂度和空间复杂度均为O(n)。") as tracker:
            self.play(FadeIn(complexity_text, shift=UP), run_time=tracker.duration)

        self.wait(2)
