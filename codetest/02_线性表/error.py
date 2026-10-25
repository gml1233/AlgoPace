# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class ContinuousSeqListSearchVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角全局图片 Logo（紧靠右上角且放大一倍，伴随顶部微调）
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("顺序表的查找", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(
                text="本节我们来学习顺序表的查找算法。该算法用于在顺序表中查找与给定值相等的元素，并返回其位置序号。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== PHASE B — CODE BLOCK CONFIG (算法代码块排版部分) =====
        # =========================================================================
        c_lines = [
            "int LocateElem(SqList L, ElemType e)",
            "{",
            "    for (int i = 0; i < L.length; i++)",
            "        if (L.elem[i] == e)",
            "            return i + 1;",
            "    return 0;",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            # 使用 "Microsoft YaHei" 字体支持无损渲染
            t = Text(stripped_line, font_size=11.5, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        SPACE_WIDTH = 0.095  # 适配中文字体的标准缩进量
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        buff_val = 0.25
        radius_val = 0.2

        code_bg = RoundedRectangle(
            corner_radius=radius_val,
            height=code_group.get_height() + 2 * buff_val,
            width=code_group.get_width() + 2 * buff_val,
            color=GRAY,
            fill_opacity=0.1,
            stroke_width=1
        )
        code_bg.move_to(code_group)

        # 使用 to_edge(RIGHT) 让长代码块紧贴右边缘，垂直中心固定在 UP * 0.2
        code_block = VGroup(code_bg, code_group).to_edge(RIGHT, buff=0.4).shift(UP * 0.2)

        # ===== CODE HIGHLIGHT HELPER =====
        self.current_line = None

        def get_track_anims(new_idx):
            anims = []
            if self.current_line is not None:
                old_idx = self.current_line
                anims.append(self.c_texts[old_idx].animate.set_color(WHITE).scale(1 / 1.2, about_edge=LEFT))

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

        # ===== FUNCTIONS FOR SEQ LIST GUI =====
        def build_annotated_sequence(values):
            l_boxes = VGroup(*[Square(side_length=0.8, color=BLUE) for _ in range(len(values))]).arrange(RIGHT, buff=0)
            l_nums = VGroup(*[Text(str(val), font_size=28, font="Arial") for val in values])
            for box, num in zip(l_boxes, l_nums):
                num.move_to(box.get_center())

            position_marks = VGroup(
                *[Text(str(index + 1), font_size=18, color=ORANGE, font="Arial") for index in range(len(values))])
            for box, mark in zip(l_boxes, position_marks):
                mark.next_to(box, UP, buff=0.12)

            index_marks = VGroup(
                *[Text(str(index), font_size=18, color=TEAL_A, font="Arial") for index in range(len(values))])
            for box, mark in zip(l_boxes, index_marks):
                mark.next_to(box, DOWN, buff=0.12)

            position_label = Text("位置", font_size=20, color=ORANGE, font="Microsoft YaHei").next_to(position_marks,
                                                                                                      LEFT, buff=0.3)
            l_label = Text("L", font_size=24, color=BLUE, font="Arial").next_to(l_boxes, LEFT, buff=0.3)
            index_label = Text("下标", font_size=20, color=TEAL_A, font="Microsoft YaHei").next_to(index_marks, LEFT,
                                                                                                   buff=0.3)

            array_group = VGroup(position_label, position_marks, l_label, l_boxes, l_nums, index_label, index_marks)
            return array_group, l_boxes, index_marks

        def build_i_pointer(anchor_mark, label_text="i"):
            # 指针从下方指向上方（指向底部的下标）
            i_arrow = Arrow(DOWN, UP, buff=0.05, tip_length=0.15).scale(0.3).next_to(anchor_mark, DOWN, buff=0.02)
            i_arrow.set_color(RED)
            i_text = Text(label_text, font_size=18, color=RED, font="Arial").next_to(i_arrow, DOWN, buff=0.02)
            return VGroup(i_arrow, i_text)

        # ===== PHASE C — ANIMATION FLOW (顺序表算法物理演练) =====
        # 修改 1：统一说“我们学习该算法的代码实现”
        with self.voiceover(text="现在，我们学习该算法的代码实现。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        L_values = [3, 7, 1, 9, 5]
        array_l, l_boxes, index_marks = build_annotated_sequence(L_values)
        # 顺序表整体向左平移至 LEFT * 3.0，与右侧的长文本代码块彻底拉开物理安全间距
        array_l.move_to(LEFT * 3.0 + UP * 0.5)

        # 修改 2：直接说“这是包含5个元素的顺序表L”
        with self.voiceover(text="这是包含5个元素的顺序表L，内部元素如图所示。") as tracker:
            self.play(Create(array_l), run_time=tracker.duration)

        length_marker = VGroup(
            Text("表长：", font_size=22, font="Microsoft YaHei", color=WHITE),
            MathTex("L.length = 5", font_size=24, color=WHITE)
        ).arrange(RIGHT, buff=0.1).next_to(array_l, UP, buff=0.6).align_to(array_l, LEFT)
        self.play(FadeIn(length_marker))

        e_target_val = 1
        e_panel = VGroup(
            Text("待查找值：", font_size=24, font="Microsoft YaHei", color=YELLOW),
            MathTex(f"e = {e_target_val}", font_size=26, color=YELLOW)
        ).arrange(RIGHT, buff=0.15).next_to(array_l, DOWN, buff=1.2).align_to(array_l, LEFT)

        # 修改 5：TTS 中“1”发音矫正（Voiceover 使用“壹”，字幕显示“1”）
        with self.voiceover(
                text="假设我们要查找值为壹的元素。",
                subcaption="假设我们要查找值为1的元素。"
        ) as tracker:
            # 引入时高亮切入函数头部
            self.play(*get_track_anims(0), FadeIn(e_panel), run_time=tracker.duration)
        self.wait(0.2)

        # ---------------- 场景演练 1：遍历查找演示 ----------------
        i_ptr = build_i_pointer(index_marks[0], label_text="i=0")

        # 修改 3：改为“进入for循环”
        with self.voiceover(text="算法进入for循环，初始化下标i为 0。") as tracker:
            self.play(*get_track_anims(2), Create(i_ptr), run_time=tracker.duration)

        # 第 1 次比较 (i=0, val=3)
        target_highlight = SurroundingRectangle(l_boxes[0], color=YELLOW, buff=0.04, stroke_width=3)
        with self.voiceover(text="当前元素的值为3，与待查找值不相等。") as tracker:
            self.play(*get_track_anims(3), Create(target_highlight), run_time=tracker.duration)
        self.play(FadeOut(target_highlight), run_time=0.2)

        # 第 2 次比较 (i=1, val=7)
        # 修改 5：i 加壹发音矫正
        with self.voiceover(
                text="i加壹，进入下一次for循环。",
                subcaption="i加1，进入下一次for循环。"
        ) as tracker:
            self.play(*get_track_anims(2), run_time=0.3)
            new_i_ptr = build_i_pointer(index_marks[1], label_text="i=1")
            self.play(Transform(i_ptr, new_i_ptr), run_time=max(0.2, tracker.duration - 0.3))

        target_highlight = SurroundingRectangle(l_boxes[1], color=YELLOW, buff=0.04, stroke_width=3)
        with self.voiceover(text="当前元素的值为7，依然不相等。") as tracker:
            self.play(*get_track_anims(3), Create(target_highlight), run_time=tracker.duration)
        self.play(FadeOut(target_highlight), run_time=0.2)

        # 第 3 次比较 (i=2, val=1) - 查找成功
        with self.voiceover(text="继续遍历。") as tracker:
            self.play(*get_track_anims(2), run_time=0.3)
            new_i_ptr = build_i_pointer(index_marks[2], label_text="i=2")
            self.play(Transform(i_ptr, new_i_ptr), run_time=max(0.2, tracker.duration - 0.3))

        target_highlight = SurroundingRectangle(l_boxes[2], color=GREEN, buff=0.04, stroke_width=3)

        # 修改 4 和 5：“当前元素的值为1”，并矫正发音
        with self.voiceover(
                text="当前元素的值为壹，等于待查找值，查找成功！",
                subcaption="当前元素的值为1，等于待查找值，查找成功！"
        ) as tracker:
            self.play(*get_track_anims(3), Create(target_highlight), l_boxes[2].animate.set_fill(GREEN, opacity=0.3),
                      run_time=tracker.duration)

        res_panel = VGroup(
            Text("查找结果：", font_size=24, font="Microsoft YaHei", color=GREEN),
            MathTex("return\\ 3", font_size=26, color=GREEN)
        ).arrange(RIGHT, buff=0.15).next_to(e_panel, DOWN, buff=0.4).align_to(e_panel, LEFT)

        # 修改 5：“下标加壹”发音矫正
        with self.voiceover(
                text="返回该元素的序号，也就是下标加壹，最终结果为3。",
                subcaption="返回该元素的序号，也就是下标加1，最终结果为3。"
        ) as tracker:
            self.play(*get_track_anims(4), Write(res_panel), run_time=tracker.duration)

        self.play(*get_track_anims(None), FadeOut(target_highlight), FadeOut(i_ptr), run_time=0.5)

        # ---------------- 场景演练 2：查找失败说明 ----------------
        with self.voiceover(
                text="如果遍历完整个顺序表都没有找到匹配的元素，算法将跳出for循环，返回0，表示查找失败。") as tracker:
            self.play(*get_track_anims(5), run_time=tracker.duration)

        self.play(*get_track_anims(None), run_time=0.5)

        # =========================================================================
        # ===== PHASE E — COMPLEXITY ANALYSIS (时空复杂度逐段细化分析) =====
        # =========================================================================
        time_box = VGroup(Text("时间复杂度：", font_size=24, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=24, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(1)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)

        complexity_panel = VGroup(time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(res_panel,
                                                                                                          DOWN,
                                                                                                          buff=0.6).align_to(
            res_panel, LEFT)

        with self.voiceover(
                text="平均情况下需要遍历一半的元素，最坏情况下需要遍历整个顺序表，因此时间复杂度为 O(n)。",
                subcaption="平均情况下需要遍历一半的元素，最坏情况下需要遍历整个顺序表，因此时间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
                text="执行过程中只使用了常数个辅助变量，没有额外开辟大规模空间，因此空间复杂度为常数级 O(壹)。",
                subcaption="执行过程中只使用了常数个辅助变量，没有额外开辟大规模空间，因此空间复杂度为常数级 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(
                text="这就是顺序表查找算法的完整演示过程。",
                subcaption="这就是顺序表查找算法的完整演示过程。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)