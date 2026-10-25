# coding=utf-8
from manim import *
import numpy as np
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class LinkedQueueDeQueueVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角 Logo
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("链队的出队", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(text="本节学习链队的出队算法。该算法用于删除链队的队头元素，并通过参数返回其值。") as tracker:
            self.wait(tracker.duration)

        # ===== 生活实例 =====
        example_title = Text("生活实例：食堂排队打饭", font_size=32, font="Microsoft YaHei", color=YELLOW).to_edge(UP,
                                                                                                                  buff=1.5)

        person1 = Circle(radius=0.4, color=BLUE, fill_opacity=0.8).move_to(LEFT * 1)
        person2 = Circle(radius=0.4, color=GREEN, fill_opacity=0.8).next_to(person1, RIGHT, buff=0.5)
        person3 = Circle(radius=0.4, color=RED, fill_opacity=0.8).next_to(person2, RIGHT, buff=0.5)

        p1_text = Text("小明", font_size=20, font="Microsoft YaHei").move_to(person1.get_center())
        p2_text = Text("小红", font_size=20, font="Microsoft YaHei").move_to(person2.get_center())
        p3_text = Text("小刚", font_size=20, font="Microsoft YaHei").move_to(person3.get_center())

        group1 = VGroup(person1, p1_text)
        group2 = VGroup(person2, p2_text)
        group3 = VGroup(person3, p3_text)
        people_group = VGroup(group1, group2, group3)

        counter = Rectangle(width=0.5, height=1.5, color=WHITE).next_to(person1, LEFT, buff=1.0)
        counter_text = Text("打饭窗口", font_size=20, font="Microsoft YaHei").next_to(counter, UP, buff=0.2)

        with self.voiceover(text="我们可以把出队操作想象成在食堂排队打饭。") as tracker:
            self.play(FadeIn(example_title), FadeIn(counter), FadeIn(counter_text), FadeIn(people_group),
                      run_time=tracker.duration)

        with self.voiceover(
                text="排在最前面的小明打完饭后离开，这就相当于队列的出队操作。随之，小红补上，成为了新队首。") as tracker:
            self.play(group1.animate.shift(UP * 2 + LEFT * 2).set_opacity(0), run_time=1.0)
            self.play(group2.animate.shift(LEFT * 1.3), group3.animate.shift(LEFT * 1.3), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 2.0))

        self.play(FadeOut(example_title), FadeOut(counter), FadeOut(counter_text), FadeOut(group2), FadeOut(group3),
                  run_time=0.5)

        # =========================================================================
        # ===== PHASE B — CODE BLOCK CONFIG =====
        # =========================================================================
        c_lines = [
            "Status DeQueue(LinkQueue &Q,QElemType &e)\n{//删除Q的队头元素，用e返回其值",
            "    if(Q.front==Q.rear) return ERROR;\n        //若队列为空，则返回ERROR",
            "    p=Q.front->next;\n        //p指向队头元素",
            "    e=p->data;\n        //e保存队头元素的值",
            "    Q.front->next=p->next;\n        //修改头节点的指针域",
            "    if(Q.rear==p) Q.rear=Q.front;\n        //最后一个元素被删，队尾指针指向头节点",
            "    delete p;\n        //释放原队头元素的空间",
            "    return OK;",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=10.5, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        SPACE_WIDTH = 0.08
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 6.25:
            code_group.scale_to_fit_width(6.25)
        if code_group.height > 5.5:
            code_group.scale_to_fit_height(5.5)
        bg_width = code_group.get_width() + 0.7
        bg_height = code_group.get_height() + 0.5
        code_bg = RoundedRectangle(corner_radius=0.2, height=bg_height, width=bg_width, color=GRAY, fill_opacity=0.1,
                                   stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.4)
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

        with self.voiceover(text="接下来我们学习算法的实际演示") as tracker:
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

        # 优化：整个队列上移，基础 Y 轴坐标从 DOWN*0.5 调整到居中(ORIGIN)
        head = build_node("", is_head=True)
        head.move_to(LEFT * 5.2 + ORIGIN)
        n1 = build_node("10")
        n1.next_to(head, RIGHT, buff=0.7)
        n2 = build_node("20", is_tail=True)
        n2.next_to(n1, RIGHT, buff=0.7)

        # 连线
        a_head = Arrow(start=head.dot.get_center(), end=n1.get_left(), buff=0.1, color=WHITE)
        a_1 = Arrow(start=n1.dot.get_center(), end=n2.get_left(), buff=0.1, color=WHITE)

        # 指针
        front_ptr = get_ptr("front", head, ORANGE, direction=UP)
        rear_ptr = get_ptr("rear", n2, ORANGE, direction=DOWN)

        with self.voiceover(
                text="假设当前链队有两个数据元素。头指针 front 指向紫色的头结点，尾指针 rear 指向最后一个结点。") as tracker:
            self.play(
                FadeIn(head, n1, n2),
                GrowArrow(a_head), GrowArrow(a_1),
                FadeIn(front_ptr), FadeIn(rear_ptr),
                run_time=tracker.duration
            )

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW =====
        # =========================================================================

        # 第一步：判空
        with self.voiceover(
                text="首先，程序判断链队是否为空。如果头指针和尾指针相等，说明队列为空，返回错误。这里队列不为空，继续向下执行。") as tracker:
            self.play(*get_track_anims(1), run_time=0.4)
            self.play(self.c_texts[1].animate.set_color(GREEN), run_time=max(0.2, tracker.duration - 0.4))

        # 第二步：p 指向队头元素
        with self.voiceover(
                text="接着，声明一个工作指针 p，将其指向头结点之后的第一个结点，也就是即将出队的队头元素。") as tracker:
            self.play(*get_track_anims(2), run_time=0.4)
            p_ptr = get_ptr("p", n1, YELLOW, direction=UP)
            self.play(FadeIn(p_ptr), run_time=max(0.2, tracker.duration - 0.4))

        # 第三步：保存元素值
        with self.voiceover(text="然后，将该结点的数据域提取出来，使用变量 e保存队头元素的值。") as tracker:
            self.play(*get_track_anims(3), run_time=0.4)
            # 优化：随着 head 上移，e_box 保持紧贴 head 下方 (buff=0.6)
            e_box = VGroup(
                Text("e =", font_size=30, font="Arial", weight=BOLD, color=YELLOW),
                Text("10", font_size=30, font="Arial", weight=BOLD, color=YELLOW)
            ).arrange(RIGHT, buff=0.2).next_to(head, DOWN, buff=0.6).align_to(head, LEFT)

            e_data_copy = n1[1].copy()
            self.play(e_data_copy.animate.move_to(e_box[1].get_center()).set_color(YELLOW).scale(1.25),
                      FadeIn(e_box[0]), run_time=max(0.2, tracker.duration - 0.4))
            self.remove(e_data_copy)
            self.add(e_box)

        # 第四步：修改头结点指针域
        with self.voiceover(text="接下来是修改链表结构，将头结点的指针域跨过结点 p，直接指向 p 的下一个结点。") as tracker:
            self.play(*get_track_anims(4), run_time=0.4)
            self.play(FadeOut(a_head), run_time=0.3)

            # 仿照双向链表删除，用长曲线绕过被删除的队头结点，表现链路跨越更新。
            new_a_head = CurvedArrow(
                head.dot.get_center(),
                n2.get_left(),
                angle=-TAU / 3,
                color=WHITE
            )
            n1_group = VGroup(n1, p_ptr, a_1)
            self.play(n1_group.animate.shift(DOWN * 1.5), run_time=0.5)
            # CurvedArrow 是 VMobject，Manim 0.21.0 的 GrowArrow 会传入
            # 不兼容的 scale_tips 参数，使用 Create 逐段绘制曲线。
            self.play(Create(new_a_head), run_time=max(0.2, tracker.duration - 1.2))

        # 第五步：若被删结点是尾结点，更新尾指针
        with self.voiceover(
                text="接下来判断：这次要删除的结点 p，是不是队列中的最后一个结点。判断条件是 Q.rear 等于 p，也就是尾指针 rear 和工作指针 p 指向同一个结点。") as tracker:
            self.play(*get_track_anims(5), run_time=0.4)
            self.play(self.c_texts[5].animate.set_color(GREEN), run_time=max(0.2, tracker.duration - 0.4))

        with self.voiceover(
                text="当前队列有两个数据结点，p 指向前面的 10，而 rear 指向后面的 20，两个指针并不相等，所以这次删除的不是最后一个结点，跳过更新尾指针。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(
                text="如果队列中仅剩最后一个数据结点，那么 p 和 Q.rear 就会指向同一个结点。此时删除这个结点以后，队列中将不再有数据结点。") as tracker:
            # 第 8 行已经在上一段讲解中高亮，避免重复调用导致 Scene.play 没有动画。
            self.wait(tracker.duration)

        with self.voiceover(
                text="因此，程序必须先执行 Q.rear 等于 Q.front，把尾指针重新指向头结点。这样既避免了 rear 指向已经释放的结点，又满足 front 等于 rear 代表队列为空的规则。") as tracker:
            self.wait(max(0.2, tracker.duration - 0.4))

        with self.voiceover(
                text="完成尾指针更新后，再执行 delete p。delete p 只负责释放 p 所指结点占用的内存，并不会自动修改 Q.rear 的值。如果不提前更新 rear，rear 就会继续保存已经被释放的地址，变成野指针。") as tracker:
            self.play(*get_track_anims(6), run_time=0.4)
            self.wait(max(0.2, tracker.duration - 0.4))

        # 第六步：释放结点空间
        with self.voiceover(text="最后，释放原队头元素 p 占据的内存空间。") as tracker:
            self.play(FadeOut(n1_group), run_time=tracker.duration)

        # 第七步：返回
        # 优化：整体上移后，res_panel 得益于上方腾出的空间，拥有更安全的垂直距离，远离底边
        res_panel = VGroup(
            Text("结果：", font_size=24, font="Microsoft YaHei", color=GREEN),
            Text("出队成功，返回 OK", font_size=22, font="Microsoft YaHei", color=GREEN)
        ).arrange(RIGHT, buff=0.1).next_to(e_box, DOWN, buff=0.8).align_to(e_box, LEFT)

        with self.voiceover(text="算法执行完毕，返回出队成功状态。") as tracker:
            self.play(*get_track_anims(7), Write(res_panel), run_time=tracker.duration)

        self.play(*get_track_anims(None), run_time=0.5)

        # =========================================================================
        # ===== PHASE E — COMPLEXITY =====
        # =========================================================================
        # 时空复杂度保持挂载在 res_panel 的右侧横向展开，高度随之抬升，彻底解决字幕遮挡问题
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(res_panel,
                                                                                                        RIGHT, buff=0.8)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(time_box,
                                                                                                         RIGHT,
                                                                                                         buff=0.8)

        with self.voiceover(
                text="因为链队的出队操作只需在队头修改几处指针指向，无需遍历，所以时间复杂度为 O(1)。",
                subcaption="因为链队的出队操作只需在队头修改几处指针指向，无需遍历，所以时间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
                text="同样，算法使用常量级的辅助空间保存元素，没有依赖数据规模的额外空间，空间复杂度也是 O(1)。",
                subcaption="同样，算法使用常量级的辅助空间保存元素，没有依赖数据规模的额外空间，空间复杂度也是 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是链队出队算法的完整演示过程。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)
