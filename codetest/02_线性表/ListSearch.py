from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


def build_annotated_sequence(values):
    l_boxes = VGroup(*[Square(side_length=0.8, color=BLUE) for _ in range(len(values))]).arrange(RIGHT, buff=0)
    l_nums = VGroup(*[Text(str(val), font_size=28) for val in values])
    for box, num in zip(l_boxes, l_nums):
        num.move_to(box.get_center())

    position_marks = VGroup(*[Text(str(index + 1), font_size=18, color=ORANGE) for index in range(len(values))])
    for box, mark in zip(l_boxes, position_marks):
        mark.next_to(box, UP, buff=0.12)

    index_marks = VGroup(*[Text(str(index), font_size=18, color=TEAL_A) for index in range(len(values))])
    for box, mark in zip(l_boxes, index_marks):
        mark.next_to(box, DOWN, buff=0.12)

    position_label = Text("位置", font_size=20, color=ORANGE).next_to(position_marks, LEFT, buff=0.3)
    l_label = Text("L", font_size=24, color=BLUE).next_to(l_boxes, LEFT, buff=0.3)
    index_label = Text("下标", font_size=20, color=TEAL_A).next_to(index_marks, LEFT, buff=0.3)

    array_group = VGroup(position_label, position_marks, l_label, l_boxes, l_nums, index_label, index_marks)
    return array_group, l_boxes, position_marks


def build_i_pointer(anchor_mark):
    i_arrow = Arrow(UP, DOWN, buff=0.05, tip_length=0.15).scale(0.3).next_to(anchor_mark, UP, buff=0.02)
    i_arrow.set_color(RED)
    i_text = Text("i", font_size=18, color=RED).next_to(i_arrow, UP, buff=0.02)
    return VGroup(i_arrow, i_text)


def build_search_code_block(font_size=18):
    code_l1 = Text("for (int i = 0; i < L.length; i++)", font_size=font_size, color=WHITE)
    code_l2 = Text("    if (L.elem[i] == e) return i + 1;", font_size=font_size, color=WHITE)
    code_l3 = Text("return 0;", font_size=font_size, color=WHITE)
    code_group = VGroup(code_l1, code_l2, code_l3).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    code_bg = SurroundingRectangle(code_group, color=GRAY, buff=0.2, fill_opacity=0.1)
    code_block = VGroup(code_bg, code_group).to_corner(UR).shift(DOWN * 0.1 + LEFT * 0.1)
    return code_block, (code_l1, code_l2, code_l3)


