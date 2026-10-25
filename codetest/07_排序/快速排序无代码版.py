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


class QuickSortNoCodeVideo(SortingNarrationMixin, VoiceoverScene):
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

        title = Text("快速排序", font_size=46, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.34)
        subtitle = Text("无代码版：核心思想演示", font_size=23, font="Microsoft YaHei", color=YELLOW)
        subtitle.next_to(title, DOWN, buff=0.12)
        self.play(FadeIn(title), FadeIn(subtitle), run_time=0.7)

        speak(
            "本节学习快速排序的核心思想。我们不讲代码，只看它怎样选出枢轴，把小的放左边，大的放右边，再递归处理左右子表。"
        )

        step_title = Text("核心思想：先定一个分界点", font_size=32, font="Microsoft YaHei", color=YELLOW).to_edge(UP, buff=1.15)
        steps = VGroup(
            Text("1. 选当前子表的第一个记录作为枢轴", font_size=23, font="Microsoft YaHei"),
            Text("2. 小于枢轴的记录放到左边", font_size=23, font="Microsoft YaHei"),
            Text("3. 大于或等于枢轴的记录放到右边", font_size=23, font="Microsoft YaHei"),
            Text("4. 枢轴落到分界处，再递归处理左右子表", font_size=23, font="Microsoft YaHei"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        steps.next_to(step_title, DOWN, buff=0.42)
        step_group = VGroup(step_title, steps).move_to(LEFT * 0.35 + DOWN * 0.05)

        speak(
            "快速排序可以理解为反复分队。每一趟先选一个枢轴，枢轴就像分界线：比它小的记录去左边，比它大的记录去右边。",
            FadeIn(step_title),
            LaggedStart(*[FadeIn(item, shift=RIGHT * 0.18) for item in steps[:3]], lag_ratio=0.18),
            run_time=1.1,
        )
        speak(
            "一趟划分结束后，枢轴已经站在最终位置。之后左子表和右子表继续重复同样的过程，直到每个子表只剩一个记录。",
            FadeIn(steps[3], shift=RIGHT * 0.18),
            steps[3].animate.set_color(GREEN),
            run_time=0.9,
        )
        self.play(FadeOut(step_group), run_time=0.5)

        values = [None, 49, 38, 65, 97, 76, 13, 27, 49, 55, 4]
        n = 10
        box_side = 0.56
        boxes = [None] * (n + 1)
        value_texts = [None] * (n + 1)
        box_group = VGroup()
        index_group = VGroup()

        def display(value):
            if value is None:
                return "-"
            return "04" if value == 4 else str(value)

        for index in range(n + 1):
            box = Square(side_length=box_side, color=GREEN if index == 0 else BLUE, stroke_width=2)
            if index > 0:
                box.next_to(box_group[-1], RIGHT, buff=0.02)
            boxes[index] = box
            box_group.add(box)
            index_group.add(
                Text(f"r[{index}]", font_size=13, font="Consolas", color=GRAY_B).next_to(box, DOWN, buff=0.08)
            )

        box_group.move_to(LEFT * 2.7 + UP * 0.55)
        for index in range(n + 1):
            index_group[index].next_to(boxes[index], DOWN, buff=0.08)
            value_texts[index] = Text(display(values[index]), font_size=19, font="Arial", color=GREEN if index == 0 else WHITE)
            value_texts[index].move_to(boxes[index].get_center())

        array_label = Text("示例数据：49, 38, 65, 97, 76, 13, 27, 49, 55, 04", font_size=19, font="Microsoft YaHei", color=YELLOW)
        array_label.next_to(box_group, UP, buff=0.24)
        status = Text("选择第一个记录 49 作为第一次枢轴", font_size=21, font="Microsoft YaHei", color=YELLOW)
        status.move_to(LEFT * 2.7 + DOWN * 1.15)
        detail = Text("r[0] 用来临时保存枢轴", font_size=17, font="Microsoft YaHei", color=GREEN)
        detail.move_to(LEFT * 2.7 + DOWN * 1.65)
        array_group = VGroup(box_group, index_group, *value_texts, array_label, status, detail)

        def set_status(content, color=YELLOW, size=21):
            return Transform(status, Text(content, font_size=size, font="Microsoft YaHei", color=color).move_to(status))

        def set_detail(content, color=GREEN):
            return Transform(detail, Text(content, font_size=17, font="Microsoft YaHei", color=color).move_to(detail))

        def update_cell(index, value, color=None):
            values[index] = value
            new_text = Text(display(value), font_size=19, font="Arial", color=color or (GREEN if index == 0 else WHITE))
            new_text.move_to(boxes[index].get_center())
            old_text = value_texts[index]
            value_texts[index] = new_text
            return ReplacementTransform(old_text, new_text)

        def set_array(new_values):
            animations = []
            for index, value in enumerate(new_values, start=1):
                if values[index] != value:
                    animations.append(update_cell(index, value))
            return animations

        def color_range(low, high, color, opacity=0.13):
            return [boxes[index].animate.set_color(color).set_fill(color, opacity=opacity) for index in range(low, high + 1)]

        def reset_colors(pivot=None, left=None, right=None):
            left = set(left or [])
            right = set(right or [])
            animations = []
            for index in range(n + 1):
                if index == 0:
                    animations.append(boxes[index].animate.set_color(GREEN).set_fill(BLACK, opacity=0))
                elif index == pivot:
                    animations.append(boxes[index].animate.set_color(YELLOW).set_fill(YELLOW, opacity=0.18))
                elif index in left:
                    animations.append(boxes[index].animate.set_color(BLUE_B).set_fill(BLUE_B, opacity=0.12))
                elif index in right:
                    animations.append(boxes[index].animate.set_color(RED_B).set_fill(RED_B, opacity=0.12))
                else:
                    animations.append(boxes[index].animate.set_color(BLUE).set_fill(BLACK, opacity=0))
            return animations

        def make_pointer(label, index, color, side="up"):
            target = boxes[index]
            if side == "up":
                arrow = Arrow(
                    target.get_top() + UP * 0.48,
                    target.get_top() + UP * 0.04,
                    buff=0.04,
                    color=color,
                    stroke_width=3.4,
                    tip_length=0.13,
                )
                text = Text(label, font_size=16, font="Consolas", color=color).next_to(arrow, UP, buff=0.02)
            else:
                arrow = Arrow(
                    target.get_bottom() + DOWN * 0.48,
                    target.get_bottom() + DOWN * 0.04,
                    buff=0.04,
                    color=color,
                    stroke_width=3.4,
                    tip_length=0.13,
                )
                text = Text(label, font_size=16, font="Consolas", color=color).next_to(arrow, DOWN, buff=0.02)
            return VGroup(arrow, text)

        pointers = {}

        def pointer_anim(name, label, index, color, side="up"):
            new_pointer = make_pointer(label, index, color, side)
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
            "现在使用统一的示例数据。注意最后一个记录写作零四，它的数值是四，排序后应该排到最前面。",
            FadeIn(array_group),
            run_time=0.9,
        )

        def show_partition(low, high, pivot_index, pivot_value, final_state, left_indices, right_indices, caption):
            speak(
                f"处理子表 r[{low}..{high}]。选 r[{low}] 的 {display(pivot_value)} 作为枢轴，low 和 high 分别从子表两端向中间搜索。",
                *reset_colors(),
                *color_range(low, high, PURPLE_B, 0.08),
                update_cell(0, pivot_value),
                pointer_anim("low", "low", low, BLUE_B, "up"),
                pointer_anim("high", "high", high, RED_B, "down"),
                set_status(f"子表 r[{low}..{high}]，pivotkey = {display(pivot_value)}", YELLOW, 20),
                set_detail("右边找小值放左侧，左边找大值放右侧", BLUE_B),
                run_time=0.9,
            )
            speak(
                caption,
                *set_array(final_state),
                update_cell(0, None),
                *reset_colors(pivot=pivot_index, left=left_indices, right=right_indices),
                set_status(f"枢轴 {display(pivot_value)} 到位：r[{pivot_index}]", GREEN, 20),
                run_time=1.0,
            )
            self.play(*[anim for anim in [fade_pointer("low"), fade_pointer("high")] if anim is not None], run_time=0.25)

        show_partition(
            1,
            10,
            6,
            49,
            [4, 38, 27, 13, 49, 49, 76, 97, 55, 65],
            [1, 2, 3, 4, 5],
            [7, 8, 9, 10],
            "第一次划分完成后，小于四十九的记录被放到左侧，较大的记录被放到右侧。另一个四十九可以出现在枢轴左侧或右侧，这不影响最终有序。",
        )
        show_partition(
            1,
            5,
            1,
            4,
            [4, 38, 27, 13, 49, 49, 76, 97, 55, 65],
            [],
            [2, 3, 4, 5],
            "左子表继续划分。零四是这个子表中最小的记录，所以枢轴零四直接落在 r[1]，它的左子表为空。",
        )
        show_partition(
            2,
            5,
            4,
            38,
            [4, 13, 27, 38, 49, 49, 76, 97, 55, 65],
            [2, 3],
            [5],
            "接着处理 r[2..5]。以三十八为枢轴后，十三和二十七进入左侧，四十九留在右侧，三十八落到 r[4]。",
        )
        show_partition(
            2,
            3,
            2,
            13,
            [4, 13, 27, 38, 49, 49, 76, 97, 55, 65],
            [],
            [3],
            "继续处理 r[2..3]。十三小于二十七，所以十三已经在自己的最终位置，二十七单独成表。",
        )
        speak(
            "到这里，第一次枢轴左边的子表已经排好，结果是零四、十三、二十七、三十八、四十九。",
            *reset_colors(left=[1, 2, 3, 4, 5], pivot=6, right=[7, 8, 9, 10]),
            set_status("左子表完成：04、13、27、38、49", GREEN, 20),
            run_time=0.85,
        )
        show_partition(
            7,
            10,
            10,
            76,
            [4, 13, 27, 38, 49, 49, 65, 55, 76, 97],
            [7, 8],
            [10],
            "现在处理右子表 r[7..10]。以七十六为枢轴后，六十五和五十五进入左侧，九十七进入右侧，七十六落到 r[9]。",
        )
        show_partition(
            7,
            8,
            8,
            65,
            [4, 13, 27, 38, 49, 49, 55, 65, 76, 97],
            [7],
            [],
            "最后处理 r[7..8]。以六十五为枢轴，五十五在它左侧，六十五落到 r[8]。右子表也完成排序。",
        )

        speak(
            "当所有子表都只剩一个记录，或者已经完成划分时，递归结束。顺序表现在已经完整有序。",
            *[
                boxes[index].animate.set_color(GREEN).set_fill(GREEN, opacity=0.13)
                for index in range(1, n + 1)
            ],
            set_status("排序完成", GREEN, 21),
            set_detail("最终顺序由表中记录直接呈现", GREEN),
            run_time=0.9,
        )

        summary = VGroup(
            Text("核心：选枢轴", font_size=23, font="Microsoft YaHei", color=YELLOW),
            Text("划分：小放左，大放右", font_size=23, font="Microsoft YaHei", color=GREEN),
            Text("递归：左右子表重复处理", font_size=23, font="Microsoft YaHei", color=BLUE_B),
            Text("稳定性：不稳定", font_size=23, font="Microsoft YaHei", color=ORANGE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.20).move_to(RIGHT * 2.7 + DOWN * 1.35)

        speak(
            "本视频讲解了快速排序算法的实现思想，如需深入学习该算法的代码实现，请后续观看该算法的代码跟踪版讲解视频。",
            FadeIn(summary),
            run_time=0.8,
        )
        speak(
            "最后看稳定性。快速排序是不稳定排序。因为划分过程中记录会围绕枢轴移动，两个相等关键字的相对先后顺序可能发生改变。",
            summary[3].animate.set_color(ORANGE),
            boxes[5].animate.set_color(ORANGE).set_fill(ORANGE, opacity=0.22),
            boxes[6].animate.set_color(ORANGE).set_fill(ORANGE, opacity=0.22),
            run_time=1.0,
        )
        self.wait(1.2)
