# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class LinkedListBase(VoiceoverScene):
    """动画公共基类，提供高复用的基础组件配置"""
    pass


class ContinuousSeqListGetPythonVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角全局图片 Logo（紧靠右上角且放大一倍，伴随顶部微调）
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("顺序表的取值（Python版）", font_size=38, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.5).shift(LEFT * 0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        # 总领句置于视频最开始
        with self.voiceover(
                text="本节我们来学习顺序表的取值 Python 版。该算法是根据指定的位置序号i，获取顺序表中第i个数据元素的值。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== NEW PHASE — VIVID ANALOGY (电影院座位生活实例部分) =====
        # =========================================================================
        with self.voiceover(text="为了更好地理解顺序表的取值，我们来看一个生活中的例子：根据电影票寻找座位。") as tracker:
            # 创建一排连续的电影院座位（模拟顺序表的连续存储空间）
            seats = VGroup(
                *[Square(side_length=0.9, color=BLUE, fill_color=BLUE, fill_opacity=0.1) for _ in range(5)]).arrange(
                RIGHT, buff=0.1)
            seats.move_to(DOWN * 0.5)

            seat_marks = VGroup(
                *[Text(f"{idx + 1}号", font_size=18, color=ORANGE, font="Microsoft YaHei") for idx in range(5)])
            for seat, mark in zip(seats, seat_marks):
                mark.next_to(seat, UP, buff=0.15)

            cinema_row = VGroup(seats, seat_marks)
            self.play(FadeIn(cinema_row), run_time=tracker.duration)

        with self.voiceover(
                text="在电影院里，所有的座位都是依次排列、固定编号的。这就像顺序表在内存中连续分布的存储单元。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="现在，假设你的电影票上写着：三号座位。") as tracker:
            # 创建电影票票据凭证
            ticket_box = RoundedRectangle(corner_radius=0.1, width=3.2, height=1.2, color=YELLOW, fill_color=YELLOW,
                                          fill_opacity=0.15)
            ticket_box.move_to(UP * 1.5 + LEFT * 3)

            ticket_title = Text("电影票", font_size=16, color=YELLOW, font="Microsoft YaHei", weight=BOLD).next_to(
                ticket_box.get_top(), DOWN, buff=0.15)
            ticket_content = Text("座位号: 03", font_size=18, color=WHITE, font="Microsoft YaHei").next_to(ticket_title,
                                                                                                           DOWN,
                                                                                                           buff=0.1)
            ticket = VGroup(ticket_box, ticket_title, ticket_content)

            self.play(FadeIn(ticket, shift=RIGHT * 0.3), run_time=tracker.duration)

        with self.voiceover(text="你不需要从一号座位开始，挨个去问每一个人：请问这是我的座位吗？") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="而是可以直接根据票上的编号“三”，一眼锁定目标位置，直接走过去坐下。") as tracker:
            target_highlight_anlg = SurroundingRectangle(seats[2], color=YELLOW, buff=0.05, stroke_width=4)

            ptr_arrow_anlg = Arrow(UP, DOWN, buff=0.05, tip_length=0.15).scale(0.4).next_to(seat_marks[2], UP, buff=0.1)
            ptr_arrow_anlg.set_color(YELLOW)

            self.play(
                Create(target_highlight_anlg),
                GrowArrow(ptr_arrow_anlg),
                seats[2].animate.set_fill(YELLOW, opacity=0.4),
                run_time=tracker.duration
            )

        with self.voiceover(
                text="这种能够根据编号直接、精准定位到对应单元的特性，就是顺序表的随机存取。因此它的取值操作非常高效，时间复杂度仅为常数级 O(1)。",
                subcaption="这种能够根据编号直接、精准定位到对应单元的特性，就是顺序表的随机存取。因此它的取值操作非常高效，时间复杂度仅为常数级 O(1)。"
        ) as tracker:
            self.wait(tracker.duration)

        # 清理生活实例
        self.play(FadeOut(cinema_row), FadeOut(ticket), FadeOut(target_highlight_anlg), FadeOut(ptr_arrow_anlg),
                  run_time=1.0)
        self.wait(0.5)

        # =========================================================================
        # ===== PHASE C — CODE BLOCK CONFIG (Python算法代码块排版部分) =====
        # =========================================================================
        c_lines = [
            "def get_elem(self, i):",
            "    if 1 <= i <= self.length:",
            "        return self.elem[i - 1]",
            "    raise Exception('位置不合法')",
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=12, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.22)

        SPACE_WIDTH = 0.095
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

        code_block = VGroup(code_bg, code_group).to_edge(RIGHT, buff=0.35).shift(UP * 0.2)

        # ===== CODE HIGHLIGHT HELPER =====
        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line:
                return []

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
            return array_group, l_boxes, position_marks

        def build_i_pointer(anchor_mark, label_text="i"):
            i_arrow = Arrow(UP, DOWN, buff=0.05, tip_length=0.15).scale(0.3).next_to(anchor_mark, UP, buff=0.02)
            i_arrow.set_color(RED)
            i_text = Text(label_text, font_size=18, color=RED, font="Arial").next_to(i_arrow, UP, buff=0.02)
            return VGroup(i_arrow, i_text)

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW (顺序表算法物理演练) =====
        # =========================================================================
        with self.voiceover(text="现在，我们学习该算法的代码实现。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        L_values = [3, 7, 1, 9, 5]
        array_l, l_boxes, position_marks = build_annotated_sequence(L_values)
        array_l.move_to(LEFT * 3.0 + UP * 0.5)

        with self.voiceover(text="假设我们有一个长度为5的顺序表L，内部元素如图所示。") as tracker:
            self.play(Create(array_l), run_time=tracker.duration)

        length_marker = VGroup(
            Text("表长：", font_size=22, font="Microsoft YaHei", color=WHITE),
            Text("self.length = 5", font_size=22, font="Consolas", color=WHITE)
        ).arrange(RIGHT, buff=0.1).next_to(array_l, UP, buff=0.6).align_to(array_l, LEFT)

        self.play(FadeIn(length_marker))
        self.wait(0.5)

        # ---------------- 场景演练 1：越界判断演示 ----------------
        i_val_err = 6
        param_panel_err = VGroup(
            Text("目标位置：", font_size=24, font="Microsoft YaHei", color=RED),
            Text(f"i = {i_val_err}", font_size=26, color=RED, font="Consolas")
        ).arrange(RIGHT, buff=0.15).next_to(code_block, DOWN, buff=0.2).align_to(code_block, LEFT)

        with self.voiceover(text=f"我们来看一种异常情况：假设尝试获取位置i等于 {i_val_err} 的元素。") as tracker:
            self.play(*get_track_anims(0), FadeIn(param_panel_err), run_time=tracker.duration)

        with self.voiceover(text="算法进入第一步，判断指定的位置i是否合法。位置i必须在 1 到表长之间。") as tracker:
            self.play(*get_track_anims(1), run_time=tracker.duration)

        with self.voiceover(
                text=f"由于当前的i等于 {i_val_err}，超过了表长 5，条件不满足，程序将抛出异常，提示位置不合法。") as tracker:
            self.play(*get_track_anims(3), run_time=0.4)
            flash_rect = SurroundingRectangle(code_bg, color=RED, buff=0.05)
            self.play(Create(flash_rect), run_time=0.5)
            self.play(FadeOut(flash_rect), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 1.4))

        self.play(*get_track_anims(None), FadeOut(param_panel_err), run_time=0.5)

        # ---------------- 场景演练 2：正常取值演示 ----------------
        i_val_ok = 3
        param_panel_ok = VGroup(
            Text("参数：", font_size=24, font="Microsoft YaHei", color=YELLOW),
            Text(f"i = {i_val_ok}", font_size=26, color=YELLOW, font="Consolas")
        ).arrange(RIGHT, buff=0.15).next_to(code_block, DOWN, buff=0.2).align_to(code_block, LEFT)

        with self.voiceover(
                text=f"接下来，我们看正常的取值流程：假设我们要获取位置i等于 {i_val_ok} 的元素。") as tracker:
            self.play(*get_track_anims(0), FadeIn(param_panel_ok), run_time=tracker.duration)

        with self.voiceover(text="再次进行边界检查。此时i等于 3，在合法的范围内，条件判断顺利通过。") as tracker:
            self.play(*get_track_anims(1), run_time=0.4)
            self.play(self.c_texts[1].animate.set_color(GREEN), run_time=max(0.2, tracker.duration - 0.4))
        self.wait(0.2)

        i_ptr = build_i_pointer(position_marks[i_val_ok - 1], label_text=f"i={i_val_ok}")
        with self.voiceover(
                text="接着执行核心取值代码。由于 Python 列表下标是从0开始计数的，所以位置为i的元素，对应下标为i减1。") as tracker:
            self.play(*get_track_anims(2), Create(i_ptr), run_time=tracker.duration)

        target_box = l_boxes[i_val_ok - 1]
        target_highlight = SurroundingRectangle(target_box, color=YELLOW, buff=0.04, stroke_width=3)
        target_val = L_values[i_val_ok - 1]
        spoken_target_val = "壹" if target_val == 1 else str(target_val)

        with self.voiceover(
                text=f"通过下标直接定位。我们成功找到了位置为 3、对应下标为 2 的数组元素，它的值为 {spoken_target_val}。",
                subcaption=f"通过下标直接定位。我们成功找到了位置为 3、对应下标为 2 的数组元素，它的值为 {target_val}。") as tracker:
            self.play(Create(target_highlight), target_box.animate.set_fill(YELLOW, opacity=0.3),
                      run_time=tracker.duration)

        res_panel = VGroup(
            Text("取值结果：", font_size=24, font="Microsoft YaHei", color=GREEN),
            Text(f"返回 {target_val}", font_size=24, font="Microsoft YaHei", color=GREEN)
        ).arrange(RIGHT, buff=0.15).move_to(LEFT * 3.0 + DOWN * 1.5)

        with self.voiceover(
                text=f"取值成功，直接返回该元素的值 {spoken_target_val}，操作顺利结束。",
                subcaption=f"取值成功，直接返回该元素的值 {target_val}，操作顺利结束。") as tracker:
            self.play(Write(res_panel), self.c_texts[2].animate.set_color(GREEN), run_time=tracker.duration)

        self.play(*get_track_anims(None), FadeOut(target_highlight), FadeOut(i_ptr), FadeOut(param_panel_ok), run_time=0.5)

        # =========================================================================
        # ===== PHASE E — COMPLEXITY ANALYSIS (时空复杂度分析) =====
        # =========================================================================
        time_box = VGroup(Text("时间复杂度：", font_size=24, font="Microsoft YaHei", color=YELLOW),
                          Text("O(1)", font_size=26, font="Consolas", color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=24, font="Microsoft YaHei", color=YELLOW),
                           Text("O(1)", font_size=26, font="Consolas", color=YELLOW)).arrange(RIGHT, buff=0.1)

        complexity_panel = VGroup(time_box, space_box).arrange(RIGHT, aligned_edge=UP, buff=0.7).next_to(res_panel,
                                                                                                          DOWN,
                                                                                                          buff=0.35).align_to(
            res_panel, LEFT)

        with self.voiceover(
                text="最后分析时间和空间。取值快在哪儿？快在能按下标直接定位，不用从第一个元素开始找。",
                subcaption="最后分析时间和空间。取值快在哪儿？快在能按下标直接定位，不用从第一个元素开始找。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
                text="无论顺序表有多长，取一次元素都只是一次地址计算和一次访问，所以时间复杂度是 O 一。",
                subcaption="无论顺序表有多长，取一次元素都只是一次地址计算和一次访问，所以时间复杂度是 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(
                text="空间上，也没有开辟新的表，只使用少量辅助变量，空间复杂度同样是 O 一。",
                subcaption="空间上，也没有开辟新的表，只使用少量辅助变量，空间复杂度同样是 O(1)。"
        ) as tracker:
            self.wait(tracker.duration)

        with self.voiceover(
                text="这就是顺序表取值算法的完整演示过程。",
                subcaption="这就是顺序表取值算法的完整演示过程。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)


# Alias
SeqListGetPythonVideo = ContinuousSeqListGetPythonVideo
