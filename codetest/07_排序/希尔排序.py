# coding=utf-8
from manim import *
import os
import sys
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(ROOT_DIR, ".agent", "skills", "sorting_algorithms", "examples"))
from sorting_base import SortingBase


class _SilentTracker:
    duration = 0.1


class _SilentVoiceover:
    def __enter__(self):
        return _SilentTracker()

    def __exit__(self, exc_type, exc, tb):
        return False


class ShellSortVideo(SortingBase):
    GROUP_COLORS = [RED, BLUE, GREEN, ORANGE, PURPLE, TEAL, PINK, GOLD]

    def create_array(self, data, show_indices=True):
        self.array_data = list(data)
        self.boxes = VGroup()
        self.labels = VGroup()

        for i, val in enumerate(self.array_data):
            box = Square(side_length=self.BOX_SIZE, color=self.COLOR_DEFAULT)
            label = "04" if val == 4 else str(val)
            num = Text(label, font_size=self.FONT_SIZE, color=WHITE)
            self.boxes.add(VGroup(box, num))

            if show_indices:
                idx_label = Text(str(i), font_size=self.INDEX_FONT_SIZE, color=GREY)
                self.labels.add(idx_label)

        self.boxes.arrange(RIGHT, buff=self.BOX_BUFF)
        self.boxes.move_to(self.array_center)

        if show_indices:
            for i, label in enumerate(self.labels):
                label.next_to(self.boxes[i], DOWN, buff=0.2)

        return self.boxes

    def set_speech_service(self, *args, **kwargs):
        pass

    def voiceover(self, text="", subcaption=None):
        return _SilentVoiceover()

    def construct(self):
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(UP * 0.1)
        self.add(logo)

        title = Text("希尔排序", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(title), run_time=0.8)

        with self.voiceover(
            text="本节我们学习希尔排序。它先把记录按较大的间隔分组，在组内做直接插入排序，再逐步缩小间隔，直到间隔为一。",
            subcaption="本节我们学习希尔排序。它先按较大间隔分组，在组内做直接插入排序，再逐步缩小间隔直到一。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE A: 算法步骤 =====
        step_title = Text("算法步骤", font_size=34, font="Microsoft YaHei", color=YELLOW).to_edge(UP, buff=1.35)
        steps = VGroup(
            Text("1. 取增量 d1，把相隔 d1 的记录分到同一组", font_size=24, font="Microsoft YaHei"),
            Text("2. 各组内部做直接插入排序", font_size=24, font="Microsoft YaHei"),
            Text("3. 继续缩小增量 d2 < d1，重复分组和排序", font_size=24, font="Microsoft YaHei"),
            Text("4. 直到增量 d = 1，完成最后一趟插入排序", font_size=24, font="Microsoft YaHei"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.34)
        steps.next_to(step_title, DOWN, buff=0.45)

        with self.voiceover(
            text="希尔排序的核心，是先让远距离的元素提前靠近正确位置，再在更小的范围内细致整理。",
            subcaption="希尔排序的核心，是先让远距离的元素提前靠近正确位置，再在更小的范围内细致整理。"
        ) as tracker:
            self.play(FadeIn(step_title), run_time=0.4)
            self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.2) for s in steps], lag_ratio=0.16), run_time=max(1.1, tracker.duration - 0.4))

        with self.voiceover(
            text="你可以把它想成整理书架：先按间隔把书分成几列，每列内部先简单排一排；然后把间隔缩小，再重新整理。",
            subcaption="你可以把它想成整理书架：先按间隔把书分成几列，每列内部先简单排一排；然后把间隔缩小，再重新整理。"
        ) as tracker:
            note = Text("先粗排，再细排", font_size=24, font="Microsoft YaHei", color=GREEN).next_to(steps, DOWN, buff=0.45)
            self.play(FadeIn(note), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        self.play(FadeOut(step_title), FadeOut(steps), FadeOut(note), run_time=0.5)

        # ===== PHASE B: 生活实例 =====
        life_title = Text("生活实例：书架分列整理", font_size=30, font="Microsoft YaHei", color=YELLOW).to_edge(UP, buff=1.0)
        shelf = Line(LEFT * 4.4 + DOWN * 1.0, RIGHT * 4.4 + DOWN * 1.0, color=GRAY_B, stroke_width=6)
        shelf_label = Text("书架", font_size=18, font="Microsoft YaHei", color=GRAY_B).next_to(shelf, DOWN, buff=0.15)
        gap_text = Text("间隔 d = 4", font_size=24, font="Microsoft YaHei", color=GREEN).to_edge(LEFT, buff=0.6).shift(UP * 1.45)

        def make_book(value, pos, color):
            body = RoundedRectangle(
                corner_radius=0.06, width=1.05, height=1.45,
                color=color, fill_color=color, fill_opacity=0.24, stroke_width=2.3
            ).move_to(pos)
            label = Text(str(value), font_size=30, font="Consolas", color=WHITE).move_to(body.get_center())
            return VGroup(body, label)

        shelf_values = [8, 1, 4]
        shelf_books = VGroup(
            make_book(8, LEFT * 2.8 + DOWN * 0.15, BLUE),
            make_book(1, ORIGIN + DOWN * 0.15, TEAL),
            make_book(4, RIGHT * 2.8 + DOWN * 0.15, BLUE),
        )
        group_caption = Text("同一组内先做直接插入排序", font_size=22, font="Microsoft YaHei", color=ORANGE).to_edge(LEFT, buff=0.6).shift(DOWN * 1.6)

        with self.voiceover(
            text="先看一个生活实例。假设书架上有几本书，我们先把间隔四本看成同一组。",
            subcaption="先看一个生活实例。假设书架上有几本书，我们先把间隔四本看成同一组。"
        ) as tracker:
            self.play(FadeIn(life_title), FadeIn(shelf), FadeIn(shelf_label), FadeIn(gap_text), FadeIn(shelf_books), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(
            text="这一组里，八号书在前，四号书在后，中间还有一号书。组内先进行一次直接插入整理。",
            subcaption="这一组里，8 在前，4 在后，中间还有 1。组内先进行一次直接插入整理。"
        ) as tracker:
            self.play(FadeIn(group_caption), run_time=0.4)
            self.play(shelf_books[1][0].animate.set_color(YELLOW), run_time=0.25)
            self.play(shelf_books[0].animate.shift(RIGHT * 1.35), shelf_books[1].animate.shift(LEFT * 2.55), run_time=0.75)
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(
            text="整理之后，一号书被放到更靠前的位置。然后再看四号书，它会继续被放到合适的空位里。",
            subcaption="整理之后，1 号书被放到更靠前的位置。然后再看 4 号书，它会继续被放到合适的空位里。"
        ) as tracker:
            self.play(shelf_books[2].animate.shift(LEFT * 1.35), run_time=0.65)
            self.play(shelf_books[0][0].animate.set_color(GREEN), shelf_books[1][0].animate.set_color(GREEN), shelf_books[2][0].animate.set_color(GREEN), run_time=0.35)
            self.play(Transform(group_caption, Text("同一组内整理完毕", font_size=22, font="Microsoft YaHei", color=GREEN).move_to(group_caption)), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 1.0))

        self.play(FadeOut(VGroup(life_title, shelf, shelf_label, gap_text, shelf_books, group_caption)), run_time=0.8)

        # ===== PHASE C: CODE PANEL =====
        code_lines = [
            "void ShellSort(SqList &L) {",
            "    int gap, i, j, key;",
            "    for (gap = L.length / 2; gap > 0; gap /= 2) {",
            "        for (i = gap; i < L.length; ++i) {",
            "            key = L.r[i];",
            "            for (j = i - gap; j >= 0 && L.r[j].key > key.key; j -= gap)",
            "                L.r[j + gap] = L.r[j];",
            "            L.r[j + gap] = key;",
            "        }",
            "    }",
            "}",
        ]
        code = self.show_code_panel("\n".join(code_lines))
        self.highlight_code_line(3)
        self.wait(0.3)

        # ===== PHASE D: ARRAY DEMO =====
        data = [49, 38, 65, 97, 76, 13, 27, 49, 55, 4]
        self.show_array(data, title="")
        self.wait(0.3)

        info = self.show_complexity_info("O(n^1.3)", "O(n^1.3)", "O(n^2)", "O(1)", False)
        step = self.show_step_text("按增量 d 分组，组内做直接插入排序")
        self.wait(self.PHASE_PAUSE)

        n = len(self.array_data)
        gap = n // 2
        round_num = 1

        while gap > 0:
            self.update_step_text(step, f"第{round_num}趟：d = {gap}，分成 {gap} 组")
            self.highlight_code_line(3)
            for g in range(gap):
                color = self.GROUP_COLORS[g % len(self.GROUP_COLORS)]
                self.highlight(list(range(g, n, gap)), color, run_time=0.25)
            self.wait(0.3)

            self.highlight_code_line(4)
            for i in range(gap, n):
                key = self.array_data[i]
                j = i
                group_color = self.GROUP_COLORS[(i % gap) % len(self.GROUP_COLORS)]
                self.highlight(i, self.COLOR_KEY, run_time=0.18)
                self.highlight_code_line(5)
                self.wait(0.08)

                while j >= gap and self.array_data[j - gap] > key:
                    self.highlight_code_line(6)
                    self.highlight(j - gap, self.COLOR_COMPARING, run_time=0.15)
                    self.array_data[j] = self.array_data[j - gap]
                    # 单元格位置固定，只将前一个记录的值写入当前空位。
                    # 移动整个方块再交换引用会让两格重合，后续各趟不断叠字。
                    moved_value = self.array_data[j - gap]
                    moved_label = "04" if moved_value == 4 else str(moved_value)
                    moved_num = Text(moved_label, font_size=self.FONT_SIZE, color=WHITE).move_to(self.boxes[j][1])
                    self.play(Transform(self.boxes[j][1], moved_num), run_time=0.24)
                    j -= gap

                self.array_data[j] = key
                self.highlight_code_line(7)
                key_label = "04" if key == 4 else str(key)
                new_num = Text(key_label, font_size=self.FONT_SIZE, color=WHITE).move_to(self.boxes[j][1].get_center())
                self.play(Transform(self.boxes[j][1], new_num), run_time=0.2)
                self.reset_colors([j], self.COLOR_SORTED if gap == 1 else self.COLOR_DEFAULT)

            self.reset_colors()
            self.update_step_text(step, f"第{round_num}趟完成：d = {gap}")
            self.wait(self.PHASE_PAUSE)

            gap //= 2
            round_num += 1

        self.play(*[self.boxes[i][0].animate.set_color(GREEN) for i in range(len(self.boxes))], run_time=0.6)
        self.update_step_text(step, "排序完成！")
        self.wait(0.5)

        cleanup = [FadeOut(VGroup(code, info, step))]
        if self._code_hl is not None:
            cleanup.append(FadeOut(self._code_hl))
            self._code_hl = None
        self.play(*cleanup, run_time=0.4)
        self.show_final_result()
        self.wait(2)
