# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class LinkedQueueEnqueueVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角 Logo
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("链队的入队", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(text="本节学习链队的入队算法。该算法用于在链队的队尾插入一个新元素。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== NEW PHASE — LIFE EXAMPLE (排队护栏的加长) =====
        # =========================================================================
        example_title = Text("生活实例：新顾客排队与护栏加长", font_size=32, font="Microsoft YaHei",
                             color=YELLOW).to_edge(UP, buff=1.5)

        customer1 = RoundedRectangle(corner_radius=0.1, width=1.8, height=0.6, color=BLUE, fill_opacity=0.8)
        customer2 = RoundedRectangle(corner_radius=0.1, width=1.8, height=0.6, color=GREEN, fill_opacity=0.8)
        customer3 = RoundedRectangle(corner_radius=0.1, width=1.8, height=0.6, color=RED, fill_opacity=0.8)

        c1_text = Text("顾客 1", font_size=16, font="Microsoft YaHei").move_to(customer1.get_center())
        c2_text = Text("顾客 2", font_size=16, font="Microsoft YaHei").move_to(customer2.get_center())
        c3_text = Text("新顾客 3", font_size=16, font="Microsoft YaHei").move_to(customer3.get_center())

        eg1 = VGroup(customer1, c1_text).move_to(LEFT * 5.2 + DOWN * 0.5)
        eg2 = VGroup(customer2, c2_text).next_to(eg1, RIGHT, buff=1.0)
        eg3 = VGroup(customer3, c3_text).next_to(eg2, RIGHT, buff=1.0).shift(UP * 1.5)

        ex_arrow1 = Arrow(start=eg1.get_right(), end=eg2.get_left(), buff=0.1, color=WHITE)

        ex_rear_ptr = Arrow(start=eg2.get_bottom() + DOWN * 0.6, end=eg2.get_bottom(), buff=0.1, color=ORANGE)
        ex_rear_text = Text("排队终点", font_size=16, font="Microsoft YaHei", color=ORANGE).next_to(ex_rear_ptr, DOWN,
                                                                                                    buff=0.1)
        ex_rear_group = VGroup(ex_rear_ptr, ex_rear_text)

        with self.voiceover(
                text="在现实排队中，链队就像是一串由隔离护栏拉起来的队伍，每个人的手里都牵着拉向下一位的隔离带。") as tracker:
            self.play(FadeIn(example_title), FadeIn(eg1), FadeIn(eg2), Create(ex_arrow1), FadeIn(ex_rear_group),
                      run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(
                text="当新顾客 3 来到队伍末尾准备排队时，原先排在最后的顾客 2 就会把手里的隔离带拉过来，挂在顾客 3 的身上。") as tracker:
            self.play(eg3.animate.shift(DOWN * 1.5), run_time=0.5)
            ex_arrow2 = Arrow(start=eg2.get_right(), end=eg3.get_left(), buff=0.1, color=WHITE)
            self.play(Create(ex_arrow2), run_time=max(0.1, tracker.duration - 0.5))

        with self.voiceover(
                text="最后，我们将‘排队终点’的指示牌向后推移，挂在新顾客 3 的身上。这就是链队最形象的入队全过程。") as tracker:
            ex_rear_group.generate_target()
            new_rear_ptr = Arrow(start=eg3.get_bottom() + DOWN * 0.6, end=eg3.get_bottom(), buff=0.1, color=ORANGE)
            new_rear_text = Text("排队终点", font_size=16, font="Microsoft YaHei", color=ORANGE).next_to(new_rear_ptr,
                                                                                                         DOWN, buff=0.1)
            ex_rear_group.target = VGroup(new_rear_ptr, new_rear_text)
            self.play(MoveToTarget(ex_rear_group), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        self.play(
            FadeOut(example_title), FadeOut(eg1), FadeOut(eg2), FadeOut(eg3),
            FadeOut(ex_arrow1), FadeOut(ex_arrow2), FadeOut(ex_rear_group),
            run_time=0.5
        )

        # =========================================================================
        # ===== PHASE B — CODE BLOCK CONFIG =====
        # =========================================================================
        c_lines = [
            "Status EnQueue(LinkQueue &Q,QElemType e)\n{//插入元素e为Q的新的队尾元素",
            "    p=new QNode;\n        //为入队元素分配节点空间，用指针p指向",
            "    p->data=e;",
            "    p->next=NULL;",
            "    Q.rear->next=p;",
            "    Q.rear=p;",
            "    return OK;",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=11.0, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.11)
        SPACE_WIDTH = 0.082
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 6.25:
            code_group.scale_to_fit_width(6.25)
        if code_group.height > 5.45:
            code_group.scale_to_fit_height(5.45)
        bg_width = code_group.get_width() + 0.65
        bg_height = code_group.get_height() + 0.5
        code_bg = RoundedRectangle(corner_radius=0.2, height=bg_height, width=bg_width, color=GRAY, fill_opacity=0.1,
                                   stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.24)
        code_bg.match_y(code_group)

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

        with self.voiceover(text="右侧是入队算法的实现代码。") as tracker:
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

        # 链队基准原点设定
        head = build_node("", is_head=True)
        head.move_to(LEFT * 5.9 + DOWN * 0.5)
        n1 = build_node("10")
        n1.next_to(head, RIGHT, buff=0.8)
        n2 = build_node("20", is_tail=True)
        n2.next_to(n1, RIGHT, buff=0.8)

        # 连线
        a_head = Arrow(start=head.dot.get_center(), end=n1.get_left(), buff=0.1, color=WHITE)
        a_1 = Arrow(start=n1.dot.get_center(), end=n2.get_left(), buff=0.1, color=WHITE)

        # 指针
        front_ptr = get_ptr("front", head, ORANGE, direction=UP)
        rear_ptr = get_ptr("rear", n2, ORANGE, direction=DOWN)

        with self.voiceover(
                text="假设当前链队已经有两个数据元素。头指针 front 指向紫色的头结点，而尾指针 rear 指向当前最后的结点。") as tracker:
            self.play(
                FadeIn(head, n1, n2),
                GrowArrow(a_head), GrowArrow(a_1),
                FadeIn(front_ptr), FadeIn(rear_ptr),
                run_time=tracker.duration
            )

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW =====
        # =========================================================================
        # 第一步：分配新结点
        with self.voiceover(text="入队的第一步，程序为新元素分配了一个空闲结点 p。") as tracker:
            self.play(*get_track_anims(1), run_time=0.4)
            p_node = build_node("")
            p_node.next_to(n2, RIGHT, buff=0.85).shift(UP * 1.0 + LEFT * 0.95)
            p_ptr = get_ptr("p", p_node, YELLOW, direction=UP)
            self.play(FadeIn(p_node), FadeIn(p_ptr), run_time=max(0.2, tracker.duration - 0.4))

        # 第三步：赋值
        with self.voiceover(text="然后将待插元素（比如 30）写入新结点 p 的数据域。") as tracker:
            self.play(*get_track_anims(2), run_time=0.4)
            val_30 = Text("30", font_size=24, font="Arial", color=GREEN).move_to(p_node[0].get_center())
            self.play(FadeIn(val_30, shift=DOWN * 0.3), run_time=max(0.2, tracker.duration - 0.4))
            p_node[1] = val_30

            # 第四步：指针域置空
        with self.voiceover(text="因为该结点即将成为队尾，所以将它的指针域置为空 NULL。") as tracker:
            self.play(*get_track_anims(3), run_time=0.4)
            set_tail(p_node, True)
            self.wait(max(0.1, tracker.duration - 0.4))

        # 第五步：链接队尾
        with self.voiceover(
                text="紧接着是关键操作：将当前队尾结点的指针域，指向这枚新结点 p，从而完成物理链接。") as tracker:
            self.play(*get_track_anims(4), run_time=0.4)
            set_tail(n2, False)

            p_group = VGroup(p_node, p_ptr)
            self.play(p_group.animate.shift(DOWN * 1.0 + RIGHT * 0.95), run_time=0.5)

            new_a_2 = Arrow(
                start=n2.dot.get_center(),
                end=p_node.get_left(),
                buff=0.08,
                color=WHITE,
                stroke_width=6,
                tip_length=0.24,
                max_tip_length_to_length_ratio=0.42,
                max_stroke_width_to_length_ratio=8,
            )
            self.play(GrowArrow(new_a_2), run_time=max(0.2, tracker.duration - 1.2))

        # 第六步：更新尾指针
        with self.voiceover(text="最后，不要忘记修改队尾指针 rear，让它重新指向真正的队尾结点 p。") as tracker:
            self.play(*get_track_anims(5), run_time=0.4)
            rear_ptr.generate_target()
            rear_ptr.target = get_ptr("rear", p_node, ORANGE, direction=DOWN)
            self.play(MoveToTarget(rear_ptr), run_time=max(0.5, tracker.duration - 0.4))

        # =========================================================================
        # ===== NEW PHASE — COMPACT PANEL CONFIG =====
        # =========================================================================
        res_text = VGroup(
            Text("结果：", font_size=20, font="Microsoft YaHei", color=GREEN),
            Text("入队成功，返回 OK", font_size=18, font="Microsoft YaHei", color=GREEN)
        ).arrange(RIGHT, buff=0.1)

        time_text = VGroup(
            Text("时间复杂度：", font_size=18, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(1)", font_size=18, color=YELLOW)
        ).arrange(RIGHT, buff=0.1)

        space_text = VGroup(
            Text("空间复杂度：", font_size=18, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(1)", font_size=18, color=YELLOW)
        ).arrange(RIGHT, buff=0.1)

        # 优化：采用纵向紧凑集束结构，完全移到链队（head）的垂直下方
        # 设定在 DOWN*1.5 左右，完美与上方的链队隔离，且高度高于底部字幕安全区
        info_panel = VGroup(res_text, time_text, space_text).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        info_panel.next_to(front_ptr, DOWN, buff=2.2).align_to(head, LEFT)

        # 第七步：返回
        with self.voiceover(text="算法执行完毕，返回入队成功状态。") as tracker:
            self.play(*get_track_anims(6), Write(info_panel[0]), run_time=tracker.duration)

        self.play(*get_track_anims(None), FadeOut(p_ptr), run_time=0.5)

        # =========================================================================
        # ===== PHASE E — COMPLEXITY =====
        # =========================================================================
        with self.voiceover(
                text="因为链队入队只需通过 rear 指针在队尾常数次修改链接关系，无需遍历，所以时间复杂度为 O(1)。",
                subcaption="因为链队入队只需通过 rear 指针在队尾常数次修改链接关系，无需遍历，所以时间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(info_panel[1]), run_time=tracker.duration)

        with self.voiceover(
                text="同样，算法只需分配一个新结点即可完成入队，没有使用依赖数据规模的额外空间，空间复杂度也是 O(1)。",
                subcaption="同样，算法只需分配一个新结点即可完成入队，没有使用依赖数据规模的额外空间，空间复杂度也是 O(1)。"
        ) as tracker:
            self.play(FadeIn(info_panel[2]), run_time=tracker.duration)

        with self.voiceover(text="以上就是链队入队算法的完整演示过程。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)
