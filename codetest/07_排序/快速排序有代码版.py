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


class QuickSortCodeVideo(SortingNarrationMixin, VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz")
        )

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(0.95).to_corner(UR, buff=0.04)
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

        title = Text("快速排序代码讲解版", font_size=38, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.24)
        self.play(FadeIn(title), run_time=0.7)

        speak(
            "本视频重点讲解快速排序的代码结构、递归调用关系，以及最后的时空复杂度和稳定性。"
        )

        code_lines = [
            "int Partition(SqList &L, int low, int high) {",
            "    int pivotkey;",
            "    L.r[0] = L.r[low];",
            "    pivotkey = L.r[low].key;",
            "    while (low < high) {",
            "        while (low < high && L.r[high].key >= pivotkey)",
            "            --high;",
            "        L.r[low] = L.r[high];",
            "        while (low < high && L.r[low].key <= pivotkey)",
            "            ++low;",
            "        L.r[high] = L.r[low];",
            "    }",
            "    L.r[low] = L.r[0];",
            "    return low;",
            "}",
            "// Recursively sort both partitions",
            "void QSort(SqList &L, int low, int high) {",
            "    int pivotloc;",
            "    if (low < high) {",
            "        pivotloc = Partition(L, low, high);",
            "        QSort(L, low, pivotloc - 1);",
            "        QSort(L, pivotloc + 1, high);",
            "    }",
            "}",
        ]

        code_texts = []
        for line in code_lines:
            item = Text(line.lstrip(" "), font_size=10.5, font="Consolas", color=WHITE)
            code_texts.append(item)
        code_group = VGroup(*code_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.055)
        space_width = 0.072
        for index, line in enumerate(code_lines):
            indent = len(line) - len(line.lstrip(" "))
            code_texts[index].shift(RIGHT * indent * space_width)

        code_bg = RoundedRectangle(
            corner_radius=0.12,
            width=code_group.get_width() + 0.42,
            height=code_group.get_height() + 0.36,
            color=GRAY_B,
            fill_color=BLACK,
            fill_opacity=0.35,
            stroke_width=1,
        ).move_to(code_group)
        code_block = VGroup(code_bg, code_group).to_edge(LEFT, buff=0.18).shift(DOWN * 0.18)
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
                    pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.11).rotate(-PI / 2)
                    pointer.next_to(code_texts[index], LEFT, buff=0.12)
                    current_line["pointer"] = pointer
                    anims.append(FadeIn(pointer))
                else:
                    pointer = current_line["pointer"]
                    pointer.generate_target()
                    pointer.target.next_to(code_texts[index], LEFT, buff=0.12)
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

        values = [49, 38, 65, 97, 76, 13, 27, 49]
        box_side = 0.54
        boxes = []
        labels = []
        nums = []
        for index, value in enumerate(values, start=1):
            box = Square(side_length=box_side, color=BLUE, stroke_width=2)
            num = Text(display(value), font_size=20, font="Arial", color=WHITE).move_to(box)
            label = Text(f"r[{index}]", font_size=13, font="Consolas", color=GRAY_B)
            boxes.append(box)
            nums.append(num)
            labels.append(label)

        row = VGroup(*[VGroup(boxes[i], nums[i]) for i in range(len(values))]).arrange(RIGHT, buff=0)
        row.move_to(RIGHT * 2.35 + UP * 0.75)
        label_group = VGroup(*labels)
        for index, label in enumerate(labels):
            label.next_to(boxes[index], DOWN, buff=0.08)
        table = VGroup(row, label_group)

        status = Text("示例数据：49, 38, 65, 97, 76, 13, 27, 49", font_size=21, font="Microsoft YaHei", color=YELLOW)
        if status.width > 6.0:
            status.scale_to_fit_width(6.0)
        status.move_to(RIGHT * 2.35 + DOWN * 0.25)

        def set_status(text, color=YELLOW, size=21):
            new_text = Text(text, font_size=size, font="Microsoft YaHei", color=color)
            if new_text.width > 6.0:
                new_text.scale_to_fit_width(6.0)
            return Transform(status, new_text.move_to(status))

        speak(
            "右侧使用统一示例数据。快速排序通常选当前子表的第一个记录作为枢轴，本例第一趟的枢轴就是四十九。",
            FadeIn(code_block),
            FadeIn(table),
            FadeIn(status),
            run_time=1.0,
        )

        speak(
            "Partition 函数负责完成一趟划分。它先把枢轴暂存到 r 零，并把枢轴关键字保存到 pivotkey 中。",
            *highlight_line(2),
            boxes[0].animate.set_color(PURPLE).set_fill(PURPLE, opacity=0.18),
            set_status("枢轴：r[1] = 49，暂存到 r[0]", PURPLE),
            run_time=0.9,
        )
        speak(
            "外层 while 的条件是 low 小于 high，也就是左右边界还没有相遇。满足条件时，先从右向左扫描。",
            *highlight_line(4),
            set_status("low 和 high 从两端向中间移动", YELLOW),
            run_time=0.8,
        )
        speak(
            "右侧内层 while 同时检查两个条件：low 小于 high，并且右侧记录的关键字大于或等于枢轴关键字。",
            *highlight_line(5),
            boxes[-1].animate.set_color(YELLOW).set_fill(YELLOW, opacity=0.16),
            set_status("右侧内层 while：high 向左寻找小于枢轴的记录", YELLOW),
            run_time=0.9,
        )
        speak(
            "条件成立就执行 high 减一。代码中的两个减号表示自减一，让右边界向左移动一个位置。",
            *highlight_line(6),
            set_status("--high：high 减 1，右边界左移", YELLOW),
            run_time=0.8,
        )
        speak(
            "找到较小记录后，将它填入左侧空位。随后检查左侧内层 while：low 小于 high，并且左侧关键字小于或等于枢轴关键字。",
            *highlight_line(8),
            boxes[0].animate.set_color(YELLOW).set_fill(YELLOW, opacity=0.16),
            set_status("左侧内层 while：low 向右寻找大于枢轴的记录", YELLOW),
            run_time=0.9,
        )
        speak(
            "条件成立就执行 low 加一。代码中的两个加号表示自增一，让左边界向右移动一个位置。",
            *highlight_line(9),
            set_status("++low：low 加 1，左边界右移", YELLOW),
            run_time=0.8,
        )
        speak(
            "一趟划分结束后，枢轴会落到最终位置。左边记录不大于它，右边记录不小于它。",
            *highlight_line(12),
            set_status("一趟划分：枢轴归位，左右子表形成", GREEN),
            *[boxes[i].animate.set_color(GREEN).set_fill(GREEN, opacity=0.12) for i in [0, 1, 2, 3]],
            *[boxes[i].animate.set_color(BLUE).set_fill(BLUE, opacity=0.08) for i in [4, 5, 6, 7]],
            run_time=1.0,
        )

        speak(
            "QSort 函数体现了递归思想。只要 low 小于 high，就先调用 Partition 定位一个枢轴，再分别递归处理左子表和右子表。",
            *highlight_line(18),
            run_time=0.8,
        )
        speak(
            "第一行递归调用负责处理枢轴左侧的子表。左子表会继续选择新的枢轴，再做同样的划分。",
            *highlight_line(20),
            set_status("递归处理左子表", BLUE_B),
            run_time=0.8,
        )
        speak(
            "第二行递归调用负责处理枢轴右侧的子表。左右子表不断重复这个过程，就形成了快速排序的递归树。",
            *highlight_line(21),
            set_status("递归处理右子表，形成递归树", BLUE_B),
            run_time=1.0,
        )

        sorted_values = [13, 27, 38, 49, 49, 65, 76, 97]
        final_anims = []
        for index, value in enumerate(sorted_values):
            final_anims.append(Transform(nums[index], Text(display(value), font_size=20, font="Arial", color=WHITE).move_to(boxes[index])))
            final_anims.append(boxes[index].animate.set_color(GREEN).set_fill(GREEN, opacity=0.15))
        speak(
            "递归不断缩小子表，直到子表中只有一个记录。最终，顺序表整体有序。",
            *highlight_line(None),
            *final_anims,
            set_status("排序完成", GREEN),
            run_time=1.0,
        )

        complexity_title = Text("时空复杂度与稳定性", font_size=30, font="Microsoft YaHei", color=YELLOW)
        complexity_rows = VGroup(
            Text("最好情况：划分均匀，递归树高度约为 log₂n", font_size=20, font="Microsoft YaHei", color=GREEN),
            Text("平均情况：通常接近均匀划分，时间复杂度 O(nlog₂n)", font_size=20, font="Microsoft YaHei", color=YELLOW),
            Text("最坏情况：每次只分出一个元素，退化为 O(n²)", font_size=20, font="Microsoft YaHei", color=ORANGE),
            Text("空间复杂度：递归栈平均 O(log₂n)，最坏 O(n)", font_size=20, font="Microsoft YaHei", color=BLUE),
            Text("稳定性：不稳定", font_size=20, font="Microsoft YaHei", color=ORANGE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        complexity_panel = VGroup(complexity_title, complexity_rows).arrange(DOWN, buff=0.28).move_to(ORIGIN + UP * 0.45)

        speak(
            "最后看快速排序的时空复杂度。它的趟数可以从递归树理解：递归树越浅，排序越快；递归树越深，排序越慢。",
            FadeOut(code_block),
            FadeOut(table),
            FadeOut(status),
            FadeIn(complexity_title),
            run_time=0.9,
        )
        speak(
            "最好情况下，每一趟都能把序列划分成两个长度接近的子表，就像折半一样。每层划分总工作量约为 n，树高约为 log n，所以时间复杂度是 O n log n。",
            FadeIn(complexity_rows[0], shift=RIGHT * 0.25),
            FadeIn(complexity_rows[1], shift=RIGHT * 0.25),
            run_time=1.0,
        )
        speak(
            "最坏情况下，比如原序列已有序而又总选第一个记录作枢轴，递归树会退化成单支树。此时要经历接近 n 趟划分，时间复杂度退化为 O n 平方。",
            FadeIn(complexity_rows[2], shift=RIGHT * 0.25),
            run_time=1.0,
        )
        speak(
            "为了减少这种退化，可以用三者取中等方法选择枢轴。理论上，快速排序平均时间复杂度为 O n log n。",
            complexity_rows[1].animate.set_color(GREEN),
            run_time=0.8,
        )
        speak(
            "空间复杂度主要来自递归调用栈。平均递归深度约为 log n，所以平均空间复杂度是 O log n；最坏单支递归时，空间复杂度为 O n。",
            FadeIn(complexity_rows[3], shift=RIGHT * 0.25),
            run_time=1.0,
        )
        speak(
            "快速排序是不稳定排序。因为划分过程中记录会围绕枢轴移动，相等关键字的相对先后顺序可能被改变。",
            FadeIn(complexity_rows[4], shift=RIGHT * 0.25),
            run_time=0.9,
        )

        self.wait(1.2)
