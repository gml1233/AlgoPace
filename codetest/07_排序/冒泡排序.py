# coding=utf-8
from manim import *
from codetest.sorting_support import SortingNarrationMixin, fit_code_block
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
try:
    from manim_voiceover import VoiceoverScene
    from generation.tts.edge_service import EdgeTTSService
except ModuleNotFoundError:
    class _SilentTracker:
        duration = 0.1

    class _SilentVoiceover:
        def __enter__(self):
            return _SilentTracker()

        def __exit__(self, exc_type, exc, tb):
            return False

    class VoiceoverScene(Scene):
        def set_speech_service(self, *args, **kwargs):
            pass

        def voiceover(self, text="", subcaption=None):
            return _SilentVoiceover()

    class EdgeTTSService:
        def __init__(self, *args, **kwargs):
            pass


class BubbleSortVideo(SortingNarrationMixin, VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(UP * 0.1)
        self.add(logo)

        title = Text("冒泡排序", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(title), run_time=0.8)

        with self.voiceover(
            text="本节学习冒泡排序。该算法是通过两两比较相邻记录关键字，如果为逆序，则进行交换，从而使关键字小的记录如气泡上浮。",
            subcaption="本节学习冒泡排序。该算法是通过两两比较相邻记录关键字，如果为逆序，则进行交换，从而使关键字小的记录如气泡上浮。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE A: LIFE EXAMPLE =====
        life_title = Text("生活实例：按身高排队", font_size=30, font="Microsoft YaHei", color=YELLOW).to_edge(UP, buff=1.25)
        ground = Line(LEFT * 4.6 + DOWN * 1.0, RIGHT * 4.6 + DOWN * 1.0, color=GRAY_B, stroke_width=5)
        ground_label = Text("队伍从左到右逐步排整齐", font_size=18, font="Microsoft YaHei", color=GRAY_B).next_to(ground, DOWN, buff=0.15)
        life_status = Text("只看相邻两个人：左边更高就交换", font_size=24, font="Microsoft YaHei", color=GREEN).to_edge(DOWN, buff=1.45)

        def make_student(height, color):
            body = RoundedRectangle(
                corner_radius=0.08,
                width=0.82,
                height=1.18,
                color=color,
                fill_color=color,
                fill_opacity=0.22,
                stroke_width=2.4,
            )
            head = Circle(radius=0.18, color=color, fill_color=color, fill_opacity=0.28, stroke_width=2).next_to(body, UP, buff=0.05)
            label = Text(str(height), font_size=24, font="Consolas", color=WHITE).move_to(body.get_center())
            return VGroup(body, head, label)

        students = VGroup(
            make_student(170, BLUE),
            make_student(160, TEAL),
            make_student(180, BLUE),
            make_student(155, TEAL),
            make_student(165, BLUE),
        ).arrange(RIGHT, buff=0.28).move_to(LEFT * 0.25 + DOWN * 0.12)
        life_values = [170, 160, 180, 155, 165]

        def swap_students(a, b):
            students[a].generate_target()
            students[b].generate_target()
            students[a].target.move_to(students[b].get_center())
            students[b].target.move_to(students[a].get_center())
            students[a], students[b] = students[b], students[a]
            life_values[a], life_values[b] = life_values[b], life_values[a]
            return MoveToTarget(students[b]), MoveToTarget(students[a])

        with self.voiceover(
            text="先看一个生活实例：按身高排队。老师不一次性看完整支队伍，而是从左到右只比较相邻两个人。",
            subcaption="先看一个生活实例：按身高排队。老师不一次性看完整支队伍，而是从左到右只比较相邻两个人。"
        ) as tracker:
            self.play(FadeIn(life_title), FadeIn(ground), FadeIn(ground_label), FadeIn(students), FadeIn(life_status), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(
            text="如果左边的人更高，就让这两个人交换位置。这样较高的人会一步一步往右移动。",
            subcaption="如果左边的人更高，就让这两个人交换位置。这样较高的人会一步一步往右移动。"
        ) as tracker:
            pair_box = SurroundingRectangle(VGroup(students[0], students[1]), color=YELLOW, buff=0.12, stroke_width=3)
            self.play(Create(pair_box), students[0][0].animate.set_color(YELLOW), students[1][0].animate.set_color(YELLOW), run_time=0.45)
            self.play(*swap_students(0, 1), run_time=0.7)
            self.play(Transform(life_status, Text("170 比 160 高，交换位置", font_size=24, font="Microsoft YaHei", color=YELLOW).to_edge(DOWN, buff=1.45)), run_time=0.35)
            self.wait(max(0.1, tracker.duration - 1.5))
            self.play(FadeOut(pair_box), run_time=0.2)

        with self.voiceover(
            text="继续向右比较。每一趟结束后，这一趟范围内最高的人，就会被换到队伍右端。",
            subcaption="继续向右比较。每一趟结束后，这一趟范围内最高的人，就会被换到队伍右端。"
        ) as tracker:
            pair_box = SurroundingRectangle(VGroup(students[2], students[3]), color=YELLOW, buff=0.12, stroke_width=3)
            self.play(Create(pair_box), run_time=0.35)
            self.play(*swap_students(2, 3), run_time=0.65)
            pair_box_2 = SurroundingRectangle(VGroup(students[3], students[4]), color=YELLOW, buff=0.12, stroke_width=3)
            self.play(ReplacementTransform(pair_box, pair_box_2), run_time=0.3)
            self.play(*swap_students(3, 4), run_time=0.65)
            right_mark = Text("本趟最高", font_size=20, font="Microsoft YaHei", color=GREEN).next_to(students[4], UP, buff=0.18)
            self.play(FadeIn(right_mark), students[4][0].animate.set_color(GREEN), Transform(life_status, Text("一趟结束，最大者到达最右端", font_size=24, font="Microsoft YaHei", color=GREEN).to_edge(DOWN, buff=1.45)), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 2.1))
            self.play(FadeOut(pair_box_2), FadeOut(right_mark), run_time=0.25)

        self.play(FadeOut(VGroup(life_title, ground, ground_label, students, life_status)), run_time=0.7)

        # ===== PHASE B: ALGORITHM STEPS =====
        step_title = Text("算法步骤与思想", font_size=34, font="Microsoft YaHei", color=YELLOW).to_edge(UP, buff=1.35)
        steps = VGroup(
            Text("1. 从 r[1] 开始，依次比较相邻两个记录", font_size=24, font="Microsoft YaHei"),
            Text("2. 若 L.r[j].key > L.r[j+1].key，说明逆序，交换它们", font_size=24, font="Microsoft YaHei"),
            Text("3. 一趟结束后，当前范围内最大记录到达右端", font_size=24, font="Microsoft YaHei"),
            Text("4. 缩小右边界 m，继续下一趟起泡排序", font_size=24, font="Microsoft YaHei"),
            Text("5. 若某一趟没有交换，flag 保持为 0，提前结束", font_size=24, font="Microsoft YaHei"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        steps.next_to(step_title, DOWN, buff=0.45)
        step_panel = VGroup(step_title, steps).move_to(LEFT * 0.45 + DOWN * 0.05)

        with self.voiceover(
            text="对应到算法中，第一步是从 r 一开始，依次比较相邻两个记录。如果前一个关键字大于后一个关键字，就说明这两个记录逆序，需要交换。",
            subcaption="对应到算法中，第一步是从 r 一开始，依次比较相邻两个记录。如果前一个关键字大于后一个关键字，就说明这两个记录逆序，需要交换。"
        ) as tracker:
            self.play(FadeIn(step_title), run_time=0.4)
            self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.2) for s in steps[:2]], lag_ratio=0.2), run_time=max(1.0, tracker.duration - 0.4))

        with self.voiceover(
            text="每完成一趟，当前范围里的最大记录就被交换到右端。下一趟不再处理这个位置，所以 m 会减一。",
            subcaption="每完成一趟，当前范围里的最大记录就被交换到右端。下一趟不再处理这个位置，所以 m 会减一。"
        ) as tracker:
            self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.2) for s in steps[2:4]], lag_ratio=0.2), run_time=max(1.0, tracker.duration))

        with self.voiceover(
            text="flag 用来判断本趟是否发生交换。如果一整趟都没有交换，说明序列已经有序，算法就可以提前停止。",
            subcaption="flag 用来判断本趟是否发生交换。如果一整趟都没有交换，说明序列已经有序，算法就可以提前停止。"
        ) as tracker:
            self.play(FadeIn(steps[4], shift=RIGHT * 0.2), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        self.play(FadeOut(step_panel), run_time=0.6)

        # ===== CODE PANEL =====
        c_lines = [
            "void BubbleSort(SqList &L) {",
            "    int m, j, flag;",
            "    ElemType t;",
            "    m = L.length - 1; flag = 1;",
            "    while ((m > 0) && (flag == 1)) {",
            "        flag = 0;",
            "        for (j = 1; j <= m; j++)",
            "            if (L.r[j].key > L.r[j + 1].key) {",
            "                flag = 1;",
            "                t = L.r[j];",
            "                L.r[j] = L.r[j + 1];",
            "                L.r[j + 1] = t;",
            "            }",
            "        --m;",
            "    }",
            "}",
        ]

        IDX_INIT = 3
        IDX_WHILE = 4
        IDX_FLAG0 = 5
        IDX_FOR = 6
        IDX_IF = 7
        IDX_FLAG1 = 8
        IDX_T = 9
        IDX_SWAP1 = 10
        IDX_SWAP2 = 11
        IDX_M_DEC = 13

        self.c_texts = []
        for line in c_lines:
            t = Text(line.lstrip(" "), font_size=12, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.11)
        space_width = 0.092
        for k, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[k].shift(RIGHT * indent_count * space_width)

        code_bg = RoundedRectangle(
            corner_radius=0.18,
            height=code_group.get_height() + 0.48,
            width=code_group.get_width() + 0.58,
            color=GRAY,
            fill_color=BLACK,
            fill_opacity=0.35,
            stroke_width=1,
        ).move_to(code_group)
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.12).to_edge(RIGHT, buff=0.2)
        fit_code_block(code_block)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line:
                return []
            anims = []
            if self.current_line is not None:
                anims.append(self.c_texts[self.current_line].animate.set_color(WHITE))
            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW))
                if not hasattr(self, "code_pointer"):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.13).rotate(-PI / 2)
                    self.code_pointer.next_to(self.c_texts[new_idx], LEFT, buff=0.16)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.c_texts[new_idx], LEFT, buff=0.16)
                    anims.append(MoveToTarget(self.code_pointer))
                self.current_line = new_idx
            else:
                if hasattr(self, "code_pointer"):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, "code_pointer")
                self.current_line = None
            return anims

        with self.voiceover(
            text="右侧是冒泡排序的核心函数。请重点关注 m、j 和 flag：m 控制本趟比较范围，j 扫描相邻记录，flag 记录本趟是否发生交换。",
            subcaption="右侧是冒泡排序的核心函数。请重点关注 m、j 和 flag：m 控制本趟比较范围，j 扫描相邻记录，flag 记录本趟是否发生交换。"
        ) as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # ===== ARRAY SETUP =====
        values = [49, 38, 65, 97, 76, 13, 27, 49]
        visual = [None] + values[:]
        n = len(values)
        box_side = 0.68

        boxes = [None]
        box_group = VGroup()
        index_group = VGroup()
        value_texts = [None] * (n + 1)
        for k in range(1, n + 1):
            box = Square(side_length=box_side, color=BLUE, stroke_width=2)
            if k > 1:
                box.next_to(box_group[-1], RIGHT, buff=0)
            boxes.append(box)
            box_group.add(box)
            index_group.add(Text(f"r[{k}]", font_size=16, font="Consolas", color=GRAY_B).next_to(box, DOWN, buff=0.12))

        box_group.move_to(LEFT * 3.1 + UP * 0.7)
        for k in range(1, n + 1):
            index_group[k - 1].next_to(boxes[k], DOWN, buff=0.12)
            value_texts[k] = Text("04" if visual[k] == 4 else str(visual[k]), font_size=23, font="Arial", color=WHITE).move_to(boxes[k].get_center())

        elem_arrow = Arrow(
            start=boxes[1].get_bottom() + DOWN * 0.72,
            end=boxes[1].get_bottom() + DOWN * 0.1,
            buff=0.04,
            tip_length=0.15,
            color=ORANGE,
            stroke_width=4,
        )
        elem_text = Text("L.r", font_size=18, color=ORANGE, font="Consolas").next_to(elem_arrow, DOWN, buff=0.03)
        elem_pointer = VGroup(elem_arrow, elem_text)
        array_group = VGroup(box_group, index_group, *value_texts[1:], elem_pointer)

        status = Text("示例顺序表：相邻记录依次比较", font_size=24, font="Microsoft YaHei", color=YELLOW).move_to(LEFT * 3.15 + DOWN * 1.2)
        var_panel = VGroup(
            Text("m = -", font_size=20, font="Consolas", color=ORANGE),
            Text("j = -", font_size=20, font="Consolas", color=YELLOW),
            Text("flag = -", font_size=20, font="Consolas", color=GREEN),
        ).arrange(RIGHT, buff=0.45).move_to(LEFT * 3.15 + DOWN * 2.0)
        m_text, j_text, flag_text = var_panel

        sorted_brace = Brace(VGroup(boxes[n]), UP, color=GREEN)
        sorted_label = Text("已到位", font_size=18, font="Microsoft YaHei", color=GREEN).next_to(sorted_brace, UP, buff=0.08)
        sorted_group = VGroup(sorted_brace, sorted_label)
        sorted_visible = False

        def update_var(text_mob, content):
            # Text 容器本身可能是黑色；从实际字形读取颜色，避免更新后消失。
            return Transform(text_mob, Text(content, font_size=20, font="Consolas", color=text_mob[0].get_color()).move_to(text_mob))

        def set_status(content, color=YELLOW, size=24):
            return Transform(status, Text(content, font_size=size, font="Microsoft YaHei", color=color).move_to(status))

        def reset_box_colors(sorted_from=None):
            anims = []
            for k in range(1, n + 1):
                if sorted_from is not None and k >= sorted_from:
                    anims.append(boxes[k].animate.set_color(GREEN).set_fill(GREEN, opacity=0.12))
                else:
                    anims.append(boxes[k].animate.set_color(BLUE).set_fill(BLACK, opacity=0))
            return anims

        def compare_marker(j):
            rect = SurroundingRectangle(VGroup(boxes[j], boxes[j + 1]), color=YELLOW, buff=0.08, stroke_width=3)
            lab = Text(f"比较 r[{j}] 和 r[{j + 1}]", font_size=18, font="Microsoft YaHei", color=YELLOW).next_to(rect, UP, buff=0.1)
            return VGroup(rect, lab)

        def display_value(value):
            return "04" if value == 4 else str(value)

        def swap_values(j):
            value_texts[j].generate_target()
            value_texts[j + 1].generate_target()
            value_texts[j].target.move_to(boxes[j + 1].get_center())
            value_texts[j + 1].target.move_to(boxes[j].get_center())
            old_left, old_right = value_texts[j], value_texts[j + 1]
            visual[j], visual[j + 1] = visual[j + 1], visual[j]
            value_texts[j], value_texts[j + 1] = old_right, old_left
            return MoveToTarget(old_left), MoveToTarget(old_right)

        def update_sorted_brace(start_index):
            nonlocal sorted_group, sorted_visible
            new_brace = Brace(VGroup(*[boxes[k] for k in range(start_index, n + 1)]), UP, color=GREEN)
            new_label = Text("已确定位置", font_size=18, font="Microsoft YaHei", color=GREEN).next_to(new_brace, UP, buff=0.08)
            new_group = VGroup(new_brace, new_label)
            old_group = sorted_group
            sorted_group = new_group
            if not sorted_visible:
                sorted_visible = True
                return FadeIn(new_group)
            return ReplacementTransform(old_group, new_group)

        with self.voiceover(
            text="示例数据为四十九、三十八、六十五、九十七、七十六、十三、二十七、四十九。顺序表连续存放，从 r 一开始依次比较。",
            subcaption="示例数据为四十九、三十八、六十五、九十七、七十六、十三、二十七、四十九。顺序表连续存放，从 r 一开始依次比较。"
        ) as tracker:
            self.play(FadeIn(array_group), FadeIn(status), FadeIn(var_panel), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))

        m = n - 1
        flag = 1
        with self.voiceover(
            text="代码先执行初始化。m 等于表长减一，所以第一趟最多比较到 r 七和 r 八；flag 等于一，让 while 循环可以进入。",
            subcaption="代码先执行初始化。m 等于表长减一，所以第一趟最多比较到 r 七和 r 八；flag 等于一，让 while 循环可以进入。"
        ) as tracker:
            self.play(
                *get_track_anims(IDX_INIT),
                update_var(m_text, f"m = {m}"),
                update_var(flag_text, "flag = 1"),
                run_time=0.8
            )
            self.wait(max(0.1, tracker.duration - 0.8))

        pass_no = 1
        max_detailed_passes = 2
        while m > 0 and flag == 1:
            with self.voiceover(
                text=f"第 {pass_no} 趟开始。while 条件成立，进入本趟扫描。",
                subcaption=f"第 {pass_no} 趟开始。while 条件成立，进入本趟扫描。"
            ) as tracker:
                self.play(*get_track_anims(IDX_WHILE), set_status(f"第 {pass_no} 趟：在 r[1..{m + 1}] 中冒泡最大值"), run_time=0.7)
                self.wait(max(0.1, tracker.duration - 0.7))

            flag = 0
            pass_swapped = False
            with self.voiceover(
                text="进入一趟排序前，先把 flag 置为零。只有发生交换时，flag 才会重新变成一。",
                subcaption="进入一趟排序前，先把 flag 置为零。只有发生交换时，flag 才会重新变成一。"
            ) as tracker:
                self.play(*get_track_anims(IDX_FLAG0), update_var(flag_text, "flag = 0"), run_time=0.7)
                self.wait(max(0.1, tracker.duration - 0.7))

            for j in range(1, m + 1):
                marker = compare_marker(j)
                left_val = visual[j]
                right_val = visual[j + 1]

                with self.voiceover(
                    text=f"for 循环让 j 等于 {j}，比较相邻的 r {j} 和 r {j + 1}，也就是 {left_val} 和 {right_val}。",
                    subcaption=f"for 循环让 j 等于 {j}，比较相邻的 r {j} 和 r {j + 1}，也就是 {left_val} 和 {right_val}。"
                ) as tracker:
                    self.play(
                        *get_track_anims(IDX_FOR),
                        update_var(j_text, f"j = {j}"),
                        *reset_box_colors(n - pass_no + 2 if pass_no > 1 else None),
                        FadeIn(marker),
                        boxes[j].animate.set_color(YELLOW).set_fill(YELLOW, opacity=0.16),
                        boxes[j + 1].animate.set_color(YELLOW).set_fill(YELLOW, opacity=0.16),
                        run_time=0.65
                    )
                    self.wait(max(0.1, tracker.duration - 0.65))

                if left_val > right_val:
                    flag = 1
                    pass_swapped = True
                    with self.voiceover(
                        text=f"{left_val} 大于 {right_val}，出现逆序，执行 if 语句内部的交换代码。",
                        subcaption=f"{left_val} 大于 {right_val}，出现逆序，执行 if 语句内部的交换代码。"
                    ) as tracker:
                        self.play(*get_track_anims(IDX_IF), boxes[j].animate.set_color(RED), boxes[j + 1].animate.set_color(RED), run_time=0.35)
                        self.play(*get_track_anims(IDX_FLAG1), update_var(flag_text, "flag = 1"), run_time=0.35)
                        self.play(*get_track_anims(IDX_T), set_status(f"用临时变量 t 保存 r[{j}] = {left_val}", ORANGE), run_time=0.35)
                        self.play(*get_track_anims(IDX_SWAP1), run_time=0.2)
                        self.play(*get_track_anims(IDX_SWAP2), *swap_values(j), set_status(f"交换完成：{right_val} 到左边，{left_val} 到右边", GREEN), run_time=0.65)
                        self.wait(max(0.1, tracker.duration - 1.9))
                else:
                    with self.voiceover(
                        text=f"{left_val} 不大于 {right_val}，相邻记录顺序正确，不需要交换。",
                        subcaption=f"{left_val} 不大于 {right_val}，相邻记录顺序正确，不需要交换。"
                    ) as tracker:
                        self.play(*get_track_anims(IDX_IF), set_status("顺序正确，不交换", GREEN), run_time=0.5)
                        self.wait(max(0.1, tracker.duration - 0.5))

                self.play(FadeOut(marker), run_time=0.15)

            with self.voiceover(
                text=f"第 {pass_no} 趟扫描结束，本趟范围内最大的记录已经到达 r {m + 1} 的位置。",
                subcaption=f"第 {pass_no} 趟扫描结束，本趟范围内最大的记录已经到达 r {m + 1} 的位置。"
            ) as tracker:
                self.play(
                    update_sorted_brace(m + 1),
                    boxes[m + 1].animate.set_color(GREEN).set_fill(GREEN, opacity=0.18),
                    set_status(f"r[{m + 1}] 已确定：{visual[m + 1]}", GREEN),
                    run_time=0.8
                )
                self.wait(max(0.1, tracker.duration - 0.8))

            m -= 1
            with self.voiceover(
                text=f"然后执行减减 m。下一趟只需要处理前 {m + 1} 个记录，右端已经到位的记录不再参加比较。",
                subcaption=f"然后执行减减 m。下一趟只需要处理前 {m + 1} 个记录，右端已经到位的记录不再参加比较。"
            ) as tracker:
                self.play(*get_track_anims(IDX_M_DEC), update_var(m_text, f"m = {m}"), run_time=0.65)
                self.wait(max(0.1, tracker.duration - 0.65))

            if not pass_swapped:
                with self.voiceover(
                    text="因为这一趟没有发生任何交换，flag 保持为零，说明序列已经有序，while 循环将提前结束。",
                    subcaption="因为这一趟没有发生任何交换，flag 保持为零，说明序列已经有序，while 循环将提前结束。"
                ) as tracker:
                    self.play(*get_track_anims(IDX_WHILE), set_status("flag = 0，序列已有序，提前结束", GREEN), run_time=0.8)
                    self.wait(max(0.1, tracker.duration - 0.8))
                break

            if pass_no >= max_detailed_passes and m > 0:
                temp = visual[:]
                temp_m = m
                temp_flag = 1
                remaining_passes = 0
                while temp_m > 0 and temp_flag == 1:
                    temp_flag = 0
                    for temp_j in range(1, temp_m + 1):
                        if temp[temp_j] > temp[temp_j + 1]:
                            temp[temp_j], temp[temp_j + 1] = temp[temp_j + 1], temp[temp_j]
                            temp_flag = 1
                    temp_m -= 1
                    remaining_passes += 1

                summary = (
                    f"前两趟已经展示了完整规则。后续 {remaining_passes} 趟仍然重复相邻比较、逆序交换、"
                    "一趟确定一个最大值的过程，所以这里直接快进到排序完成。"
                )
                with self.voiceover(text=summary, subcaption=summary) as tracker:
                    final_anims = []
                    for k in range(1, n + 1):
                        visual[k] = temp[k]
                        final_text = Text(display_value(temp[k]), font_size=23, font="Arial", color=WHITE).move_to(boxes[k].get_center())
                        final_anims.append(Transform(value_texts[k], final_text))
                        final_anims.append(boxes[k].animate.set_color(GREEN).set_fill(GREEN, opacity=0.16))
                    self.play(
                        *get_track_anims(IDX_WHILE),
                        set_status("后续各趟同理，快进到最终有序序列", GREEN, size=22),
                        *final_anims,
                        run_time=1.2
                    )
                    self.wait(max(0.1, tracker.duration - 1.2))
                break

            pass_no += 1

        self.play(*reset_box_colors(1), run_time=0.5)
        result_text = Text("排序结果：13  27  38  49  49  65  76  97", font_size=23, font="Microsoft YaHei", color=GREEN).move_to(LEFT * 3.15 + DOWN * 1.15)
        with self.voiceover(
            text="最终，所有记录从小到大排列完成，结果为十三、二十七、三十八、四十九、四十九、六十五、七十六、九十七。以上就是冒泡排序代码的执行过程。",
            subcaption="最终，所有记录从小到大排列完成，结果为十三、二十七、三十八、四十九、四十九、六十五、七十六、九十七。以上就是冒泡排序代码的执行过程。"
        ) as tracker:
            self.play(
                *get_track_anims(None),
                Transform(status, result_text),
                FadeOut(var_panel),
                FadeOut(sorted_group),
                run_time=0.8
            )
            self.wait(max(0.1, tracker.duration - 0.8))

        complexity_title = Text("时空复杂度与稳定性", font_size=34, font="Microsoft YaHei", color=YELLOW)
        complexity_rows = VGroup(
            Text("最好情况：已有序，一趟扫描后提前结束", font_size=23, font="Microsoft YaHei", color=GREEN),
            Text("最坏情况：逆序，需要多趟比较和频繁交换", font_size=23, font="Microsoft YaHei", color=ORANGE),
            Text("平均、最坏时间复杂度：O(n²)", font_size=23, font="Microsoft YaHei", color=YELLOW),
            Text("空间复杂度：O(1)；稳定性：稳定", font_size=23, font="Microsoft YaHei", color=BLUE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
        complexity_panel = VGroup(complexity_title, complexity_rows).arrange(DOWN, buff=0.45).move_to(ORIGIN + DOWN * 0.15)

        intro = "最后看冒泡排序的时空复杂度和稳定性。这里的复杂度说的是随数据规模增长，算法运行时间和辅助空间如何变化。"
        with self.voiceover(text=intro, subcaption=intro) as tracker:
            self.play(FadeOut(code_block), FadeOut(array_group), FadeOut(status), FadeIn(complexity_title), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        best_text = "最好情况下，初始序列已经有序。算法只需要一趟扫描，完成 n 减一 次相邻比较，没有交换，flag 保持为零后提前结束。"
        with self.voiceover(text=best_text, subcaption=best_text) as tracker:
            self.play(FadeIn(complexity_rows[0], shift=RIGHT * 0.25), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.5))

        time_text = "最坏情况下，初始序列正好逆序。算法要进行多趟扫描，每趟都把当前范围内的最大记录交换到右端，而且一次交换包含三次记录移动。"
        with self.voiceover(text=time_text, subcaption=time_text) as tracker:
            self.play(FadeIn(complexity_rows[1], shift=RIGHT * 0.25), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.5))

        space_text = "把所有趟数累加起来，平均和最坏情况下的比较与移动都属于平方级增长，所以冒泡排序的时间复杂度为 O n 平方。"
        with self.voiceover(text=space_text, subcaption=space_text) as tracker:
            self.play(FadeIn(complexity_rows[2], shift=RIGHT * 0.25), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.5))

        stable_text = "空间复杂度是 O 一，因为只使用少量变量和临时记录。冒泡排序也是稳定排序，相等关键字不会触发交换。"
        with self.voiceover(text=stable_text, subcaption=stable_text) as tracker:
            self.play(FadeIn(complexity_rows[3], shift=RIGHT * 0.25), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.5))

        self.wait(1.0)
