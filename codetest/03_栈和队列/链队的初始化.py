# coding=utf-8
from manim import *
import numpy as np
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class LinkedQueueInitVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角 Logo
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("链队的初始化", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(text="本节学习链队的初始化算法。该算法用于构造一个空的链队，头结点的指针域置空") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== NEW PHASE — LIFE EXAMPLE (排队通道的建立) =====
        # =========================================================================
        example_title = Text("生活实例：排队通道的建立", font_size=32, font="Microsoft YaHei", color=YELLOW).to_edge(UP,
                                                                                                                    buff=1.5)

        # 构造取号机（相当于头结点）
        kiosk = Rectangle(width=1.2, height=1.6, color=PURPLE, fill_opacity=0.6)
        kiosk_text = Text("取号机", font_size=18, font="Microsoft YaHei").move_to(kiosk.get_center())
        kiosk_group = VGroup(kiosk, kiosk_text).move_to(LEFT * 4.0 + DOWN * 0.5)

        # 指向排队通道起点和终点的标记
        start_arrow = Arrow(start=kiosk_group.get_top() + UP * 0.6, end=kiosk_group.get_top(), buff=0.1, color=GREEN)
        start_text = Text("排队起点", font_size=16, font="Microsoft YaHei", color=GREEN).next_to(start_arrow, UP,
                                                                                                 buff=0.1)

        end_arrow = Arrow(start=kiosk_group.get_bottom() + DOWN * 0.6, end=kiosk_group.get_bottom(), buff=0.1,
                          color=ORANGE)
        end_text = Text("排队终点", font_size=16, font="Microsoft YaHei", color=ORANGE).next_to(end_arrow, DOWN,
                                                                                                buff=0.1)

        ptrs = VGroup(start_arrow, start_text, end_arrow, end_text)

        with self.voiceover(
                text="我们可以把队列想象成银行的排队系统。在银行开门、顾客到来之前，需要先准备好一台取号机。") as tracker:
            self.play(FadeIn(example_title), FadeIn(kiosk_group), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(
                text="此时大厅里空无一人，取号机所在的这个位置，既是整个排队序列的起点，也是终点。这正是链队的初始化。") as tracker:
            self.play(FadeIn(ptrs), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        # 动画结束，彻底清空生活实例相关的组件
        self.play(FadeOut(example_title), FadeOut(kiosk_group), FadeOut(ptrs), run_time=0.5)

        # =========================================================================
        # ===== PHASE B — CODE BLOCK CONFIG =====
        # =========================================================================
        c_lines = [
            "Status InitQueue(LinkQueue &Q)\n{//构造一个空队列Q",
            "    Q.front=Q.rear=new QNode;\n        //生成新节点作为头节点，队头和队尾指针指向此节点",
            "    Q.front->next=NULL;\n        //头节点的指针域置空",
            "    return OK;",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=12.0, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.13)
        SPACE_WIDTH = 0.095
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 6.25:
            code_group.scale_to_fit_width(6.25)
        if code_group.height > 5.4:
            code_group.scale_to_fit_height(5.4)
        bg_width = code_group.get_width() + 0.65
        bg_height = code_group.get_height() + 0.5
        code_bg = RoundedRectangle(corner_radius=0.2, height=bg_height, width=bg_width, color=GRAY, fill_opacity=0.1,
                                   stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.4)
        code_bg.match_y(code_group)

        # 优化：代码块紧贴 logo 下方，防止与标题和 logo 产生遮挡
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.2).to_edge(RIGHT, buff=0.4)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line: return [Wait(0.001)]
            anims = []
            if self.current_line is not None:
                anims.append(self.c_texts[self.current_line].animate.set_color(WHITE).scale(1 / 1.08, about_edge=LEFT))
            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW).scale(1.08, about_edge=LEFT))
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

        with self.voiceover(text="右侧是链队初始化算法的 C 语言实现代码。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # =========================================================================
        # ===== PHASE C — VISUALIZATION SETUP =====
        # =========================================================================
        def build_node(val_str, is_head=False, is_tail=False):
            color = PURPLE if is_head else BLUE
            data_box = Rectangle(width=1.1, height=0.8, color=color)
            ptr_box = Rectangle(width=0.4, height=0.8, color=color).next_to(data_box, RIGHT, buff=0)
            dot = Dot(radius=0.06, color=color).move_to(ptr_box.get_center())
            data_text = Text(val_str, font_size=24, font="Arial", color=WHITE).move_to(data_box.get_center())
            tail_marker = Text("^", font_size=24, color=color).move_to(ptr_box.get_center())

            if is_tail:
                dot.set_opacity(0)
                tail_marker.set_opacity(1)
            else:
                dot.set_opacity(1)
                tail_marker.set_opacity(0)

            node = VGroup(data_box, data_text, ptr_box, dot, tail_marker)
            node.dot = dot
            node.tail_marker = tail_marker
            return node

        def set_tail(node, is_tail=True):
            if is_tail:
                node.dot.set_opacity(0)
                node.tail_marker.set_opacity(1)
            else:
                node.dot.set_opacity(1)
                node.tail_marker.set_opacity(0)

        def get_ptr(label, target_mobj, color=GREEN, direction=UP):
            if np.array_equal(direction, UP):
                arrow = Arrow(start=target_mobj.get_top() + UP * 0.8, end=target_mobj.get_top(), buff=0.1, color=color)
                txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, UP, buff=0.1)
            else:
                arrow = Arrow(start=target_mobj.get_bottom() + DOWN * 0.8, end=target_mobj.get_bottom(), buff=0.1,
                              color=color)
                txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, DOWN, buff=0.1)
            return VGroup(arrow, txt)

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW =====
        # =========================================================================

        # 第一步：同时生成头结点，并让 front、rear 指向该结点
        with self.voiceover(
                text="第一步，生成一个新结点作为头结点，同时让队头指针 front 和队尾指针 rear 都指向这个结点。") as tracker:
            self.play(*get_track_anims(1), run_time=0.4)
            head = build_node("", is_head=True)
            head.move_to(LEFT * 4.5 + DOWN * 0.5)
            front_ptr = get_ptr("front", head, ORANGE, direction=UP)
            rear_ptr = get_ptr("rear", head, ORANGE, direction=DOWN)

            self.play(FadeIn(head), FadeIn(front_ptr), FadeIn(rear_ptr),
                      run_time=max(0.2, tracker.duration - 0.4))

        # 第二步：指针域置空
        with self.voiceover(text="第二步，将头结点的指针域，置为空，表示当前队列为空，没有任何数据元素。") as tracker:
            self.play(*get_track_anims(2), run_time=0.4)
            set_tail(head, True)
            self.wait(max(0.1, tracker.duration - 0.4))

        # 第三步：返回
        with self.voiceover(text="第三步，返回 OK，一个空队列构造完毕。") as tracker:
            self.play(*get_track_anims(3), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 0.4))

        # 优化：移交至更左侧，并采用横向一字平铺展开，彻底避开大代码块
        res_panel = VGroup(
            Text("结果：", font_size=22, font="Microsoft YaHei", color=GREEN),
            Text("初始化成功，返回 OK", font_size=20, font="Microsoft YaHei", color=GREEN)
        ).arrange(RIGHT, buff=0.1).move_to(LEFT * 4.0 + DOWN * 2.3)

        with self.voiceover(text="算法执行完毕，返回初始化成功状态。") as tracker:
            self.play(*get_track_anims(3), Write(res_panel), run_time=tracker.duration)

        self.play(*get_track_anims(None), run_time=0.5)

        # =========================================================================
        # ===== PHASE E — COMPLEXITY =====
        # =========================================================================
        # 优化：紧随结果面板右侧进行水平排列，高度抬升（DOWN * 2.3），完全规避底部沉底字幕的遮挡
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(res_panel,
                                                                                                        RIGHT, buff=0.6)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(time_box,
                                                                                                         RIGHT,
                                                                                                         buff=0.6)

        with self.voiceover(
                text="由于算法只包含少量的内存分配和指针赋值操作，且没有循环结构，所以时间复杂度为 O(1)。",
                subcaption="由于算法只包含少量的内存分配和指针赋值操作，且没有循环结构，所以时间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
                text="同样，算法只需分配一个头结点，没有使用其他的额外空间，因此空间复杂度也是 O(1)。",
                subcaption="同样，算法只需分配一个头结点，没有使用其他的额外空间，因此空间复杂度也是 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是链队初始化算法的完整演示过程。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)
