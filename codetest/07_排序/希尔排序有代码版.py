# coding=utf-8
from manim import *
from codetest.sorting_support import SortingNarrationMixin, fit_code_block
import warnings

warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*",
    category=UserWarning,
)

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


class ShellSortCodeVideo(SortingNarrationMixin, VoiceoverScene):
    GROUP_COLORS = [RED_B, BLUE_B, GREEN_B, ORANGE, PURPLE_B]

    def construct(self):
        self.set_speech_service(
            EdgeTTSService(
                voice="zh-CN-YunxiNeural",
                rate="+0%",
                volume="+0%",
                pitch="+0Hz",
            )
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

        opening = (
            "本视频重点讲解希尔排序算法的代码实现与逐行运行跟踪，"
            "如尚未掌握该算法的设计思路，建议首先观看学习该算法的无代码跟踪版讲解视频。"
        )
        with narrate(opening) as tracker:
            self.wait(tracker.duration)

        title = Text("希尔排序代码讲解版", font_size=38, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.24)
        self.play(FadeIn(title), run_time=0.7)

        def make_code_block(lines, font_size=11):
            code_texts = []
            for line in lines:
                item = Text(line.lstrip(" "), font_size=font_size, font="Consolas", color=WHITE)
                code_texts.append(item)
            code_group = VGroup(*code_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.095)
            for index, line in enumerate(lines):
                indent = len(line) - len(line.lstrip(" "))
                code_texts[index].shift(RIGHT * indent * 0.085)
            code_bg = RoundedRectangle(
                corner_radius=0.18,
                height=code_group.height + 0.45,
                width=code_group.width + 0.56,
                color=GRAY,
                fill_color=BLACK,
                fill_opacity=0.35,
                stroke_width=1,
            ).move_to(code_group)
            block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.12).to_edge(RIGHT, buff=0.18)
            fit_code_block(block)
            return block, code_bg, code_texts

        tracker_state = {"line": None, "pointer": None, "texts": None}

        def bind_code(texts, bg):
            tracker_state["line"] = None
            tracker_state["pointer"] = None
            tracker_state["texts"] = texts

        def track_line(new_index):
            texts = tracker_state["texts"]
            old_index = tracker_state["line"]
            if new_index == old_index:
                return []
            anims = []
            if old_index is not None:
                anims.append(texts[old_index].animate.set_color(WHITE))
            if new_index is None:
                if tracker_state["pointer"] is not None:
                    anims.append(FadeOut(tracker_state["pointer"]))
                    tracker_state["pointer"] = None
                tracker_state["line"] = None
                return anims

            anims.append(texts[new_index].animate.set_color(YELLOW))
            if tracker_state["pointer"] is None:
                pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.13).rotate(-PI / 2)
                pointer.next_to(texts[new_index], LEFT, buff=0.15)
                tracker_state["pointer"] = pointer
                anims.append(FadeIn(pointer))
            else:
                pointer = tracker_state["pointer"]
                pointer.generate_target()
                pointer.target.next_to(texts[new_index], LEFT, buff=0.15)
                anims.append(MoveToTarget(pointer))

            tracker_state["line"] = new_index
            return anims

        shell_lines = [
            "void ShellInsert(SqList &L, int dk) {",
            "    int i, j;",
            "    for (i = dk + 1; i <= L.length; ++i) {",
            "        if (L.r[i].key < L.r[i - dk].key) {",
            "            L.r[0] = L.r[i];",
            "            for (j = i - dk;",
            "                 j > 0 && L.r[0].key < L.r[j].key;",
            "                 j -= dk)",
            "                L.r[j + dk] = L.r[j];",
            "            L.r[j + dk] = L.r[0];",
            "        }",
            "    }",
            "}",
        ]
        code_block, code_bg, code_texts = make_code_block(shell_lines)
        bind_code(code_texts, code_bg)

        speak(
            "这次我们只保留希尔排序的核心代码。ShellSort 负责按增量序列反复调用 ShellInsert，真正的移动和插入都发生在 ShellInsert 中。",
            FadeIn(code_block),
            run_time=0.9,
        )

        values = [None, 49, 38, 65, 97, 76, 13, 27, 49, 55, 4]
        display_values = [None, "49", "38", "65", "97", "76", "13", "27", "49", "55", "04"]
        n = 10
        box_side = 0.52
        boxes = [None] * (n + 1)
        value_texts = [None] * (n + 1)
        box_group = VGroup()
        index_group = VGroup()
        for index in range(n + 1):
            box = Square(side_length=box_side, color=GREEN if index == 0 else BLUE, stroke_width=2)
            if index > 0:
                box.next_to(box_group[-1], RIGHT, buff=0.02)
            boxes[index] = box
            box_group.add(box)
            index_group.add(Text(f"r[{index}]", font_size=12, font="Consolas", color=GRAY_B).next_to(box, DOWN, buff=0.08))
        box_group.move_to(LEFT * 3.05 + UP * 0.58)
        for index in range(n + 1):
            index_group[index].next_to(boxes[index], DOWN, buff=0.08)
            label = "-" if display_values[index] is None else display_values[index]
            value_texts[index] = Text(label, font_size=18, font="Arial", color=GREEN if index == 0 else WHITE)
            value_texts[index].move_to(boxes[index].get_center())

        array_label = Text("示例数据：49, 38, 65, 97, 76, 13, 27, 49, 55, 04", font_size=18, font="Microsoft YaHei", color=YELLOW)
        array_label.next_to(box_group, UP, buff=0.24)
        status = Text("准备按增量序列 5, 3, 1 演示", font_size=21, font="Microsoft YaHei", color=YELLOW)
        status.move_to(LEFT * 3.05 + DOWN * 1.12)
        vars_panel = VGroup(
            Text("dk = -", font_size=18, font="Consolas", color=PURPLE_B),
            Text("i = -", font_size=18, font="Consolas", color=YELLOW),
            Text("j = -", font_size=18, font="Consolas", color=ORANGE),
            Text("r[0] = -", font_size=18, font="Consolas", color=GREEN),
        ).arrange(RIGHT, buff=0.34).move_to(LEFT * 3.05 + DOWN * 1.75)
        dk_text, i_text, j_text, guard_text = vars_panel
        tip = Text("本版只演示代表性几趟，帮助理解代码如何推动数据变化", font_size=17, font="Microsoft YaHei", color=BLUE_B)
        tip.move_to(LEFT * 3.05 + DOWN * 2.2)
        array_group = VGroup(box_group, index_group, *value_texts, array_label, status, vars_panel, tip)

        speak(
            "示例数据换成十个记录。最后一个写作零四，它的数值就是四，排序时会排到最前面。",
            FadeIn(array_group),
            run_time=0.9,
        )

        def set_status(content, color=YELLOW, size=21):
            return Transform(status, Text(content, font_size=size, font="Microsoft YaHei", color=color).move_to(status))

        def set_tip(content, color=BLUE_B):
            return Transform(tip, Text(content, font_size=17, font="Microsoft YaHei", color=color).move_to(tip))

        def update_var(text_mob, content):
            # Text 容器本身可能是黑色；从实际字形读取颜色，避免更新后消失。
            return Transform(text_mob, Text(content, font_size=18, font="Consolas", color=text_mob[0].get_color()).move_to(text_mob))

        def update_cell(index, value, display=None, color=None):
            values[index] = value
            if display is None:
                display = "-" if value is None else ("04" if value == 4 else str(value))
            display_values[index] = display
            new_text = Text(display, font_size=18, font="Arial", color=color or (GREEN if index == 0 else WHITE))
            new_text.move_to(boxes[index].get_center())
            old_text = value_texts[index]
            value_texts[index] = new_text
            return ReplacementTransform(old_text, new_text)

        def set_all_values(new_values):
            anims = []
            for index, value in enumerate(new_values, start=1):
                if values[index] != value:
                    anims.append(update_cell(index, value))
            return anims

        def reset_colors(active=None, color=BLUE_B):
            active = set(active or [])
            anims = []
            for index in range(n + 1):
                if index == 0:
                    anims.append(boxes[index].animate.set_color(GREEN).set_fill(BLACK, opacity=0))
                elif index in active:
                    anims.append(boxes[index].animate.set_color(color).set_fill(color, opacity=0.14))
                else:
                    anims.append(boxes[index].animate.set_color(BLUE).set_fill(BLACK, opacity=0))
            return anims

        def color_group(indices, color):
            return [boxes[index].animate.set_color(color).set_fill(color, opacity=0.16) for index in indices]

        def make_pointer(label, index, color, direction="up"):
            target = boxes[max(0, min(n, index))]
            if direction == "up":
                arrow = Arrow(
                    target.get_top() + UP * 0.44,
                    target.get_top() + UP * 0.03,
                    buff=0.04,
                    color=color,
                    stroke_width=3.2,
                    tip_length=0.13,
                )
                text = Text(label, font_size=15, font="Consolas", color=color).next_to(arrow, UP, buff=0.02)
            else:
                arrow = Arrow(
                    target.get_bottom() + DOWN * 0.44,
                    target.get_bottom() + DOWN * 0.03,
                    buff=0.04,
                    color=color,
                    stroke_width=3.2,
                    tip_length=0.13,
                )
                text = Text(label, font_size=15, font="Consolas", color=color).next_to(arrow, DOWN, buff=0.02)
            return VGroup(arrow, text)

        pointers = {}

        def pointer_anim(name, label, index, color, direction="up"):
            new_pointer = make_pointer(label, index, color, direction)
            if name not in pointers:
                pointers[name] = new_pointer
                return FadeIn(new_pointer)
            old_pointer = pointers[name]
            pointers[name] = new_pointer
            return ReplacementTransform(old_pointer, new_pointer)

        def fade_pointer(name):
            if name in pointers:
                pointer = pointers.pop(name)
                return FadeOut(pointer)
            return None

        speak(
            "先看 ShellSort 的外层循环。它每次取一个 dt[k]，然后把这个增量传给 ShellInsert。因此 dt 等于五、三、一时，ShellInsert 会被调用三次。",
            *track_line(0),
            set_tip("dt = [5, 3, 1]，每个增量对应一次 ShellInsert 调用", GREEN),
            run_time=0.9,
        )

        # ===== dk = 5：用成对分组说明“远距离先移动” =====
        speak(
            "第一趟令 dk 等于五。for 语句从 i 等于 dk 加一开始，也就是从 r[6] 开始检查。",
            *track_line(2),
            update_var(dk_text, "dk = 5"),
            update_var(i_text, "i = 6"),
            pointer_anim("i", "i", 6, YELLOW, "up"),
            set_status("第 1 趟：dk = 5", YELLOW),
            run_time=0.8,
        )
        groups_5 = [[1, 6], [2, 7], [3, 8], [4, 9], [5, 10]]
        for group_index, group in enumerate(groups_5):
            color = self.GROUP_COLORS[group_index % len(self.GROUP_COLORS)]
            speak(
                "当 dk 等于五时，下标相差五的两个记录为一组。例如 "
                + " 和 ".join(f"r[{index}]" for index in group)
                + " 属于同一组。",
                *color_group(group, color),
                set_tip("同组下标相差 dk，只在组内做插入排序", color),
                run_time=0.45,
            )

        speak(
            "用其中一组看代码执行。r[6] 是十三，r[1] 是四十九，十三小于四十九，所以 if 条件成立。",
            *track_line(3),
            *reset_colors([1, 6], RED_B),
            pointer_anim("i", "i", 6, YELLOW, "up"),
            update_var(i_text, "i = 6"),
            set_status("13 < 49，进入 if", RED_B),
            run_time=0.85,
        )
        speak(
            "进入 if 后，先把 r[6] 暂存到 r[0]。接着 j 等于 i 减 dk，也就是一，指向同组前一个记录。",
            *track_line(4),
            update_cell(0, 13),
            update_var(guard_text, "r[0] = 13"),
            *track_line(5),
            update_var(j_text, "j = 1"),
            pointer_anim("j", "j", 1, ORANGE, "down"),
            run_time=0.9,
        )
        speak(
            "判断内层 for 条件：j 大于零，并且 r[0] 的十三小于 r[1] 的四十九，所以执行后移。",
            *track_line(6),
            boxes[1].animate.set_color(ORANGE).set_fill(ORANGE, opacity=0.2),
            set_status("13 < 49，r[1] 后移到 r[6]", ORANGE),
            run_time=0.8,
        )
        speak(
            "执行 L.r[j + dk] 等于 L.r[j]，也就是把四十九移到 r[6]；随后把 r[0] 中的十三放回 r[1]。",
            *track_line(8),
            update_cell(6, 49),
            *track_line(9),
            update_cell(1, 13),
            set_status("第一组插入完成：13 提前，49 后移", GREEN),
            run_time=0.9,
        )
        speak(
            "同理，第一趟会继续处理后面的四个二元组。这里不逐项展开，只展示这一趟结束后的整体效果。",
            *track_line(2),
            *set_all_values([13, 27, 49, 55, 4, 49, 38, 65, 97, 76]),
            *reset_colors(),
            set_status("dk = 5 结束：远距离的小记录被提前", GREEN, size=19),
            run_time=0.9,
        )

        # ===== dk = 3：展示一组多元素插入 =====
        speak(
            "第二趟把增量缩小为三。此时每一组的数据量变多，例如 r[1]、r[4]、r[7]、r[10] 属于同一组。",
            *track_line(0),
            update_var(dk_text, "dk = 3"),
            *reset_colors([1, 4, 7, 10], BLUE_B),
            set_tip("增量变小后，每组包含更多记录，组内更接近直接插入排序", BLUE_B),
            run_time=0.9,
        )
        speak(
            "看一个代表性插入：在这组中，r[7] 是三十八，前一个同组位置 r[4] 是五十五，三十八更小，所以 if 条件成立。",
            *track_line(3),
            pointer_anim("i", "i", 7, YELLOW, "up"),
            update_var(i_text, "i = 7"),
            boxes[7].animate.set_color(RED).set_fill(RED, opacity=0.18),
            boxes[4].animate.set_color(RED).set_fill(RED, opacity=0.18),
            set_status("38 < 55，进入 if", RED_B),
            run_time=0.9,
        )
        speak(
            "暂存三十八以后，内层 for 发现三十八小于五十五，于是把五十五从 r[4] 后移到 r[7]。",
            *track_line(4),
            update_cell(0, 38),
            update_var(guard_text, "r[0] = 38"),
            *track_line(8),
            update_cell(7, 55),
            update_var(j_text, "j = 4"),
            pointer_anim("j", "j", 4, ORANGE, "down"),
            run_time=0.9,
        )
        speak(
            "j 再减去 dk 后来到 r[1]。因为三十八不小于十三，后移停止，最后把三十八插回 r[4]。",
            *track_line(7),
            update_var(j_text, "j = 1"),
            pointer_anim("j", "j", 1, ORANGE, "down"),
            *track_line(9),
            update_cell(4, 38),
            set_status("38 插入 r[4]，这一组保持有序", GREEN),
            run_time=0.95,
        )
        speak(
            "第二趟的其他组也按同样逻辑处理。为了控制视频长度，这里直接给出 dk 等于三完成后的状态。",
            *set_all_values([13, 4, 49, 38, 27, 49, 55, 65, 97, 76]),
            *reset_colors(),
            set_status("dk = 3 结束：序列进一步接近有序", GREEN, size=19),
            run_time=0.9,
        )

        # ===== dk = 1：说明回到普通插入排序并给最终结果 =====
        speak(
            "最后一趟 dk 等于一。此时所有记录都在同一组，代码仍然是同一个 ShellInsert，只是它退化成一次完整的直接插入排序。",
            *track_line(0),
            update_var(dk_text, "dk = 1"),
            *reset_colors(list(range(1, n + 1)), PURPLE_B),
            set_tip("dk = 1 时，全体记录进入同一组", PURPLE_B),
            run_time=0.9,
        )
        speak(
            "这一趟不再逐个元素展开。请记住代码路径仍然一样：先判断 if，必要时暂存到 r[0]，再通过内层 for 让较大的记录按 dk 向后移动，最后把 r[0] 写回空位。",
            *track_line(3),
            *track_line(4),
            *track_line(6),
            *track_line(8),
            *track_line(9),
            set_status("dk = 1：按直接插入排序完成最终整理", YELLOW, size=19),
            run_time=1.1,
        )
        speak(
            "完成最后一趟后，顺序表从小到大排列为：零四、十三、二十七、三十八、四十九、四十九、五十五、六十五、七十六、九十七。",
            update_cell(0, None),
            *set_all_values([4, 13, 27, 38, 49, 49, 55, 65, 76, 97]),
            *[
                boxes[index].animate.set_color(GREEN).set_fill(GREEN, opacity=0.14)
                for index in range(1, n + 1)
            ],
            set_status("排序完成", GREEN, size=21),
            run_time=1.0,
        )

        self.play(
            *track_line(None),
            *[animation for animation in [fade_pointer("i"), fade_pointer("j")] if animation is not None],
            FadeOut(status),
            FadeOut(vars_panel),
            FadeOut(tip),
            run_time=0.45,
        )

        summary = VGroup(
            Text("代码核心：ShellSort 控制增量，ShellInsert 完成当前增量下的组内插入排序", font_size=18, font="Microsoft YaHei", color=YELLOW),
            Text("时间复杂度：取决于增量序列 dt，不是固定的单一公式", font_size=18, font="Microsoft YaHei", color=YELLOW),
            Text("常见结论：通常优于直接插入排序，最坏情况可达 O(n^2)", font_size=18, font="Microsoft YaHei", color=YELLOW),
            Text("空间复杂度：O(1)，只使用 r[0]、i、j、dk 等常数个辅助变量", font_size=18, font="Microsoft YaHei", color=GREEN),
            Text("稳定性：不稳定，相等关键字可能在不同分组移动中改变相对次序", font_size=18, font="Microsoft YaHei", color=ORANGE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.13).move_to(LEFT * 2.55 + DOWN * 1.75)

        speak(
            "总结一下，ShellSort 负责控制增量，ShellInsert 负责在当前增量下做组内插入排序。",
            FadeIn(summary[0]),
            run_time=0.8,
        )
        speak(
            "先看时间复杂度。希尔排序和直接插入排序不同，它的时间复杂度不是一个固定的简单公式，而是和增量序列 dt 的选择密切相关。",
            FadeIn(summary[1]),
            run_time=0.9,
        )
        speak(
            "原因在于，每一趟 ShellInsert 都会按照当前 dk 分组。dk 取得不同，分组方式不同，每组内部需要比较和移动的记录数量也不同，所以总运行时间会随增量序列变化。",
            code_texts[2].animate.set_color(YELLOW),
            code_texts[6].animate.set_color(YELLOW),
            run_time=1.0,
        )
        speak(
            "一般来说，前几趟大增量会把远处的小记录提前，使序列更接近有序。因此希尔排序通常比直接插入排序更快。",
            FadeIn(summary[2]),
            run_time=0.9,
        )
        speak(
            "但如果增量序列选择得不好，或者数据分布不理想，最坏情况下仍然可能退化到 O n 平方。所以教材中常写作：时间复杂度与增量序列有关，最坏可达 O n 平方。",
            summary[2].animate.set_color(ORANGE),
            run_time=1.0,
        )
        speak(
            "再看空间复杂度。整个排序过程中，数组本身仍在原地调整。额外使用的只有 r[0] 这个暂存单元，以及 i、j、dk 等少量变量。",
            FadeIn(summary[3]),
            run_time=0.9,
        )
        speak(
            "这些辅助变量的数量不会随着记录个数 n 增加而增加，所以希尔排序的辅助空间复杂度是 O 一。",
            summary[3].animate.set_color(GREEN),
            run_time=0.8,
        )
        speak(
            "最后看稳定性。希尔排序是不稳定排序。由于记录会按照不同增量分组，两个相等关键字可能在跨距离移动时改变原来的先后顺序。",
            FadeIn(summary[4]),
            boxes[4].animate.set_color(ORANGE).set_fill(ORANGE, opacity=0.22),
            boxes[5].animate.set_color(ORANGE).set_fill(ORANGE, opacity=0.22),
            run_time=1.0,
        )

        self.wait(1.2)
