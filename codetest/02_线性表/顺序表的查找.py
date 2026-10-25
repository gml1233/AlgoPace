# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class LinkedListBase(VoiceoverScene):
    """动画公共基类，提供高复用的基础组件配置"""
    pass


class ContinuousSeqListSearchVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角全局图片 Logo（紧靠右上角且放大一倍，伴随顶部微调）
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("顺序表的查找", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        # 【核心修改】将原本在算法演练开头的总领句完美移至视频最开始
        with self.voiceover(
                text="本节我们来学习顺序表的查找。该算法是根据指定的元素值e，查找顺序表中第1个与e相等的元素。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== PHASE B — VIVID ANALOGY (花名册实例：极简引入版) =====
        # =========================================================================
        names_list = ["张三", "李四", "王五", "赵六", "钱七"]

        with self.voiceover(text="在学习算法前，我们先看一个生活实例：老师在班级花名册中寻找学生“王五”。") as tracker:
            # 1. 创建花名册
            roster_boxes = VGroup(
                *[Rectangle(width=2.8, height=0.6, color=BLUE, fill_color=BLUE, fill_opacity=0.1) for _ in
                  range(5)]).arrange(DOWN, buff=0.1)
            roster_boxes.move_to(RIGHT * 2.2 + DOWN * 0.5)

            roster_texts = VGroup(
                *[Text(name, font_size=20, font="Microsoft YaHei", color=WHITE) for name in names_list])
            for box, text in zip(roster_boxes, roster_texts):
                text.move_to(box.get_center())

            roster_marks = VGroup(
                *[Text(f"第 {idx + 1} 行", font_size=16, font="Microsoft YaHei", color=ORANGE) for idx in range(5)])
            for box, mark in zip(roster_boxes, roster_marks):
                mark.next_to(box, LEFT, buff=0.3)

            roster_label = Text("班级花名册", font_size=22, font="Microsoft YaHei", color=BLUE_A).next_to(roster_boxes,
                                                                                                          UP, buff=0.3)
            roster_group = VGroup(roster_boxes, roster_texts, roster_marks, roster_label)

            # 2. 创建查找目标卡片
            target_box_ok = RoundedRectangle(corner_radius=0.1, width=3.2, height=1.2, color=YELLOW, fill_color=YELLOW,
                                             fill_opacity=0.15)
            target_box_ok.move_to(LEFT * 2.8 + UP * 0.8)

            target_title_ok = Text("待查学生", font_size=16, font="Microsoft YaHei", color=YELLOW, weight=BOLD).next_to(
                target_box_ok.get_top(), DOWN, buff=0.15)
            target_content_ok = Text("姓名: 王五", font_size=18, font="Microsoft YaHei", color=WHITE).next_to(
                target_title_ok, DOWN, buff=0.1)
            target_panel_ok = VGroup(target_box_ok, target_title_ok, target_content_ok)

            self.play(FadeIn(roster_group), FadeIn(target_panel_ok, shift=RIGHT * 0.3), run_time=tracker.duration)

        with self.voiceover(
                text="由于不知道名字具体在哪一航，老师只能从第一航开始，逐航向下核对，直到找到为止。",
                subcaption="由于不知道名字具体在哪行，老师只能从第一行开始，逐行向下核对，直到找到为止。") as tracker:
            # 快速连贯的线性扫描动画，模拟逐个比对的线性开销
            step_time = tracker.duration / 3.0

            # 查张三
            scan_rect = SurroundingRectangle(roster_boxes[0], color=RED, buff=0.04, stroke_width=3)
            self.play(Create(scan_rect), run_time=step_time * 0.5)
            self.play(FadeOut(scan_rect), run_time=step_time * 0.5)

            # 查李四
            scan_rect.move_to(roster_boxes[1])
            self.play(Create(scan_rect), run_time=step_time * 0.5)
            self.play(FadeOut(scan_rect), run_time=step_time * 0.5)

            # 查王五 (匹配成功)
            scan_rect2 = SurroundingRectangle(roster_boxes[2], color=YELLOW, buff=0.04, stroke_width=4)
            self.play(Create(scan_rect2), roster_boxes[2].animate.set_fill(YELLOW, opacity=0.4), run_time=step_time)

        with self.voiceover(
                text="这种从头到尾、按顺序依次比对的线性排查过程，就是顺序表按值查找的核心逻辑。接下来我们看代码实现。") as tracker:
            self.wait(tracker.duration)

        # 快速清理生活实例，切入算法
        self.play(FadeOut(roster_group), FadeOut(target_panel_ok), FadeOut(scan_rect2), run_time=0.8)

        # =========================================================================
        # ===== PHASE C — CODE BLOCK CONFIG (算法代码块排版部分) =====
        # =========================================================================
        c_lines = [
            "int LocateElem(SqList L, ElemType e)",
            "{",
            "    for (int i = 0; i < L.length; i++)",
            "        if (L.elem[i] == e) return i + 1; ",
            "    return 0; ",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=11.5, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        SPACE_WIDTH = 0.095
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        buff_val = 0.25
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

        code_block = VGroup(code_bg, code_group).to_edge(RIGHT, buff=0.4).shift(UP * 0.2)

        self.current_line = None

        def get_track_anims(new_idx):
            # 防御机制：避免重复放大引发的叠加变形
            if new_idx == self.current_line:
                return []

            anims = []
            if self.current_line is not None:
                old_idx = self.current_line
                anims.append(self.c_texts[old_idx].animate.set_color(WHITE).scale(1 / 1.2, about_edge=LEFT))

            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW).scale(1.2, about_edge=LEFT))

                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.15).rotate(-PI / 2)
                    self.code_pointer.next_to(self.c_texts[new_idx], LEFT, buff=0.2)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.c_texts[new_idx], LEFT, buff=0.2)
                    anims.append(MoveToTarget(self.code_pointer))

                self.current_line = new_idx
            else:
                if hasattr(self, 'code_pointer'):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, 'code_pointer')
                self.current_line = None

            return anims

        def build_annotated_sequence(values):
            l_boxes = VGroup(*[Square(side_length=0.8, color=BLUE) for _ in range(len(values))]).arrange(RIGHT, buff=0)
            l_nums = VGroup(*[Text(str(val), font_size=28, font="Arial") for val in values])
            for box, num in zip(l_boxes, l_nums):
                num.move_to(box.get_center())

            position_marks = VGroup(
                *[Text(str(index + 1), font_size=18, color=ORANGE, font="Arial") for index in range(len(values))])
            for box, mark in zip(l_boxes, position_marks):
                mark.next_to(box, UP, buff=0.12)

            index_marks = VGroup(
                *[Text(str(index), font_size=18, color=TEAL_A, font="Arial") for index in range(len(values))])
            for box, mark in zip(l_boxes, index_marks):
                mark.next_to(box, DOWN, buff=0.12)

            position_label = Text("位置", font_size=20, color=ORANGE, font="Microsoft YaHei").next_to(position_marks,
                                                                                                      LEFT, buff=0.3)
            l_label = Text("L", font_size=24, color=BLUE, font="Arial").next_to(l_boxes, LEFT, buff=0.3)
            index_label = Text("下标", font_size=20, color=TEAL_A, font="Microsoft YaHei").next_to(index_marks, LEFT,
                                                                                                   buff=0.3)

            array_group = VGroup(position_label, position_marks, l_label, l_boxes, l_nums, index_label, index_marks)
            return array_group, l_boxes, index_marks

        def build_scan_pointer(anchor_mark, label_text="i"):
            i_arrow = Arrow(DOWN, UP, buff=0.05, tip_length=0.15).scale(0.3).next_to(anchor_mark, DOWN, buff=0.02)
            i_arrow.set_color(RED)
            i_text = Text(label_text, font_size=18, color=RED, font="Arial").next_to(i_arrow, DOWN, buff=0.02)
            return VGroup(i_arrow, i_text)

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW (顺序表算法物理演练) =====
        # =========================================================================
        # 修改点 1：统一都说我们学习该算法的代码实现
        with self.voiceover(text="现在，我们来看该算法的代码实现。",
                            subcaption="现在，我们来看该算法的代码实现。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        L_values = [3, 7, 1, 9, 5]
        array_l, l_boxes, index_marks = build_annotated_sequence(L_values)
        array_l.move_to(LEFT * 3.0 + UP * 0.5)

        # 修改点 2：不说演练，改为“这是包含5个元素的顺序表L”
        with self.voiceover(text="这是包含5个元素的顺序表L。", subcaption="这是包含5个元素的顺序表L。") as tracker:
            self.play(Create(array_l), run_time=tracker.duration)
        self.wait(0.3)

        # ---------------- 场景演练 1：查找失败演示 ----------------
        e_val_err = 8
        param_panel_err = VGroup(
            Text("查找目标：", font_size=24, font="Microsoft YaHei", color=RED),
            MathTex(f"e = {e_val_err}", font_size=26, color=RED)
        ).arrange(RIGHT, buff=0.15).next_to(code_block, DOWN, buff=0.2).align_to(code_block, LEFT)

        with self.voiceover(
                text=f"第一种情况，假设我们要查找一个不存在的数值，设置目标值 e 等于 {e_val_err}。") as tracker:
            self.play(FadeIn(param_panel_err), run_time=tracker.duration)

        # 修改点 3：“进入循环结构”改为“进入for循环”
        with self.voiceover(text="进入for循环，变量i从下标 0 开始，向后遍历每一个元素。",
                            subcaption="进入for循环，变量i从下标 0 开始，向后遍历每一个元素。") as tracker:
            self.play(*get_track_anims(2), run_time=tracker.duration)

        scan_ptr = build_scan_pointer(index_marks[0], label_text="i=0")
        self.play(Create(scan_ptr), run_time=0.5)

        for idx in range(len(L_values)):
            if idx > 0:
                new_ptr = build_scan_pointer(index_marks[idx], label_text=f"i={idx}")
                self.play(Transform(scan_ptr, new_ptr), run_time=0.4)

            curr_rect = SurroundingRectangle(l_boxes[idx], color=RED, buff=0.04)
            curr_val = L_values[idx]

            # 【核心修复点】动态拦截数字1，将其替换为汉字发音，而画面字幕 subcaption 依然保持显示数字格式
            spoken_val = "壹" if curr_val == 1 else str(curr_val)

            with self.voiceover(
                    text=f"当前元素{spoken_val}与待查找元素e不相等。",
                    subcaption=f"当前元素{curr_val}与待查找元素e不相等。"
            ) as tracker:
                self.play(*get_track_anims(3), Create(curr_rect), run_time=tracker.duration * 0.6)
                self.play(FadeOut(curr_rect), run_time=tracker.duration * 0.4)

        with self.voiceover(text="遍历了整个顺序表，都没有找到与目标值8相等的元素。") as tracker:
            self.play(*get_track_anims(2), run_time=tracker.duration)

        with self.voiceover(text="程序跳出循环，最终返回 0，表示查找失败。") as tracker:
            self.play(*get_track_anims(4), run_time=tracker.duration)
            flash_rect = SurroundingRectangle(code_bg, color=RED, buff=0.05)
            self.play(Create(flash_rect), run_time=0.5)
            self.play(FadeOut(flash_rect), run_time=0.5)

        self.play(*get_track_anims(None), FadeOut(param_panel_err), FadeOut(scan_ptr), run_time=0.5)

        # ---------------- 场景演练 2：查找成功演示 ----------------
        e_val_ok = 1
        param_panel_ok = VGroup(
            Text("查找目标：", font_size=24, font="Microsoft YaHei", color=YELLOW),
            MathTex(f"e = {e_val_ok}", font_size=26, color=YELLOW)
        ).arrange(RIGHT, buff=0.15).next_to(code_block, DOWN, buff=0.2).align_to(code_block, LEFT)

        # 修改点 5：避免"1"读错，通过text使用"壹"发音，通过subcaption控制显示的文字
        with self.voiceover(text="第二种情况，来看查找成功的流程。设定查找目标值 e 等于 壹。",
                            subcaption="第二种情况，来看查找成功的流程。设定查找目标值 e 等于 1。") as tracker:
            self.play(*get_track_anims(0), FadeIn(param_panel_ok), run_time=tracker.duration)

        with self.voiceover(text="程序重新启动循环，再次从下标 0 开始依次比对。") as tracker:
            self.play(*get_track_anims(2), run_time=tracker.duration)

        scan_ptr = build_scan_pointer(index_marks[0], label_text="i=0")
        self.play(Create(scan_ptr), run_time=0.4)

        # i=0 (值3)
        curr_rect0 = SurroundingRectangle(l_boxes[0], color=RED, buff=0.04)
        with self.voiceover(text="当前元素3与待查找元素e不相等。") as tracker:
            self.play(*get_track_anims(3), Create(curr_rect0), run_time=tracker.duration * 0.6)
            self.play(FadeOut(curr_rect0), run_time=tracker.duration * 0.4)

        # i=1 (值7)
        new_ptr1 = build_scan_pointer(index_marks[1], label_text="i=1")
        self.play(Transform(scan_ptr, new_ptr1), *get_track_anims(2), run_time=0.4)
        curr_rect1 = SurroundingRectangle(l_boxes[1], color=RED, buff=0.04)
        with self.voiceover(text="当前元素7与待查找元素e不相等。") as tracker:
            self.play(*get_track_anims(3), Create(curr_rect1), run_time=tracker.duration * 0.6)
            self.play(FadeOut(curr_rect1), run_time=tracker.duration * 0.4)

        # i=2 (值1) 匹配成功
        new_ptr2 = build_scan_pointer(index_marks[2], label_text="i=2")
        # 修改点 4 和 5：“判断当前元素的值等于 1”改为“当前元素的值为1”，并处理"1"的发音防读错
        with self.voiceover(text="当变量i增加到 2 时，当前元素的值为壹，条件成立。",
                            subcaption="当变量i增加到 2 时，当前元素的值为1，条件成立。") as tracker:
            self.play(Transform(scan_ptr, new_ptr2), *get_track_anims(2), run_time=0.4)
            self.play(*get_track_anims(3), run_time=max(0.2, tracker.duration - 0.4))

        target_box = l_boxes[2]
        target_highlight = SurroundingRectangle(target_box, color=YELLOW, buff=0.04, stroke_width=3)
        res_panel = VGroup(
            Text("查找结果：", font_size=24, font="Microsoft YaHei", color=GREEN),
            Text("成功，返回序号 3", font_size=22, font="Microsoft YaHei", color=GREEN)
        ).arrange(RIGHT, buff=0.15).move_to(LEFT * 3.0 + DOWN * 1.5)

        # 修改点 5：处理加“1”的发音防读错
        with self.voiceover(text="查找成功.程序立刻执行返回语句，将下标i加上 壹 得到序号 3 并返回。",
                            subcaption="查找成功。程序立刻执行返回语句，将下标i加上 1 得到序号 3 并返回。") as tracker:
            self.play(
                Create(target_highlight),
                target_box.animate.set_fill(YELLOW, opacity=0.3),
                self.c_texts[3].animate.set_color(GREEN),
                Write(res_panel),
                run_time=tracker.duration
            )

        self.play(*get_track_anims(None), FadeOut(target_highlight), FadeOut(scan_ptr), run_time=0.5)

        # =========================================================================
        # ===== PHASE E — 时空复杂度分析 =====
        # =========================================================================
        # 复杂度分析单独清场展示，避免底部字幕与原有顺序表、代码块互相遮挡。
        scene_items = [m for m in self.mobjects if m is not algo_title and not isinstance(m, ImageMobject)]
        self.play(*[FadeOut(m) for m in scene_items], run_time=0.6)

        def row(parts, buff=0.09):
            mobs = []
            for content, font_kind, color, font_size in parts:
                font = "Microsoft YaHei" if font_kind == "c" else "Arial"
                mobs.append(Text(content, font_size=font_size, font=font, color=color))
            return VGroup(*mobs).arrange(RIGHT, buff=buff)

        e_head = Text("按值查找，要比较多少次？", font_size=24, font="Microsoft YaHei",
                      color=YELLOW, weight=BOLD)
        r1 = row([("目标在第 1 个位置（最好）：比较", "c", GRAY_A, 20), ("1", "n", GREEN_B, 21),
                  ("次", "c", GRAY_A, 20)])
        r2 = row([("目标在第 n 个位置（最坏）：比较", "c", GRAY_A, 20), ("n", "n", GREEN_B, 21),
                  ("次", "c", GRAY_A, 20)])
        r3 = row([("目标不存在：也要比较", "c", GRAY_A, 20), ("n", "n", GREEN_B, 21),
                  ("次", "c", GRAY_A, 20)])
        r4 = row([("目标在第 i 个位置：比较", "c", GRAY_A, 20), ("i", "n", GREEN_B, 21),
                  ("次", "c", GRAY_A, 20)])
        r5 = row([("每个位置机会均等，平均次数", "c", GRAY_A, 20),
                  ("= (1 + 2 + ... + n) / n", "n", GOLD, 21)])
        r6 = row([("也就是", "c", GRAY_A, 20), ("E = (n + 1) / 2", "n", GOLD, 25)])
        analysis = VGroup(e_head, r1, r2, r3, r4, r5, r6).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
        analysis.move_to([-0.35, 0.35, 0])

        with self.voiceover(
                text="最后分析时间和空间。按值查找慢在哪儿？慢在不知道目标在哪，只能从前往后一个个比。",
                subcaption="最后分析时间和空间。按值查找慢在哪儿？慢在不知道目标在哪，只能从前往后一个个比。"
        ) as tracker:
            self.play(FadeIn(e_head), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
                text="如果目标就在第 1 个位置，比较一次就能找到，这是最好情况。",
                subcaption="如果目标就在第 1 个位置，比较一次就能找到，这是最好情况。"
        ) as tracker:
            self.play(FadeIn(r1, shift=RIGHT * 0.2), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
                text="如果目标在第 n 个位置，就要一路比较到最后，一共比较 n 次。",
                subcaption="如果目标在第 n 个位置，就要一路比较到最后，一共比较 n 次。"
        ) as tracker:
            self.play(FadeIn(r2, shift=RIGHT * 0.2), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
                text="如果目标根本不存在，也必须把整个表扫完，所以同样要比较 n 次。",
                subcaption="如果目标根本不存在，也必须把整个表扫完，所以同样要比较 n 次。"
        ) as tracker:
            self.play(FadeIn(r3, shift=RIGHT * 0.2), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
                text="一般地说，目标在第 i 个位置时，算法正好比较 i 次。",
                subcaption="一般地说，目标在第 i 个位置时，算法正好比较 i 次。"
        ) as tracker:
            self.play(FadeIn(r4, shift=RIGHT * 0.2), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 0.6))

        with self.voiceover(
                text="假设目标出现在每个位置的机会都一样，把每种情况平均起来，平均比较次数是 n 加 1 的一半。",
                subcaption="假设目标出现在每个位置的机会都一样，把每种情况平均起来，平均比较次数是 (n + 1) / 2。"
        ) as tracker:
            self.play(FadeIn(r5, shift=RIGHT * 0.2), run_time=0.7)
            self.play(FadeIn(r6, shift=RIGHT * 0.2), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 1.3))

        self.play(FadeOut(analysis), run_time=0.5)

        time_row = VGroup(Text("时间复杂度：", font_size=24, font="Microsoft YaHei", color=YELLOW),
                          Text("O(n)", font_size=28, font="Arial", color=YELLOW)).arrange(RIGHT, buff=0.12)
        time_note = row([("平均比较次数和表长成正比", "c", GRAY_A, 18)])
        space_row = VGroup(Text("空间复杂度：", font_size=24, font="Microsoft YaHei", color=YELLOW),
                           Text("O(1)", font_size=28, font="Arial", color=YELLOW)).arrange(RIGHT, buff=0.12)
        space_note = row([("只多用了 i 这一个扫描变量", "c", GRAY_A, 18)])
        summary = VGroup(
            VGroup(time_row, time_note).arrange(DOWN, aligned_edge=LEFT, buff=0.16),
            VGroup(space_row, space_note).arrange(DOWN, aligned_edge=LEFT, buff=0.16),
        ).arrange(RIGHT, aligned_edge=UP, buff=1.0).move_to([-0.15, 0.25, 0])

        with self.voiceover(
                text="也就是说，平均比较次数和表长成正比，所以时间复杂度是 O n。",
                subcaption="也就是说，平均比较次数和表长成正比，所以时间复杂度是 O(n)。"
        ) as tracker:
            self.play(FadeIn(time_row), run_time=0.6)
            self.play(FadeIn(time_note), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 1.2))

        with self.voiceover(
                text="空间上，算法只多用了 i 这一个扫描变量，和表有多长没关系，所以空间复杂度是 O 一。",
                subcaption="空间上，算法只多用了 i 这一个扫描变量，和表有多长没关系，所以空间复杂度是 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_row), run_time=0.6)
            self.play(FadeIn(space_note), run_time=0.6)
            self.wait(max(0.2, tracker.duration - 1.2))

        with self.voiceover(
                text="这就是顺序表按值查找算法的完整演示过程。",
                subcaption="这就是顺序表按值查找算法的完整演示过程。"
        ) as tracker:
            self.play(Indicate(summary, color=BLUE_B, scale_factor=1.03), run_time=1.0)
            self.wait(max(0.2, tracker.duration - 1.0))

        self.wait(2)
