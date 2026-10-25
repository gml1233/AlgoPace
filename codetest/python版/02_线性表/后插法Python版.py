# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import numpy as np
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class LinkedListBase(VoiceoverScene):
    """单链表动画公共基类（带头结点，链表head指向头结点）
    提供统一的链表可视化、遍历指针、结点高亮、插入和删除动画方法等
    """

    # ========== 颜色规范 ==========
    COLOR_DEFAULT = BLUE
    COLOR_HEAD = PURPLE
    COLOR_CURRENT = YELLOW
    COLOR_TARGET = RED
    COLOR_INSERT = GREEN
    COLOR_L_PTR = ORANGE

    # ========== 布局参数 ==========
    NODE_WIDTH = 1.2
    NODE_HEIGHT = 0.8
    NODE_SPACING = 1.6
    FONT_SIZE = 32

    def setup(self):
        self.nodes = []
        self.node_mobjects = VGroup()
        self.arrows = VGroup()

    def set_tail(self, node, is_tail=True):
        if is_tail:
            if hasattr(node, 'dot'):
                node.dot.set_opacity(0)
            if hasattr(node, 'tail_marker'):
                node.tail_marker.set_opacity(1)
        else:
            if hasattr(node, 'dot'):
                node.dot.set_opacity(1)
            if hasattr(node, 'tail_marker'):
                node.tail_marker.set_opacity(0)

    def create_node(self, value_str, color=COLOR_DEFAULT, is_tail=False):
        node_group = VGroup()

        rect = Rectangle(width=self.NODE_WIDTH, height=self.NODE_HEIGHT, color=color)

        divider_x = self.NODE_WIDTH / 4
        divider = Line(
            start=rect.get_top() + RIGHT * divider_x,
            end=rect.get_bottom() + RIGHT * divider_x,
            color=color
        )

        val_text = Text(str(value_str), font_size=self.FONT_SIZE, font="Arial")
        val_text.move_to(rect.get_center() + LEFT * (self.NODE_WIDTH / 8))

        dot_center = rect.get_center() + RIGHT * (self.NODE_WIDTH * 3 / 8)
        dot = Dot(radius=0.04, color=color).move_to(dot_center)

        tail_marker = Text("^", font_size=self.FONT_SIZE, color=color).move_to(dot_center)

        if is_tail:
            dot.set_opacity(0)
            tail_marker.set_opacity(1)
        else:
            dot.set_opacity(1)
            tail_marker.set_opacity(0)

        node_group.add(rect, divider, val_text, tail_marker, dot)
        node_group.tail_marker = tail_marker
        node_group.dot = dot

        node_group.rect = rect
        node_group.divider = divider
        node_group.val_text = val_text
        node_group.value = value_str

        return node_group

    def create_arrow_between(self, node1, node2, color=WHITE, end_pos=None):
        target_pos = end_pos if end_pos is not None else node2.get_left()
        return Arrow(
            start=node1.dot.get_center(),
            end=target_pos,
            buff=0,
            color=color,
            max_tip_length_to_length_ratio=0.15
        )

    def add_pointer_head(self, label="head"):
        head_node = self.nodes[0]
        l_text = Text(label, font_size=26, color=self.COLOR_L_PTR)

        l_arrow = Arrow(
            start=head_node.get_left() + LEFT * 1.0,
            end=head_node.get_left(),
            buff=0,
            color=self.COLOR_L_PTR
        )
        l_text.next_to(l_arrow.get_start(), LEFT, buff=0.15)

        new_L_pointer = VGroup(l_text, l_arrow)
        if hasattr(self, 'L_pointer'):
            self.play(ReplacementTransform(self.L_pointer, new_L_pointer))
            self.L_pointer = new_L_pointer
        else:
            self.L_pointer = new_L_pointer
            self.play(FadeIn(self.L_pointer))

    def create_pointer(self, node, label_text, color=COLOR_CURRENT, direction=DOWN, offset=0):
        text = Text(label_text, font_size=self.FONT_SIZE, color=color)
        shift_left = LEFT * offset

        if direction[1] < 0:
            arrow = Arrow(
                start=node.get_bottom() + shift_left + DOWN * 1.0,
                end=node.get_bottom() + shift_left,
                buff=0,
                color=color
            )
            text.next_to(arrow.get_start(), DOWN, buff=0.2)
        else:
            arrow = Arrow(
                start=node.get_top() + shift_left + UP * 1.0,
                end=node.get_top() + shift_left,
                buff=0,
                color=color
            )
            text.next_to(arrow.get_start(), UP, buff=0.2)

        ptr_group = VGroup(text, arrow)
        ptr_group.text_obj = text
        ptr_group.arrow_obj = arrow
        return ptr_group

    def reset_node_color(self, index, run_time=0.5):
        color = self.COLOR_HEAD if index == 0 else self.COLOR_DEFAULT
        node = self.nodes[index]
        self.play(
            node.rect.animate.set_color(color),
            node.divider.animate.set_color(color),
            node.dot.animate.set_color(color),
            run_time=run_time
        )


