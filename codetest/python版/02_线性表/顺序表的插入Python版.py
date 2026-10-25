# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class LinkedListBase(VoiceoverScene):
    """动画公共基类，提供高复用的基础组件配置"""
    pass


class ContinuousSeqListInsertPythonVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角全局图片 Logo（紧靠右上角且放大一倍，伴随顶部微调）
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("顺序表的插入（Python版）", font_size=38, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.5).shift(LEFT * 0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        # 总领句置于视频最开始
        with self.voiceover(
                text="本节我们来学习顺序表的插入算法 Python 版。该算法是在顺序表的第i个位置插入新的元素e，并使表长加1。",
                subcaption="本节我们来学习顺序表的插入算法 Python 版。该算法是在顺序表的第i个位置插入新的元素e，并使表长加1。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== PHASE B — VIVID ANALOGY (排队加人生活实例部分) =====
        # =========================================================================
        with self.voiceover(text="在学习算法前，我们先看一个生活实例：排队队伍中插入一位新成员。") as tracker:
            # 创建 4 个排队的顾客方块（模拟顺序表中紧凑相邻的连续元素）
            people = VGroup(
                *[RoundedRectangle(corner_radius=0.1, width=1.1, height=1.1, color=BLUE, fill_color=BLUE, fill_opacity=0.2)
                  for _ in range(4)]
            ).arrange(RIGHT, buff=0.15).move_to(DOWN * 0.6 + LEFT * 0.5)

            p_labels = VGroup(
                *[Text(f"{idx + 1}号", font_size=20, font="Microsoft YaHei", color=WHITE) for idx in range(4)]
            )
            for person, lbl in zip(people, p_labels):
                lbl.move_to(person.get_center())

            pos_marks = VGroup(
                *[Text(f"位置{idx + 1}", font_size=16, font="Microsoft YaHei", color=ORANGE) for idx in range(4)]
            )
            for person, mark in zip(people, pos_marks):
                mark.next_to(person, UP, buff=0.15)

            queue_title = Text("紧凑排队队伍", font_size=20, font="Microsoft YaHei", color=BLUE_A).next_to(people, LEFT, buff=0.4)
            queue_group = VGroup(people, p_labels, pos_marks, queue_title)

            # 新成员卡片
            new_person = RoundedRectangle(corner_radius=0.1, width=1.1, height=1.1, color=GREEN, fill_color=GREEN, fill_opacity=0.35)
            new_p_lbl = Text("新成员", font_size=18, font="Microsoft YaHei", color=GREEN_A).move_to(new_person.get_center())
            new_member_group = VGroup(new_person, new_p_lbl).move_to(UP * 1.5 + LEFT * 0.5)

            self.play(FadeIn(queue_group), FadeIn(new_member_group, shift=DOWN * 0.3), run_time=tracker.duration)

        with self.voiceover(
                text="队伍中的成员紧密相邻。现在新成员需要插入到第 2 个位置。",
                subcaption="队伍中的成员紧密相邻。现在新成员需要插入到第 2 个位置。") as tracker:
            pos2_highlight = SurroundingRectangle(people[1], color=YELLOW, buff=0.08, stroke_width=3)
            self.play(Create(pos2_highlight), run_time=tracker.duration)

        with self.voiceover(
                text="为了腾出第 2 个位置，排在第 2 位及之后的所有人，都必须从后向前、依次向后退一个身位。",
                subcaption="为了腾出第 2 个位置，排在第 2 位及之后的所有人，都必须从后向前、依次向后退一个身位。") as tracker:
            step_shift = RIGHT * 1.25
            self.play(
                people[3].animate.shift(step_shift), p_labels[3].animate.shift(step_shift),
                run_time=0.6
            )
            self.play(
                people[2].animate.shift(step_shift), p_labels[2].animate.shift(step_shift),
                run_time=0.6
            )
            self.play(
                people[1].animate.shift(step_shift), p_labels[1].animate.shift(step_shift),
                FadeOut(pos2_highlight),
                run_time=0.6
            )
            self.wait(max(0.1, tracker.duration - 1.8))

        with self.voiceover(
                text="空位腾出后，新成员才能顺利插入进去。",
                subcaption="空位腾出后，新成员才能顺利插入进去。") as tracker:
            target_pos = people[0].get_center() + RIGHT * 1.25
            self.play(new_member_group.animate.move_to(target_pos), run_time=tracker.duration)

        with self.voiceover(
                text="这种在连续存储中，为腾出空位必须将后续元素依次后移的机制，就是顺序表插入的核心逻辑。接下来我们看代码实现。",
                subcaption="这种在连续存储中，为腾出空位必须将后续元素依次后移的机制，就是顺序表插入的核心逻辑。接下来我们看代码实现。") as tracker:
            self.wait(tracker.duration)

        # 快速清理生活实例
        self.play(
            FadeOut(queue_group), FadeOut(new_member_group),
            run_time=0.8
        )
        self.wait(0.3)

        # =========================================================================
        # ===== PHASE C — CODE BLOCK CONFIG (Python算法代码块排版部分) =====
        # =========================================================================
        c_lines = [
            "def list_insert(self, i, e):",
            "    if self.length == max_size:",
            "        raise Exception('空间已满')",
            "    if i < 1 or i > self.length + 1:",
            "        raise Exception('位置不合法')",
            "    for idx in range(self.length - 1, i - 2, -1):",
            "        self.elem[idx + 1] = self.elem[idx]",
            "    self.elem[i - 1] = e",
            "    self.length += 1",
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=11, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.17)

        SPACE_WIDTH = 0.095
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        buff_val = 0.22
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

        code_block = VGroup(code_bg, code_group).to_edge(RIGHT, buff=0.35).shift(UP * 0.1)

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
        def build_annotated_sequence(values, capacity=6):
            l_boxes = VGroup()
            for idx in range(capacity):
                if idx < len(values):
                    sq = Square(side_length=0.75, color=BLUE)
                else:
                    sq = Square(side_length=0.75, color=GRAY, stroke_opacity=0.6)
                l_boxes.add(sq)
            l_boxes.arrange(RIGHT, buff=0)

            l_nums = VGroup()
            for idx in range(capacity):
                if idx < len(values):
                    txt = Text(str(values[idx]), font_size=24, font="Arial")
                else:
                    txt = Text("", font_size=24, font="Arial")
                txt.move_to(l_boxes[idx].get_center())
                l_nums.add(txt)

            position_marks = VGroup(
                *[Text(str(index + 1), font_size=16, color=ORANGE, font="Arial") for index in range(capacity)])
            for box, mark in zip(l_boxes, position_marks):
                mark.next_to(box, UP, buff=0.1)

            index_marks = VGroup(
                *[Text(str(index), font_size=16, color=TEAL_A, font="Arial") for index in range(capacity)])
            for box, mark in zip(l_boxes, index_marks):
                mark.next_to(box, DOWN, buff=0.1)

            position_label = Text("位置", font_size=18, color=ORANGE, font="Microsoft YaHei").next_to(position_marks,
                                                                                                        LEFT, buff=0.25)
            l_label = Text("L", font_size=22, color=BLUE, font="Arial").next_to(l_boxes, LEFT, buff=0.25)
            index_label = Text("下标", font_size=18, color=TEAL_A, font="Microsoft YaHei").next_to(index_marks, LEFT,
                                                                                                     buff=0.25)

            array_group = VGroup(position_label, position_marks, l_label, l_boxes, l_nums, index_label, index_marks)
            return array_group, l_boxes, l_nums, position_marks, index_marks

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW (顺序表算法物理演练) =====
        # =========================================================================
        with self.voiceover(text="现在，我们学习该算法的代码实现。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        initial_values = [12, 25, 36, 48, 60]
        array_l, l_boxes, l_nums, position_marks, index_marks = build_annotated_sequence(initial_values, capacity=6)
        array_l.move_to(LEFT * 3.1 + UP * 0.6)

        with self.voiceover(text="假设我们有一个长度为 5 的顺序表 L，当前内部包含 5 个元素，如图所示。") as tracker:
            self.play(Create(array_l), run_time=tracker.duration)

        length_marker = VGroup(
            Text("表长：", font_size=20, font="Microsoft YaHei", color=WHITE),
            Text("self.length = 5", font_size=20, font="Consolas", color=WHITE)
        ).arrange(RIGHT, buff=0.1).next_to(array_l, UP, buff=0.5).align_to(array_l, LEFT)

        capacity_info = VGroup(
            Text("最大容量：", font_size=18, font="Microsoft YaHei", color=GRAY_A),
            Text("max_size = 100", font_size=18, font="Consolas", color=GRAY_A)
        ).arrange(RIGHT, buff=0.1).next_to(length_marker, RIGHT, buff=0.5)

        self.play(FadeIn(length_marker), FadeIn(capacity_info))
        self.wait(0.5)

        # ---------------- 步骤 1：空间是否已满判断 ----------------
        with self.voiceover(
                text="第一步，检查存储空间是否已满。如果 self.length 等于 max_size，则空间已满，抛出异常。",
                subcaption="第一步，检查存储空间是否已满。如果 self.length == max_size，则空间已满，抛出异常。") as tracker:
            self.play(*get_track_anims(1), run_time=tracker.duration)

        with self.voiceover(
                text="当前表长为 5，远未达到最大容量 100，空间充足，算法继续向下执行。",
                subcaption="当前表长为 5，远未达到最大容量 100，空间充足，算法继续向下执行。") as tracker:
            self.wait(tracker.duration)

        # ---------------- 步骤 2：插入位置合法性判断 ----------------
        with self.voiceover(
                text="第二步，检查插入位置i是否合法。i的有效范围是 1 到 self.length 加 1。",
                subcaption="第二步，检查插入位置i是否合法。i的有效范围是 1 到 self.length + 1。") as tracker:
            self.play(*get_track_anims(3), run_time=tracker.duration)

        with self.voiceover(
                text="也就是说，在当前表长为 5 的情况下，i 的合法取值范围是 1 到 6。若 i 小于 1 或大于 6，则抛出位置不合法异常。",
                subcaption="在当前表长为 5 的情况下，i 的合法取值范围是 1 到 6。若 i < 1 或 i > 6，则抛出位置不合法异常。") as tracker:
            self.wait(tracker.duration)

        # ---------------- 步骤 3：正常插入演示 (i = 3, e = 99) ----------------
        insert_i = 3
        insert_e = 99

        param_panel = VGroup(
            Text("参数：", font_size=20, font="Microsoft YaHei", color=YELLOW),
            Text(f"i = {insert_i},  e = {insert_e}", font_size=22, color=YELLOW, font="Consolas")
        ).arrange(RIGHT, buff=0.12).next_to(code_block, DOWN, buff=0.25).align_to(code_block, LEFT)

        with self.voiceover(
                text=f"现在，假设我们要执行插入操作：在第 {insert_i} 个位置，插入新元素 {insert_e}。",
                subcaption=f"假设我们要执行插入操作：在第 {insert_i} 个位置，插入新元素 {insert_e}。") as tracker:
            self.play(*get_track_anims(0), FadeIn(param_panel), run_time=tracker.duration)

        # 目标插入位置高亮提醒
        target_slot_box = l_boxes[insert_i - 1]
        slot_highlight = SurroundingRectangle(target_slot_box, color=YELLOW, buff=0.04, stroke_width=3)
        with self.voiceover(
                text=f"由于要在第 {insert_i} 个位置插入，因此该位置及之后的所有元素，都必须依次向后移动一格。",
                subcaption=f"由于要在第 {insert_i} 个位置插入，因此该位置及之后的所有元素，都必须依次向后移动一格。") as tracker:
            self.play(Create(slot_highlight), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
                text="算法进入 for 循环。在 Python 中，通过 range 函数从后向前倒序遍历。",
                subcaption="算法进入 for 循环。在 Python 中，通过 range 函数从后向前倒序遍历。") as tracker:
            self.play(*get_track_anims(5), run_time=tracker.duration)

        with self.voiceover(
                text="循环起始下标为 self.length 减 1 即下标 4，步长为负 1，一直遍历到 i 减 1 即下标 2 为止。",
                subcaption="起始下标为 self.length - 1 即下标 4，步长为 -1，遍历到 i - 1 即下标 2 为止。") as tracker:
            self.wait(tracker.duration)

        # ---------------- 循环元素后移演练 ----------------
        def create_idx_pointer(box_idx):
            arrow = Arrow(DOWN, UP, buff=0.05, tip_length=0.15).scale(0.3).next_to(index_marks[box_idx], DOWN, buff=0.05)
            arrow.set_color(YELLOW)
            lbl = Text(f"idx={box_idx}", font_size=15, color=YELLOW, font="Consolas").next_to(arrow, DOWN, buff=0.05)
            return VGroup(arrow, lbl)

        # idx = 4: elem[4] (60) -> elem[5]
        idx_ptr = create_idx_pointer(4)
        with self.voiceover(
                text="首先 idx 等于 4，执行循环体：将下标 4 的元素 60 后移到下标 5。",
                subcaption="首先 idx = 4，执行循环体：self.elem[5] = self.elem[4]，元素 60 后移。") as tracker:
            self.play(*get_track_anims(6), FadeIn(idx_ptr), run_time=0.6)
            new_text_5 = Text("60", font_size=24, font="Arial", color=YELLOW).move_to(l_boxes[5].get_center())
            self.play(
                TransformFromCopy(l_nums[4], new_text_5),
                l_boxes[5].animate.set_color(BLUE).set_stroke(opacity=1),
                run_time=0.8
            )
            l_nums[5] = new_text_5
            self.add(l_nums[5])
            self.wait(max(0.1, tracker.duration - 1.4))

        # idx = 3: elem[3] (48) -> elem[4]
        idx_ptr_3 = create_idx_pointer(3)
        with self.voiceover(
                text="接着 idx 变为 3，将下标 3 的元素 48 后移到下标 4。",
                subcaption="接着 idx = 3，执行 self.elem[4] = self.elem[3]，元素 48 后移。") as tracker:
            self.play(*get_track_anims(5), ReplacementTransform(idx_ptr, idx_ptr_3), run_time=0.5)
            idx_ptr = idx_ptr_3
            self.play(*get_track_anims(6), run_time=0.3)
            new_text_4 = Text("48", font_size=24, font="Arial", color=YELLOW).move_to(l_boxes[4].get_center())
            self.play(
                Transform(l_nums[4], new_text_4),
                run_time=0.8
            )
            self.wait(max(0.1, tracker.duration - 1.6))

        # idx = 2: elem[2] (36) -> elem[3]
        idx_ptr_2 = create_idx_pointer(2)
        with self.voiceover(
                text="然后 idx 变为 2，将下标 2 的元素 36 后移到下标 3。",
                subcaption="然后 idx = 2，执行 self.elem[3] = self.elem[2]，元素 36 后移。") as tracker:
            self.play(*get_track_anims(5), ReplacementTransform(idx_ptr, idx_ptr_2), run_time=0.5)
            idx_ptr = idx_ptr_2
            self.play(*get_track_anims(6), run_time=0.3)
            new_text_3 = Text("36", font_size=24, font="Arial", color=YELLOW).move_to(l_boxes[3].get_center())
            self.play(
                Transform(l_nums[3], new_text_3),
                run_time=0.8
            )
            self.wait(max(0.1, tracker.duration - 1.6))

        # 循环结束，空出位置
        empty_text_2 = Text("", font_size=24, font="Arial").move_to(l_boxes[2].get_center())
        with self.voiceover(
                text="for 循环执行完毕。此时第 3 个位置、也就是下标 2 的存储单元已经成功腾出空位。",
                subcaption="for 循环执行完毕。此时第 3 个位置（下标 2）已成功腾出空位。") as tracker:
            self.play(
                FadeOut(idx_ptr),
                Transform(l_nums[2], empty_text_2),
                l_boxes[2].animate.set_color(YELLOW),
                run_time=0.8
            )
            self.wait(max(0.1, tracker.duration - 0.8))

        # ---------------- 步骤 4：放入新元素 ----------------
        new_val_mobj = Text(str(insert_e), font_size=26, font="Arial", color=GREEN).move_to(
            l_boxes[2].get_center() + UP * 1.5
        )
        with self.voiceover(
                text=f"接着执行赋值语句。将新元素 {insert_e} 放入第 {insert_i} 个位置，即下标为 i 减 1 的位置。",
                subcaption=f"执行 self.elem[i - 1] = e，将新元素 {insert_e} 放入下标为 {insert_i - 1} 的位置。") as tracker:
            self.play(*get_track_anims(7), FadeIn(new_val_mobj, shift=DOWN * 0.3), run_time=0.5)
            self.play(
                new_val_mobj.animate.move_to(l_boxes[2].get_center()),
                l_boxes[2].animate.set_color(GREEN),
                run_time=0.8
            )
            l_nums[2] = new_val_mobj
            self.wait(max(0.1, tracker.duration - 1.3))

        # ---------------- 步骤 5：表长加 1 ----------------
        new_length_marker = VGroup(
            Text("表长：", font_size=20, font="Microsoft YaHei", color=WHITE),
            Text("self.length = 6", font_size=20, font="Consolas", color=GREEN)
        ).arrange(RIGHT, buff=0.1).move_to(length_marker.get_center()).align_to(length_marker, LEFT)

        with self.voiceover(
                text="最后执行表长加 1，self.length 更新为 6。插入操作顺利完成！",
                subcaption="最后执行 self.length += 1，表长更新为 6。插入操作顺利完成！") as tracker:
            self.play(*get_track_anims(8), Transform(length_marker, new_length_marker), run_time=0.8)
            all_reset_anims = [box.animate.set_color(BLUE) for box in l_boxes]
            all_reset_anims.extend([num.animate.set_color(WHITE) for num in l_nums if num.text != ""])
            all_reset_anims.append(FadeOut(slot_highlight))
            self.play(*all_reset_anims, run_time=0.6)
            self.wait(max(0.1, tracker.duration - 1.4))

        self.play(*get_track_anims(None), FadeOut(param_panel), run_time=0.5)

        # =========================================================================
        # ===== PHASE E — COMPLEXITY ANALYSIS (时空复杂度分析) =====
        # =========================================================================
        time_row = VGroup(
            Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
            Text("O(n)", font_size=26, font="Arial", color=YELLOW)
        ).arrange(RIGHT, buff=0.1)

        time_best = Text("最好情况：在表尾插入 (i=n+1)，移动 0 次，O(1)", font_size=15, font="Microsoft YaHei", color=GRAY_A)
        time_worst = Text("最坏情况：在表头插入 (i=1)，移动 n 次，O(n)", font_size=15, font="Microsoft YaHei", color=GRAY_A)
        time_avg = Text("平均情况：各个位置等概率，平均移动 n/2 次，O(n)", font_size=15, font="Microsoft YaHei", color=GRAY_A)

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
                text="最后分析时间和空间复杂度。插入操作的时间主要耗费在循环后移元素上。",
                subcaption="最后分析时间和空间复杂度。插入操作的时间主要耗费在循环后移元素上。") as tracker:
            self.play(FadeIn(time_row), run_time=tracker.duration)

        with self.voiceover(
                text="最好情况下在表尾插入，无需移动元素，时间复杂度为 O 一。",
                subcaption="最好情况下在表尾插入 (i=n+1)，移动 0 次，时间复杂度为 O(1)。") as tracker:
            self.play(FadeIn(time_best), run_time=tracker.duration)

        with self.voiceover(
                text="最坏情况下在表头插入，需要后移全部 n 个元素，时间复杂度为 O n。",
                subcaption="最坏情况下在表头插入 (i=1)，需要后移全部 n 个元素，时间复杂度为 O(n)。") as tracker:
            self.play(FadeIn(time_worst), run_time=tracker.duration)

        with self.voiceover(
                text="在每个位置插入概率均等时，平均需要移动一半的元素，因此平均时间复杂度为 O n。",
                subcaption="各个位置插入概率均等时，平均移动 n/2 次，因此平均时间复杂度为 O(n)。") as tracker:
            self.play(FadeIn(time_avg), run_time=tracker.duration)

        with self.voiceover(
                text="空间上，算法仅使用常数个辅助变量，未开辟额外存储空间，因此空间复杂度为 O 一。",
                subcaption="算法仅使用常数个辅助变量，辅助空间复杂度为 O(1)。") as tracker:
            self.play(FadeIn(space_group), run_time=tracker.duration)

        with self.voiceover(
                text="这就是顺序表插入算法 Python 版的完整演示过程。",
                subcaption="这就是顺序表插入算法 Python 版的完整演示过程。") as tracker:
            self.play(Indicate(complexity_panel, color=BLUE_B, scale_factor=1.03), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))

        self.wait(2)


# Alias
SeqListInsertPythonVideo = ContinuousSeqListInsertPythonVideo
