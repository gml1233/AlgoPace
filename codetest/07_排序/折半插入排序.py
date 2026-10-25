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


class BinaryInsertionSortVideo(SortingNarrationMixin, VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(UP * 0.1)
        self.add(logo)

        title = Text("折半插入排序", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(title), run_time=0.8)

        with self.voiceover(
            text="本节我们学习折半插入排序。该算法是采用折半查找法查找当前记录在已排好序的序列中的插入位置，将当前记录插入到该位置，从而得到一个新的有序表。",
            subcaption="本节我们学习折半插入排序。该算法是采用折半查找法查找当前记录在已排好序的序列中的插入位置，将当前记录插入到该位置，从而得到一个新的有序表。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE A: LIFE EXAMPLE =====
        life_title = Text("生活实例：整理书架上的编号图书", font_size=26, font="Microsoft YaHei", color=YELLOW)
        life_title.move_to(LEFT * 3.15 + UP * 2.55)

        shelf_y = 0.45
        shelf_left = -5.55
        shelf_right = -0.55
        shelf = Line([shelf_left, shelf_y, 0], [shelf_right, shelf_y, 0], color=GRAY_B, stroke_width=6)
        shelf_label = Text("书架", font_size=18, font="Microsoft YaHei", color=GRAY_B).next_to(shelf, DOWN, buff=0.15)

        book_values = [13, 27, 38, 49, 65, 76, 97]
        book_width = 0.52
        book_height = 1.08
        book_gap = 0.08
        book_spacing = book_width + book_gap
        books = VGroup()
        book_texts = VGroup()
        for idx, val in enumerate(book_values):
            x = shelf_left + 0.38 + idx * book_spacing
            book = RoundedRectangle(
                corner_radius=0.05,
                width=book_width,
                height=book_height,
                color=BLUE if idx % 2 == 0 else TEAL,
                fill_color=BLUE if idx % 2 == 0 else TEAL,
                fill_opacity=0.22,
                stroke_width=2.2,
            ).move_to([x, shelf_y + book_height / 2, 0])
            spine = Text(str(val), font_size=20, font="Consolas", color=WHITE).move_to(book.get_center())
            books.add(book)
            book_texts.add(spine)

        new_book = RoundedRectangle(
            corner_radius=0.05,
            width=book_width,
            height=book_height,
            color=GREEN,
            fill_color=GREEN,
            fill_opacity=0.26,
            stroke_width=2.4,
        ).move_to([-2.0, -1.55, 0])
        new_book_text = Text("42", font_size=21, font="Consolas", color=WHITE).move_to(new_book.get_center())
        new_book_group = VGroup(new_book, new_book_text)
        new_book_tag = Text("新到图书", font_size=18, font="Microsoft YaHei", color=GREEN).next_to(new_book_group, DOWN, buff=0.12)

        def make_book_pointer(name, index, color, label, y_shift=0.0):
            book = books[index]
            start = np.array([book.get_center()[0], book.get_top()[1] + 0.43 + y_shift, 0])
            end = np.array([book.get_center()[0], book.get_top()[1] + 0.05, 0])
            arrow = Arrow(start=start, end=end, buff=0.05, color=color, stroke_width=4)
            txt = Text(label, font_size=17, font="Consolas", color=color).next_to(arrow, UP, buff=0.03)
            ptr = VGroup(arrow, txt)
            return ptr

        life_status = Text("这排书已经按编号排好序", font_size=22, font="Microsoft YaHei", color=GREEN).move_to(LEFT * 3.2 + DOWN * 2.4)

        self.play(FadeIn(life_title), FadeIn(shelf), FadeIn(shelf_label), FadeIn(VGroup(books, book_texts)), run_time=1.0)
        self.play(FadeIn(new_book_group, shift=DOWN * 0.2), FadeIn(new_book_tag), run_time=0.8)

        low_ptr = make_book_pointer("low", 0, BLUE_B, "low")
        high_ptr = make_book_pointer("high", 6, RED_B, "high")
        mid_ptr = make_book_pointer("mid", 3, PURPLE_B, "m")
        self.play(FadeIn(low_ptr), FadeIn(high_ptr), run_time=0.7)

        with self.voiceover(
            text="先把新来的四十二号图书放在下面。书架上已有的书从小到大排好，我们现在要为它找到合适的位置。",
            subcaption="先把新来的 42 号图书放在下面。书架上的书已经从小到大排好。"
        ) as tracker:
            self.play(Transform(life_status, Text("先找插入位置，再把后面的书整体右移", font_size=22, font="Microsoft YaHei", color=YELLOW).move_to(LEFT * 3.15 + DOWN * 2.4)), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(
            text="先看中间的四十九号书。四十二比四十九小，所以插入位置一定在左半边。",
            subcaption="先看中间的 49 号书。42 比 49 小，所以插入位置在左半边。"
        ) as tracker:
            self.play(FadeIn(mid_ptr), run_time=0.4)
            self.play(books[3].animate.set_color(PURPLE_B).set_fill(PURPLE_B, opacity=0.25), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 0.8))
        self.play(FadeOut(mid_ptr), run_time=0.2)

        high_ptr_2 = make_book_pointer("high", 2, RED_B, "high")
        with self.voiceover(
            text="再把 high 收到三十八号书这里。四十二不小于三十八，所以继续往右找。",
            subcaption="再把 high 收到 38 号书这里。42 不小于 38，所以继续往右找。"
        ) as tracker:
            self.play(ReplacementTransform(high_ptr, high_ptr_2), run_time=0.5)
            self.play(books[2].animate.set_color(RED_B).set_fill(RED_B, opacity=0.22), run_time=0.35)
            self.wait(max(0.1, tracker.duration - 0.85))
        high_ptr = high_ptr_2

        low_ptr_2 = make_book_pointer("low", 3, BLUE_B, "low")
        with self.voiceover(
            text="这一次 low 和 high 已经逼近到一块了，说明插入位置就在三十八号和四十九号之间。",
            subcaption="low 和 high 已经逼近，插入位置就在 38 和 49 之间。"
        ) as tracker:
            self.play(ReplacementTransform(low_ptr, low_ptr_2), run_time=0.5)
            self.play(books[3].animate.set_color(GREEN).set_fill(GREEN, opacity=0.18), run_time=0.35)
            self.wait(max(0.1, tracker.duration - 0.85))
        low_ptr = low_ptr_2

        insert_brace = Brace(VGroup(books[2], books[3]), DOWN, color=GREEN)
        insert_label = Text("插入点", font_size=18, font="Microsoft YaHei", color=GREEN).next_to(insert_brace, DOWN, buff=0.08)
        with self.voiceover(
            text="现在把四十九号及其后面的书整体往右挪出一个空位，再把四十二号放进去。",
            subcaption="把 49 号及其后面的书整体往右挪出一个空位，再把 42 号放进去。"
        ) as tracker:
            insert_target = books[3].get_center().copy()
            self.play(Create(insert_brace), FadeIn(insert_label), run_time=0.4)
            shift_anims = []
            for k in range(3, len(books)):
                shift_anims.append(books[k].animate.shift(RIGHT * book_spacing))
                shift_anims.append(book_texts[k].animate.shift(RIGHT * book_spacing))
            self.play(*shift_anims, run_time=0.8)
            self.wait(max(0.1, tracker.duration - 1.2))

        with self.voiceover(
            text="最后，四十二号书归位。这样一来，它就被插到了正确的位置，书架依然保持有序。",
            subcaption="最后 42 号书归位，书架依然保持有序。"
        ) as tracker:
            self.play(
                new_book_group.animate.move_to(insert_target),
                FadeOut(new_book_tag),
                run_time=0.75
            )
            self.play(
                Transform(life_status, Text("插入完成，书架仍然有序", font_size=22, font="Microsoft YaHei", color=GREEN).move_to(LEFT * 3.15 + DOWN * 2.4)),
                FadeOut(insert_brace),
                FadeOut(insert_label),
                run_time=0.5
            )
            self.wait(max(0.1, tracker.duration - 1.25))

        self.play(
            FadeOut(VGroup(life_title, shelf, shelf_label, books, book_texts, new_book_group, life_status, low_ptr, high_ptr)),
            run_time=0.7
        )

        # ===== PHASE B: 思想与步骤 =====
        step_title = Text("算法步骤", font_size=34, font="Microsoft YaHei", color=YELLOW).to_edge(UP, buff=1.35)
        steps = VGroup(
            Text("1. r[1] 先看作长度为 1 的有序序列", font_size=24, font="Microsoft YaHei"),
            Text("2. 依次取 r[i]，把它暂存到监视哨 r[0]", font_size=24, font="Microsoft YaHei"),
            Text("3. 在 r[1..i-1] 中用 low、high、m 折半定位", font_size=24, font="Microsoft YaHei"),
            Text("4. 将插入点之后的记录后移，再把 r[0] 写回空位", font_size=24, font="Microsoft YaHei"),
            Text("5. 重复 n - 1 次，得到长度为 n 的有序序列", font_size=24, font="Microsoft YaHei"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        steps.next_to(step_title, DOWN, buff=0.45)
        # 连同下面两行比较/移动说明一起为字幕预留底部空间。
        step_panel = VGroup(step_title, steps).scale(0.85).move_to(LEFT * 1.1 + UP * 0.4)

        with self.voiceover(
            text="对应到算法中，r 一先看作有序序列。之后从 i 等于二开始，每一轮都把 r i 插入到前面已经排好序的 r 一到 r i 减一中。",
            subcaption="对应到算法中，r[1] 先看作有序序列；从 i = 2 开始，把 r[i] 插入 r[1..i-1]。"
        ) as tracker:
            self.play(FadeIn(step_title), run_time=0.4)
            self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.2) for s in steps], lag_ratio=0.16), run_time=max(1.2, tracker.duration - 0.4))

        with self.voiceover(
            text="与直接插入排序相比，折半插入排序的关键变化，是先用二分的方式确定插入位置，再集中移动元素。",
            subcaption="关键变化：先用折半查找确定插入位置，再集中后移元素。"
        ) as tracker:
            note = VGroup(
                Text("查找位置：O(log i) 次比较", font_size=24, font="Microsoft YaHei", color=GREEN),
                Text("移动元素：仍可能需要 O(i) 次后移", font_size=24, font="Microsoft YaHei", color=ORANGE),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(steps, DOWN, buff=0.45)
            self.play(FadeIn(note), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        self.play(FadeOut(step_panel), FadeOut(note), run_time=0.5)

        # ===== PHASE B: CODE BLOCK =====
        c_lines = [
            "void BInsertSort(SqList &L) {",
            "    int i, j, low, high, m;",
            "    for (i = 2; i <= L.length; ++i) {",
            "        L.r[0] = L.r[i];",
            "        low = 1; high = i - 1;",
            "        while (low <= high) {",
            "            m = (low + high) / 2;",
            "            if (L.r[0].key < L.r[m].key)",
            "                high = m - 1;",
            "            else",
            "                low = m + 1;",
            "        }",
            "        for (j = i - 1; j >= high + 1; --j)",
            "            L.r[j + 1] = L.r[j];",
            "        L.r[high + 1] = L.r[0];",
            "    }",
            "}",
        ]

        IDX_FOR = 2
        IDX_GUARD = 3
        IDX_RANGE = 4
        IDX_WHILE = 5
        IDX_MID = 6
        IDX_COMPARE = 7
        IDX_HIGH = 8
        IDX_ELSE = 9
        IDX_LOW = 10
        IDX_SHIFT_FOR = 12
        IDX_SHIFT = 13
        IDX_INSERT = 14

        self.c_texts = []
        for line in c_lines:
            t = Text(line.lstrip(" "), font_size=12, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        space_width = 0.095
        for k, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[k].shift(RIGHT * indent_count * space_width)

        code_bg = RoundedRectangle(
            corner_radius=0.18,
            height=code_group.get_height() + 0.48,
            width=code_group.get_width() + 0.55,
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
            text="右侧是折半插入排序的核心代码。请特别关注三个变量：low、high 和 m，它们负责在有序子表中折半定位。",
            subcaption="右侧是折半插入排序的核心代码。low、high 和 m 负责在有序子表中折半定位。"
        ) as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # ===== PHASE C: ARRAY SETUP =====
        values = [49, 38, 65, 97, 76, 13, 27, 49, 55, 4]
        visual = [None] + values[:]
        n = len(values)
        box_side = 0.68

        boxes = VGroup()
        value_texts = [None] * (n + 1)
        index_texts = VGroup()
        for k in range(n + 1):
            stroke = GREEN if k == 0 else BLUE
            box = Square(side_length=box_side, color=stroke, stroke_width=2)
            if k > 0:
                box.next_to(boxes[-1], RIGHT, buff=0)
            boxes.add(box)
            idx = Text(f"r[{k}]", font_size=16, font="Consolas", color=GRAY_B).next_to(box, DOWN, buff=0.12)
            index_texts.add(idx)

        boxes.move_to(LEFT * 3.2 + UP * 0.65)
        for k, idx in enumerate(index_texts):
            idx.next_to(boxes[k], DOWN, buff=0.12)

        for k in range(n + 1):
            label = "-" if visual[k] is None else ("04" if visual[k] == 4 else str(visual[k]))
            color = GREEN if k == 0 else WHITE
            value_texts[k] = Text(label, font_size=23, font="Arial", color=color).move_to(boxes[k].get_center())

        # L.r 放在数组左上角，不与 high=0 的指针共用底部位置。
        elem_text = Text("L.r", font_size=18, color=ORANGE, font="Consolas")
        elem_text.next_to(boxes[0], UP, buff=0.18)
        array_group = VGroup(boxes, index_texts, *value_texts, elem_text)

        ordered_brace = VectorizedPoint(boxes[1].get_top())
        ordered_label = Text("有序区：r[1]", font_size=18, font="Microsoft YaHei", color=GREEN).move_to(LEFT * 3.2 + UP * 2.35)

        status = Text("初始：r[1] 自成有序序列", font_size=24, font="Microsoft YaHei", color=YELLOW).move_to(LEFT * 3.15 + DOWN * 1.35)
        var_panel = VGroup(
            Text("i = -", font_size=20, font="Consolas", color=YELLOW),
            Text("low = -", font_size=20, font="Consolas", color=BLUE_B),
            Text("high = -", font_size=20, font="Consolas", color=RED_B),
            Text("m = -", font_size=20, font="Consolas", color=PURPLE_B),
            Text("r[0] = -", font_size=20, font="Consolas", color=GREEN),
        ).arrange(RIGHT, buff=0.32).move_to(LEFT * 3.1 + DOWN * 2.05)
        i_text, low_text, high_text, mid_text, guard_text = var_panel

        def make_pointer(label, index, color, direction="up", x_offset=0.0):
            target = boxes[index]
            x = target.get_center()[0] + x_offset
            top_y = target.get_top()[1]
            bottom_y = target.get_bottom()[1]
            # 指针标签分层：low/high 同下标或相邻时也不重叠。
            # 底部箭头从索引文字下方开始；有序区范围在独立的顶部文字行显示。
            if direction == "up":
                lane_y = 1.85 if label == "i" else 1.35
                x += 0.14 if label == "i" else -0.14
                arrow = Arrow([x, lane_y - 0.15, 0], [x, top_y + 0.05, 0],
                              buff=0.02, color=color, stroke_width=3)
                txt = Text(label, font_size=16, font="Consolas", color=color).move_to([x, lane_y, 0])
            else:
                lane_y = -0.42 if label == "low" else -0.93
                x += -0.15 if label == "low" else 0.15
                arrow = Arrow([x, lane_y + 0.14, 0], [x, bottom_y - 0.38, 0],
                              buff=0.01, color=color, stroke_width=3)
                txt = Text(label, font_size=16, font="Consolas", color=color).move_to([x, lane_y, 0])
            return VGroup(arrow, txt)

        pointers = {}

        def pointer_anim(name, label, index, color, direction="up", x_offset=0.0):
            index = max(0, min(n, index))
            new_ptr = make_pointer(label, index, color, direction, x_offset)
            if name not in pointers:
                pointers[name] = new_ptr
                return FadeIn(new_ptr)
            pointers[name].generate_target()
            pointers[name].target = new_ptr
            return MoveToTarget(pointers[name])

        def fade_pointer(name):
            if name in pointers:
                ptr = pointers.pop(name)
                return FadeOut(ptr)
            return None

        def update_cell(index, new_value, color=None):
            visual[index] = new_value
            label = "-" if new_value is None else ("04" if new_value == 4 else str(new_value))
            new_text = Text(label, font_size=23, font="Arial", color=color or (GREEN if index == 0 else WHITE)).move_to(boxes[index].get_center())
            old = value_texts[index]
            value_texts[index] = new_text
            return ReplacementTransform(old, new_text)

        def update_var(text_mob, content):
            # Text 容器本身可能是黑色；从实际字形读取颜色，避免更新后消失。
            new_text = Text(content, font_size=20, font="Consolas", color=text_mob[0].get_color()).move_to(text_mob)
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
            new_brace = VectorizedPoint(boxes[end_index].get_top())
            new_label = Text(f"有序区：r[1..{end_index}]", font_size=18, font="Microsoft YaHei", color=GREEN).move_to(ordered_label)
            old_brace, old_label = ordered_brace, ordered_label
            ordered_brace, ordered_label = new_brace, new_label
            return ReplacementTransform(old_brace, new_brace), ReplacementTransform(old_label, new_label)

        with self.voiceover(
            text="示例序列为四十九、三十八、六十五、九十七、七十六、十三、二十七、四十九、五十五、零四。左侧的 r 零号单元用于暂存待插入记录。",
            subcaption="示例序列为 49、38、65、97、76、13、27、49、55、04。左侧 r[0] 用于暂存待插入记录。"
        ) as tracker:
            self.play(FadeIn(array_group), FadeIn(status), FadeIn(var_panel), run_time=1.0)
            self.play(FadeIn(ordered_brace), FadeIn(ordered_label), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 1.4))

        with self.voiceover(
            text="开始时只有 r 一属于有序子表，从 i 等于二的位置开始执行插入。",
            subcaption="开始时只有 r[1] 属于有序子表，从 i = 2 的位置开始执行插入。"
        ) as tracker:
            self.play(*get_track_anims(IDX_FOR), pointer_anim("i", "i", 2, YELLOW, "up"), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        # ===== PHASE D: BINARY INSERTION SORT FLOW =====
        def speak_num(num):
            return str(num)

        for i in range(2, n + 1):
            self.play(
                *get_track_anims(IDX_FOR),
                pointer_anim("i", "i", i, YELLOW, "up"),
                update_var(i_text, f"i = {i}"),
                *reset_box_colors(i - 1),
                *update_ordered_brace(i - 1),
                run_time=0.55
            )

            temp = visual[i]
            with self.voiceover(
                text=f"第 {i - 1} 轮，先取出 r {i} 的值 {speak_num(temp)}，保存到监视哨 r 零。",
                subcaption=f"第 {i - 1} 轮，取出 r[{i}] = {temp}，保存到监视哨 r[0]。"
            ) as tracker:
                self.play(*get_track_anims(IDX_GUARD), boxes[i].animate.set_color(YELLOW), update_cell(0, temp, GREEN), update_var(guard_text, f"r[0] = {temp}"), run_time=0.75)
                self.wait(max(0.1, tracker.duration - 0.75))

            low, high = 1, i - 1
            with self.voiceover(
                text=f"查找区间初始化为 low 等于一，high 等于 {i - 1}，也就是前面已经有序的子表。",
                subcaption=f"查找区间初始化：low = 1，high = {i - 1}，范围是 r[1..{i - 1}]。"
            ) as tracker:
                self.play(
                    *get_track_anims(IDX_RANGE),
                    update_var(low_text, f"low = {low}"),
                    update_var(high_text, f"high = {high}"),
                    pointer_anim("low", "low", low, BLUE_B, "down"),
                    pointer_anim("high", "high", high, RED_B, "down"),
                    set_status(f"在 r[1..{i - 1}] 中折半查找 {temp} 的位置"),
                    run_time=0.8
                )
                self.wait(max(0.1, tracker.duration - 0.8))

            while low <= high:
                m = (low + high) // 2
                with self.voiceover(
                    text=f"因为 low 不超过 high，继续折半。当前中点 m 等于 {m}，比较 r 零中的 {speak_num(temp)} 和 r {m} 的 {speak_num(visual[m])}。",
                    subcaption=f"low <= high，m = ({low} + {high}) / 2 = {m}。比较 r[0] = {temp} 与 r[{m}] = {visual[m]}。"
                ) as tracker:
                    self.play(
                        *get_track_anims(IDX_WHILE),
                        *reset_box_colors(i - 1),
                        boxes[i].animate.set_color(YELLOW),
                        pointer_anim("mid", "m", m, PURPLE_B, "up"),
                        update_var(mid_text, f"m = {m}"),
                        run_time=0.5
                    )
                    self.play(*get_track_anims(IDX_MID), boxes[m].animate.set_color(PURPLE_B).set_fill(PURPLE_B, opacity=0.22), run_time=0.35)
                    self.wait(max(0.1, tracker.duration - 0.85))

                if temp < visual[m]:
                    old_high = high
                    high = m - 1
                    with self.voiceover(
                        text=f"{speak_num(temp)} 小于 {speak_num(visual[m])}，说明插入点在前半区间，于是 high 改为 m 减一，也就是 {high}。",
                        subcaption=f"{temp} < r[{m}] = {visual[m]}，插入点在前半区间，high = m - 1 = {high}。"
                    ) as tracker:
                        self.play(*get_track_anims(IDX_COMPARE), boxes[0].animate.set_color(GREEN), boxes[m].animate.set_color(RED), run_time=0.35)
                        self.play(
                            *get_track_anims(IDX_HIGH),
                            update_var(high_text, f"high = {high}"),
                            pointer_anim("high", "high", high, RED_B, "down"),
                            set_status(f"{temp} < r[{m}]，high 从 {old_high} 收缩到 {high}", RED_B),
                            run_time=0.55
                        )
                        self.wait(max(0.1, tracker.duration - 0.9))
                else:
                    old_low = low
                    low = m + 1
                    if temp == visual[m]:
                        reason = "两个关键字相等。为保持稳定性，新记录放在已有相等记录之后"
                        comparison = "="
                    else:
                        reason = f"{speak_num(temp)} 大于 {speak_num(visual[m])}，插入位置在中点右侧"
                        comparison = ">"
                    with self.voiceover(
                        text=f"{reason}，所以 low 改为 m 加一，也就是 {low}。",
                        subcaption=f"{temp} {comparison} r[{m}] = {visual[m]}。{reason}；low = m + 1 = {low}。"
                    ) as tracker:
                        self.play(*get_track_anims(IDX_COMPARE), boxes[0].animate.set_color(GREEN), boxes[m].animate.set_color(BLUE_B), run_time=0.35)
                        self.play(*get_track_anims(IDX_ELSE), run_time=0.15)
                        self.play(
                            *get_track_anims(IDX_LOW),
                            update_var(low_text, f"low = {low}"),
                            pointer_anim("low", "low", low, BLUE_B, "down"),
                            set_status(f"{temp} >= r[{m}]，low 从 {old_low} 推进到 {low}", BLUE_B),
                            run_time=0.55
                        )
                        self.wait(max(0.1, tracker.duration - 1.05))

            insert_pos = high + 1
            with self.voiceover(
                text=f"当 low 大于 high 时，折半查找结束。按照代码，最终插入位置是 high 加一，也就是 r {insert_pos}。",
                subcaption=f"low = {low} > high = {high}，查找结束。插入位置是 high + 1 = {insert_pos}。"
            ) as tracker:
                insert_marker = SurroundingRectangle(boxes[insert_pos], color=GREEN, buff=0.08, stroke_width=3)
                mid_fade = fade_pointer("mid")
                mid_anims = [mid_fade] if mid_fade is not None else []
                self.play(*get_track_anims(IDX_WHILE), *mid_anims, run_time=0.25)
                self.play(Create(insert_marker), boxes[insert_pos].animate.set_color(GREEN), set_status(f"插入位置：r[{insert_pos}]"), run_time=0.6)
                self.wait(max(0.1, tracker.duration - 0.85))

            if insert_pos <= i - 1:
                with self.voiceover(
                    text=f"接下来将 r {insert_pos} 到 r {i - 1} 的记录全部向后移动一位，给待插入记录腾出空位。",
                    subcaption=f"将 r[{insert_pos}..{i - 1}] 整体后移一位，给 r[0] 腾出空位。"
                ) as tracker:
                    self.play(*get_track_anims(IDX_SHIFT_FOR), set_status(f"后移区间：r[{insert_pos}..{i - 1}]", ORANGE), run_time=0.5)
                    self.wait(max(0.1, tracker.duration - 0.5))
            else:
                with self.voiceover(
                    text="这一次插入位置正好就是当前位置，所以不需要后移记录，只要把监视哨写回当前位置。",
                    subcaption="插入位置正好是当前位置，不需要后移记录。"
                ) as tracker:
                    self.play(*get_track_anims(IDX_SHIFT_FOR), set_status("插入位置不变，无需后移", GREEN), run_time=0.5)
                    self.wait(max(0.1, tracker.duration - 0.5))

            j_ptr_visible = False
            for j in range(i - 1, insert_pos - 1, -1):
                with self.voiceover(
                    text=f"把 r {j} 的值 {speak_num(visual[j])} 向后移动到 r {j + 1}。",
                    subcaption=f"r[{j + 1}] = r[{j}]，也就是把 {visual[j]} 后移一位。"
                ) as tracker:
                    anims = [
                        *get_track_anims(IDX_SHIFT),
                        boxes[j].animate.set_color(ORANGE).set_fill(ORANGE, opacity=0.25),
                        boxes[j + 1].animate.set_color(ORANGE).set_fill(ORANGE, opacity=0.18),
                        pointer_anim("j", "j", j, ORANGE, "up", 0.0),
                    ]
                    if not j_ptr_visible:
                        j_ptr_visible = True
                    self.play(*anims, update_var(mid_text, f"m = -"), run_time=0.55)
                    moved_value = visual[j]
                    self.play(update_cell(j + 1, moved_value, ORANGE), run_time=0.45)
                    visual[j + 1] = moved_value
                    self.wait(max(0.1, tracker.duration - 1.0))

            with self.voiceover(
                text=f"最后把监视哨 r 零中的 {speak_num(temp)} 写入 r {insert_pos}。这一轮结束后，r 一到 r {i} 都已经有序。",
                subcaption=f"最后把 r[0] = {temp} 写入 r[{insert_pos}]。本轮结束后，r[1..{i}] 有序。"
            ) as tracker:
                self.play(*get_track_anims(IDX_INSERT), update_cell(insert_pos, temp, GREEN), run_time=0.65)
                visual[insert_pos] = temp
                cleanup = [anim for anim in [FadeOut(insert_marker), fade_pointer("j")] if anim is not None]
                self.play(
                    *cleanup,
                    set_status(f"插入完成：r[1..{i}] 有序", GREEN),
                    *reset_box_colors(i),
                    *update_ordered_brace(i),
                    run_time=0.7
                )
                self.wait(max(0.1, tracker.duration - 1.35))

        # ===== PHASE E: RESULT AND COMPLEXITY =====
        self.play(
            *get_track_anims(None),
            *[anim for anim in [fade_pointer("i"), fade_pointer("low"), fade_pointer("high"), fade_pointer("mid"), fade_pointer("j")] if anim is not None],
            run_time=0.5
        )

        with self.voiceover(
            text="循环结束后，整个 r 一到 r n 都成为有序序列。排序结果是零四、十三、二十七、三十八、四十九、四十九、五十五、六十五、七十六、九十七。",
            subcaption="循环结束后，整个 r[1..n] 都成为有序序列。排序结果是 04、13、27、38、49、49、55、65、76、97。"
        ) as tracker:
            result_text = Text("排序结果：04  13  27  38  49  49  55  65  76  97", font_size=23, font="Microsoft YaHei", color=GREEN).move_to(LEFT * 3.1 + DOWN * 1.02)
            self.play(Transform(status, result_text), *reset_box_colors(n), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        compare_box = VGroup(
            Text("查找位置：折半查找，比较次数更少", font_size=20, font="Microsoft YaHei", color=YELLOW),
        )
        move_box = VGroup(
            Text("移动记录：仍要顺序后移，移动次数没有减少", font_size=20, font="Microsoft YaHei", color=ORANGE),
        )
        time_box = VGroup(
            Text("时间复杂度：O(n²)", font_size=22, font="Microsoft YaHei", color=YELLOW),
        )
        space_box = VGroup(
            Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
            Text("O(1)", font_size=26, font="Consolas", color=YELLOW),
        ).arrange(RIGHT, buff=0.12)
        stable_box = VGroup(
            Text("稳定性：", font_size=22, font="Microsoft YaHei", color=YELLOW),
            Text("稳定", font_size=22, font="Microsoft YaHei", color=GREEN),
        ).arrange(RIGHT, buff=0.12)
        summary = VGroup(compare_box, move_box, time_box, space_box, stable_box).arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to(LEFT * 3.05 + DOWN * 1.6)

        self.play(FadeOut(var_panel), FadeOut(status), run_time=0.3)

        caption = "折半插入排序的改进点，在于查找插入位置。它用折半查找替代顺序查找，所以平均来说，关键字比较次数会减少。"
        with self.voiceover(text=caption, subcaption=caption) as tracker:
            self.play(FadeIn(compare_box), run_time=0.7)
            self.wait(max(0.1, tracker.duration - 0.7))

        caption = "但是，找到位置以后，记录仍然要一个一个向后移动。也就是说，折半只减少比较次数，并没有减少移动次数。"
        with self.voiceover(text=caption, subcaption=caption) as tracker:
            self.play(FadeIn(move_box), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        caption = "因此，在平均情况下，折半插入排序通常比直接插入排序少做一些比较，但整体运行时间仍然受记录移动影响，时间复杂度仍为 O n 平方。"
        with self.voiceover(text=caption, subcaption=caption) as tracker:
            self.play(FadeIn(time_box), run_time=0.7)
            self.wait(max(0.1, tracker.duration - 0.7))

        with self.voiceover(
            text="空间方面，算法只使用监视哨和少量变量，所以空间复杂度是 O 一。相等关键字会插到已有相等元素之后，因此折半插入排序是稳定排序。",
            subcaption="空间复杂度为 O(1)。相等关键字会插到已有相等元素之后，因此折半插入排序稳定。"
        ) as tracker:
            self.play(FadeIn(space_box), FadeIn(stable_box), run_time=0.7)
            self.wait(max(0.1, tracker.duration - 0.7))

        self.wait(2)
