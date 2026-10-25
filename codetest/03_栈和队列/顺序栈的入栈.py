# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class LinkedListBase(VoiceoverScene):
    """动画公共基类"""
    pass


class ContinuousSeqStackPushVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角 Logo
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("顺序栈的入栈", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        # 总领句
        with self.voiceover(text="本节我们来学习顺序栈的入栈算法。该算法是在栈顶插入一个新的数据元素。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== NEW PHASE — LIFE EXAMPLE (盘子的入栈) =====
        # =========================================================================
        example_title = Text("生活实例：放置新盘子", font_size=32, font="Microsoft YaHei", color=YELLOW).to_edge(UP,
                                                                                                                buff=1.5)

        # 构造盘子，用不同颜色的圆角矩形表示
        plate1 = RoundedRectangle(corner_radius=0.1, width=3.0, height=0.4, color=BLUE, fill_opacity=0.8)
        plate2 = RoundedRectangle(corner_radius=0.1, width=3.0, height=0.4, color=GREEN, fill_opacity=0.8)
        plate3 = RoundedRectangle(corner_radius=0.1, width=3.0, height=0.4, color=RED, fill_opacity=0.8)  # 即将新入栈的盘子

        p1_text = Text("盘子 1", font_size=18, font="Microsoft YaHei").move_to(plate1.get_center())
        p2_text = Text("盘子 2", font_size=18, font="Microsoft YaHei").move_to(plate2.get_center())
        p3_text = Text("新盘子 3", font_size=18, font="Microsoft YaHei").move_to(plate3.get_center())

        g1 = VGroup(plate1, p1_text).move_to(DOWN * 1.5)
        g2 = VGroup(plate2, p2_text).next_to(g1, UP, buff=0.1)
        g3 = VGroup(plate3, p3_text).next_to(g2, UP, buff=1.2)  # 初始让新盘子悬空

        table_line = Line(LEFT * 2.5, RIGHT * 2.5, color=WHITE).next_to(g1, DOWN, buff=0.05)

        with self.voiceover(text="同样以叠盘子为例。当我们洗好一个新的盘子时，总是把它放在这叠盘子的最顶端。") as tracker:
            self.play(FadeIn(example_title), Create(table_line), FadeIn(g1), FadeIn(g2), run_time=0.6)
            # 模拟新盘子垂直降落、叠加到顶部的动作
            self.play(g3.animate.next_to(g2, UP, buff=0.1), run_time=tracker.duration - 0.6)

        with self.voiceover(
                text="这种在已有盘子堆的顶端继续叠加新盘子的动作，就完美对应了数据结构中栈的入栈操作。") as tracker:
            self.wait(tracker.duration)

        # 动画结束，彻底清空生活实例相关的组件，为后面的算法演示留出干净空间
        self.play(FadeOut(example_title), FadeOut(table_line), FadeOut(g1), FadeOut(g2), FadeOut(g3), run_time=0.5)

        # =========================================================================
        # ===== PHASE B — CODE BLOCK CONFIG =====
        # =========================================================================
        c_lines = [
            "Status Push(SqStack &S, SElemType e)",
            "{",
            "    if (S.top - S.base == S.stacksize) return ERROR; //栈满",
            "    *S.top++=e ； //将元素e压入栈顶，栈顶指针加1",
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

        code_bg = RoundedRectangle(
            corner_radius=0.2,
            height=bg_height,
            width=bg_width,
            color=GRAY,
            fill_opacity=0.1,
            stroke_width=1
        )

        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.4)
        code_bg.match_y(code_group)

        # 优化：采用 next_to 挂载在 logo 下方，彻底避免向上遮挡标题和 logo
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

        # ===== FUNCTIONS FOR STACK GUI =====
        def build_stack_boxes(max_size=3):
            return VGroup(*[Square(side_length=0.8, color=BLUE) for _ in range(max_size)]).arrange(UP, buff=0).move_to(
                LEFT * 3.0 + UP * 1.0)

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

        def get_base_ptr(boxes):
            return get_ptr("S.base", boxes[0], ORANGE, direction=RIGHT)

        def get_top_ptr_at(idx, boxes):
            if idx < len(boxes):
                target_mobj = boxes[idx]
            else:
                target_mobj = Square(side_length=0.8).move_to(boxes[-1].get_center() + UP * 0.8)
            return get_ptr("S.top", target_mobj, GREEN, direction=LEFT)

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW =====
        # =========================================================================
        with self.voiceover(text="现在，我们来看该算法的代码实现与物理执行过程。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # ---------------- 场景演练 1：栈满 ----------------
        MAX_SIZE = 3
        s1_boxes = build_stack_boxes(MAX_SIZE)
        s1_elements = VGroup(
            Text("3", font_size=26, font="Arial").move_to(s1_boxes[0].get_center()),
            Text("2", font_size=26, font="Arial").move_to(s1_boxes[1].get_center()),
            Text("1", font_size=26, font="Arial").move_to(s1_boxes[2].get_center())
        )
        s1_base_ptr = get_base_ptr(s1_boxes)
        s1_top_ptr = get_top_ptr_at(3, s1_boxes)

        stack_size_label = VGroup(Text("栈最大容量：", font_size=18, font="Microsoft YaHei", color=GRAY_A),
                                  MathTex("S.stacksize = 3", font_size=20, color=GRAY_A)).arrange(RIGHT,
                                                                                                  buff=0.1).next_to(
            s1_boxes, UP, buff=0.3).align_to(s1_boxes, LEFT)
        param_panel_err = VGroup(Text("当前状态：", font_size=22, font="Microsoft YaHei", color=RED),
                                 Text("尝试压入新元素 9", font_size=20, font="Microsoft YaHei", color=RED)).arrange(
            RIGHT, buff=0.15).next_to(code_block, DOWN, buff=0.2).align_to(code_block, LEFT)

        self.add(s1_boxes, s1_elements, s1_base_ptr, s1_top_ptr, stack_size_label, param_panel_err)

        with self.voiceover(
                text="首先，我们来看一种异常情况：假设当前的顺序栈已经填满了数值 3、2、1，此时我们尝试继续压入新元素 9 。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(
                text="算法进入第一步，判断栈顶指针 S.top 与栈底指针 S.base 的差值是否等于最大容量。") as tracker:
            self.play(*get_track_anims(2), run_time=tracker.duration)

        with self.voiceover(text="由于目前指针差值刚好等于最大容量 3 ，触发栈满条件，算法返回 ERROR。") as tracker:
            flash_rect = SurroundingRectangle(code_bg, color=RED, buff=0.0)
            self.play(Create(flash_rect), run_time=0.5)
            self.play(FadeOut(flash_rect), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 1.0))

        self.remove(stack_size_label)
        self.play(*get_track_anims(None), FadeOut(s1_boxes), FadeOut(s1_elements), FadeOut(s1_base_ptr),
                  FadeOut(s1_top_ptr), FadeOut(param_panel_err), run_time=0.5)
        self.wait(0.2)

        # ---------------- 场景演练 2：正常入栈 ----------------
        s2_boxes = build_stack_boxes(MAX_SIZE)
        s2_elements = VGroup(
            Text("3", font_size=26, font="Arial").move_to(s2_boxes[0].get_center()),
            Text("2", font_size=26, font="Arial").move_to(s2_boxes[1].get_center())
        )
        s2_base_ptr = get_base_ptr(s2_boxes)
        s2_top_ptr = get_top_ptr_at(2, s2_boxes)

        param_panel_ok = VGroup(Text("入栈参数：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                                MathTex("e = 10", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.15).next_to(
            code_block, DOWN, buff=0.2).align_to(code_block, LEFT)

        self.add(s2_boxes, s2_elements, s2_base_ptr, s2_top_ptr, param_panel_ok)

        with self.voiceover(text="接下来看正常入栈：假设栈内包含数值 3 和 2，我们要压入新元素 10。") as tracker:
            self.play(*get_track_anims(0), run_time=tracker.duration)

        with self.voiceover(text="边界检查通过，此时栈顶指针指向索引为 2 的空闲位置。") as tracker:
            self.play(*get_track_anims(2), run_time=tracker.duration)

        with self.voiceover(text="执行入栈操作。首先将元素 10 写入当前 S.top 所指向的格子。") as tracker:
            self.play(*get_track_anims(3), run_time=0.5)
            new_val = Text("10", font_size=26, font="Arial", color=GREEN).move_to(s2_boxes[2].get_center())
            self.play(FadeIn(new_val, shift=DOWN * 0.3), run_time=max(0.2, tracker.duration - 0.5))

        with self.voiceover(text="随后栈顶指针 S.top 自动向上平移递增，指向下一个可用的空闲位置。") as tracker:
            target_top_ptr_final = get_top_ptr_at(3, s2_boxes)
            self.play(Transform(s2_top_ptr, target_top_ptr_final), run_time=tracker.duration)

        # 优化：搬移至更左侧，并采用横向一字平铺展开，为时空复杂度抬升腾出完美的视觉中轨线
        res_panel = VGroup(
            Text("结果：", font_size=22, font="Microsoft YaHei", color=GREEN),
            Text("入栈成功，返回 OK", font_size=20, font="Microsoft YaHei", color=GREEN)
        ).arrange(RIGHT, buff=0.1).move_to(LEFT * 4.0 + DOWN * 1.6)

        with self.voiceover(text="入栈成功，算法最终返回 OK。") as tracker:
            self.play(*get_track_anims(4), Write(res_panel), run_time=tracker.duration)

        self.play(*get_track_anims(None), run_time=0.3)

        # ===== PHASE E — COMPLEXITY =====
        # 优化：跟随结果面板在同一水平高度（DOWN * 1.6）横向向右展开，彻底避开最下方的字幕安全区
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(res_panel,
                                                                                                        RIGHT, buff=0.6)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(time_box,
                                                                                                         RIGHT,
                                                                                                         buff=0.6)

        with self.voiceover(
                text="由于顺序栈入栈操作是通过指针寻址直接定位内存单元，不需要进行任何数据遍历，因此算法的时间复杂度为 O(1) 。",
                subcaption="由于顺序栈入栈操作是通过指针寻址直接定位内存单元，不需要进行任何数据遍历，因此算法的时间复杂度为 O(1) 。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
                text="整个入栈流程仅利用了常数个控制变量与指针，没有引入并开辟任何多余的动态辅助空间，额外空间复杂度同样为 O(1) 。",
                subcaption="整个入栈流程仅利用了常数个控制变量与指针，没有引入并开辟任何多余的动态辅助空间，额外空间复杂度同样为 O(1) 。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="这就是顺序栈入栈算法的完整演示过程。") as tracker:
            self.wait(tracker.duration)
        self.wait(2)