class ContinuousTailInsertPythonVideo(LinkedListBase):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角全局图片 Logo
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # 火车烟雾追踪器
        smoke_tracker = ValueTracker(0)
        smoke_opacity_tracker = ValueTracker(0)
        self.add(smoke_tracker)
        smoke_tracker.add_updater(lambda m, dt: m.increment_value(dt * 0.8))

        # ===== PHASE A — OPENING =====
        algo_title = Text("后插法创建单链表（Python版）", font_size=38, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.5).shift(LEFT * 0.6)
        self.add(algo_title)

        sentences = [
            "本节我们将学习使用后插法创建单链表的 Python 版。",
            "该算法是通过将新结点逐个插入到链表的尾部来创建链表。"
        ]
        for sentence in sentences:
            with self.voiceover(text=sentence) as tracker:
                self.wait(tracker.duration)

        # ===== NEW PHASE — VIVID ANALOGY (组装火车生活实例) =====
        with self.voiceover(text="先来看一个生活实例：通过在尾部逐节加挂车厢，来从零组装一列火车。") as tracker:

            def create_beautified_train_car(color, text, is_head=False):
                car_w, car_h = 1.8, 1.1
                car_group = VGroup()

                body = RoundedRectangle(
                    corner_radius=0.12, width=car_w, height=car_h, color=color,
                    fill_color=color, fill_opacity=0.25, stroke_width=3
                )
                car_group.add(body)

                if is_head:
                    window = Rectangle(width=0.4, height=0.4, color=color, fill_color=WHITE, fill_opacity=0.7,
                                       stroke_width=1.5)
                    window.move_to(body.get_center() + LEFT * 0.45 + UP * 0.2)
                    decor_line = Line(body.get_left() + UP * 0.1, body.get_right() + UP * 0.1, color=color,
                                      stroke_width=1.5)
                    chimney = RoundedRectangle(corner_radius=0.04, width=0.22, height=0.36, color=color,
                                               fill_color=color, fill_opacity=0.7, stroke_width=2)
                    chimney.move_to(body.get_top() + LEFT * 0.18 + UP * 0.16)

                    smoke_group = always_redraw(lambda: VGroup(
                        Circle(radius=0.08 + (smoke_tracker.get_value() % 1) * 0.08, color=LIGHT_GRAY, stroke_width=0,
                               fill_opacity=smoke_opacity_tracker.get_value() * 0.6 * (
                                           1 - (smoke_tracker.get_value() % 1))).move_to(
                            chimney.get_top() + RIGHT * 0.18 + UP * 0.18 + (RIGHT * 0.1 + UP * 0.1) * (
                                        smoke_tracker.get_value() % 1)),
                        Circle(radius=0.12 + ((smoke_tracker.get_value() + 0.3) % 1) * 0.1, color=LIGHT_GRAY,
                               stroke_width=0, fill_opacity=smoke_opacity_tracker.get_value() * 0.5 * (
                                        1 - ((smoke_tracker.get_value() + 0.3) % 1))).move_to(
                            chimney.get_top() + RIGHT * 0.42 + UP * 0.42 + (RIGHT * 0.15 + UP * 0.15) * (
                                        (smoke_tracker.get_value() + 0.3) % 1)),
                        Circle(radius=0.17 + ((smoke_tracker.get_value() + 0.6) % 1) * 0.12, color=LIGHT_GRAY,
                               stroke_width=0, fill_opacity=smoke_opacity_tracker.get_value() * 0.4 * (
                                        1 - ((smoke_tracker.get_value() + 0.6) % 1))).move_to(
                            chimney.get_top() + RIGHT * 0.72 + UP * 0.72 + (RIGHT * 0.2 + UP * 0.2) * (
                                        (smoke_tracker.get_value() + 0.6) % 1))
                    ))

                    car_group.add(window, decor_line, chimney, smoke_group)
                    car_group.chimney = chimney
                    car_group.smoke_group = smoke_group
                else:
                    window1 = Rectangle(width=0.35, height=0.35, color=color, fill_color=WHITE, fill_opacity=0.6,
                                        stroke_width=1.5)
                    window1.move_to(body.get_center() + LEFT * 0.4 + UP * 0.15)
                    window2 = Rectangle(width=0.35, height=0.35, color=color, fill_color=WHITE, fill_opacity=0.6,
                                        stroke_width=1.5)
                    window2.move_to(body.get_center() + RIGHT * 0.4 + UP * 0.15)
                    car_group.add(window1, window2)

                wheel_y = body.get_bottom()[1] - 0.05
                wheel1 = Circle(radius=0.18, color=GRAY_D, fill_color=LIGHT_GRAY, fill_opacity=1, stroke_width=2.5)
                wheel1.move_to([body.get_center()[0] - 0.5, wheel_y, 0])
                wheel2 = Circle(radius=0.18, color=GRAY_D, fill_color=LIGHT_GRAY, fill_opacity=1, stroke_width=2.5)
                wheel2.move_to([body.get_center()[0] + 0.5, wheel_y, 0])

                w_dot1 = Dot(wheel1.get_center(), radius=0.04, color=GRAY_D)
                w_dot2 = Dot(wheel2.get_center(), radius=0.04, color=GRAY_D)

                label = Text(text, font_size=18, font="Sans", weight=BOLD, color=WHITE).move_to(
                    body.get_center() + DOWN * 0.25)
                car_group.add(wheel1, wheel2, w_dot1, w_dot2, label)

                car_group.body = body
                return car_group

            def move_train_car_body_to(car, target_pos):
                car.shift(np.array(target_pos) - car.body.get_center())
                return car

            def create_beautified_coupler(start_pt, end_pt, color=GRAY):
                line = Line(start_pt, end_pt, color=color, stroke_width=4)
                center_dot = Dot(line.get_center(), radius=0.06, color=color)
                return VGroup(line, center_dot)

            TRAIN_Y = 0.2

            locomotive = move_train_car_body_to(create_beautified_train_car(self.COLOR_HEAD, "火车头", is_head=True),
                                                [-2.6, TRAIN_Y, 0])

            r_arrow_anlg = Arrow(start=locomotive.body.get_top() + UP * 0.8, end=locomotive.body.get_top(), buff=0,
                                 color=GREEN)
            r_text_anlg = Text("r", font_size=28, color=GREEN).next_to(r_arrow_anlg.get_start(), UP, buff=0.1)
            r_ptr_anlg = VGroup(r_text_anlg, r_arrow_anlg)

            self.play(
                FadeIn(locomotive, shift=RIGHT * 0.3),
                FadeIn(r_ptr_anlg),
                smoke_opacity_tracker.animate.set_value(1),
                run_time=1.5
            )

        with self.voiceover(text="初始时，只有孤零零的一个火车头。尾指针r也同时指向它，代表当前的火车尾部。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="当运来第一节新车厢10时，我们将其加挂到当前尾指针r所指车厢的后面。") as tracker:
            car_10 = move_train_car_body_to(create_beautified_train_car(BLUE, "车厢 10"), [0.0, TRAIN_Y, 0])
            self.play(FadeIn(car_10, shift=LEFT * 0.5), run_time=1.2)

        with self.voiceover(text="连接挂钩，将车厢10固定在火车尾部。") as tracker:
            coupler1 = create_beautified_coupler(locomotive.body.get_right(), car_10.body.get_left(), WHITE)
            self.play(Create(coupler1), run_time=1.0)

        with self.voiceover(text="挂载完毕后，尾指针r随之向后移动，指向这个全新的尾部车厢。") as tracker:
            r_arrow_target1 = Arrow(start=car_10.body.get_top() + UP * 0.8, end=car_10.body.get_top(), buff=0,
                                    color=GREEN)
            r_text_target1 = Text("r", font_size=28, color=GREEN).next_to(r_arrow_target1.get_start(), UP, buff=0.1)
            r_ptr_target1 = VGroup(r_text_target1, r_arrow_target1)
            self.play(ReplacementTransform(r_ptr_anlg, r_ptr_target1), run_time=1.0)
            r_ptr_anlg = r_ptr_target1

        with self.voiceover(text="随后，又运来一节新车厢20。同样将其加挂到当前r指针所指的尾部后面。") as tracker:
            car_20 = move_train_car_body_to(create_beautified_train_car(BLUE, "车厢 20"), [2.6, TRAIN_Y, 0])
            self.play(FadeIn(car_20, shift=LEFT * 0.5), run_time=1.2)

        with self.voiceover(text="再次建立连接。") as tracker:
            coupler2 = create_beautified_coupler(car_10.body.get_right(), car_20.body.get_left(), WHITE)
            self.play(Create(coupler2), run_time=1.0)

        with self.voiceover(text="随后尾指针r再次更新，向后移动，始终保持指向最新的火车尾部。") as tracker:
            r_arrow_target2 = Arrow(start=car_20.body.get_top() + UP * 0.8, end=car_20.body.get_top(), buff=0,
                                    color=GREEN)
            r_text_target2 = Text("r", font_size=28, color=GREEN).next_to(r_arrow_target2.get_start(), UP, buff=0.1)
            r_ptr_target2 = VGroup(r_text_target2, r_arrow_target2)
            self.play(ReplacementTransform(r_ptr_anlg, r_ptr_target2), run_time=1.0)
            r_ptr_anlg = r_ptr_target2

        with self.voiceover(
                text="以此类推，通过在尾部不断加挂新车厢，就能依次组装好整列火车。这与后插法创建单链表的逻辑完全一致。下面我们学习代码实现。") as tracker:
            self.wait(tracker.duration)

        # 优雅淡出火车资产
        self.play(
            VGroup(locomotive, car_10, car_20, coupler1, coupler2, r_ptr_anlg).animate.fade(1),
            smoke_opacity_tracker.animate.set_value(0),
            run_time=1.0
        )
        self.remove(locomotive, car_10, car_20, coupler1, coupler2, r_ptr_anlg)
        smoke_tracker.clear_updaters()

        # ===== PHASE B — CODE BLOCK =====
        c_lines = [
            "def create_list_r(self, l_data):",
            "    r = self.head",
            "    for data in l_data:",
            "        p = LNode(data)",
            "        r.next = p",
            "        r = r.next"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip("  ")
            t = Text(stripped_line, font_size=13, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.2)

        SPACE_WIDTH = 0.105
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip("  "))
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

        # 代码块位置设定
        code_block = VGroup(code_bg, code_group).to_edge(RIGHT, buff=0.35).shift(UP * 0.0)

        input_params = VGroup(
            Text("参数：", font_size=24, font="Microsoft YaHei", color=YELLOW),
            Text("l_data = [10, 20, 30]", font_size=18, font="Consolas", color=YELLOW)
        ).arrange(RIGHT, buff=0.15).next_to(code_block, DOWN, buff=0.2).align_to(code_block, LEFT)

        self.current_line = None

        def get_track_anims(new_idx):
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

        with self.voiceover(text="假设我们需要根据列表数据创建包含3个元素的单链表。") as tracker:
            self.play(FadeIn(code_block), FadeIn(input_params), run_time=tracker.duration)
        self.wait(0.5)

        # ===== PHASE C — INITIALIZATION =====
        with self.voiceover(text="首先，单链表已初始化包含一个头结点，头指针 head 指向头结点。") as tracker:
            head_node = self.create_node("", color=self.COLOR_HEAD, is_tail=True)
            head_node.move_to(LEFT * 4 + UP * 0.2)
            self.play(FadeIn(head_node))

            self.nodes.append(head_node)
            self.node_mobjects.add(head_node)

            self.add_pointer_head(label="head")
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(text="执行 r 等于 self.head，设置尾指针r，初始时指向头结点。") as tracker:
            self.play(*get_track_anims(1), run_time=1.0)
            r_ptr = self.create_pointer(head_node, "r", color=GREEN, direction=UP, offset=0.0)
            self.play(FadeIn(r_ptr))
            self.wait(max(0.1, tracker.duration - 1.0))

        # ===== PHASE D — LOOP AND INSERTION =====
        input_values = [10, 20, 30]
        input_queue_box = Rectangle(width=3, height=1, color=WHITE).move_to(DOWN * 1.8 + LEFT * 4.5)
        queue_label = Text("输入列表 l_data", font_size=20, font="Microsoft YaHei").next_to(input_queue_box, UP, buff=0.15)

        data_texts = VGroup(*[Text(str(val), font_size=28, font="Arial") for val in input_values]).arrange(RIGHT,
                                                                                                           buff=0.5).move_to(
            input_queue_box)

        with self.voiceover(text="准备进入for循环，依次读入列表中的数据元素，建立单链表。") as tracker:
            self.play(*get_track_anims(2), FadeIn(input_queue_box), FadeIn(queue_label), FadeIn(data_texts),
                      run_time=tracker.duration)

        for i, val in enumerate(input_values):
            data_text = data_texts[i]

            with self.voiceover(text=f"接下来插入新结点{val}。") as tracker:
                self.wait(tracker.duration)

            with self.voiceover(text=f"生成新结点p，并将数据元素 {val} 赋值给它的数据域。") as tracker:
                self.play(*get_track_anims(3), run_time=0.8)

                prev_node = self.nodes[-1]
                new_node = self.create_node("", color=self.COLOR_INSERT, is_tail=True)
                new_node.move_to(prev_node.get_center() + RIGHT * self.NODE_SPACING)

                p_ptr = self.create_pointer(new_node, "p", color=self.COLOR_CURRENT, direction=DOWN, offset=0.0)

                self.play(FadeIn(new_node), FadeIn(p_ptr), run_time=0.8)

                target_val_text = Text(str(val), font_size=self.FONT_SIZE, font="Arial").move_to(
                    new_node.rect.get_center() + LEFT * (self.NODE_WIDTH / 8))

                self.play(data_text.animate.move_to(target_val_text.get_center()), run_time=0.8)

                new_node.val_text.become(target_val_text)
                self.remove(data_text)

                self.wait(max(0.1, tracker.duration - 2.4))

            with self.voiceover(text="执行 r.next 等于 p，将新结点p插入到尾结点r之后。") as tracker:
                self.play(*get_track_anims(4), run_time=0.8)
                self.set_tail(prev_node, is_tail=False)
                new_arrow = self.create_arrow_between(prev_node, new_node, color=WHITE)
                self.arrows.add(new_arrow)
                self.play(GrowArrow(new_arrow), run_time=0.8)
                self.wait(max(0.1, tracker.duration - 1.6))

            with self.voiceover(text="执行 r 等于 r.next，尾指针r向后移动，指向新的尾结点p。") as tracker:
                self.play(*get_track_anims(5), run_time=0.8)

                target_r_ptr = self.create_pointer(new_node, "r", color=GREEN, direction=UP, offset=0.0)
                self.play(r_ptr.animate.move_to(target_r_ptr.get_center()), run_time=0.8)

                self.wait(max(0.1, tracker.duration - 1.6))

            # 结点完成插入，更新状态
            self.nodes.append(new_node)
            self.node_mobjects.add(new_node)

            # 为下一次循环做准备
            self.play(FadeOut(p_ptr))
            self.play(*get_track_anims(2), run_time=0.4)
            self.reset_node_color(len(self.nodes) - 1, run_time=0.4)

        # ===== 循环结束 =====
        with self.voiceover(text="所有数据元素插入完毕，退出循环。") as tracker:
            self.play(*get_track_anims(None), FadeOut(input_queue_box), FadeOut(queue_label), run_time=tracker.duration)

        # ===== PHASE E — COMPLEXITY =====
        complexity_panel = VGroup(
            VGroup(Text("时间复杂度：", font_size=24, font="Microsoft YaHei", color=YELLOW),
                   Text("O(n)", font_size=26, font="Consolas", color=YELLOW)).arrange(RIGHT, buff=0.1),
            VGroup(Text("空间复杂度：", font_size=24, font="Microsoft YaHei", color=YELLOW),
                   Text("O(1)", font_size=26, font="Consolas", color=YELLOW)).arrange(RIGHT, buff=0.1),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(LEFT * 3.5 + DOWN * 2)

        with self.voiceover(
                text="因为需要遍历整个输入序列，该算法的时间复杂度为 O n。此外仅使用了几个辅助指针变量，所以辅助空间复杂度为 O 一。",
                subcaption="因为需要遍历整个输入序列，该算法的时间复杂度为O(n)。此外仅使用了几个辅助指针变量，所以辅助空间复杂度为O(1)。"
        ) as tracker:
            self.play(FadeIn(complexity_panel), run_time=tracker.duration)

        with self.voiceover(text="这就是后插法创建单链表 Python 版的完整过程。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)


# Alias
TailInsertPythonVideo = ContinuousTailInsertPythonVideo
