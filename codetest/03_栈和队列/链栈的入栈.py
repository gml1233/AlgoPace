# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class LinkedListBase(VoiceoverScene):
    """动画公共基类"""
    pass


class ContinuousLinkStackPushVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角 Logo
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("链栈的入栈", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        # 总领句
        with self.voiceover(
                text="本节我们来学习链栈的入栈算法。该算法是将新元素压入链栈的栈顶。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== NEW PHASE — LIFE EXAMPLE (多节吊饰的挂接) =====
        # =========================================================================
        # 优化：上提标题 buff 至 1.2，防止垂直方向上过度下压
        example_title = Text("生活实例：多节吊饰的挂接", font_size=32, font="Microsoft YaHei", color=YELLOW).to_edge(UP,
                                                                                                                    buff=1.2)

        # 优化：将生活实例的 X 轴整体左移至 LEFT * 4.8，彻底拉开与中央大标题的横向距离，防冲突
        charm1 = RoundedRectangle(corner_radius=0.1, width=2.5, height=0.5, color=BLUE, fill_opacity=0.8)
        charm2 = RoundedRectangle(corner_radius=0.1, width=2.5, height=0.5, color=GREEN, fill_opacity=0.8)
        charm3 = RoundedRectangle(corner_radius=0.1, width=2.5, height=0.5, color=RED, fill_opacity=0.8)

        c1_text = Text("挂件 1", font_size=18, font="Microsoft YaHei").move_to(charm1.get_center())
        c2_text = Text("挂件 2", font_size=18, font="Microsoft YaHei").move_to(charm2.get_center())
        c3_text = Text("新挂件 3", font_size=18, font="Microsoft YaHei").move_to(charm3.get_center())

        eg1 = VGroup(charm1, c1_text).move_to(LEFT * 4.8 + DOWN * 1.0)
        eg2 = VGroup(charm2, c2_text).next_to(eg1, UP, buff=0.8)
        eg3 = VGroup(charm3, c3_text).move_to(LEFT * 4.8 + UP * 1.8)  # 优化：降低初始悬空高度，保证视窗内的舒适度

        ex_arrow1 = Arrow(start=eg2.get_bottom(), end=eg1.get_top(), buff=0.1, color=WHITE)
        ex_s_ptr = Arrow(start=eg2.get_left() + LEFT * 0.6, end=eg2.get_left(), buff=0.1, color=GREEN)
        ex_s_text = Text("主吊绳", font_size=18, font="Microsoft YaHei", color=GREEN).next_to(ex_s_ptr, LEFT, buff=0.1)
        ex_s_group = VGroup(ex_s_ptr, ex_s_text)

        with self.voiceover(
                text="我们可以把链栈的入栈想象成组装一串吊饰：每个挂件下方都有一个挂钩，显式地链向下一个挂件。") as tracker:
            self.play(FadeIn(example_title), FadeIn(eg1), FadeIn(eg2), Create(ex_arrow1), FadeIn(ex_s_group),
                      run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(
                text="当我们要加入一个新挂件 3 时，我们首先让新挂件底部的挂钩，勾住当前最上方的挂件 2 。") as tracker:
            self.play(FadeIn(eg3, shift=DOWN * 0.4), run_time=0.5)
            ex_arrow2 = Arrow(start=eg3.get_bottom(), end=eg2.get_top(), buff=0.1, color=WHITE)
            self.play(Create(ex_arrow2), run_time=max(0.1, tracker.duration - 0.5))

        with self.voiceover(
                text="最后，将主吊绳的控制权转移到新挂件 3 上。这样，新挂件就成为了整个链式吊饰的顶部。") as tracker:
            ex_s_group.generate_target()
            new_ptr = Arrow(start=eg3.get_left() + LEFT * 0.6, end=eg3.get_left(), buff=0.1, color=GREEN)
            new_text = Text("主吊绳", font_size=18, font="Microsoft YaHei", color=GREEN).next_to(new_ptr, LEFT,
                                                                                                 buff=0.1)
            ex_s_group.target = VGroup(new_ptr, new_text)
            self.play(MoveToTarget(ex_s_group), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        self.play(
            FadeOut(example_title), FadeOut(eg1), FadeOut(eg2), FadeOut(eg3),
            FadeOut(ex_arrow1), FadeOut(ex_arrow2), FadeOut(ex_s_group),
            run_time=0.5
        )

        # =========================================================================
        # ===== PHASE B — CODE BLOCK CONFIG =====
        # =========================================================================
        c_lines = [
            "Status Push(LinkStack &S, SElemType e)\n{//在栈顶插入元素e",
            "    p=new StackNode;\n        //生成新节点",
            "    p->data=e;\n        //将新节点数据域置为e",
            "    p->next=S;\n        //将新节点插入栈顶",
            "    S=p;\n        //修改栈顶指针为p",
            "    return OK;",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=12.0, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.13)
        SPACE_WIDTH = 0.095
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 6.25:
            code_group.scale_to_fit_width(6.25)
        if code_group.height > 5.4:
            code_group.scale_to_fit_height(5.4)
        bg_width = code_group.get_width() + 0.65
        bg_height = code_group.get_height() + 0.5
        code_bg = RoundedRectangle(corner_radius=0.2, height=bg_height, width=bg_width, color=GRAY, fill_opacity=0.1,
                                   stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.4)
        code_bg.match_y(code_group)

        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.2).to_edge(RIGHT, buff=0.4)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line: return [Wait(0.001)]
            anims = []
            if self.current_line is not None:
                anims.append(self.c_texts[self.current_line].animate.set_color(WHITE).scale(1 / 1.08, about_edge=LEFT))
            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW).scale(1.08, about_edge=LEFT))
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

        # ===== FUNCTIONS FOR LINKED STACK GUI =====
        def build_node(val_str="", is_tail=False):
            data_box = Rectangle(width=0.8, height=0.6, color=BLUE)
            data_text = Text(val_str, font_size=24, font="Arial").move_to(
                data_box.get_center()) if val_str else VGroup()
            next_box = Rectangle(width=0.4, height=0.6, color=BLUE).next_to(data_box, RIGHT, buff=0)
            dot = Dot(radius=0.05, color=WHITE).move_to(next_box.get_center())
            tail_marker = Text("^", font_size=24, color=WHITE).move_to(next_box.get_center())

            if is_tail:
                dot.set_opacity(0)
                tail_marker.set_opacity(1)
            else:
                dot.set_opacity(1)
                tail_marker.set_opacity(0)

            node = VGroup(data_box, data_text, next_box, dot, tail_marker)
            node.dot = dot
            node.tail_marker = tail_marker
            return node

        def get_ptr(label, target_mobj, color=GREEN, direction=LEFT):
            if np.array_equal(direction, UP):
                arrow = Arrow(start=target_mobj.get_top() + UP * 0.8, end=target_mobj.get_top(), buff=0.1, color=color)
                txt = Text(label, font_size=20, color=color, font="Arial").next_to(arrow, UP, buff=0.1)
            else:
                arrow = Arrow(start=target_mobj.get_left() + LEFT * 0.8, end=target_mobj.get_left(), buff=0.1,
                              color=color)
                txt = Text(label, font_size=20, color=color, font="Arial").next_to(arrow, LEFT, buff=0.1)
            return VGroup(arrow, txt)

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW =====
        # =========================================================================
        with self.voiceover(text="现在，我们来看该算法的代码实现与物理执行过程。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # 优化：物理实体也同步向左侧极化推移（LEFT * 4.8），腾出中央轨道
        n1 = build_node("2", is_tail=False).move_to(LEFT * 4.8 + ORIGIN)
        n2 = build_node("1", is_tail=True).move_to(LEFT * 4.8 + DOWN * 1.5)

        a1 = Arrow(start=n1.dot.get_center(), end=n2[2].get_top(), buff=0.1, color=WHITE)
        s_ptr = get_ptr("S", n1, GREEN)

        self.add(n1, n2, a1, s_ptr)

        with self.voiceover(text="假设当前链栈中已有两个元素，栈顶指针 S 稳稳地指向当前的栈顶首元结点。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="首先，程序动态分配内存，在堆区生成一个全新的空结点 p 。") as tracker:
            self.play(*get_track_anims(1), run_time=0.4)
            p_node = build_node("")
            p_node.move_to(LEFT * 4.8 + UP * 1.5)
            p_ptr = get_ptr("p", p_node, ORANGE, direction=UP)
            self.play(FadeIn(p_node), FadeIn(p_ptr), run_time=max(0.2, tracker.duration - 0.4))

        with self.voiceover(text="随后，将待插元素 10 写入新结点 p 的数据域中。") as tracker:
            self.play(*get_track_anims(2), run_time=0.5)
            val_10 = Text("10", font_size=24, font="Arial", color=GREEN).move_to(p_node[0].get_center())
            self.play(FadeIn(val_10, shift=DOWN * 0.3), run_time=max(0.2, tracker.duration - 0.5))
            p_node[1] = val_10

        with self.voiceover(
                text="接下来是入栈的核心操作：将新结点 p 的指针域指向当前的栈顶结点 S。这样就把新结点链接到了链栈的最顶端。") as tracker:
            self.play(*get_track_anims(3), run_time=0.5)
            p_arrow = Arrow(start=p_node.dot.get_center(), end=n1[2].get_top(), buff=0.1, color=WHITE)
            self.play(GrowArrow(p_arrow), run_time=max(0.2, tracker.duration - 0.5))

        with self.voiceover(text="最后，修改栈顶指针 S ，使其重新指向新的栈顶结点 p 。") as tracker:
            self.play(*get_track_anims(4), run_time=0.5)
            s_ptr.generate_target()
            s_ptr.target = get_ptr("S", p_node, GREEN)
            self.play(MoveToTarget(s_ptr), run_time=max(0.2, tracker.duration - 0.5))

        # 优化：由于左侧链栈永不消失，结果面板不能再放置在极左侧，而是建立在极其安全的中间空白区 (LEFT * 1.2)
        res_panel = VGroup(
            Text("结果：", font_size=22, font="Microsoft YaHei", color=GREEN),
            Text("入栈成功，返回 OK", font_size=20, font="Microsoft YaHei", color=GREEN)
        ).arrange(RIGHT, buff=0.1).move_to(LEFT * 1.2 + DOWN * 0.6)

        with self.voiceover(text="入栈操作全部完成，算法返回 OK 标志。") as tracker:
            self.play(*get_track_anims(5), Write(res_panel), run_time=tracker.duration)

        self.play(*get_track_anims(None), FadeOut(p_ptr), run_time=0.5)

        # 【核心优化】：彻底删除了原本在此处的 FadeOut 语句，确保链栈结构永久留存屏幕！

        # =========================================================================
        # ===== PHASE E — COMPLEXITY =====
        # =========================================================================
        # 优化：为了和常驻屏幕的左侧链栈拉开安全距离，时空复杂度面板紧随结果面板向下进行【垂直轨道纵向铺开】
        # Y轴跨度从 DOWN*0.6 顺延至 DOWN*1.8，位置精准可控，完美避开沉底字幕和左侧实体的双重夹击
        time_box = VGroup(
            Text("时间复杂度：", font_size=20, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(1)", font_size=20, color=YELLOW)
        ).arrange(RIGHT, buff=0.1).next_to(res_panel, DOWN, buff=0.3).align_to(res_panel, LEFT)

        space_box = VGroup(
            Text("空间复杂度：", font_size=20, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(1)", font_size=20, color=YELLOW)
        ).arrange(RIGHT, buff=0.1).next_to(time_box, DOWN, buff=0.3).align_to(time_box, LEFT)

        with self.voiceover(
                text="链栈的入栈只需在栈顶进行常数次指针变换，无需遍历寻找位置，因此时间复杂度为 O(1)。",
                subcaption="链栈的入栈只需在栈顶进行常数次指针变换，无需遍历寻找位置，因此时间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
                text="每次入栈仅需动态开辟一个新结点的内存空间，并没有使用额外的辅助数组，因此空间复杂度同样为 O(1)。",
                subcaption="每次入栈仅需动态开辟一个新结点的内存空间，并没有使用额外的辅助数组，因此空间复杂度同样为 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="这就是链栈入栈算法的完整演示过程。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)
