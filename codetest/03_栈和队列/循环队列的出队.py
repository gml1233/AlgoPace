# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)

from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
class CircularQueueDequeueVideo(VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角 Logo
        logo = (
            ImageMobject(r"resource\Pitcure\front.png")
            .scale_to_fit_height(2.0)
            .to_corner(UR, buff=0.05)
            .shift(UP * 0.1)
        )
        self.add(logo)
        self.add_foreground_mobject(logo)

        # 标题：不指定字体，保持和单链表系列一致；稍微上移
        title = (
            Text(
                "循环队列的出队",
                font_size=48,
                weight=BOLD
            )
            .to_edge(UP, buff=0.45)
        )
        self.play(FadeIn(title), run_time=0.8)

        with self.voiceover(text="本节我们来学习循环队列的出队操作，该算法将循环队列的队头元素出队。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== NEW PHASE — LIFE EXAMPLE (旋转寿司的取餐) =====
        # =========================================================================
        example_title = Text("生活实例：旋转寿司的取餐", font_size=32, font="Microsoft YaHei", color=YELLOW).to_edge(UP, buff=1.5)

        # 用圆形模拟首尾相连的传送带
        conveyor = Circle(radius=1.5, color=BLUE, stroke_width=4).move_to(DOWN * 0.3)

        # 在圆环上分布4个小盘子表示槽位
        angles = [0, PI / 2, PI, 3 * PI / 2]
        slots = VGroup(
            *[Circle(radius=0.32, color=GRAY_A, fill_opacity=0.35).move_to(conveyor.point_at_angle(a)) for a in angles]
        )

        s1_text = Text("寿司3", font_size=13, font="Microsoft YaHei").move_to(slots[0].get_center())
        s2_text = Text("空位", font_size=13, font="Microsoft YaHei", color=GRAY).move_to(slots[1].get_center())
        s3_text = Text("寿司1", font_size=13, font="Microsoft YaHei", color=GREEN).move_to(slots[2].get_center())  # 队头（最早存入）
        s4_text = Text("寿司2", font_size=13, font="Microsoft YaHei").move_to(slots[3].get_center())

        s_texts = VGroup(s1_text, s2_text, s3_text, s4_text)

        # 取餐位标记（相当于头指针 front）
        pickup_arrow = Arrow(start=slots[2].get_left() + LEFT * 0.7, end=slots[2].get_left(), buff=0.06, color=GREEN)
        pickup_label = Text("取餐标记(队头)", font_size=15, font="Microsoft YaHei", color=GREEN).next_to(pickup_arrow, LEFT, buff=0.1)
        pickup_group = VGroup(pickup_arrow, pickup_label)

        with self.voiceover(
            text="队列遵循先进先出规则，先来的元素先离开。这就像在旋转寿司传送带前取餐，有一个标记专门用来定位当前队列最前面的元素。"
        ) as tracker:
            self.play(FadeIn(example_title), Create(conveyor), FadeIn(slots), FadeIn(s_texts), FadeIn(pickup_group), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
            text="当队头元素被取走之后，原本的位置就失效了，我们不能再让标记停留在失效的位置上。"
        ) as tracker:
            empty_text = Text("空位", font_size=13, font="Microsoft YaHei", color=GRAY).move_to(slots[2].get_center())
            self.play(
                s3_text.animate.shift(LEFT * 0.4).set_opacity(0),
                slots[2].animate.set_color(GRAY),
                run_time=0.6
            )
            self.play(FadeIn(empty_text), run_time=0.3)
            self.wait(max(0.1, tracker.duration - 0.9))

        with self.voiceover(
            text="所以出队操作必须移动这个标记，让标记挪到下一个元素上，持续对准新的队头，保证每次出队都能拿到现存队列里最先存入的数据。"
        ) as tracker:
            # 标记顺延移动到下一个元素（寿司2）
            target_arrow = Arrow(start=slots[3].get_bottom() + DOWN * 0.7, end=slots[3].get_bottom(), buff=0.06, color=GREEN)
            target_label = Text("取餐标记(新队头)", font_size=15, font="Microsoft YaHei", color=GREEN).next_to(target_arrow, DOWN, buff=0.1)
            target_pickup_group = VGroup(target_arrow, target_label)

            self.play(
                Transform(pickup_group, target_pickup_group),
                slots[3].animate.set_color(GREEN),
                s4_text.animate.set_color(GREEN),
                run_time=1.2
            )
            self.wait(max(0.1, tracker.duration - 1.2))

        # 淡出生活实例资产，为后续算法代码演示腾出干净空间
        self.play(
            FadeOut(example_title),
            FadeOut(conveyor),
            FadeOut(slots),
            FadeOut(s_texts),
            FadeOut(empty_text),
            FadeOut(pickup_group),
            run_time=0.6
        )

        # ===========================
        # C++ 代码区
        # ===========================
        c_lines = [
            "Status DeQueue(SqQueue &Q, QElemType &e)",
            "{",
            "    if (Q.front == Q.rear)",
            "        return ERROR;",
            "    e = Q.base[Q.front];",
            "    Q.front = (Q.front + 1) % MAXQSIZE;",
            "    return OK;",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(
                stripped_line,
                font_size=12,
                font="Consolas",
                color=WHITE
            )
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(
            DOWN,
            aligned_edge=LEFT,
            buff=0.18
        )

        SPACE_WIDTH = 0.095
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        code_bg = RoundedRectangle(
            corner_radius=0.2,
            height=code_group.get_height() + 0.6,
            width=code_group.get_width() * 1.2 + 0.8,
            color=GRAY,
            fill_opacity=0.1,
            stroke_width=1
        )
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.4)
        code_bg.match_y(code_group)

        code_block = (
            VGroup(code_bg, code_group)
            .next_to(logo, DOWN, buff=0.3)
            .to_edge(RIGHT, buff=0.35)
            .shift(DOWN * 0.25)
        )

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line:
                return []

            anims = []

            if self.current_line is not None:
                anims.append(
                    self.c_texts[self.current_line]
                    .animate
                    .set_color(WHITE)
                    .scale(1 / 1.2, about_edge=LEFT)
                )

            if new_idx is not None:
                anims.append(
                    self.c_texts[new_idx]
                    .animate
                    .set_color(YELLOW)
                    .scale(1.2, about_edge=LEFT)
                )

                if not hasattr(self, "code_pointer"):
                    self.code_pointer = (
                        Triangle(fill_opacity=1, color=YELLOW)
                        .scale(0.15)
                        .rotate(-PI / 2)
                    )
                    self.code_pointer.next_to(
                        self.c_texts[new_idx],
                        LEFT,
                        buff=0.2
                    )
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(
                        self.c_texts[new_idx],
                        LEFT,
                        buff=0.2
                    )
                    anims.append(MoveToTarget(self.code_pointer))

                self.current_line = new_idx

            else:
                if hasattr(self, "code_pointer"):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, "code_pointer")

                self.current_line = None

            return anims

        with self.voiceover(
            text="右侧是循环队列出队算法的 C++ 实现。",
            subcaption="右侧是循环队列出队算法的 C++ 实现。"
        ) as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # ===========================
        # 循环队列图示
        # ===========================
        MAXQSIZE = 6
        box_side = 0.8

        boxes = VGroup(
            *[
                Square(side_length=box_side, color=BLUE)
                for _ in range(MAXQSIZE)
            ]
        )
        boxes.arrange(RIGHT, buff=0)
        boxes.move_to(LEFT * 3.5 + UP * 0.55)

        indices = VGroup()
        positions = VGroup()

        for i, box in enumerate(boxes):
            idx_txt = Text(
                str(i),
                font_size=20,
                color=GRAY
            ).next_to(box, DOWN, buff=0.2)

            pos_txt = Text(
                str(i + 1),
                font_size=20,
                color=GRAY
            ).next_to(box, UP, buff=0.2)

            indices.add(idx_txt)
            positions.add(pos_txt)

        pos_label = Text(
            "位置",
            font_size=20,
            color=GRAY
        ).next_to(positions[0], LEFT, buff=0.3)

        idx_label = Text(
            "索引",
            font_size=20,
            color=GRAY
        ).next_to(indices[0], LEFT, buff=0.3)

        val1 = Text("10", font_size=24, font="Arial", color=WHITE).move_to(boxes[0].get_center())
        val2 = Text("20", font_size=24, font="Arial", color=WHITE).move_to(boxes[1].get_center())
        val3 = Text("30", font_size=24, font="Arial", color=WHITE).move_to(boxes[2].get_center())

        def get_ptr(label, index, color, direction=UP):
            if np.array_equal(direction, UP):
                target = positions[index]
                arrow = Arrow(
                    start=target.get_top() + UP * 0.9,
                    end=target.get_top(),
                    buff=0.1,
                    color=color
                )
                txt = Text(
                    label,
                    font_size=20,
                    font="Arial",
                    color=color
                ).next_to(arrow, UP, buff=0.12)
            else:
                target = indices[index]
                arrow = Arrow(
                    start=target.get_bottom() + DOWN * 1.05,
                    end=target.get_bottom(),
                    buff=0.12,
                    color=color
                )
                txt = Text(
                    label,
                    font_size=20,
                    font="Arial",
                    color=color
                ).next_to(arrow, DOWN, buff=0.14)

            return VGroup(arrow, txt)

        front_idx = 0
        rear_idx = 3

        front_ptr = get_ptr("front", front_idx, GREEN, direction=DOWN)
        rear_ptr = get_ptr("rear", rear_idx, ORANGE, direction=UP)

        with self.voiceover(text="假设队列的最大容量为6，我们用一维数组表示循环队列。") as tracker:
            self.play(
                FadeIn(boxes),
                FadeIn(indices),
                FadeIn(positions),
                FadeIn(pos_label),
                FadeIn(idx_label),
                run_time=max(0.5, tracker.duration - 0.5)
            )

        with self.voiceover(text="当前队列中有三个元素，分别是10、20和30。front指向队头元素10，rear指向队尾后面的空闲位置。") as tracker:
            self.play(
                FadeIn(val1),
                FadeIn(val2),
                FadeIn(val3),
                FadeIn(front_ptr),
                FadeIn(rear_ptr),
                run_time=tracker.duration
            )

        # ===========================
        # 第一步：判断队空
        # ===========================
        with self.voiceover(text="第一步，判断队列是否为空。") as tracker:
            self.play(*get_track_anims(2), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.5))

        calc_text = Text(
            "front = 0, rear = 3, front != rear",
            font_size=22,
            font="Consolas",
            color=YELLOW
        ).next_to(boxes, UP, buff=1.55)

        with self.voiceover(text="队空的条件是front等于rear。现在front不等于rear，队列不为空，可以执行出队操作。") as tracker:
            self.play(Write(calc_text), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(text="如果队列为空，就直接返回ERROR。当前队列不为空，所以继续执行。") as tracker:
            self.play(FadeOut(calc_text), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.5))

        # ===========================
        # 第二步：保存队头元素
        # ===========================
        out_text = VGroup(
            Text("保存队头元素：", font_size=24, color=YELLOW),
            Text("e = 10", font_size=24, font="Consolas", color=YELLOW)
        ).arrange(RIGHT, buff=0.1).move_to(LEFT * 3.5 + DOWN * 2.15)

        with self.voiceover(text="第二步，保存队头元素。也就是把front当前指向的位置中的元素赋值给e。") as tracker:
            self.play(*get_track_anims(4), run_time=0.5)
            self.play(
                boxes[0].animate.set_color(YELLOW),
                val1.animate.set_color(YELLOW),
                FadeIn(out_text),
                run_time=max(0.5, tracker.duration - 0.5)
            )

        # ===========================
        # 第三步：front 加 1
        # ===========================
        with self.voiceover(text="第三步，队头指针front加1。由于是循环队列，所以需要对最大容量取余。") as tracker:
            self.play(*get_track_anims(5), run_time=0.5)

            front_idx = (front_idx + 1) % MAXQSIZE

            front_ptr.generate_target()
            front_ptr.target = get_ptr("front", front_idx, GREEN, direction=DOWN)

            self.play(
                MoveToTarget(front_ptr),
                val1.animate.set_opacity(0.25),
                boxes[0].animate.set_color(BLUE),
                run_time=max(0.7, tracker.duration - 0.5)
            )

        move_text = Text(
            "front = (0 + 1) % 6 = 1",
            font_size=22,
            font="Consolas",
            color=GREEN
        ).next_to(boxes, UP, buff=1.55)

        with self.voiceover(text="此时front从0移动到1，原来的队头元素10完成出队。") as tracker:
            self.play(Write(move_text), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        # ===========================
        # 返回 OK
        # ===========================
        res_panel = VGroup(
            Text("结果：", font_size=22, color=GREEN),
            Text("出队成功，返回 OK，e = 10", font_size=20, color=GREEN)
        ).arrange(RIGHT, buff=0.1).move_to(LEFT * 4.25 + DOWN * 2.45)

        with self.voiceover(text="最后返回OK，表示出队操作成功完成。") as tracker:
            self.play(
                FadeOut(move_text),
                FadeOut(out_text),
                *get_track_anims(6),
                Write(res_panel),
                run_time=tracker.duration
            )

        self.play(*get_track_anims(None), run_time=0.5)

        # ===========================
        # 复杂度分析
        # 放在结果右边
        # ===========================
        time_box = VGroup(
            Text("时间复杂度：", font_size=20, color=YELLOW),
            Text("O(1)", font_size=20, font="Consolas", color=YELLOW)
        ).arrange(RIGHT, buff=0.08).next_to(res_panel, RIGHT, buff=0.35)

        space_box = VGroup(
            Text("空间复杂度：", font_size=20, color=YELLOW),
            Text("O(1)", font_size=20, font="Consolas", color=YELLOW)
        ).arrange(RIGHT, buff=0.08).next_to(time_box, RIGHT, buff=0.3)

        with self.voiceover(
            text="循环队列的出队只需要一次判空、一次取值和一次指针运算，所以时间复杂度为O一。",
            subcaption="循环队列的出队只需要一次判空、一次取值和一次指针运算，所以时间复杂度为O(1)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
            text="同时，算法只使用了常数级辅助空间，所以空间复杂度也是O（1）。",
            subcaption="同时，算法没有使用额外空间，所以空间复杂度也是O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是循环队列出队算法的执行演示。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)