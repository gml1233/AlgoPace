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


class DirectInsertionSortVideo(SortingNarrationMixin, VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(UP * 0.1)
        self.add(logo)

        title = Text("直接插入排序", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(title), run_time=0.8)

        with self.voiceover(
            text="本节我们学习直接插入排序。它的思想很像整理书架：左边始终保持有序，每次从右边取出一本书，插入到左边合适的位置。",
            subcaption="本节我们学习直接插入排序。它的思想很像整理书架：左边始终保持有序，每次从右边取出一本书，插入到左边合适的位置。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE A: 思想与步骤 =====
        step_title = Text("算法步骤", font_size=34, font="Microsoft YaHei", color=YELLOW).to_edge(UP, buff=1.35)
        steps = VGroup(
            Text("1. r[1] 先看作只有一个元素的有序序列", font_size=24, font="Microsoft YaHei"),
            Text("2. 依次取 r[i]，在 r[1..i-1] 中顺序查找插入位置", font_size=24, font="Microsoft YaHei"),
            Text("3. 比它大的记录逐个后移，最后把 r[i] 插入空位", font_size=24, font="Microsoft YaHei"),
            Text("4. 重复 n - 1 次，得到长度为 n 的有序序列", font_size=24, font="Microsoft YaHei"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        steps.next_to(step_title, DOWN, buff=0.45)
        step_panel = VGroup(step_title, steps).move_to(LEFT * 1.1 + DOWN * 0.1)

        with self.voiceover(
            text="首先明确算法步骤。初始时，第一项 r 一已经有序；随后循环 n 减一轮，每轮把当前元素插入前面已经排好序的子表。",
            subcaption="首先明确算法步骤。初始时，第一项 r[1] 已经有序；随后循环 n - 1 轮，每轮把当前元素插入前面已经排好序的子表。"
        ) as tracker:
            self.play(FadeIn(step_title), run_time=0.4)
            self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.2) for s in steps], lag_ratio=0.18), run_time=max(1.2, tracker.duration - 0.4))

        with self.voiceover(
            text="这里的 r 零号单元是监视哨，用来临时保存待插入记录。它不会出现在最终排序结果中。",
            subcaption="这里的 r[0] 是监视哨，用来临时保存待插入记录。它不会出现在最终排序结果中。"
        ) as tracker:
            guard_note = Text("r[0]：监视哨，暂存待插入记录", font_size=24, font="Microsoft YaHei", color=GREEN).next_to(steps, DOWN, buff=0.5)
            self.play(FadeIn(guard_note), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        self.play(FadeOut(step_panel), FadeOut(guard_note), run_time=0.5)

        # ===== PHASE A2: 生活实例 =====
        life_title = Text(
            "生活实例：图书按编号上架",
            font_size=30,
            font="Microsoft YaHei",
            color=YELLOW,
        ).next_to(title, DOWN, buff=0.28)
        table = Line(LEFT * 4.6 + DOWN * 1.0, RIGHT * 4.6 + DOWN * 1.0, color=GRAY_B, stroke_width=6)
        table_label = Text("书架", font_size=18, font="Microsoft YaHei", color=GRAY_B).next_to(table, DOWN, buff=0.14)
        sorted_label = Text("已排好序的书", font_size=22, font="Microsoft YaHei", color=GREEN).to_edge(LEFT, buff=0.7).shift(UP * 1.35)
        incoming_label = Text("新书", font_size=22, font="Microsoft YaHei", color=TEAL).to_edge(RIGHT, buff=0.9).shift(UP * 1.35)

        def make_book(value, pos, color=BLUE):
            card = RoundedRectangle(
                corner_radius=0.06,
                width=0.92,
                height=1.55,
                color=color,
                fill_color=color,
                fill_opacity=0.24,
                stroke_width=2.3,
            ).move_to(pos)
            spine = Line(card.get_left() + UP * 0.56, card.get_left() + DOWN * 0.56, color=color, stroke_width=4)
            num = Text(str(value), font_size=28, font="Consolas", color=WHITE).move_to(card.get_center())
            return VGroup(card, spine, num)

        shelf_books = VGroup(
            make_book(12, LEFT * 3.6 + DOWN * 0.04, BLUE),
            make_book(27, LEFT * 2.2 + DOWN * 0.04, BLUE),
            make_book(34, LEFT * 0.8 + DOWN * 0.04, BLUE),
            make_book(49, RIGHT * 0.6 + DOWN * 0.04, BLUE),
            make_book(65, RIGHT * 2.0 + DOWN * 0.04, BLUE),
        )
        card_12, card_27, card_34, card_49, card_65 = shelf_books
        card_38 = make_book(38, RIGHT * 4.0 + DOWN * 0.04, TEAL)
        incoming_arrow = Arrow(start=RIGHT * 4.1 + UP * 0.9, end=RIGHT * 4.1 + DOWN * 0.1, color=TEAL, buff=0.06, stroke_width=4)

        with self.voiceover(
            text="先来看一个生活实例：图书上架。书架上已经按编号排好五本书，新书来了以后，要找到合适的位置插进去。",
            subcaption="先来看一个生活实例：图书上架。书架上已经按编号排好五本书，新书来了以后，要找到合适的位置插进去。"
        ) as tracker:
            self.play(
                FadeIn(life_title),
                FadeIn(table),
                FadeIn(table_label),
                FadeIn(sorted_label),
                FadeIn(incoming_label),
                FadeIn(shelf_books),
                FadeIn(card_38),
                FadeIn(incoming_arrow),
                run_time=1.0
            )
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(
            text="先看三十四号书和四十九号书之间的位置。现在要插入三十八号书，得先和前面的书比较。",
            subcaption="先看 34 号书和 49 号书之间的位置。现在要插入 38 号书，得先和前面的书比较。"
        ) as tracker:
            self.play(card_38.animate.move_to(LEFT * 0.2 + DOWN * 0.04), run_time=0.6)
            self.play(card_34[0].animate.set_color(YELLOW), card_49[0].animate.set_color(YELLOW), run_time=0.35)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
            text="三十八比四十九小，所以四十九和后面的书往后挪一格，三十八就插到中间。",
            subcaption="38 比 49 小，所以 49 和后面的书往后挪一格，38 就插到中间。"
        ) as tracker:
            self.play(card_49.animate.shift(RIGHT * 1.55), card_65.animate.shift(RIGHT * 1.55), run_time=0.6)
            self.play(card_38.animate.move_to(RIGHT * 0.2 + DOWN * 0.04), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(
            text="再看六十五号书，它比前面的书更大，所以直接接在后面就行。",
            subcaption="再看 65 号书，它比前面的书更大，所以直接接在后面就行。"
        ) as tracker:
            self.play(card_12[0].animate.set_color(GREEN), card_27[0].animate.set_color(GREEN), card_34[0].animate.set_color(GREEN), card_38[0].animate.set_color(GREEN), card_49[0].animate.set_color(GREEN), card_65[0].animate.set_color(GREEN), run_time=0.3)
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(
            text="这样，书架就从十二、二十七、三十四、四十九、六十五，变成了十二、二十七、三十四、三十八、四十九、六十五。这就是直接插入排序的插入过程。",
            subcaption="这样，书架就从 12、27、34、49、65 变成了 12、27、34、38、49、65。这就是直接插入排序的插入过程。"
        ) as tracker:
            final_note = Text("左边始终有序，右边依次插入", font_size=22, font="Microsoft YaHei", color=GREEN).to_edge(DOWN, buff=1.45)
            self.play(FadeIn(final_note), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 0.4))

        self.play(FadeOut(VGroup(life_title, table, table_label, sorted_label, incoming_label, shelf_books, card_38, incoming_arrow, final_note)), run_time=0.8)

        # ===== PHASE B: CODE BLOCK =====
        c_lines = [
            "void InsertSort(SqList &L) {",
            "    int i, j;",
            "    for (i = 2; i <= L.length; ++i) {",
            "        if (L.r[i].key < L.r[i - 1].key) {",
            "            L.r[0] = L.r[i];",
            "            L.r[i] = L.r[i - 1];",
            "            for (j = i - 2; L.r[0].key < L.r[j].key; --j)",
            "                L.r[j + 1] = L.r[j];",
            "            L.r[j + 1] = L.r[0];",
            "        }",
            "    }",
            "}",
        ]

        IDX_FOR = 2
        IDX_IF = 3
        IDX_GUARD = 4
        IDX_FIRST_SHIFT = 5
        IDX_INNER_FOR = 6
        IDX_SHIFT = 7
        IDX_INSERT = 8

        self.c_texts = []
        for line in c_lines:
            t = Text(line.lstrip(" "), font_size=13, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        space_width = 0.105
        for k, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[k].shift(RIGHT * indent_count * space_width)

        code_bg = RoundedRectangle(
            corner_radius=0.18,
            height=code_group.get_height() + 0.55,
            width=code_group.get_width() + 0.65,
            color=GRAY,
            fill_color=BLACK,
            fill_opacity=0.35,
            stroke_width=1,
        ).move_to(code_group)
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.2).to_edge(RIGHT, buff=0.25)
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
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.14).rotate(-PI / 2)
                    self.code_pointer.next_to(self.c_texts[new_idx], LEFT, buff=0.18)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.c_texts[new_idx], LEFT, buff=0.18)
                    anims.append(MoveToTarget(self.code_pointer))
                self.current_line = new_idx
            else:
                if hasattr(self, "code_pointer"):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, "code_pointer")
                self.current_line = None
            return anims

        with self.voiceover(
            text="右侧是直接插入排序的核心代码。接下来我们用一组数据，按代码执行顺序完整演示。",
            subcaption="右侧是直接插入排序的核心代码。接下来我们用一组数据，按代码执行顺序完整演示。"
        ) as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # ===== PHASE C: ARRAY SETUP =====
        values = [49, 38, 65, 97, 76, 13, 27, 49, 55, 4]
        visual = [None] + values[:]
        n = len(values)
        box_side = 0.64

        boxes = VGroup()
        value_texts = [None] * (n + 1)
        index_texts = VGroup()
        for k in range(n + 1):
            stroke = GREEN if k == 0 else BLUE
            box = Square(side_length=box_side, color=stroke, stroke_width=2)
            if k > 0:
                box.next_to(boxes[-1], RIGHT, buff=0.06)
            boxes.add(box)
            idx = Text(f"r[{k}]", font_size=16, font="Consolas", color=GRAY_B).next_to(box, DOWN, buff=0.12)
            index_texts.add(idx)

        boxes.move_to(LEFT * 3.2 + UP * 0.6)
        for k, idx in enumerate(index_texts):
            idx.next_to(boxes[k], DOWN, buff=0.12)

        for k in range(n + 1):
            label = "-" if visual[k] is None else ("04" if visual[k] == 4 else str(visual[k]))
            color = GREEN if k == 0 else WHITE
            value_texts[k] = Text(label, font_size=23, font="Arial", color=color).move_to(boxes[k].get_center())

        array_group = VGroup(boxes, index_texts, *value_texts)

        ordered_brace = Brace(VGroup(boxes[1]), UP, color=GREEN)
        ordered_label = Text("有序子表", font_size=18, font="Microsoft YaHei", color=GREEN).next_to(ordered_brace, UP, buff=0.08)

        status = Text("初始：r[1] 自成有序序列", font_size=24, font="Microsoft YaHei", color=YELLOW).move_to(LEFT * 3.1 + DOWN * 1.25)
        var_panel = VGroup(
            Text("i = -", font_size=22, font="Consolas", color=YELLOW),
            Text("j = -", font_size=22, font="Consolas", color=ORANGE),
            Text("r[0] = -", font_size=22, font="Consolas", color=GREEN),
        ).arrange(RIGHT, buff=0.5).move_to(LEFT * 3.1 + DOWN * 2.0)
        i_text, j_text, guard_text = var_panel

        def make_pointer(label, index, color, direction="up"):
            target = boxes[index]
            if direction == "up":
                arrow = Arrow(start=target.get_top() + UP * 0.55, end=target.get_top(), buff=0.06, color=color, stroke_width=4)
                txt = Text(label, font_size=20, font="Consolas", color=color).next_to(arrow, UP, buff=0.05)
            else:
                arrow = Arrow(start=target.get_bottom() + DOWN * 0.55, end=target.get_bottom(), buff=0.06, color=color, stroke_width=4)
                txt = Text(label, font_size=20, font="Consolas", color=color).next_to(arrow, DOWN, buff=0.05)
            return VGroup(arrow, txt)

        i_ptr = make_pointer("i", 2, YELLOW, "up")
        j_ptr = make_pointer("j", 1, ORANGE, "down")

        def move_pointer(ptr, label, index, color, direction="up"):
            ptr.generate_target()
            ptr.target = make_pointer(label, index, color, direction)
            return MoveToTarget(ptr)

        def update_cell(index, new_value, color=None):
            visual[index] = new_value
            label = "-" if new_value is None else ("04" if new_value == 4 else str(new_value))
            new_text = Text(label, font_size=23, font="Arial", color=color or (GREEN if index == 0 else WHITE)).move_to(boxes[index].get_center())
            old = value_texts[index]
            value_texts[index] = new_text
            return ReplacementTransform(old, new_text)

        def update_var(text_mob, content):
            # Text 容器本身可能是黑色；从实际字形读取颜色，避免更新后消失。
            new_text = Text(content, font_size=22, font="Consolas", color=text_mob[0].get_color()).move_to(text_mob)
            return Transform(text_mob, new_text)

        def set_status(content, color=YELLOW):
            new_text = Text(content, font_size=24, font="Microsoft YaHei", color=color).move_to(status)
            return Transform(status, new_text)

        def reset_box_colors(upto_sorted):
            anims = []
            for k, box in enumerate(boxes):
                if k == 0:
                    anims.append(box.animate.set_color(GREEN).set_fill(BLACK, opacity=0))
                elif 1 <= k <= upto_sorted:
                    anims.append(box.animate.set_color(GREEN).set_fill(GREEN, opacity=0.12))
                else:
                    anims.append(box.animate.set_color(BLUE).set_fill(BLACK, opacity=0))
            return anims

        def update_ordered_brace(end_index):
            nonlocal ordered_brace, ordered_label
            new_brace = Brace(VGroup(*[boxes[k] for k in range(1, end_index + 1)]), UP, color=GREEN)
            new_label = Text("有序子表", font_size=18, font="Microsoft YaHei", color=GREEN).next_to(new_brace, UP, buff=0.08)
            old_brace, old_label = ordered_brace, ordered_label
            ordered_brace, ordered_label = new_brace, new_label
            return ReplacementTransform(old_brace, new_brace), ReplacementTransform(old_label, new_label)

        with self.voiceover(
            text="示例序列为四十九、三十八、六十五、九十七、七十六、十三、二十七、四十九、五十五、零四。左侧加出的 r 零号单元，就是监视哨。",
            subcaption="示例序列为 49、38、65、97、76、13、27、49、55、04。左侧加出的 r[0]，就是监视哨。"
        ) as tracker:
            self.play(FadeIn(array_group), FadeIn(status), FadeIn(var_panel), run_time=1.0)
            self.play(FadeIn(ordered_brace), FadeIn(ordered_label), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 1.4))

        with self.voiceover(
            text="开始时只有 r 一属于有序子表，从 i 等于二的位置开始向后扫描。",
            subcaption="开始时只有 r[1] 属于有序子表，从 i = 2 的位置开始向后扫描。"
        ) as tracker:
            self.play(*get_track_anims(IDX_FOR), FadeIn(i_ptr), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        # ===== PHASE D: INSERTION SORT FLOW =====
        def describe_value(num):
            return str(num)

        for i in range(2, n + 1):
            self.play(*get_track_anims(IDX_FOR), move_pointer(i_ptr, "i", i, YELLOW, "up"), update_var(i_text, f"i = {i}"), run_time=0.45)
            self.play(*reset_box_colors(i - 1), *update_ordered_brace(i - 1), run_time=0.35)

            if visual[i] >= visual[i - 1]:
                with self.voiceover(
                    text=f"第 {i - 1} 轮，检查 r {i} 的值是 {describe_value(visual[i])}。它不小于前一个元素 {describe_value(visual[i - 1])}，说明已经在正确位置，本轮不需要移动。",
                    subcaption=f"第 {i - 1} 轮，检查 r[{i}] = {visual[i]}。它不小于 r[{i - 1}] = {visual[i - 1]}，本轮不需要移动。"
                ) as tracker:
                    self.play(*get_track_anims(IDX_IF), boxes[i].animate.set_color(YELLOW), boxes[i - 1].animate.set_color(YELLOW), run_time=0.5)
                    self.play(set_status(f"r[{i}] >= r[{i - 1}]，无需插入", GREEN), run_time=0.4)
                    self.wait(max(0.1, tracker.duration - 0.9))
                continue

            with self.voiceover(
                text=f"第 {i - 1} 轮，r {i} 的值是 {describe_value(visual[i])}，小于前一个元素 {describe_value(visual[i - 1])}，需要把它插入前面的有序子表。",
                subcaption=f"第 {i - 1} 轮，r[{i}] = {visual[i]} 小于 r[{i - 1}] = {visual[i - 1]}，需要插入有序子表。"
            ) as tracker:
                self.play(*get_track_anims(IDX_IF), boxes[i].animate.set_color(RED), boxes[i - 1].animate.set_color(RED), run_time=0.55)
                self.play(set_status(f"取出 r[{i}]，准备插入", YELLOW), run_time=0.35)
                self.wait(max(0.1, tracker.duration - 0.9))

            temp = visual[i]
            with self.voiceover(
                text=f"先把待插入记录 {describe_value(temp)} 暂存到监视哨 r 零中。",
                subcaption=f"先把待插入记录 {temp} 暂存到监视哨 r[0] 中。"
            ) as tracker:
                self.play(*get_track_anims(IDX_GUARD), update_cell(0, temp, GREEN), update_var(guard_text, f"r[0] = {temp}"), run_time=0.7)
                self.wait(max(0.1, tracker.duration - 0.7))

            with self.voiceover(
                text=f"然后把 r {i - 1} 后移到 r {i}，为插入位置腾出空间。",
                subcaption=f"然后把 r[{i - 1}] 后移到 r[{i}]，为插入位置腾出空间。"
            ) as tracker:
                self.play(*get_track_anims(IDX_FIRST_SHIFT), boxes[i - 1].animate.set_fill(ORANGE, opacity=0.28), run_time=0.35)
                self.play(update_cell(i, visual[i - 1], ORANGE), run_time=0.45)
                visual[i] = visual[i - 1]
                self.wait(max(0.1, tracker.duration - 0.8))

            j = i - 2
            if i == 2:
                j_ptr.become(make_pointer("j", max(j, 0), ORANGE, "down"))
                self.play(update_var(j_text, f"j = {j}"), FadeIn(j_ptr), run_time=0.45)
            else:
                self.play(update_var(j_text, f"j = {j}"), move_pointer(j_ptr, "j", max(j, 0), ORANGE, "down"), run_time=0.45)

            while j >= 1 and temp < visual[j]:
                with self.voiceover(
                    text=f"接着从后向前查找。因为监视哨中的 {describe_value(temp)} 仍然小于 r {j} 的 {describe_value(visual[j])}，所以 r {j} 继续后移。",
                    subcaption=f"因为 r[0] = {temp} 小于 r[{j}] = {visual[j]}，所以 r[{j}] 继续后移。"
                ) as tracker:
                    self.play(*get_track_anims(IDX_INNER_FOR), boxes[j].animate.set_color(ORANGE), boxes[j + 1].animate.set_color(ORANGE), run_time=0.45)
                    self.play(*get_track_anims(IDX_SHIFT), update_cell(j + 1, visual[j], ORANGE), run_time=0.5)
                    self.wait(max(0.1, tracker.duration - 0.95))
                visual[j + 1] = visual[j]
                j -= 1
                if j >= 1:
                    self.play(update_var(j_text, f"j = {j}"), move_pointer(j_ptr, "j", j, ORANGE, "down"), run_time=0.4)
                else:
                    self.play(update_var(j_text, "j = 0"), move_pointer(j_ptr, "j", 0, ORANGE, "down"), run_time=0.4)

            insert_pos = j + 1
            if j >= 1:
                compare_text = f"此时 r[0] = {temp} 不再小于 r[{j}] = {visual[j]}，插入位置就是 r[{insert_pos}]。"
                voice_text = f"此时监视哨中的 {describe_value(temp)} 不再小于 r {j} 的 {describe_value(visual[j])}，插入位置就是 r {insert_pos}。"
            else:
                compare_text = f"已经查到有序子表最前端，插入位置就是 r[{insert_pos}]。"
                voice_text = f"已经查到有序子表最前端，插入位置就是 r {insert_pos}。"

            with self.voiceover(text=voice_text, subcaption=compare_text) as tracker:
                self.play(*get_track_anims(IDX_INNER_FOR), boxes[insert_pos].animate.set_color(GREEN), run_time=0.45)
                self.wait(max(0.1, tracker.duration - 0.45))

            with self.voiceover(
                text=f"最后把监视哨中的 {describe_value(temp)} 写回 r {insert_pos}，本轮插入完成。",
                subcaption=f"最后把 r[0] 中的 {temp} 写回 r[{insert_pos}]，本轮插入完成。"
            ) as tracker:
                self.play(*get_track_anims(IDX_INSERT), update_cell(insert_pos, temp, GREEN), run_time=0.65)
                visual[insert_pos] = temp
                self.play(set_status(f"插入完成：r[1..{i}] 有序", GREEN), *reset_box_colors(i), *update_ordered_brace(i), run_time=0.55)
                self.wait(max(0.1, tracker.duration - 1.2))

        # ===== PHASE E: RESULT AND COMPLEXITY =====
        self.play(*get_track_anims(None), FadeOut(i_ptr), FadeOut(j_ptr), run_time=0.5)

        with self.voiceover(
            text="循环结束后，整个 r 一到 r n 都成为有序序列。排序结果是零四、十三、二十七、三十八、四十九、四十九、五十五、六十五、七十六、九十七。",
            subcaption="循环结束后，整个 r[1..n] 都成为有序序列。排序结果是 04、13、27、38、49、49、55、65、76、97。"
        ) as tracker:
            result_text = Text("排序结果：04  13  27  38  49  49  55  65  76  97", font_size=23, font="Microsoft YaHei", color=GREEN).move_to(LEFT * 3.1 + DOWN * 0.95)
            self.play(Transform(status, result_text), *reset_box_colors(n), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        pass_box = VGroup(
            Text("单趟插入：移动量取决于待插记录前面有多少更大元素", font_size=18, font="Microsoft YaHei", color=YELLOW),
        )
        best_box = VGroup(
            Text("最好情况：序列已有序，只需线性扫描", font_size=18, font="Microsoft YaHei", color=GREEN),
        )
        worst_box = VGroup(
            Text("最坏情况：每趟都要向前查找并大量后移", font_size=18, font="Microsoft YaHei", color=ORANGE),
        )
        avg_box = VGroup(
            Text("平均情况：比较和移动次数都随 n² 量级增长", font_size=18, font="Microsoft YaHei", color=YELLOW),
        )
        time_box = VGroup(
            Text("时间复杂度：O(n²)", font_size=20, font="Microsoft YaHei", color=YELLOW),
            Text("空间复杂度：O(1)", font_size=20, font="Microsoft YaHei", color=BLUE),
            Text("稳定性：稳定", font_size=20, font="Microsoft YaHei", color=GREEN),
        ).arrange(RIGHT, buff=0.28)
        summary = VGroup(pass_box, best_box, worst_box, avg_box, time_box).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to(LEFT * 3.05 + DOWN * 1.6)

        self.play(FadeOut(var_panel), FadeOut(status), run_time=0.3)

        caption = "分析直接插入排序，关键看每一趟插入时，待插记录前面有多少元素比它大。更大的元素越多，比较和后移就越多。"
        with self.voiceover(text=caption, subcaption=caption) as tracker:
            self.play(FadeIn(pass_box), run_time=0.7)
            self.wait(max(0.1, tracker.duration - 0.7))

        caption = "最好情况下，原序列已经有序。每一趟只需确认当前位置正确，几乎不发生移动，整个过程只需要线性规模的比较。"
        with self.voiceover(text=caption, subcaption=caption) as tracker:
            self.play(FadeIn(best_box), run_time=0.7)
            self.wait(max(0.1, tracker.duration - 0.7))

        caption = "最坏情况下，原序列正好逆序。新记录每次都要插到当前有序区的最前面，因此前面的记录会不断向后移动。"
        with self.voiceover(text=caption, subcaption=caption) as tracker:
            self.play(FadeIn(worst_box), run_time=0.7)
            self.wait(max(0.1, tracker.duration - 0.7))

        caption = "从次数上看，第 i 趟最多会产生 i 级别的比较和移动；把 n 减一 趟累加起来，就会形成平方级增长。"
        with self.voiceover(text=caption, subcaption=caption) as tracker:
            self.play(worst_box.animate.set_color(ORANGE), run_time=0.7)
            self.wait(max(0.1, tracker.duration - 0.7))

        caption = "所以最坏情况下，总比较次数和总移动次数都近似与 n 平方成正比，也就是数据量翻倍，耗时可能接近变为四倍。"
        with self.voiceover(text=caption, subcaption=caption) as tracker:
            self.play(worst_box.animate.scale(1.04, about_edge=LEFT), run_time=0.7)
            self.wait(max(0.1, tracker.duration - 0.7))

        caption = "平均情况下，虽然不会像逆序那样每趟都移动到底，但比较和移动的总量仍然属于平方级。"
        with self.voiceover(text=caption, subcaption=caption) as tracker:
            self.play(FadeIn(avg_box), run_time=0.7)
            self.wait(max(0.1, tracker.duration - 0.7))

        caption = "因此，直接插入排序的平均和最坏时间复杂度都记为 O n 平方。它只使用监视哨和少量变量，空间复杂度为 O 一。"
        with self.voiceover(text=caption, subcaption=caption) as tracker:
            self.play(FadeIn(time_box[0]), FadeIn(time_box[1]), run_time=0.7)
            self.wait(max(0.1, tracker.duration - 0.7))

        caption = "直接插入排序是稳定排序。因为只有当前面的关键字大于待插入记录时才后移，相等关键字不会越过彼此。"
        with self.voiceover(text=caption, subcaption=caption) as tracker:
            self.play(FadeIn(time_box[2]), run_time=0.7)
            self.wait(max(0.1, tracker.duration - 0.7))

        self.wait(2)
