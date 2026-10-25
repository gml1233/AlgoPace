# coding=utf-8
from manim import *
import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService

class LinkedQueueGetHeadVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角 Logo
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("取链队的队头元素", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(text="本节学习取链队的队头元素的算法。该算法是返回链队队头元素的值，队头指针保持不变。") as tracker:
            self.wait(tracker.duration)

        # ===== 生活实例 =====
        example_title = Text("生活实例：确认队列首位", font_size=32, font="Microsoft YaHei", color=YELLOW).to_edge(UP, buff=1.5)
        
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
        
        with self.voiceover(text="取队头元素，就好比在食堂排队时，食堂阿姨探头看一眼排在最前面的人是谁。") as tracker:
            self.play(FadeIn(example_title), FadeIn(counter), FadeIn(counter_text), FadeIn(people_group), run_time=tracker.duration)
            
        with self.voiceover(text="阿姨确认了最前面是小明，但小明还在排队没有离开，所以整个队伍的结构并没有发生任何改变。") as tracker:
            # 高亮一下排在最前面的小明
            self.play(person1.animate.set_color(YELLOW), run_time=0.5)
            self.play(person1.animate.set_color(BLUE), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 1.0))
            
        self.play(FadeOut(example_title), FadeOut(counter), FadeOut(counter_text), FadeOut(people_group), run_time=0.5)

        # =========================================================================
        # ===== PHASE B — CODE BLOCK CONFIG =====
        # =========================================================================
        c_lines = [
            "QElemType GetHead(LinkQueue Q)",
            "{",
            "    if (Q.front != Q.rear) {",
            "        return Q.front->next->data;",
            "    }",
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
        code_bg = RoundedRectangle(corner_radius=0.2, height=bg_height, width=bg_width, color=GRAY, fill_opacity=0.1, stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.4)
        code_bg.match_y(code_group)
        
        code_block = VGroup(code_bg, code_group).to_edge(RIGHT, buff=0.4).shift(UP * 0.4)

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

        with self.voiceover(text="接下来我们学习算法的实际演示。") as tracker:
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

        def get_ptr(label, target_mobj, color=GREEN, direction=UP):
            if np.array_equal(direction, UP):
                arrow = Arrow(start=target_mobj.get_top() + UP * 0.8, end=target_mobj.get_top(), buff=0.1, color=color)
                txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, UP, buff=0.1)
            else:
                arrow = Arrow(start=target_mobj.get_bottom() + DOWN * 0.8, end=target_mobj.get_bottom(), buff=0.1, color=color)
                txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, DOWN, buff=0.1)
            return VGroup(arrow, txt)

        # 初始化链队：头结点 + 数据结点 10 + 数据结点 20
        head = build_node("", is_head=True)
        head.move_to(LEFT * 5.2 + DOWN * 0.5)
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

        with self.voiceover(text="假设当前链队有两个数据元素。头指针 front 指向紫色的头结点，尾指针 rear 指向最后一个结点。") as tracker:
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
        with self.voiceover(text="首先，程序判断链队是否为空。如果头尾指针不相等，说明队列非空，可以进行取值操作。") as tracker:
            self.play(*get_track_anims(2), run_time=0.4)
            self.play(self.c_texts[2].animate.set_color(GREEN), run_time=max(0.2, tracker.duration - 0.4))

        # 第二步：返回队头元素
        with self.voiceover(text="随后，通过 front 指针找到头结点的下一个结点，也就是队头结点，并提取它的数据域直接返回。") as tracker:
            self.play(*get_track_anims(3), run_time=0.4)
            
            # 高亮一下路径 Q.front -> next -> data
            self.play(head.dot.animate.set_color(YELLOW), run_time=0.3)
            self.play(a_head.animate.set_color(YELLOW), run_time=0.3)
            self.play(n1[1].animate.set_color(YELLOW), run_time=0.3)
            
            # 提取数据
            e_box = VGroup(
                Text("队头元素 =", font_size=24, font="Microsoft YaHei", color=GREEN),
                Text("10", font_size=24, font="Arial", color=GREEN)
            ).arrange(RIGHT, buff=0.2).next_to(head, DOWN, buff=1.5).align_to(head, LEFT)
            
            e_data_copy = n1[1].copy()
            self.play(e_data_copy.animate.move_to(e_box[1].get_center()).set_color(GREEN), FadeIn(e_box[0]), run_time=0.6)
            self.remove(e_data_copy)
            self.add(e_box)
            
            # 恢复颜色
            self.play(head.dot.animate.set_color(PURPLE), a_head.animate.set_color(WHITE), n1[1].animate.set_color(WHITE), run_time=0.4)

        with self.voiceover(text="需要注意的是，整个过程中没有任何结点的指针指向发生改变，因此也没有修改头指针，队列的结构完好无损。") as tracker:
            self.wait(tracker.duration)

        # 结束
        res_panel = VGroup(
            Text("结果：", font_size=22, font="Microsoft YaHei", color=GREEN), 
            Text("成功获取队头元素", font_size=20, font="Microsoft YaHei", color=GREEN),
            Text("10", font_size=22, font="Arial", color=GREEN)
        ).arrange(RIGHT, buff=0.1).next_to(code_bg, DOWN, buff=0.4).align_to(code_bg, LEFT)

        self.play(*get_track_anims(None), Write(res_panel), run_time=1.0)

        # =========================================================================
        # ===== PHASE E — COMPLEXITY =====
        # =========================================================================
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW), MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(res_panel, DOWN, buff=0.3).align_to(res_panel, LEFT)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW), MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(time_box, DOWN, buff=0.2).align_to(time_box, LEFT)

        with self.voiceover(
            text="因为取队头元素仅仅是通过前驱结点找到第一个数据结点进行访问，无需遍历，所以时间复杂度为 O(1)。",
            subcaption="因为取队头元素仅仅是通过前驱结点找到第一个数据结点进行访问，无需遍历，所以时间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
            text="同样，该算法没有使用额外的辅助空间，空间复杂度也是 O(1)。",
            subcaption="同样，该算法没有使用额外的辅助空间，空间复杂度也是 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是取链队队头元素算法的完整演示过程。") as tracker:
            self.wait(tracker.duration)
            
        self.wait(2)
