# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class CircularQueueEnqueueVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角 Logo
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("循环队列的入队", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        # 总领句
        with self.voiceover(
                text="本节我们来学习循环队列的入队操作。该算法在循环队列的队尾插入一个新的元素。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== NEW PHASE — LIFE EXAMPLE (旋转寿司的补位) =====
        # =========================================================================
        example_title = Text("生活实例：旋转寿司的补位", font_size=32, font="Microsoft YaHei", color=YELLOW).to_edge(UP,
                                                                                                                    buff=1.5)

        # 用一个大圆形模拟旋转寿司的传送带
        conveyor = Circle(radius=1.5, color=BLUE, stroke_width=4).move_to(LEFT * 3.5 + DOWN * 0.5)

        # 在圆环上分布4个小盘子表示槽位
        angles = [0, PI / 2, PI, 3 * PI / 2]
        slots = VGroup(
            *[Circle(radius=0.3, color=GRAY_A, fill_opacity=0.4).move_to(conveyor.point_at_angle(a)) for a in angles])

        s1_text = Text("寿司", font_size=14, font="Microsoft YaHei").move_to(slots[0].get_center())
        s2_text = Text("寿司", font_size=14, font="Microsoft YaHei").move_to(slots[1].get_center())
        s3_text = Text("空位", font_size=14, font="Microsoft YaHei", color=GRAY).move_to(
            slots[2].get_center())  # 准备放入的空位
        s4_text = Text("寿司", font_size=14, font="Microsoft YaHei").move_to(slots[3].get_center())

        s_texts = VGroup(s1_text, s2_text, s3_text, s4_text)

        # 厨师放寿司的入口标记（相当于尾指针 rear）
        chef_arrow = Arrow(start=slots[2].get_left() + LEFT * 0.6, end=slots[2].get_left(), buff=0.05, color=ORANGE)
        chef_label = Text("厨师放置位", font_size=16, font="Microsoft YaHei", color=ORANGE).next_to(chef_arrow, LEFT,
                                                                                                    buff=0.1)
        chef_group = VGroup(chef_arrow, chef_label)

        with self.voiceover(
                text="我们可以把循环队列想象成一个圆形的旋转寿司传送带，传送带上的槽位是固定且首尾相连的。") as tracker:
            self.play(FadeIn(example_title), Create(conveyor), FadeIn(slots), FadeIn(s_texts), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(
                text="厨师守在固定的放置位。当传送带转动时，只要当前转过来的是一个空位，厨师就可以把一盘新寿司放上去。") as tracker:
            self.play(FadeIn(chef_group), run_time=0.4)
            # 模拟放入新寿司，文字由“空位”变为“新寿司”并高亮
            new_s_text = Text("新寿司", font_size=14, font="Microsoft YaHei", color=YELLOW).move_to(
                slots[2].get_center())
            self.play(Transform(s3_text, new_s_text), slots[2].animate.set_color(YELLOW),
                      run_time=max(0.1, tracker.duration - 0.4))

        with self.voiceover(
                text="寿司放好后，下一个槽位转过来成为新的放置点。这种首尾顺延、循环补位的过程，正是循环队列入队的写照。") as tracker:
            # 模拟传送带逆时针转动 90 度，让下一个槽位对准厨师
            full_conveyor_group = VGroup(slots, s_texts)
            self.play(Rotate(full_conveyor_group, angle=PI / 2, about_point=conveyor.get_center()), run_time=1.2)
            self.wait(max(0.1, tracker.duration - 1.2))

        # 动画结束，彻底清空生活实例资产，为算法演示腾出干净空间
        self.play(FadeOut(example_title), FadeOut(conveyor), FadeOut(slots), FadeOut(s_texts), FadeOut(chef_group),
                  run_time=0.5)

        # =========================================================================
        # ===== PHASE B — CODE BLOCK CONFIG =====
        # =========================================================================
        c_lines = [
            "Status EnQueue(SqQueue &Q, QElemType e)",
            "{",
            "    if ((Q.rear + 1) % MAXQSIZE == Q.front) {",
            "        return ERROR;",
            "    }",
            "    Q.base[Q.rear] = e;",
            "    Q.rear = (Q.rear + 1) % MAXQSIZE;",
            "    return OK;",
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

        bg_width = code_group.get_width() * 1.2 + 0.8
        bg_height = code_group.get_height() + 0.6
        code_bg = RoundedRectangle(corner_radius=0.2, height=bg_height, width=bg_width, color=GRAY, fill_opacity=0.1,
                                   stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.4)
        code_bg.match_y(code_group)

        # 优化：采用 next_to 挂载在 logo 下方，彻底避免向上遮挡标题和 logo
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.2).to_edge(RIGHT, buff=0.4)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line: return []
            anims = []
            if self.current_line is not None:
                anims.append(self.c_texts[self.current_line].animate.set_color(WHITE).scale(1 / 1.2, about_edge=LEFT))
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

        with self.voiceover(text="右侧是入队算法的 C 语言实现，让我们结合动态图示来拆解这个过程。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # =========================================================================
        # ===== PHASE C — VISUALIZATION SETUP =====
        # =========================================================================
        MAXQSIZE = 6
        box_side = 0.8
        boxes = VGroup(*[Square(side_length=box_side, color=BLUE) for _ in range(MAXQSIZE)])
        boxes.arrange(RIGHT, buff=0)
        boxes.move_to(LEFT * 3.5 + UP * 0.5)

        indices = VGroup()
        positions = VGroup()
        for i, box in enumerate(boxes):
            idx_txt = Text(str(i), font_size=20, color=GRAY).next_to(box, DOWN, buff=0.2)
            indices.add(idx_txt)
            pos_txt = Text(str(i + 1), font_size=20, color=GRAY).next_to(box, UP, buff=0.2)
            positions.add(pos_txt)

        val1 = Text("10", font_size=24, font="Arial", color=WHITE).move_to(boxes[0].get_center())
        val2 = Text("20", font_size=24, font="Arial", color=WHITE).move_to(boxes[1].get_center())
        val3 = Text("30", font_size=24, font="Arial", color=WHITE).move_to(boxes[2].get_center())

        pos_label = Text("位置", font_size=20, font="Microsoft YaHei", color=GRAY).next_to(positions[0], LEFT, buff=0.3)
        idx_label = Text("索引", font_size=20, font="Microsoft YaHei", color=GRAY).next_to(indices[0], LEFT, buff=0.3)

        queue_group = VGroup(boxes, indices, positions, val1, val2, val3, pos_label, idx_label)

        def get_ptr(label, index, color, direction=UP):
            if np.array_equal(direction, UP):
                target = positions[index]
                arrow = Arrow(start=target.get_top() + UP * 0.8, end=target.get_top(), buff=0.1, color=color)
                txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, UP, buff=0.1)
            else:
                target = indices[index]
                arrow = Arrow(start=target.get_bottom() + DOWN * 0.8, end=target.get_bottom(), buff=0.1, color=color)
                txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, DOWN, buff=0.1)
            return VGroup(arrow, txt)

        front_idx = 0
        rear_idx = 3
        front_ptr = get_ptr("front", front_idx, GREEN, direction=DOWN)
        rear_ptr = get_ptr("rear", rear_idx, ORANGE, direction=UP)

        with self.voiceover(text="假设队列的最大容量为 6，我们通过一维数组来存储数据。") as tracker:
            self.play(FadeIn(boxes), FadeIn(indices), FadeIn(positions), FadeIn(pos_label), FadeIn(idx_label),
                      run_time=max(0.5, tracker.duration - 0.5))

        with self.voiceover(
                text="当前队列中已经有三个元素。头指针 front 指向索引 0 的队头元素，而尾指针 rear 指向索引 3 的空闲位置。") as tracker:
            self.play(FadeIn(val1, val2, val3), FadeIn(front_ptr), FadeIn(rear_ptr), run_time=tracker.duration)

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW =====
        # =========================================================================
        # 第一步：判空
        with self.voiceover(
                text="在入队前，需要判断队列是否已满。为了区分队空和队满，循环队列通常牺牲一个存储单元。") as tracker:
            self.play(*get_track_anims(2), run_time=0.4)
            self.wait(tracker.duration - 0.4)

        with self.voiceover(text="判满条件是：尾指针加 1 对最大容量取余后，是否等于头指针。") as tracker:
            calc_text = MathTex(r"(3 + 1) \bmod 6 = 4 \neq 0", font_size=32, color=YELLOW).next_to(boxes, UP, buff=2)
            self.play(Write(calc_text), run_time=0.5)
            self.wait(tracker.duration - 0.5)

        with self.voiceover(text="计算结果表明队未满，不会进入溢出错误的处理分支。") as tracker:
            self.play(*get_track_anims(3), run_time=0.3)
            self.play(*get_track_anims(4), run_time=0.3)
            self.play(FadeOut(calc_text), run_time=0.3)
            self.wait(tracker.duration - 0.9)

        # 第二步：入队
        with self.voiceover(text="接下来，将新元素插入队尾，也就是 rear 当前指向的位置。") as tracker:
            self.play(*get_track_anims(5), run_time=0.4)
            new_val = Text("40", font_size=24, font="Arial", color=YELLOW).move_to(boxes[rear_idx].get_center())
            self.play(FadeIn(new_val, shift=DOWN * 0.3), run_time=max(0.2, tracker.duration - 0.4))

        # 第三步：尾指针加 1 取余
        with self.voiceover(text="随后，将尾指针 rear 的数值加 1。因为是循环队列，所以需要再次使用取余运算。") as tracker:
            self.play(*get_track_anims(6), run_time=0.4)
            rear_idx = (rear_idx + 1) % MAXQSIZE
            rear_ptr.generate_target()
            rear_ptr.target = get_ptr("rear", rear_idx, ORANGE, direction=UP)
            self.play(MoveToTarget(rear_ptr), run_time=max(0.5, tracker.duration - 0.4))

        # 第四步：返回 OK
        # 优化：采用独立横向排列，向左侧推移，完美避开右侧代码面板，高度建立在极其安全的安全线上（DOWN * 1.6）
        res_panel = VGroup(
            Text("结果：", font_size=22, font="Microsoft YaHei", color=GREEN),
            Text("入队成功，返回 OK", font_size=20, font="Microsoft YaHei", color=GREEN)
        ).arrange(RIGHT, buff=0.1).move_to(LEFT * 4.0 + DOWN * 1.6)

        with self.voiceover(text="到这里，元素入队操作成功完成。") as tracker:
            self.play(*get_track_anims(7), Write(res_panel), run_time=tracker.duration)

        self.play(*get_track_anims(None), run_time=0.5)

        # =========================================================================
        # ===== PHASE E — COMPLEXITY =====
        # =========================================================================
        # 优化：紧随结果面板右侧进行水平排列，高度随之抬升，彻底规避视频底部沉底字幕的遮挡
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(res_panel,
                                                                                                        RIGHT, buff=0.6)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(time_box,
                                                                                                         RIGHT,
                                                                                                         buff=0.4)

        with self.voiceover(
                text="循环队列的入队只需要执行一次数组赋值和一次指针运算，并没有涉及到元素的移动，所以时间复杂度是 O(1)。",
                subcaption="循环队列的入队只需要执行一次数组赋值和一次指针运算，并没有涉及到元素的移动，所以时间复杂度是 O(1)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
                text="同样，由于运算中不需要借助额外的大小随数据规模变化的辅助空间，空间复杂度也是 O(1)。",
                subcaption="同样，由于运算中不需要借助额外的大小随数据规模变化的辅助空间，空间复杂度也是 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是循环队列入队算法的执行演示。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)