# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class SeqStackInitVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角 Logo
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("顺序栈的初始化", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(text="本节学习顺序栈的初始化算法。该算法用于在内存中构造一个空的顺序栈。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== NEW PHASE — LIFE EXAMPLE (盘子的堆叠) =====
        # =========================================================================
        example_title = Text("生活实例：盘子的堆叠", font_size=32, font="Microsoft YaHei", color=YELLOW).to_edge(UP,
                                                                                                                buff=1.5)

        # 构造三个盘子，用不同颜色的圆角矩形表示
        plate1 = RoundedRectangle(corner_radius=0.1, width=3.0, height=0.4, color=BLUE, fill_opacity=0.8)
        plate2 = RoundedRectangle(corner_radius=0.1, width=3.0, height=0.4, color=GREEN, fill_opacity=0.8)
        plate3 = RoundedRectangle(corner_radius=0.1, width=3.0, height=0.4, color=RED, fill_opacity=0.8)

        p1_text = Text("盘子 1", font_size=18, font="Microsoft YaHei").move_to(plate1.get_center())
        p2_text = Text("盘子 2", font_size=18, font="Microsoft YaHei").move_to(plate2.get_center())
        p3_text = Text("盘子 3", font_size=18, font="Microsoft YaHei").move_to(plate3.get_center())

        g1 = VGroup(plate1, p1_text).move_to(DOWN * 1.5)
        g2 = VGroup(plate2, p2_text).next_to(g1, UP, buff=0.1)
        g3 = VGroup(plate3, p3_text).next_to(g2, UP, buff=0.1)

        table_line = Line(LEFT * 2.5, RIGHT * 2.5, color=WHITE).next_to(g1, DOWN, buff=0.05)

        with self.voiceover(text="在生活中，我们经常会把盘子一个个叠放起来。") as tracker:
            self.play(FadeIn(example_title), Create(table_line), run_time=0.5)
            # 模拟盘子从上往下依次落下的堆叠过程
            self.play(FadeIn(g1, shift=UP * 1.5), run_time=0.4)
            self.play(FadeIn(g2, shift=UP * 1.5), run_time=0.4)
            self.play(FadeIn(g3, shift=UP * 1.5), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 1.7))

        with self.voiceover(
                text="当我们需要使用盘子时，只能从最上面移走刚放上去的盘子。这种后进先出的结构，在数据结构中就被称为栈。") as tracker:
            # 模拟拿走最上面的盘子3
            self.play(g3.animate.shift(UP * 1.5).set_opacity(0), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))

        # 清空生活实例相关的组件，为接下来的算法演示腾出左侧空间
        self.play(FadeOut(example_title), FadeOut(table_line), FadeOut(g1), FadeOut(g2), run_time=0.5)

        # =========================================================================
        # ===== PHASE B — CODE BLOCK CONFIG =====
        # =========================================================================
        c_lines = [
            "Status InitStack(SqStack &S)",
            "{",
            "    S.base = new SElemType[MAXSIZE];",
            "    if (!S.base)",
            "        exit(OVERFLOW);",
            "    S.top = S.base;",
            "    S.stacksize = MAXSIZE;",
            "    return OK;",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=11.5, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        SPACE_WIDTH = 0.095
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        bg_width = code_group.get_width() * 1.2 + 0.8
        bg_height = code_group.get_height() + 0.6
        code_bg = RoundedRectangle(corner_radius=0.2, height=bg_height, width=bg_width, color=GRAY, fill_opacity=0.1,
                                   stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.4)
        code_bg.match_y(code_group)

        # 优化：代码块紧贴 logo 下方，防止与标题和 logo 产生遮挡
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.2).to_edge(RIGHT, buff=0.4)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line: return []
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

        with self.voiceover(text="右侧是顺序栈初始化算法的代码实现。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # =========================================================================
        # ===== PHASE C — VISUALIZATION SETUP =====
        # =========================================================================
        def build_seq_stack_boxes(max_size=5):
            return VGroup(*[Square(side_length=0.8, color=BLUE) for _ in range(max_size)]).arrange(UP, buff=0)

        def get_ptr(label, target_mobj, color=GREEN, direction=UP):
            if np.array_equal(direction, UP):
                arrow = Arrow(start=target_mobj.get_top() + UP * 0.8, end=target_mobj.get_top(), buff=0.1, color=color)
                txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, UP, buff=0.1)
            elif np.array_equal(direction, DOWN):
                arrow = Arrow(start=target_mobj.get_bottom() + DOWN * 0.8, end=target_mobj.get_bottom(), buff=0.1,
                              color=color)
                txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, DOWN, buff=0.1)
            elif np.array_equal(direction, LEFT):
                arrow = Arrow(start=target_mobj.get_left() + LEFT * 0.8, end=target_mobj.get_left(), buff=0.1,
                              color=color)
                txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, LEFT, buff=0.1)
            else:  # RIGHT
                arrow = Arrow(start=target_mobj.get_right() + RIGHT * 0.8, end=target_mobj.get_right(), buff=0.1,
                              color=color)
                txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, RIGHT, buff=0.1)
            return VGroup(arrow, txt)

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW =====
        # =========================================================================
        # 第一步：动态分配空间
        with self.voiceover(text="首先，程序向系统申请并动态分配一块大小为 MAXSIZE 的数组空间。") as tracker:
            self.play(*get_track_anims(2), run_time=0.4)
            boxes = build_seq_stack_boxes(5).move_to(LEFT * 3.5 + DOWN * 0.5)
            base_ptr = get_ptr("S.base", boxes[0], ORANGE, direction=RIGHT)
            self.play(FadeIn(boxes), FadeIn(base_ptr), run_time=max(0.2, tracker.duration - 0.4))

        # 第二步：内存分配检查
        with self.voiceover(
                text="接着检查内存分配是否成功。如果基址指针非空，说明分配成功，跳过异常退出处理分支。") as tracker:
            self.play(*get_track_anims(3), run_time=0.4)
            self.play(self.c_texts[3].animate.set_color(GREEN), run_time=0.3)
            self.play(self.c_texts[3].animate.set_color(YELLOW), run_time=max(0.1, tracker.duration - 0.7))

        # 第三步：初始化栈顶指针
        with self.voiceover(
                text="核心操作来了：因为初始为空栈，内部没有任何元素，所以将栈顶指针 S.top 置为与栈底指针 S.base 相同的位置。这标志着此时是一个空栈。") as tracker:
            self.play(*get_track_anims(5), run_time=0.4)
            top_ptr = get_ptr("S.top", boxes[0], GREEN, direction=LEFT)
            self.play(FadeIn(top_ptr, shift=RIGHT * 0.5), run_time=max(0.5, tracker.duration - 0.4))

        # 第四步：设置最大容量
        with self.voiceover(text="然后，记录栈的当前最大容量 S.stacksize 等于 MAXSIZE。") as tracker:
            self.play(*get_track_anims(6), run_time=0.4)
            stack_size_label = VGroup(
                Text("最大容量：", font_size=20, font="Microsoft YaHei", color=GRAY_A),
                Text("S.stacksize = 5", font_size=20, font="Arial", color=GRAY_A)
            ).arrange(RIGHT, buff=0.1).next_to(boxes, UP, buff=0.4)
            self.play(Write(stack_size_label), run_time=max(0.2, tracker.duration - 0.4))

        # 第五步：成功返回
        # 优化：放置在左侧安全区域，完全脱离右侧，防止在代码块过长时发生挤压
        res_panel = VGroup(
            Text("结果：", font_size=22, font="Microsoft YaHei", color=GREEN),
            Text("初始化成功，返回 OK", font_size=20, font="Microsoft YaHei", color=GREEN)
        ).arrange(RIGHT, buff=0.1).move_to(LEFT * 4.0 + DOWN * 3.0)

        with self.voiceover(text="最后，初始化圆满成功，算法返回 OK。一个崭新的空顺序栈就构建完毕了。") as tracker:
            self.play(*get_track_anims(7), Write(res_panel), run_time=tracker.duration)

        self.play(*get_track_anims(None), run_time=0.5)

        # =========================================================================
        # ===== PHASE E — COMPLEXITY =====
        # =========================================================================
        # 优化：紧贴结果面板右侧横向平铺展开，高度上移，保证不被底部视频字幕遮挡
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(res_panel,
                                                                                                        RIGHT, buff=0.6)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(time_box,
                                                                                                         RIGHT,
                                                                                                         buff=0.6)

        with self.voiceover(
                text="顺序栈的初始化只涉及开辟空间与常数次的指针赋值操作，因此时间复杂度为 O(1)。",
                subcaption="顺序栈的初始化只涉及开辟空间与常数次的指针赋值操作，因此时间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
                text="由于除了开辟栈本身的存储空间外，并没有引入依赖数据规模的额外辅助空间，因此空间复杂度也是 O(1)。",
                subcaption="由于除了开辟栈本身的存储空间外，并没有引入依赖数据规模的额外辅助空间，因此空间复杂度也是 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是顺序栈初始化算法的完整演示过程。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)