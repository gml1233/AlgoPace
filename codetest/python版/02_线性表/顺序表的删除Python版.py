# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class LinkedListBase(VoiceoverScene):
    """动画公共基类，提供高复用的基础组件配置"""
    pass


class ContinuousSeqListDeletePythonVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角全局图片 Logo（紧靠右上角且放大一倍，伴随顶部微调）
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("顺序表的删除（Python版）", font_size=38, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.5).shift(LEFT * 0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        # 总领句置于视频最开始
        with self.voiceover(
                text="本节我们来学习顺序表的删除算法 Python 版。该算法是删除顺序表中第i个数据元素，并使表长减1。",
                subcaption="本节我们来学习顺序表的删除算法 Python 版。该算法是删除顺序表中第i个数据元素，并使表长减1。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== PHASE B — VIVID ANALOGY (排队离队生活实例部分) =====
        # =========================================================================
        with self.voiceover(text="在学习算法前，我们先看一个生活实例：排队队伍中有人离队。") as tracker:
            # 创建 5 个排队的顾客方块（模拟顺序表中紧凑相邻的连续元素）
            people = VGroup(
                *[RoundedRectangle(corner_radius=0.1, width=1.0, height=1.0, color=BLUE, fill_color=BLUE, fill_opacity=0.2)
                  for _ in range(5)]
            ).arrange(RIGHT, buff=0.15).move_to(DOWN * 0.6 + LEFT * 0.5)

            p_labels = VGroup(
                *[Text(f"{idx + 1}号", font_size=18, font="Microsoft YaHei", color=WHITE) for idx in range(5)]
            )
            for person, lbl in zip(people, p_labels):
                lbl.move_to(person.get_center())

            pos_marks = VGroup(
                *[Text(f"位置{idx + 1}", font_size=15, font="Microsoft YaHei", color=ORANGE) for idx in range(5)]
            )
            for person, mark in zip(people, pos_marks):
                mark.next_to(person, UP, buff=0.15)

            queue_title = Text("紧凑排队队伍", font_size=18, font="Microsoft YaHei", color=BLUE_A).next_to(people, LEFT, buff=0.35)
            queue_group = VGroup(people, p_labels, pos_marks, queue_title)

            self.play(FadeIn(queue_group), run_time=tracker.duration)

        with self.voiceover(
                text="队伍中的成员紧密排列。现在第 3 个位置的顾客因故离开了队伍。",
                subcaption="队伍中的成员紧密排列。现在第 3 个位置的顾客因故离开了队伍。") as tracker:
            leaving_target = VGroup(people[2], p_labels[2])
            self.play(
                leaving_target.animate.set_color(RED).shift(UP * 1.2),
                run_time=0.8
            )
            self.play(FadeOut(leaving_target), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
                text="此时第 3 个位置出现了空缺。为了保持队伍连续无缝隙，排在后面的 4 号和 5 号顾客必须依次向前移动一个身位，填补空位。",
                subcaption="第 3 位出现空缺，后面的 4 号和 5 号顾客必须依次向前移动一个身位，填补空位。") as tracker:
            step_shift = LEFT * 1.15
            self.play(
                people[3].animate.shift(step_shift), p_labels[3].animate.shift(step_shift),
                run_time=0.7
            )
            self.play(
                people[4].animate.shift(step_shift), p_labels[4].animate.shift(step_shift),
                run_time=0.7
            )
            self.wait(max(0.1, tracker.duration - 1.4))

        with self.voiceover(
                text="平移完成后，空隙被彻底消除，队伍恢复紧凑整齐。这种为消除空缺将后续元素依次向前平移的机制，正是顺序表删除操作的核心逻辑。",
                subcaption="平移完成后空隙消除，队伍恢复紧凑。将后续元素依次前移消除空缺，正是顺序表删除操作的核心逻辑。") as tracker:
            self.wait(tracker.duration)

        # 快速清理生活实例
        self.play(
            FadeOut(queue_group), FadeOut(people[3]), FadeOut(people[4]), FadeOut(p_labels[3]), FadeOut(p_labels[4]),
            run_time=0.8
        )
        self.wait(0.3)

        # =========================================================================
        # ===== PHASE C — CODE BLOCK CONFIG (Python算法代码块排版部分) =====
        # =========================================================================
        c_lines = [
            "def list_delete(self, i):",
            "    if i < 1 or i > self.length:",
            "        raise Exception('位置不合法')",
            "    for idx in range(i, self.length):",
            "        self.elem[idx - 1] = self.elem[idx]",
            "    self.length -= 1",
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=11.5, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.20)

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

        code_block = VGroup(code_bg, code_group).to_edge(RIGHT, buff=0.35).shift(UP * 0.15)

        # ===== CODE HIGHLIGHT HELPER =====
        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line:
                return []

            anims = []
            if self.current_line is not None:
                old_idx = self.current_line
                anims.append(self.c_texts[old_idx].animate.set_color(WHITE).scale(1 / 1.15, about_edge=LEFT))

            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW).scale(1.15, about_edge=LEFT))

                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.13).rotate(-PI / 2)
                    self.code_pointer.next_to(self.c_texts[new_idx], LEFT, buff=0.18)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.c_texts[new_idx], LEFT, buff=0.18)
                    anims.append(MoveToTarget(self.code_pointer))

                self.current_line = new_idx
            else:
                if hasattr(self, 'code_pointer'):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, 'code_pointer')
                self.current_line = None

            return anims

        # ===== FUNCTIONS FOR SEQ LIST GUI =====
        def build_annotated_sequence(values, capacity=5):
            l_boxes = VGroup(*[Square(side_length=0.8, color=BLUE) for _ in range(capacity)]).arrange(RIGHT, buff=0)

            l_nums = VGroup()
            for idx in range(capacity):
                txt = Text(str(values[idx]), font_size=26, font="Arial")
                txt.move_to(l_boxes[idx].get_center())
                l_nums.add(txt)

            position_marks = VGroup(
                *[Text(str(index + 1), font_size=18, color=ORANGE, font="Arial") for index in range(capacity)])
            for box, mark in zip(l_boxes, position_marks):
                mark.next_to(box, UP, buff=0.12)

            index_marks = VGroup(
                *[Text(str(index), font_size=18, color=TEAL_A, font="Arial") for index in range(capacity)])
            for box, mark in zip(l_boxes, index_marks):
                mark.next_to(box, DOWN, buff=0.12)

            position_label = Text("位置", font_size=20, color=ORANGE, font="Microsoft YaHei").next_to(position_marks,
                                                                                                        LEFT, buff=0.25)
            l_label = Text("L", font_size=24, color=BLUE, font="Arial").next_to(l_boxes, LEFT, buff=0.25)
            index_label = Text("下标", font_size=20, color=TEAL_A, font="Microsoft YaHei").next_to(index_marks, LEFT,
                                                                                                     buff=0.25)

            array_group = VGroup(position_label, position_marks, l_label, l_boxes, l_nums, index_label, index_marks)
            return array_group, l_boxes, l_nums, position_marks, index_marks

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW (顺序表算法物理演练) =====
        # =========================================================================
        with self.voiceover(text="现在，我们学习该算法的代码实现。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        initial_values = [15, 28, 42, 56, 70]
        array_l, l_boxes, l_nums, position_marks, index_marks = build_annotated_sequence(initial_values, capacity=5)
        array_l.move_to(LEFT * 3.1 + UP * 0.6)

        with self.voiceover(text="假设我们有一个长度为 5 的顺序表 L，当前内部包含 5 个元素，如图所示。") as tracker:
            self.play(Create(array_l), run_time=tracker.duration)

        length_marker = VGroup(
            Text("表长：", font_size=22, font="Microsoft YaHei", color=WHITE),
            Text("self.length = 5", font_size=22, font="Consolas", color=WHITE)
        ).arrange(RIGHT, buff=0.1).next_to(array_l, UP, buff=0.6).align_to(array_l, LEFT)

        self.play(FadeIn(length_marker))
        self.wait(0.5)

        # ---------------- 步骤 1：删除位置合法性判断 ----------------
        with self.voiceover(
                text="第一步，检查要删除的位置i是否合法。i的有效范围必须在 1 到 self.length 之间。",
                subcaption="第一步，检查要删除的位置i是否合法。i的有效范围是 1 到 self.length。") as tracker:
            self.play(*get_track_anims(1), run_time=tracker.duration)

        with self.voiceover(
                text="也就是说，当前表长为 5 时，只能删除第 1 到第 5 个位置的元素。若 i 小于 1 或大于 5，程序将抛出位置不合法异常。",
                subcaption="当前表长为 5 时，合法范围是 1 到 5。若 i < 1 或 i > 5，程序将抛出位置不合法异常。") as tracker:
            self.wait(tracker.duration)

        # ---------------- 步骤 2：正常删除演示 (i = 3) ----------------
        delete_i = 3
        param_panel = VGroup(
            Text("参数：", font_size=22, font="Microsoft YaHei", color=YELLOW),
            Text(f"i = {delete_i}", font_size=24, color=YELLOW, font="Consolas")
        ).arrange(RIGHT, buff=0.12).next_to(code_block, DOWN, buff=0.3).align_to(code_block, LEFT)

        with self.voiceover(
                text=f"现在，假设我们要删除第 {delete_i} 个位置的元素。",
                subcaption=f"假设我们要删除第 {delete_i} 个位置的元素。") as tracker:
            self.play(*get_track_anims(0), FadeIn(param_panel), run_time=tracker.duration)

        # 目标删除单元高亮并移除元素
        del_box = l_boxes[delete_i - 1]
        del_num = l_nums[delete_i - 1]
        del_highlight = SurroundingRectangle(del_box, color=RED, buff=0.04, stroke_width=3)

        with self.voiceover(
                text=f"第 {delete_i} 个位置对应的下标为 i 减 1 即下标 2，元素值为 42。我们将其移出。",
                subcaption=f"第 {delete_i} 个位置对应下标 i - 1 即下标 2，值为 42。") as tracker:
            self.play(Create(del_highlight), del_box.animate.set_color(RED), run_time=0.6)
            self.play(
                del_num.animate.shift(UP * 1.0).set_opacity(0),
                run_time=0.8
            )
            self.wait(max(0.1, tracker.duration - 1.4))

        # ---------------- 步骤 3：for 循环元素前移 ----------------
        with self.voiceover(
                text="为了消除空位，算法进入 for 循环。在 Python 中，通过 range 函数从下标 i 开始，遍历到表长前一位。",
                subcaption="算法进入 for 循环。通过 range(i, self.length) 遍历需要前移的元素下标。") as tracker:
            self.play(*get_track_anims(3), run_time=tracker.duration)

        with self.voiceover(
                text="当前 i 等于 3，self.length 为 5，因此 idx 依次遍历下标 3 和下标 4。",
                subcaption="当前 i = 3，self.length = 5，因此 idx 依次遍历下标 3 和下标 4。") as tracker:
            self.wait(tracker.duration)

        def create_idx_pointer(box_idx):
            arrow = Arrow(DOWN, UP, buff=0.05, tip_length=0.15).scale(0.3).next_to(index_marks[box_idx], DOWN, buff=0.05)
            arrow.set_color(YELLOW)
            lbl = Text(f"idx={box_idx}", font_size=16, color=YELLOW, font="Consolas").next_to(arrow, DOWN, buff=0.05)
            return VGroup(arrow, lbl)

        # idx = 3: elem[2] = elem[3] (48 前移)
        idx_ptr_3 = create_idx_pointer(3)
        with self.voiceover(
                text="首先 idx 等于 3，执行循环体：将下标 3 的元素 48 前移到下标 2 的位置。",
                subcaption="首先 idx = 3，执行 self.elem[idx - 1] = self.elem[idx]，将元素 48 前移到下标 2。") as tracker:
            self.play(*get_track_anims(4), FadeIn(idx_ptr_3), run_time=0.5)
            self.play(
                l_nums[3].animate.move_to(l_boxes[2].get_center()),
                del_box.animate.set_color(BLUE),
                FadeOut(del_highlight),
                run_time=0.8
            )
            l_nums[2] = l_nums[3]
            self.wait(max(0.1, tracker.duration - 1.3))

        # idx = 4: elem[3] = elem[4] (70 前移)
        idx_ptr_4 = create_idx_pointer(4)
        with self.voiceover(
                text="接着 idx 变为 4，将下标 4 的元素 70 前移到下标 3 的位置。",
                subcaption="接着 idx = 4，执行 self.elem[3] = self.elem[4]，将元素 70 前移到下标 3。") as tracker:
            self.play(*get_track_anims(3), ReplacementTransform(idx_ptr_3, idx_ptr_4), run_time=0.5)
            self.play(*get_track_anims(4), run_time=0.3)
            self.play(
                l_nums[4].animate.move_to(l_boxes[3].get_center()),
                run_time=0.8
            )
            l_nums[3] = l_nums[4]
            self.wait(max(0.1, tracker.duration - 1.6))

        # 循环结束
        with self.voiceover(
                text="for 循环执行完毕。所有后续元素均已成功向前平移了一格。",
                subcaption="for 循环执行完毕。所有后续元素均已成功向前平移了一格。") as tracker:
            empty_tail = Text("", font_size=26, font="Arial").move_to(l_boxes[4].get_center())
            l_nums[4] = empty_tail
            self.play(
                FadeOut(idx_ptr_4),
                l_boxes[4].animate.set_color(GRAY).set_stroke(opacity=0.5),
                run_time=0.8
            )
            self.wait(max(0.1, tracker.duration - 0.8))

        # ---------------- 步骤 4：表长减 1 ----------------
        new_length_marker = VGroup(
            Text("表长：", font_size=22, font="Microsoft YaHei", color=WHITE),
            Text("self.length = 4", font_size=22, font="Consolas", color=GREEN)
        ).arrange(RIGHT, buff=0.1).move_to(length_marker.get_center()).align_to(length_marker, LEFT)

        with self.voiceover(
                text="最后执行表长减 1，self.length 更新为 4。删除操作顺利完成！",
                subcaption="最后执行 self.length -= 1，表长更新为 4。删除操作顺利完成！") as tracker:
            self.play(*get_track_anims(5), Transform(length_marker, new_length_marker), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        self.play(*get_track_anims(None), FadeOut(param_panel), run_time=0.5)

        # =========================================================================
        # ===== PHASE E — COMPLEXITY ANALYSIS (时空复杂度分析) =====
        # =========================================================================
        time_row = VGroup(
            Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
            Text("O(n)", font_size=26, font="Arial", color=YELLOW)
        ).arrange(RIGHT, buff=0.1)

        time_best = Text("最好情况：删除表尾元素 (i=n)，移动 0 次，O(1)", font_size=15, font="Microsoft YaHei", color=GRAY_A)
        time_worst = Text("最坏情况：删除表头元素 (i=1)，移动 n-1 次，O(n)", font_size=15, font="Microsoft YaHei", color=GRAY_A)
        time_avg = Text("平均情况：各个位置等概率，平均移动 (n-1)/2 次，O(n)", font_size=15, font="Microsoft YaHei", color=GRAY_A)

        time_group = VGroup(time_row, time_best, time_worst, time_avg).arrange(DOWN, aligned_edge=LEFT, buff=0.12)

        space_row = VGroup(
            Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
            Text("O(1)", font_size=26, font="Arial", color=YELLOW)
        ).arrange(RIGHT, buff=0.1)
        space_note = Text("仅占用常数个辅助存储单元", font_size=15, font="Microsoft YaHei", color=GRAY_A)
        space_group = VGroup(space_row, space_note).arrange(DOWN, aligned_edge=LEFT, buff=0.12)

        complexity_panel = VGroup(time_group, space_group).arrange(RIGHT, aligned_edge=UP, buff=0.7).move_to(
            LEFT * 2.8 + DOWN * 1.6
        )

        with self.voiceover(
                text="最后分析时间和空间复杂度。删除操作的时间主要耗费在循环前移元素上。",
                subcaption="最后分析时间和空间复杂度。删除操作的时间主要耗费在循环前移元素上。") as tracker:
            self.play(FadeIn(time_row), run_time=tracker.duration)

        with self.voiceover(
                text="最好情况下删除表尾元素，无需移动元素，时间复杂度为 O 一。",
                subcaption="最好情况下删除表尾元素 (i=n)，移动 0 次，时间复杂度为 O(1)。") as tracker:
            self.play(FadeIn(time_best), run_time=tracker.duration)

        with self.voiceover(
                text="最坏情况下删除表头元素，需要前移全部 n 减 1 个元素，时间复杂度为 O n。",
                subcaption="最坏情况下删除表头元素 (i=1)，需要前移全部 n-1 个元素，时间复杂度为 O(n)。") as tracker:
            self.play(FadeIn(time_worst), run_time=tracker.duration)

        with self.voiceover(
                text="在每个位置删除概率均等时，平均需要移动一半的元素，因此平均时间复杂度为 O n。",
                subcaption="各个位置删除概率均等时，平均移动 (n-1)/2 次，因此平均时间复杂度为 O(n)。") as tracker:
            self.play(FadeIn(time_avg), run_time=tracker.duration)

        with self.voiceover(
                text="空间上，算法仅使用常数个辅助变量，空间复杂度为 O 一。",
                subcaption="算法仅使用常数个辅助变量，辅助空间复杂度为 O(1)。") as tracker:
            self.play(FadeIn(space_group), run_time=tracker.duration)

        with self.voiceover(
                text="这就是顺序表删除算法 Python 版的完整演示过程。",
                subcaption="这就是顺序表删除算法 Python 版的完整演示过程。") as tracker:
            self.play(Indicate(complexity_panel, color=BLUE_B, scale_factor=1.03), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))

        self.wait(2)


# Alias
SeqListDeletePythonVideo = ContinuousSeqListDeletePythonVideo
