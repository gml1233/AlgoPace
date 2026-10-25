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


class SelectionSortVideo(SortingNarrationMixin, VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz")
        )

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(1.0).to_corner(UR, buff=0.04)
        self.add(logo)

        def narrate(caption):
            return self.voiceover(text=caption, subcaption=caption)

        def speak(caption, *animations, run_time=0.8):
            animations = [animation for animation in animations if animation is not None]
            with narrate(caption) as tracker:
                if animations:
                    self.play(*animations, run_time=run_time)
                else:
                    self.wait(run_time)
                self.wait(max(0.1, tracker.duration - run_time))

        title = Text("简单选择排序", font_size=44, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.34)
        self.play(FadeIn(title), run_time=0.7)

        speak(
            "本节学习简单选择排序。该算法是每一趟从待排序的记录中选出关键字最小的记录，按顺序将其放在已排好序的记录序列的最后，直到全部排完为止。"
        )

        # ===== PHASE A: LIFE EXAMPLE =====
        life_title = Text("生活实例：挑最小编号图书", font_size=30, font="Microsoft YaHei", color=YELLOW).to_edge(UP, buff=1.05)
        shelf = Line(LEFT * 4.5 + DOWN * 1.05, RIGHT * 4.5 + DOWN * 1.05, color=GRAY_B, stroke_width=5)
        book_values = [49, 38, 65, 97, 76, 13, 27]
        book_group = VGroup()
        for value in book_values:
            book = RoundedRectangle(
                corner_radius=0.06, width=0.78, height=1.18,
                color=BLUE, fill_color=BLUE, fill_opacity=0.18, stroke_width=2.2
            )
            label = Text(str(value), font_size=24, font="Consolas", color=WHITE).move_to(book)
            book_group.add(VGroup(book, label))
        book_group.arrange(RIGHT, buff=0.22).move_to(DOWN * 0.1)
        # 将生活实例状态文案上移，给底部语音字幕留出独立空间。
        life_status = Text("先从所有书里挑编号最小的一本，放到最左侧", font_size=22, font="Microsoft YaHei", color=GREEN).to_edge(DOWN, buff=1.35)

        speak(
            "先看一个生活实例。整理一排编号图书时，可以先不急着全部排序，而是先从所有图书中挑出编号最小的一本。",
            FadeIn(life_title),
            FadeIn(shelf),
            FadeIn(book_group),
            FadeIn(life_status),
            run_time=1.0,
        )
        first_scan = SurroundingRectangle(VGroup(*book_group), color=YELLOW, buff=0.12, stroke_width=3)
        speak(
            "第一轮查看整排图书。扫描后发现最小编号是十三，于是准备把它放到第一个位置。",
            Create(first_scan),
            book_group[5][0].animate.set_color(YELLOW).set_fill(YELLOW, opacity=0.25),
            book_group[0][0].animate.set_color(ORANGE).set_fill(ORANGE, opacity=0.18),
            Transform(life_status, Text("第一轮：找到 13，与最左侧 49 交换", font_size=22, font="Microsoft YaHei", color=YELLOW).to_edge(DOWN, buff=1.35)),
            run_time=1.0,
        )
        book_group[0].generate_target()
        book_group[5].generate_target()
        book_group[0].target.move_to(book_group[5].get_center())
        book_group[5].target.move_to(book_group[0].get_center())
        book_group[0], book_group[5] = book_group[5], book_group[0]
        speak(
            "交换后，第一个位置已经确定。接下来只看剩余图书，再挑出其中最小的一本。",
            MoveToTarget(book_group[5]),
            MoveToTarget(book_group[0]),
            FadeOut(first_scan),
            book_group[0][0].animate.set_color(GREEN).set_fill(GREEN, opacity=0.22),
            Transform(life_status, Text("第一个位置确定，继续处理剩余图书", font_size=22, font="Microsoft YaHei", color=GREEN).to_edge(DOWN, buff=1.35)),
            run_time=1.0,
        )
        second_scan = SurroundingRectangle(VGroup(*book_group[1:]), color=YELLOW, buff=0.12, stroke_width=3)
        speak(
            "第二轮从剩余部分开始。此时剩下的最小编号是二十七，把它和第二个位置的三十八交换。",
            Create(second_scan),
            book_group[6][0].animate.set_color(YELLOW).set_fill(YELLOW, opacity=0.25),
            book_group[1][0].animate.set_color(ORANGE).set_fill(ORANGE, opacity=0.18),
            Transform(life_status, Text("第二轮：找到 27，与第二个位置 38 交换", font_size=22, font="Microsoft YaHei", color=YELLOW).to_edge(DOWN, buff=1.35)),
            run_time=1.0,
        )
        book_group[1].generate_target()
        book_group[6].generate_target()
        book_group[1].target.move_to(book_group[6].get_center())
        book_group[6].target.move_to(book_group[1].get_center())
        book_group[1], book_group[6] = book_group[6], book_group[1]
        speak(
            "这样，前两个位置都确定了。选择排序就是不断重复：在剩余部分中选择最小者，放到当前最前面。",
            MoveToTarget(book_group[6]),
            MoveToTarget(book_group[1]),
            FadeOut(second_scan),
            book_group[1][0].animate.set_color(GREEN).set_fill(GREEN, opacity=0.22),
            Transform(life_status, Text("重复选择最小者，逐步扩大已排好区域", font_size=22, font="Microsoft YaHei", color=GREEN).to_edge(DOWN, buff=1.35)),
            run_time=1.0,
        )
        self.play(FadeOut(VGroup(life_title, shelf, book_group, life_status)), run_time=0.7)

        # ===== PHASE B: ALGORITHM STEPS =====
        step_title = Text("算法步骤与思想", font_size=34, font="Microsoft YaHei", color=YELLOW).to_edge(UP, buff=1.25)
        steps = VGroup(
            Text("1. 第 i 趟从 r[i..n] 中寻找关键字最小的记录", font_size=24, font="Microsoft YaHei"),
            Text("2. 用 k 记录本趟最小记录的位置", font_size=24, font="Microsoft YaHei"),
            Text("3. 若 k != i，则交换 r[i] 与 r[k]", font_size=24, font="Microsoft YaHei"),
            Text("4. 每趟确定一个最终位置，共进行 n-1 趟", font_size=24, font="Microsoft YaHei"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        steps.next_to(step_title, DOWN, buff=0.42)

        speak(
            "回到算法本身。当前这一轮只处理未排序区 r i 到 r n，在这段范围里找到最小关键字，并用 k 保存它的位置。",
            FadeIn(step_title),
            LaggedStart(*[FadeIn(item, shift=RIGHT * 0.18) for item in steps[:2]], lag_ratio=0.18),
            run_time=1.1,
        )
        speak(
            "如果最小记录不在当前位置，就交换 r i 和 r k。交换后，r i 的位置确定，下一趟从 r i 加一 开始。",
            LaggedStart(*[FadeIn(item, shift=RIGHT * 0.18) for item in steps[2:]], lag_ratio=0.18),
            run_time=1.0,
        )
        self.play(FadeOut(VGroup(step_title, steps)), run_time=0.6)

        # ===== PHASE C: CODE PANEL =====
        code_lines = [
            "void SelectSort(SqList &L) {",
            "    int i, j, k;",
            "    ElemType t;",
            "    for (i = 1; i < L.length; ++i) {",
            "        k = i;",
            "        for (j = i + 1; j <= L.length; ++j)",
            "            if (L.r[j].key < L.r[k].key)",
            "                k = j;",
            "        if (k != i) {",
            "            t = L.r[i];",
            "            L.r[i] = L.r[k];",
            "            L.r[k] = t;",
            "        }",
            "    }",
            "}",
        ]

        code_texts = []
        for line in code_lines:
            item = Text(line.lstrip(" "), font_size=11.5, font="Consolas", color=WHITE)
            code_texts.append(item)
        code_group = VGroup(*code_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.095)
        space_width = 0.083
        for index, line in enumerate(code_lines):
            indent = len(line) - len(line.lstrip(" "))
            code_texts[index].shift(RIGHT * indent * space_width)

        code_bg = RoundedRectangle(
            corner_radius=0.14,
            width=code_group.get_width() + 0.48,
            height=code_group.get_height() + 0.42,
            color=GRAY_B,
            fill_color=BLACK,
            fill_opacity=0.35,
            stroke_width=1,
        ).move_to(code_group)
        code_block = VGroup(code_bg, code_group).to_edge(RIGHT, buff=0.18).shift(UP * 0.08)
        fit_code_block(code_block)

        current_line = {"index": None, "pointer": None}

        def highlight_line(index):
            anims = []
            old = current_line["index"]
            if old is not None and old != index:
                anims.append(code_texts[old].animate.set_color(WHITE))
            if index is not None:
                if old != index:
                    anims.append(code_texts[index].animate.set_color(YELLOW))
                if current_line["pointer"] is None:
                    pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.12).rotate(-PI / 2)
                    pointer.next_to(code_texts[index], LEFT, buff=0.14)
                    current_line["pointer"] = pointer
                    anims.append(FadeIn(pointer))
                else:
                    pointer = current_line["pointer"]
                    pointer.generate_target()
                    pointer.target.next_to(code_texts[index], LEFT, buff=0.14)
                    anims.append(MoveToTarget(pointer))
                current_line["index"] = index
            else:
                if current_line["pointer"] is not None:
                    anims.append(FadeOut(current_line["pointer"]))
                    current_line["pointer"] = None
                current_line["index"] = None
            return anims

        def display(value):
            return "04" if value == 4 else str(value)

        values = [49, 38, 65, 97, 76, 13, 27, 49, 55, 4]
        visual = [None] + values[:]
        n = len(values)
        box_side = 0.58
        boxes = [None]
        nums = [None]
        labels = VGroup()
        row_items = VGroup()
        for index in range(1, n + 1):
            box = Square(side_length=box_side, color=BLUE, stroke_width=2)
            num = Text(display(visual[index]), font_size=21, font="Arial", color=WHITE).move_to(box)
            item = VGroup(box, num)
            boxes.append(box)
            nums.append(num)
            row_items.add(item)
            labels.add(Text(f"r[{index}]", font_size=13, font="Consolas", color=GRAY_B))
        row_items.arrange(RIGHT, buff=0)
        row_items.move_to(LEFT * 3.05 + UP * 0.8)
        for index in range(1, n + 1):
            labels[index - 1].next_to(boxes[index], DOWN, buff=0.08)
        table = VGroup(row_items, labels)

        status = Text("示例顺序表：从未排序区中反复选择最小记录", font_size=21, font="Microsoft YaHei", color=YELLOW)
        status.move_to(LEFT * 3.05 + DOWN * 0.38)
        vars_panel = VGroup(
            Text("i = -", font_size=19, font="Consolas", color=ORANGE),
            Text("j = -", font_size=19, font="Consolas", color=YELLOW),
            Text("k = -", font_size=19, font="Consolas", color=GREEN),
        ).arrange(RIGHT, buff=0.38).move_to(LEFT * 3.05 + DOWN * 1.18)
        i_text, j_text, k_text = vars_panel

        def set_status(text, color=YELLOW, size=21):
            return Transform(status, Text(text, font_size=size, font="Microsoft YaHei", color=color).move_to(status))

        def update_var(text_mob, content):
            # Text 容器本身可能是黑色；从实际字形读取颜色，避免更新后消失。
            return Transform(text_mob, Text(content, font_size=19, font="Consolas", color=text_mob[0].get_color()).move_to(text_mob))

        def reset_colors(sorted_to=0):
            anims = []
            for index in range(1, n + 1):
                if index <= sorted_to:
                    anims.append(boxes[index].animate.set_color(GREEN).set_fill(GREEN, opacity=0.13))
                else:
                    anims.append(boxes[index].animate.set_color(BLUE).set_fill(BLACK, opacity=0))
            return anims

        def swap_cells(a, b):
            nums[a].generate_target()
            nums[b].generate_target()
            nums[a].target.move_to(boxes[b].get_center())
            nums[b].target.move_to(boxes[a].get_center())
            old_a, old_b = nums[a], nums[b]
            visual[a], visual[b] = visual[b], visual[a]
            nums[a], nums[b] = old_b, old_a
            return MoveToTarget(old_a), MoveToTarget(old_b)

        speak(
            "右侧是选择排序的核心代码。重点观察三层含义：外层 i 控制趟数，内层 j 扫描未排序区，k 保存当前最小记录的位置。",
            FadeIn(code_block),
            FadeIn(table),
            FadeIn(status),
            FadeIn(vars_panel),
            run_time=1.0,
        )

        max_detailed_passes = 2
        for i in range(1, n):
            if i > max_detailed_passes:
                temp = visual[:]
                for ii in range(i, n):
                    k = ii
                    for jj in range(ii + 1, n + 1):
                        if temp[jj] < temp[k]:
                            k = jj
                    if k != ii:
                        temp[ii], temp[k] = temp[k], temp[ii]
                quick_anims = []
                for index in range(1, n + 1):
                    visual[index] = temp[index]
                    quick_anims.append(Transform(nums[index], Text(display(temp[index]), font_size=21, font="Arial", color=WHITE).move_to(boxes[index])))
                    quick_anims.append(boxes[index].animate.set_color(GREEN).set_fill(GREEN, opacity=0.13))
                speak(
                    "前两趟已经展示了完整规则。后续各趟仍然重复寻找最小记录、必要时交换的过程，这里直接快进到排序完成。",
                    *highlight_line(3),
                    *quick_anims,
                    set_status("后续各趟同理，快进到最终有序序列", GREEN, size=20),
                    run_time=1.2,
                )
                break

            speak(
                f"第 {i} 趟开始。外层 for 让 i 等于 {i}，本趟要在 r {i} 到 r {n} 中寻找最小记录。",
                *highlight_line(3),
                update_var(i_text, f"i = {i}"),
                *reset_colors(i - 1),
                set_status(f"第 {i} 趟：在 r[{i}..{n}] 中选择最小记录", YELLOW, size=20),
                run_time=0.85,
            )

            k = i
            speak(
                f"先执行 k 等于 i，所以当前暂时认为 r {i} 中的 {display(visual[i])} 是本趟最小记录。",
                *highlight_line(4),
                update_var(k_text, f"k = {k}"),
                boxes[k].animate.set_color(GREEN).set_fill(GREEN, opacity=0.18),
                set_status(f"当前最小位置 k = {k}", GREEN),
                run_time=0.85,
            )

            for j in range(i + 1, n + 1):
                speak(
                    f"内层 for 让 j 等于 {j}，比较 r {j} 的 {display(visual[j])} 和当前最小 r {k} 的 {display(visual[k])}。",
                    *highlight_line(5),
                    update_var(j_text, f"j = {j}"),
                    *reset_colors(i - 1),
                    boxes[j].animate.set_color(YELLOW).set_fill(YELLOW, opacity=0.18),
                    boxes[k].animate.set_color(GREEN).set_fill(GREEN, opacity=0.18),
                    run_time=0.75,
                )
                if visual[j] < visual[k]:
                    k = j
                    speak(
                        f"{display(visual[j])} 更小，条件成立，更新 k 为 {k}。",
                        *highlight_line(6),
                        *highlight_line(7),
                        update_var(k_text, f"k = {k}"),
                        boxes[j].animate.set_color(GREEN).set_fill(GREEN, opacity=0.24),
                        set_status(f"发现新的最小记录：r[{k}] = {display(visual[k])}", GREEN, size=20),
                        run_time=0.85,
                    )
                else:
                    speak(
                        f"{display(visual[j])} 不小于 {display(visual[k])}，k 不变。",
                        *highlight_line(6),
                        set_status("当前记录不是更小值，继续向后扫描", BLUE_B, size=20),
                        run_time=0.55,
                    )

            if k != i:
                old_i, old_k = visual[i], visual[k]
                speak(
                    f"内层扫描结束，最小记录在 r {k}。因为 k 不等于 i，所以交换 r {i} 和 r {k}。",
                    *highlight_line(8),
                    boxes[i].animate.set_color(ORANGE).set_fill(ORANGE, opacity=0.18),
                    boxes[k].animate.set_color(ORANGE).set_fill(ORANGE, opacity=0.18),
                    set_status(f"交换 r[{i}]={display(old_i)} 与 r[{k}]={display(old_k)}", ORANGE, size=20),
                    run_time=0.85,
                )
                speak(
                    f"交换完成，r {i} 的位置确定为 {display(old_k)}。",
                    *highlight_line(9),
                    *highlight_line(10),
                    *highlight_line(11),
                    *swap_cells(i, k),
                    boxes[i].animate.set_color(GREEN).set_fill(GREEN, opacity=0.15),
                    set_status(f"r[{i}] 已确定", GREEN),
                    run_time=1.0,
                )
            else:
                speak(
                    f"本趟最小记录已经在 r {i}，不需要交换。",
                    *highlight_line(8),
                    boxes[i].animate.set_color(GREEN).set_fill(GREEN, opacity=0.15),
                    set_status(f"r[{i}] 已确定，无需交换", GREEN, size=20),
                    run_time=0.8,
                )

        final_values = [4, 13, 27, 38, 49, 49, 55, 65, 76, 97]
        if visual[1:] != final_values:
            final_anims = []
            for index, value in enumerate(final_values, start=1):
                visual[index] = value
                final_anims.append(Transform(nums[index], Text(display(value), font_size=21, font="Arial", color=WHITE).move_to(boxes[index])))
                final_anims.append(boxes[index].animate.set_color(GREEN).set_fill(GREEN, opacity=0.13))
            self.play(*final_anims, run_time=0.8)

        speak(
            "经过 n 减一 趟选择，顺序表按关键字从小到大排列完成。",
            *highlight_line(None),
            FadeOut(vars_panel),
            *reset_colors(n),
            set_status("排序完成", GREEN),
            run_time=0.8,
        )

        # ===== PHASE D: COMPLEXITY AND STABILITY =====
        complexity_title = Text("时空复杂度与稳定性", font_size=34, font="Microsoft YaHei", color=YELLOW)
        complexity_rows = VGroup(
            Text("移动次数较少：最好不移动，最坏约 3(n-1)", font_size=23, font="Microsoft YaHei", color=GREEN),
            Text("比较次数与初始状态无关，约为 n²/2", font_size=23, font="Microsoft YaHei", color=YELLOW),
            Text("时间复杂度：O(n²)；空间复杂度：O(1)", font_size=23, font="Microsoft YaHei", color=BLUE),
            Text("稳定性：方法可稳定，交换实现不稳定", font_size=23, font="Microsoft YaHei", color=ORANGE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
        complexity_panel = VGroup(complexity_title, complexity_rows).arrange(DOWN, buff=0.42).move_to(ORIGIN + DOWN * 0.05)

        speak(
            "最后看时空复杂度。简单选择排序的记录移动次数比较少。正序时最小记录已经在当前位置，不需要移动；逆序时，每趟至多交换一次。",
            FadeOut(code_block),
            FadeOut(table),
            FadeOut(status),
            FadeIn(complexity_title),
            FadeIn(complexity_rows[0], shift=RIGHT * 0.25),
            run_time=1.0,
        )
        speak(
            "但比较次数不会因为初始序列有序而减少。每一趟都要扫描未排序区寻找最小关键字，总比较次数约为 n 平方的一半。",
            FadeIn(complexity_rows[1], shift=RIGHT * 0.25),
            run_time=1.0,
        )
        speak(
            "因此，简单选择排序的时间复杂度为 O n 平方。算法只使用 i、j、k 和临时变量 t，空间复杂度为 O 一。",
            FadeIn(complexity_rows[2], shift=RIGHT * 0.25),
            run_time=0.9,
        )
        speak(
            "稳定性要分开看。选择排序方法本身可以设计成稳定的；但本代码采用直接交换记录的策略，可能改变相等关键字的相对次序，所以这个实现是不稳定的。",
            FadeIn(complexity_rows[3], shift=RIGHT * 0.25),
            run_time=1.0,
        )

        self.wait(1.2)