# ---------------------- 场景1：初始化与输入展示 ----------------------
class SceneInitialization(VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        title = Text("顺序表的查找", font_size=40, color=WHITE).to_edge(UP)
        with self.voiceover(text="本节演示顺序表的查找算法。") as tracker:
            self.play(Write(title), run_time=tracker.duration)
        self.wait(0.5)

        L_values = [3, 7, 1, 9, 5]
        e_value = 7

        array_l, l_boxes, position_marks = build_annotated_sequence(L_values)
        array_l.move_to(UP * 1.5)

        with self.voiceover(text="我们有一个顺序表L，包含元素3,7,1,9,5。") as tracker:
            self.play(Create(array_l), run_time=tracker.duration)
        self.wait(1)

        e_display = Text(f"待查找值 e = {e_value}", font_size=32, color=YELLOW).next_to(array_l, DOWN, buff=1.0)
        with self.voiceover(text=f"我们要查找值为{e_value}的元素。") as tracker:
            self.play(Write(e_display), run_time=tracker.duration)
        self.wait(1)

        i_ptr = build_i_pointer(position_marks[0])

        with self.voiceover(text="初始化指针 i，指向顺序表的第一个元素。") as tracker:
            self.play(Create(i_ptr), run_time=tracker.duration)
        self.wait(2)

        length_marker = Text(f"长度 = {len(L_values)}", font_size=20, color=WHITE).next_to(array_l, RIGHT, buff=1)
        self.play(Write(length_marker))
        self.wait(1)


# ---------------------- 场景2：逐个比较 ----------------------
class SceneTraversal(VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        L_values = [3, 7, 1, 9, 5]
        e_value = 7

        array_l, l_boxes, position_marks = build_annotated_sequence(L_values)
        array_l.move_to(UP * 1.5)

        i_ptr = build_i_pointer(position_marks[0])

        e_display = Text(f"待查找值 e = {e_value}", font_size=32, color=YELLOW).next_to(array_l, DOWN, buff=1.0)

        title = Text("逐个比较过程", font_size=40, color=WHITE).to_edge(UP)
        code_block, (code_l1, code_l2, code_l3) = build_search_code_block()
        self.play(Write(title), FadeIn(array_l, e_display, i_ptr), FadeIn(code_block))
        self.wait(0.5)

        current_box = l_boxes[0]
        compare_highlight = SurroundingRectangle(current_box, color=YELLOW, buff=0.05)
        with self.voiceover(text="首先比较第一个元素3与7。") as tracker:
            self.play(code_l1.animate.set_color(YELLOW), Create(compare_highlight), run_time=tracker.duration)
        self.wait(0.5)

        with self.voiceover(text="3不等于7，查找未命中。") as tracker:
            self.play(code_l2.animate.set_color(YELLOW), current_box.animate.set_fill(RED, opacity=0.3), run_time=0.3)
            self.play(current_box.animate.set_fill(BLUE, opacity=0.2), code_l2.animate.set_color(WHITE), run_time=0.3)
        self.play(FadeOut(compare_highlight))

        with self.voiceover(text="指针i向右移动到下一个元素。") as tracker:
            self.play(i_ptr.animate.next_to(position_marks[1], UP, buff=0.02), run_time=tracker.duration)
        self.wait(0.5)

        second_compare = SurroundingRectangle(l_boxes[1], color=YELLOW, buff=0.05)
        with self.voiceover(text="接下来比较第二个元素7与7。") as tracker:
            self.play(Create(second_compare), code_l2.animate.set_color(YELLOW), run_time=tracker.duration)
        self.wait(0.5)
        with self.voiceover(text="我们发现二者相等，查找成功。") as tracker:
            self.wait(tracker.duration)


# ---------------------- 场景3：查找成功（本次唯一修改处） ----------------------
class SceneSuccess(VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        L_values = [3, 7, 1, 9, 5]
        e_value = 7
        array_l, l_boxes, position_marks = build_annotated_sequence(L_values)
        array_l.move_to(UP * 1.5)

        i_ptr_group = build_i_pointer(position_marks[1])

        e_display = Text(f"待查找值 e = {e_value}", font_size=32, color=YELLOW).next_to(array_l, DOWN, buff=0.9)

        title = Text("查找成功", font_size=40, color=WHITE).to_edge(UP)
        code_block, (code_l1, code_l2, code_l3) = build_search_code_block()
        code_l1.set_color(YELLOW)
        code_l2.set_color(YELLOW)
        self.play(Write(title), FadeIn(array_l, e_display, i_ptr_group), FadeIn(code_block))
        self.wait(0.5)

        match_box = l_boxes[1]
        match_highlight = SurroundingRectangle(match_box, color=GREEN, buff=0.05)
        with self.voiceover(text="发现L[1]等于7，查找成功！") as tracker:
            self.play(Create(match_highlight), match_box.animate.set_fill(GREEN, opacity=0.4),
                      run_time=tracker.duration)
        self.wait(0.5)

        result_text = Text("返回序号 2", font_size=36, color=GREEN).next_to(e_display, DOWN, buff=0.7)
        with self.voiceover(text="根据算法，返回该元素的序号，即下标加一，结果为2。") as tracker:
            self.play(Write(result_text), run_time=tracker.duration)
        result_text.shift(UP * 0.25)

        self.wait(1.5)

        # ========== 关键修改：上移底部文字，buff从0.6→0.4，彻底避开字幕 ==========
        fail_note = Text("若查找值不在表中（例如 e=8），则遍历结束返回0",
                         font_size=22, color=WHITE).next_to(result_text, DOWN, buff=0.45)
        fail_note.shift(UP * 0.2)
        with self.voiceover(text="如果要查找的值不在顺序表中，例如查找8，则遍历所有元素后返回0。") as tracker:
            self.play(Write(fail_note), code_l2.animate.set_color(WHITE), code_l3.animate.set_color(YELLOW),
                      run_time=tracker.duration)
        self.wait(2)


# ---------------------- 场景4：复杂度分析 ----------------------
class SceneComplexity(VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        title = Text("复杂度分析", font_size=40, color=WHITE).to_edge(UP)
        with self.voiceover(text="最后，我们对顺序表的查找算法进行复杂度分析。") as tracker:
            self.play(Write(title), run_time=tracker.duration)

        time_main = Text("时间复杂度：O(n)", color=YELLOW, font_size=36).move_to(UP * 0.5)
        time_explain = Text("平均查找长度(n+1)/2，最坏情况需比较n次",
                            font_size=26, color=WHITE).next_to(time_main, DOWN, buff=0.6)

        with self.voiceover(text="查找的时间复杂度为O(n)，因为最坏情况下需要遍历整个顺序表。") as tracker:
            self.play(Write(time_main), Write(time_explain), run_time=tracker.duration)
        self.wait(1)

        space_main = Text("空间复杂度：O(1)", color=BLUE, font_size=36).move_to(DOWN * 1.0)
        space_explain = Text("仅使用常数个辅助变量，不需额外数组存储空间",
                             font_size=26, color=WHITE).next_to(space_main, DOWN, buff=0.6)

        with self.voiceover(text="空间复杂度为O(1)，算法只用了固定的几个指针变量，没有额外的存储开销。") as tracker:
            self.play(Write(space_main), Write(space_explain), run_time=tracker.duration)

        self.wait(3)
