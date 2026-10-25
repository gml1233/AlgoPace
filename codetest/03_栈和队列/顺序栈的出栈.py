# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class SeqStackPopVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角 Logo
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("顺序栈的出栈", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(text="本节学习顺序栈的出栈算法。出栈操作用于删除并返回栈顶元素。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== NEW PHASE — LIFE EXAMPLE (取走最上面的盘子) =====
        # =========================================================================
        example_title = Text("生活实例：取走最上面的盘子", font_size=32, font="Microsoft YaHei", color=YELLOW).to_edge(
            UP, buff=1.5)

        # 构造三个叠放的盘子，用不同颜色的圆角矩形表示
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

        with self.voiceover(text="当我们从一叠堆放好的盘子中取盘子去使用时，同样只能从最上方拿。") as tracker:
            self.play(FadeIn(example_title), Create(table_line), FadeIn(g1), FadeIn(g2), FadeIn(g3), run_time=0.6)
            # 模拟最上方的盘子3被拿走的动作
            self.play(g3.animate.shift(UP * 1.5).set_opacity(0), run_time=tracker.duration - 0.6)

        with self.voiceover(text="把最顶部的盘子拿走移出，这个过程就完美对应了数据结构中栈的出栈（Pop）操作。") as tracker:
            self.wait(tracker.duration)

        # 动画结束，彻底清空生活实例相关的组件，为后面的算法演示留出干净空间
        self.play(FadeOut(example_title), FadeOut(table_line), FadeOut(g1), FadeOut(g2), run_time=0.5)

        # =========================================================================
        # ===== PHASE B — CODE BLOCK CONFIG =====
        # =========================================================================
        c_lines = [
            "Status Pop(SqStack &S, SElemType &e)",
            "{",
            "    if (S.base == S.top)",
            "        return ERROR;",
            "    e = *(--S.top);",
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

        with self.voiceover(text="右侧是出栈算法的代码实现，我们将分情况进行演示。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # =========================================================================
        # ===== PHASE C — VISUALIZATION SETUP =====
        # =========================================================================
        def build_seq_stack_boxes(max_size=3):
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

        # ---------------- 场景演练 1：栈空报错 ----------------
        MAX_SIZE = 3
        s1_boxes = build_seq_stack_boxes(MAX_SIZE).move_to(LEFT * 3.5 + DOWN * 0.5)

        s1_base_ptr = get_ptr("S.base", s1_boxes[0], ORANGE, direction=RIGHT)
        s1_top_ptr = get_ptr("S.top", s1_boxes[0], GREEN, direction=LEFT)

        param_panel_err = VGroup(Text("当前状态：", font_size=22, font="Microsoft YaHei", color=RED),
                                 Text("空栈，无元素", font_size=20, font="Microsoft YaHei", color=RED)).arrange(RIGHT,
                                                                                                               buff=0.15).next_to(
            code_block, DOWN, buff=0.2).align_to(code_block, LEFT)

        self.add(s1_boxes, s1_base_ptr, s1_top_ptr, param_panel_err)

        with self.voiceover(text="首先，我们来看异常情况：假设当前顺序栈中没有任何元素，是一个空栈。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="算法第一步会判断栈顶指针 S.top 与栈底指针 S.base 是否指向同一位置。") as tracker:
            self.play(*get_track_anims(2), run_time=tracker.duration)

        with self.voiceover(text="由于它们完全重合，说明此时无元素可弹，触发空栈条件，算法返回 ERROR。") as tracker:
            self.play(*get_track_anims(3), run_time=0.3)
            flash_rect = SurroundingRectangle(code_bg, color=RED, buff=0.0)
            self.play(Create(flash_rect), run_time=0.4)
            self.play(FadeOut(flash_rect), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 1.1))

        # 清空场景 1 资产
        self.play(*get_track_anims(None), FadeOut(s1_boxes), FadeOut(s1_base_ptr), FadeOut(s1_top_ptr),
                  FadeOut(param_panel_err), run_time=0.5)
        self.wait(0.2)

        # ---------------- 场景演练 2：正常出栈 ----------------
        s2_boxes = build_seq_stack_boxes(MAX_SIZE).move_to(LEFT * 3.5 + DOWN * 0.5)
        val_10 = Text("10", font_size=26, font="Arial").move_to(s2_boxes[0].get_center())
        val_20 = Text("20", font_size=26, font="Arial").move_to(s2_boxes[1].get_center())
        s2_elements = VGroup(val_10, val_20)

        s2_base_ptr = get_ptr("S.base", s2_boxes[0], ORANGE, direction=RIGHT)
        s2_top_ptr = get_ptr("S.top", s2_boxes[2], GREEN, direction=LEFT)

        e_label = VGroup(
            Text("接收参数 e = ", font_size=22, font="Microsoft YaHei", color=YELLOW),
            Text("?", font_size=22, font="Arial", color=YELLOW)
        ).arrange(RIGHT, buff=0.1).move_to(LEFT * 4.0 + UP * 2.0)

        self.add(s2_boxes, s2_elements, s2_base_ptr, s2_top_ptr, e_label)

        with self.voiceover(
                text="接下来看正常出栈流程：假设栈内已经有两个数值 10 和 20，S.top 指向空闲位置。画面上方准备了变量 e 接收弹出的值。") as tracker:
            self.play(*get_track_anims(0), run_time=tracker.duration)

        with self.voiceover(text="边界检查判断通过。") as tracker:
            self.play(*get_track_anims(2), run_time=tracker.duration)

        with self.voiceover(
                text="随后执行出栈核心操作。首先是前置自减操作：S.top 指针向下移动一格，重新指向当前的栈顶元素 20。") as tracker:
            self.play(*get_track_anims(4), run_time=0.4)
            target_top_ptr = get_ptr("S.top", s2_boxes[1], GREEN, direction=LEFT)
            self.play(Transform(s2_top_ptr, target_top_ptr), run_time=max(0.5, tracker.duration - 0.4))

        with self.voiceover(text="接着解引用，将 S.top 所指格子里的数值，提取并赋值给参数 e 。") as tracker:
            copy_val = val_20.copy()
            self.play(copy_val.animate.move_to(e_label[1].get_center()), run_time=0.8)
            new_e_val = Text("20", font_size=22, font="Arial", color=YELLOW).move_to(e_label[1].get_center())
            self.remove(e_label[1], copy_val)
            e_label.add(new_e_val)
            # 在原栈中淡出该元素，表示逻辑删除
            self.play(FadeOut(val_20), run_time=max(0.2, tracker.duration - 0.8))

        # 优化：搬移至更左侧，并采用横向一字平铺展开，为时空复杂度抬升腾出完美的布局安全区
        res_panel = VGroup(
            Text("结果：", font_size=22, font="Microsoft YaHei", color=GREEN),
            Text("出栈成功，返回 OK", font_size=20, font="Microsoft YaHei", color=GREEN)
        ).arrange(RIGHT, buff=0.1).move_to(LEFT * 4.0 + DOWN * 1.6)

        with self.voiceover(text="最终元素成功弹出，算法返回 OK。") as tracker:
            self.play(*get_track_anims(5), Write(res_panel), run_time=tracker.duration)

        self.play(*get_track_anims(None), run_time=0.4)

        # ===== PHASE E — COMPLEXITY =====
        # 优化：与结果面板在同一水平高度（DOWN * 1.6）横向向右平行铺开，彻底拉离被字幕遮挡的深水区
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(res_panel,
                                                                                                        RIGHT, buff=0.6)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(time_box,
                                                                                                         RIGHT,
                                                                                                         buff=0.6)

        with self.voiceover(
                text="顺序栈的出栈操作只涉及修改栈顶指针和赋值，完全不需要遍历数据，因此时间复杂度为 O(1)。",
                subcaption="顺序栈的出栈操作只涉及修改栈顶指针和赋值，完全不需要遍历数据，因此时间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
                text="在执行过程中，也没有引入任何依赖数据规模的多余辅助空间，额外空间复杂度同样为 O(1)。",
                subcaption="在执行过程中，也没有引入任何依赖数据规模的多余辅助空间，额外空间复杂度同样为 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是顺序栈出栈算法的完整演示过程。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)