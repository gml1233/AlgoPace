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


class ShellSortNoCodeVideo(SortingNarrationMixin, VoiceoverScene):
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

        intro_caption = (
            "本节我们学习希尔排序，该算法将整个待排序记录序列分割成几组，对每组分别进行直接插入排序，"
            "然后增加每组的数据量，重新分组。经过几次分组排序后，再对全体记录进行一次直接插入排序。"
        )
        with narrate(intro_caption) as tracker:
            self.wait(tracker.duration)

        title = Text("希尔排序", font_size=46, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.34)
        subtitle = Text("无代码版：核心思想与代表性过程", font_size=23, font="Microsoft YaHei", color=YELLOW)
        subtitle.next_to(title, DOWN, buff=0.12)
        self.play(FadeIn(title), FadeIn(subtitle), run_time=0.7)

        idea_title = Text("核心思想", font_size=31, font="Microsoft YaHei", color=YELLOW).to_edge(UP, buff=1.12)
        ideas = VGroup(
            Text("1. 直接插入排序一次只挪一格，远处的小记录移动很慢", font_size=21, font="Microsoft YaHei"),
            Text("2. 希尔排序先取较大增量 d，让相隔 d 的记录分到一组", font_size=21, font="Microsoft YaHei"),
            Text("3. 每组内部做直接插入排序，小记录可以一次跨过多个位置", font_size=21, font="Microsoft YaHei"),
            Text("4. 逐步缩小 d，先粗略调整，再越来越精细地整理", font_size=21, font="Microsoft YaHei"),
            Text("5. 当 d = 1 时，全体记录同组，完成最后一次直接插入排序", font_size=21, font="Microsoft YaHei"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        ideas.next_to(idea_title, DOWN, buff=0.34)
        idea_group = VGroup(idea_title, ideas).move_to(LEFT * 0.45 + DOWN * 0.05)

        speak(
            "在学习希尔排序之前，先回想直接插入排序。直接插入排序每次只在相邻位置之间比较和后移。如果一个很小的记录一开始在很靠后的位置，它要被移动到前面，就可能需要一格一格地向前挪很多次。",
            FadeIn(idea_title),
            FadeIn(ideas[0], shift=RIGHT * 0.18),
            run_time=1.0,
        )
        speak(
            "希尔排序的改进点，就在于先不急着相邻比较，而是取一个较大的增量 d。凡是下标相差 d 的记录，都放到同一组里。这样，相隔较远的记录也能提前发生比较。",
            FadeIn(ideas[1], shift=RIGHT * 0.18),
            run_time=1.0,
        )
        speak(
            "在每一个小组内部，我们仍然使用直接插入排序。由于同组记录之间隔着 d 个位置，所以一个较小的记录不是只能前进一格，而是可以沿着自己的小组一次跨过多个位置。",
            FadeIn(ideas[2], shift=RIGHT * 0.18),
            ideas[2].animate.set_color(GREEN),
            run_time=1.0,
        )
        speak(
            "完成一趟分组插入排序后，再把增量 d 缩小。增量越小，每组包含的记录越多，排序也越精细。可以把这个过程理解为：前几趟先粗略调整整体位置，后几趟再慢慢修正局部顺序。",
            FadeIn(ideas[3], shift=RIGHT * 0.18),
            ideas[3].animate.set_color(GREEN),
            run_time=1.0,
        )
        speak(
            "最后，当增量 d 等于一时，所有记录都属于同一组。这一趟就是完整的直接插入排序。因为前面已经把序列调整得比较接近有序，所以最后整理通常会轻松很多。",
            FadeIn(ideas[4], shift=RIGHT * 0.18),
            ideas[4].animate.set_color(GREEN),
            run_time=1.0,
        )
        self.play(FadeOut(idea_group), run_time=0.5)

        values = [49, 38, 65, 97, 76, 13, 27, 49, 55, 4]
        display_values = ["49", "38", "65", "97", "76", "13", "27", "49", "55", "04"]
        n = len(values)
        box_side = 0.58
        boxes = []
        value_texts = []
        index_texts = VGroup()
        box_group = VGroup()

        for index in range(n):
            box = Square(side_length=box_side, color=BLUE, stroke_width=2)
            if index > 0:
                box.next_to(box_group[-1], RIGHT, buff=0.02)
            boxes.append(box)
            box_group.add(box)
            index_texts.add(
                Text(
                    f"r[{index + 1}]",
                    font_size=13,
                    font="Consolas",
                    color=GRAY_B,
                ).next_to(box, DOWN, buff=0.08)
            )

        box_group.move_to(LEFT * 0.25 + UP * 0.55)
        for index in range(n):
            index_texts[index].next_to(boxes[index], DOWN, buff=0.08)
            value_texts.append(
                Text(display_values[index], font_size=20, font="Arial", color=WHITE).move_to(boxes[index].get_center())
            )

        array_label = Text(
            "示例数据：49, 38, 65, 97, 76, 13, 27, 49, 55, 04",
            font_size=20,
            font="Microsoft YaHei",
            color=YELLOW,
        ).next_to(box_group, UP, buff=0.26)
        status = Text("采用代表性增量序列：5, 3, 1", font_size=22, font="Microsoft YaHei", color=YELLOW)
        status.move_to(DOWN * 1.08)
        tip = Text("本版不逐趟逐项展开，只用关键几步讲清核心思想", font_size=18, font="Microsoft YaHei", color=BLUE_B)
        tip.move_to(DOWN * 1.58)
        array_group = VGroup(box_group, index_texts, *value_texts, array_label, status, tip)

        def set_status(content, color=YELLOW, size=22):
            return Transform(status, Text(content, font_size=size, font="Microsoft YaHei", color=color).move_to(status))

        def set_tip(content, color=BLUE_B):
            return Transform(tip, Text(content, font_size=18, font="Microsoft YaHei", color=color).move_to(tip))

        def update_cell(index, value, display=None):
            values[index] = value
            if display is None:
                display = "04" if value == 4 else str(value)
            display_values[index] = display
            new_text = Text(display, font_size=20, font="Arial", color=WHITE).move_to(boxes[index].get_center())
            old_text = value_texts[index]
            value_texts[index] = new_text
            return ReplacementTransform(old_text, new_text)

        def set_all_values(new_values):
            anims = []
            for index, value in enumerate(new_values):
                if values[index] != value:
                    anims.append(update_cell(index, value))
            return anims

        def reset_colors(active=None, color=BLUE_B):
            active = set(active or [])
            anims = []
            for index, box in enumerate(boxes):
                if index in active:
                    anims.append(box.animate.set_color(color).set_fill(color, opacity=0.16))
                else:
                    anims.append(box.animate.set_color(BLUE).set_fill(BLACK, opacity=0))
            return anims

        def group_anims(groups):
            anims = []
            for group_index, group in enumerate(groups):
                color = self.GROUP_COLORS[group_index % len(self.GROUP_COLORS)]
                for index in group:
                    anims.append(boxes[index - 1].animate.set_color(color).set_fill(color, opacity=0.15))
            return anims

        speak(
            "现在看这组具体数据。最后一个零四按数值四参与排序，最终应该被排到最前面。",
            FadeIn(array_group),
            run_time=0.9,
        )

        groups_5 = [[1, 6], [2, 7], [3, 8], [4, 9], [5, 10]]
        speak(
            "第一趟取增量五。下标相差五的记录分到同一组，因此十个记录会形成五个二元组。",
            *group_anims(groups_5),
            set_status("第 1 趟：d = 5，形成五个二元组", YELLOW),
            set_tip("远距离记录先比较，能更早移动到大致正确的区域", GREEN),
            run_time=0.9,
        )
        speak(
            "看第一组：r[1] 是四十九，r[6] 是十三。十三更小，所以这一组内部整理后，十三提前，四十九后移。",
            *reset_colors([0, 5], RED_B),
            update_cell(0, 13),
            update_cell(5, 49),
            set_status("13 < 49：小记录提前，大记录后移", GREEN),
            run_time=0.95,
        )
        speak(
            "其余二元组按同样思路处理。第一趟结束后，远距离的小记录已经被提前，序列变得更接近有序。",
            *set_all_values([13, 27, 49, 55, 4, 49, 38, 65, 97, 76]),
            *reset_colors(),
            set_status("d = 5 结束：13  27  49  55  04  49  38  65  97  76", GREEN, size=18),
            run_time=1.0,
        )

        speak(
            "第二趟把增量缩小为三。此时每组包含的记录更多，例如 r[1]、r[4]、r[7]、r[10] 属于同一组。",
            *reset_colors([0, 3, 6, 9], BLUE_B),
            set_status("第 2 趟：d = 3，组内记录数量增加", YELLOW),
            set_tip("增量缩小，每组内部更像一次直接插入排序", BLUE_B),
            run_time=0.9,
        )
        speak(
            "看一个代表性变化：在某一组中，三十八需要插到五十五之前。它会让五十五后移，再把三十八放入空位。",
            *reset_colors([0, 3, 6], ORANGE),
            update_cell(6, 55),
            update_cell(3, 38),
            set_status("代表性插入：38 插到 55 前面", GREEN),
            run_time=1.0,
        )
        speak(
            "第二趟完成后，序列进一步接近有序。这里直接展示这一趟的结果，不再把每个小组都逐项展开。",
            *set_all_values([13, 4, 49, 38, 27, 49, 55, 65, 97, 76]),
            *reset_colors(),
            set_status("d = 3 结束：13  04  49  38  27  49  55  65  97  76", GREEN, size=18),
            run_time=1.0,
        )

        speak(
            "最后一趟增量变成一。所有记录进入同一组，此时希尔排序就回到了完整的直接插入排序，用来完成最终整理。",
            *reset_colors(list(range(n)), PURPLE_B),
            set_status("最后一趟：d = 1，全体记录进入同一组", YELLOW),
            set_tip("d = 1 保证最终得到完整有序序列", PURPLE_B),
            run_time=0.9,
        )
        speak(
            "因为前面几趟已经让序列大致有序，所以最后这次直接插入排序的移动量通常会比一开始直接排序少得多。",
            set_status("前面先粗排，最后再精排", YELLOW),
            run_time=0.8,
        )
        speak(
            "最终，记录按关键字从小到大排列为：零四、十三、二十七、三十八、四十九、四十九、五十五、六十五、七十六、九十七。",
            *set_all_values([4, 13, 27, 38, 49, 49, 55, 65, 76, 97]),
            *[
                boxes[index].animate.set_color(GREEN).set_fill(GREEN, opacity=0.15)
                for index in range(n)
            ],
            set_status("排序完成", GREEN, size=21),
            set_tip("希尔排序：先按较大增量粗排，再按较小增量精排", GREEN),
            run_time=1.0,
        )

        summary = VGroup(
            Text("算法思想：分组插入排序，增量逐渐缩小", font_size=22, font="Microsoft YaHei", color=YELLOW),
            Text("稳定性：不稳定，相等关键字可能因分组移动改变相对次序", font_size=20, font="Microsoft YaHei", color=ORANGE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(DOWN * 1.8)

        speak(
            "总结一下，希尔排序的关键不是换一种插入方式，而是改变比较间隔。先用大增量粗略调整，再用小增量逐步细化，最后在增量为一时完成整体有序。",
            FadeOut(tip),
            FadeIn(summary),
            run_time=1.0,
        )
        speak(
            "最后看稳定性。希尔排序是不稳定排序。比如这组数据中有两个四十九，由于算法会按照不同增量分组，后面的四十九可能先跨距离移动到前面，因此不能保证相等关键字仍保持原来的先后顺序。",
            boxes[4].animate.set_color(ORANGE).set_fill(ORANGE, opacity=0.22),
            boxes[5].animate.set_color(ORANGE).set_fill(ORANGE, opacity=0.22),
            summary[-1].animate.set_color(ORANGE),
            run_time=1.0,
        )

        end_caption = (
            "本视频讲解了希尔排序算法的实现思想，如需深入学习该算法的代码实现，"
            "请后续观看该算法的代码跟踪版讲解视频。"
        )
        with narrate(end_caption) as tracker:
            self.wait(tracker.duration)

        self.wait(1.0)
