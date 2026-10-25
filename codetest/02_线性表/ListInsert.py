# coding=utf-8
from manim import *
import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import numpy as np  # safety import (LLM output may use np)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
class LinkedListBase(VoiceoverScene):
    """单链表动画公共基类（带头结点，链表L指向头结点）
    提供统一的链表可视化、遍历指针、节点高亮、插入和删除动画方法等
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
        
        val_text = Text(str(value_str), font_size=self.FONT_SIZE)
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

    def setup_list_data(self, values, start_pos=LEFT*4):
        self.nodes = []
        self.node_mobjects = VGroup()
        self.arrows = VGroup()
        
        node_values = [""] + values  
        
        for i, val in enumerate(node_values):
            color = self.COLOR_HEAD if i == 0 else self.COLOR_DEFAULT
            is_tail = (i == len(node_values) - 1)
            node = self.create_node(val, color=color, is_tail=is_tail)
            
            if i == 0:
                node.move_to(start_pos)
            else:
                prev_node = self.nodes[-1]
                node.next_to(prev_node, RIGHT, buff=self.NODE_SPACING - self.NODE_WIDTH)

            self.nodes.append(node)
            self.node_mobjects.add(node)

        for i in range(len(self.nodes) - 1):
            arrow = self.create_arrow_between(self.nodes[i], self.nodes[i+1])
            self.arrows.add(arrow)

        group = VGroup(self.node_mobjects, self.arrows)
        group.move_to(LEFT * 3.6 + UP * 1.2)

        self.play(FadeIn(self.node_mobjects), FadeIn(self.arrows))
        
        self.add_pointer_L()
        self.wait(0.5)

    def create_arrow_between(self, node1, node2, color=WHITE, end_pos=None):
        """创建从 node1 到 node2 的指针箭头，允许自定义终点 end_pos"""
        target_pos = end_pos if end_pos is not None else node2.get_left()
        return Arrow(
            start=node1.dot.get_center(),
            end=target_pos,
            buff=0,
            color=color,
            max_tip_length_to_length_ratio=0.15
        )

    def add_pointer_L(self):
        head_node = self.nodes[0]
        l_text = Text("L", font_size=self.FONT_SIZE, color=self.COLOR_L_PTR)
        l_arrow = Arrow(
            start=head_node.get_top() + UP * 1,
            end=head_node.get_top(),
            buff=0,
            color=self.COLOR_L_PTR
        )
        l_text.next_to(l_arrow.get_start(), UP, buff=0.2)
        
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

    def move_pointer(self, ptr_group, new_node, direction=DOWN, run_time=0.5):
        target_ptr = self.create_pointer(new_node, ptr_group.text_obj.text, ptr_group.text_obj.get_color(), direction)
        self.play(ptr_group.animate.move_to(target_ptr.get_center()), run_time=run_time)

    def highlight_node(self, index, color=COLOR_TARGET, run_time=0.5):
        node = self.nodes[index]
        self.play(
            node.rect.animate.set_color(color),
            node.divider.animate.set_color(color),
            node.dot.animate.set_color(color),
            run_time=run_time
        )
        
    def reset_node_color(self, index, run_time=0.5):
        color = self.COLOR_HEAD if index == 0 else self.COLOR_DEFAULT
        self.highlight_node(index, color, run_time)

    def show_step_text(self, text_str):
        if hasattr(self, 'step_text') and self.step_text in self.mobjects:
            self.remove(self.step_text)
        self.step_text = Text(text_str, font_size=self.FONT_SIZE-6).to_edge(UP, buff=0.5)
        self.play(FadeIn(self.step_text))

    def update_step_text(self, new_str):
        new_text = Text(new_str, font_size=self.FONT_SIZE-6).to_edge(UP, buff=0.5)
        self.play(Transform(self.step_text, new_text))

# ==== SHARED VISUAL CONTRACT ====
SHARED_DATA = [10, 30, 15]
SHARED_POINTER_NAMES = ['p', 's']

class ContinuousLinkedListVideo(LinkedListBase):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 新增：连续冒烟的追踪器及其透明度控制追踪器
        smoke_tracker = ValueTracker(0)
        smoke_opacity_tracker = ValueTracker(0)
        
        # 将 smoke_tracker 加入场景，并挂载 updater 使其在渲染期间每一帧平滑自增
        self.add(smoke_tracker)
        smoke_tracker.add_updater(lambda m, dt: m.increment_value(dt * 0.8))

        # ===== PHASE A — OPENING =====
        algo_title = Text("单链表的插入", font_size=48, weight=BOLD).to_edge(UP, buff=0.6)
        self.add(algo_title)
        
        sentences = [
            "本节我们学习单链表的插入算法。",
            "该算法是在表的第i个位置插入一个新的数据元素e，表长加1"
        ]
        for sentence in sentences:
            with self.voiceover(text=sentence) as tracker:
                self.wait(tracker.duration)

        # ===== NEW PHASE — VIVID ANALOGY =====
        with self.voiceover(text="先来看一个生活实例：给火车加挂一节车厢") as tracker:
            
            def create_beautified_train_car(color, text, is_head=False):
                car_w, car_h = 1.8, 1.1
                car_group = VGroup()

                # 基底车身
                body = RoundedRectangle(
                    corner_radius=0.12,
                    width=car_w,
                    height=car_h,
                    color=color,
                    fill_color=color,
                    fill_opacity=0.25,
                    stroke_width=3
                )
                car_group.add(body)

                if is_head:
                    window = Rectangle(
                        width=0.4, height=0.4, color=color,
                        fill_color=WHITE, fill_opacity=0.7, stroke_width=1.5
                    )
                    window.move_to(body.get_center() + LEFT * 0.45 + UP * 0.2)

                    decor_line = Line(
                        body.get_left() + UP * 0.1, body.get_right() + UP * 0.1,
                        color=color, stroke_width=1.5
                    )

                    chimney = RoundedRectangle(
                        corner_radius=0.04, width=0.22, height=0.36,
                        color=color, fill_color=color, fill_opacity=0.7, stroke_width=2
                    )
                    chimney.move_to(body.get_top() + LEFT * 0.18 + UP * 0.16)

                    # --- 修改点：使用 always_redraw 绑定追踪器 ---
                    smoke_group = always_redraw(lambda: VGroup(
                        # 小烟圈 (基础周期)
                        Circle(
                            radius=0.08 + (smoke_tracker.get_value() % 1) * 0.08,
                            color=LIGHT_GRAY, stroke_width=0,
                            fill_opacity=smoke_opacity_tracker.get_value() * 0.6 * (1 - (smoke_tracker.get_value() % 1))
                        ).move_to(chimney.get_top() + RIGHT * 0.18 + UP * 0.18 + (RIGHT * 0.1 + UP * 0.1) * (smoke_tracker.get_value() % 1)),
                        
                        # 中烟圈 (相位偏移 0.3)
                        Circle(
                            radius=0.12 + ((smoke_tracker.get_value() + 0.3) % 1) * 0.1,
                            color=LIGHT_GRAY, stroke_width=0,
                            fill_opacity=smoke_opacity_tracker.get_value() * 0.5 * (1 - ((smoke_tracker.get_value() + 0.3) % 1))
                        ).move_to(chimney.get_top() + RIGHT * 0.42 + UP * 0.42 + (RIGHT * 0.15 + UP * 0.15) * ((smoke_tracker.get_value() + 0.3) % 1)),
                        
                        # 大烟圈 (相位偏移 0.6)
                        Circle(
                            radius=0.17 + ((smoke_tracker.get_value() + 0.6) % 1) * 0.12,
                            color=LIGHT_GRAY, stroke_width=0,
                            fill_opacity=smoke_opacity_tracker.get_value() * 0.4 * (1 - ((smoke_tracker.get_value() + 0.6) % 1))
                        ).move_to(chimney.get_top() + RIGHT * 0.72 + UP * 0.72 + (RIGHT * 0.2 + UP * 0.2) * ((smoke_tracker.get_value() + 0.6) % 1))
                    ))

                    car_group.add(window, decor_line, chimney, smoke_group)
                    car_group.chimney = chimney
                    car_group.smoke_group = smoke_group
                else:
                    window1 = Rectangle(
                        width=0.35, height=0.35, color=color,
                        fill_color=WHITE, fill_opacity=0.6, stroke_width=1.5
                    )
                    window1.move_to(body.get_center() + LEFT * 0.4 + UP * 0.15)
                    window2 = Rectangle(
                        width=0.35, height=0.35, color=color,
                        fill_color=WHITE, fill_opacity=0.6, stroke_width=1.5
                    )
                    window2.move_to(body.get_center() + RIGHT * 0.4 + UP * 0.15)
                    car_group.add(window1, window2)

                wheel_y = body.get_bottom()[1] - 0.05
                wheel1 = Circle(radius=0.18, color=GRAY_D, fill_color=LIGHT_GRAY, fill_opacity=1, stroke_width=2.5)
                wheel1.move_to([body.get_center()[0] - 0.5, wheel_y, 0])
                wheel2 = Circle(radius=0.18, color=GRAY_D, fill_color=LIGHT_GRAY, fill_opacity=1, stroke_width=2.5)
                wheel2.move_to([body.get_center()[0] + 0.5, wheel_y, 0])

                w_dot1 = Dot(wheel1.get_center(), radius=0.04, color=GRAY_D)
                w_dot2 = Dot(wheel2.get_center(), radius=0.04, color=GRAY_D)

                label = Text(text, font_size=18, font="Sans", weight=BOLD, color=WHITE).move_to(body.get_center() + DOWN * 0.25)
                car_group.add(wheel1, wheel2, w_dot1, w_dot2, label)

                car_group.body = body
                return car_group

            def move_train_car_body_to(car, target_pos):
                car.shift(np.array(target_pos) - car.body.get_center())
                return car

            def train_car_body_shift_to(car, target_pos):
                return np.array(target_pos) - car.body.get_center()

            TRAIN_Y = 1.2  
            
            locomotive = move_train_car_body_to(create_beautified_train_car(self.COLOR_HEAD, "火车头", is_head=True), [-2.6, TRAIN_Y, 0])
            car_p = move_train_car_body_to(create_beautified_train_car(BLUE, "车厢 p"), [0.0, TRAIN_Y, 0])
            car_next = move_train_car_body_to(create_beautified_train_car(BLUE, "后继车厢"), [2.6, TRAIN_Y, 0])

            def create_beautified_coupler(start_pt, end_pt, color=GRAY):
                line = Line(start_pt, end_pt, color=color, stroke_width=4)
                center_dot = Dot(line.get_center(), radius=0.06, color=color)
                return VGroup(line, center_dot)

            coupler0 = create_beautified_coupler(locomotive.body.get_right(), car_p.body.get_left(), GRAY)
            old_coupler = create_beautified_coupler(car_p.body.get_right(), car_next.body.get_left(), WHITE)

            # --- 修改点：同时淡入车身与冒烟透明度 ---
            self.play(
                FadeIn(locomotive, shift=RIGHT * 0.3),
                FadeIn(car_p, shift=RIGHT * 0.3),
                FadeIn(car_next, shift=RIGHT * 0.3),
                Create(coupler0),
                Create(old_coupler),
                smoke_opacity_tracker.animate.set_value(1), # 让烟雾配合 FadeIn 显现
                run_time=1.5
            )

        with self.voiceover(text="现在需要在车厢p和它的后继车厢之间，加挂一节新车厢s。") as tracker:
            car_s = move_train_car_body_to(
                create_beautified_train_car(GREEN, "新车厢 s"),
                [(car_p.body.get_right()[0] + car_next.body.get_left()[0]) / 2, TRAIN_Y - 2.2, 0]
            )
            self.play(FadeIn(car_s, shift=UP * 1.0), run_time=1.2)

        with self.voiceover(text="第一步，将新车厢s与后继车厢连接") as tracker:
            new_coupler2 = create_beautified_coupler(car_s.body.get_right(), car_next.body.get_left(), GREEN)
            self.play(Create(new_coupler2), run_time=1.0)

        with self.voiceover(text="第二步，断开车厢p与后继车厢的连接，再将车厢p与新车厢s连接") as tracker:
            new_coupler1 = create_beautified_coupler(car_p.body.get_right(), car_s.body.get_left(), YELLOW)
            self.play(
                FadeOut(old_coupler, scale=0.8),
                Create(new_coupler1),
                run_time=1.0
            )

        with self.voiceover(text="这样，新车厢s成功插入整列火车之中，这与单链表的插入操作完全一致，下面学习该算法的代码实现") as tracker:
            total_w = 4 * 1.8 + 3 * 0.5  
            start_x = -total_w / 2 + 0.9  

            loco_target_pos = [start_x, TRAIN_Y, 0]
            carp_target_pos = [start_x + 2.3, TRAIN_Y, 0]
            cars_target_pos = [start_x + 4.6, TRAIN_Y, 0]
            carnext_target_pos = [start_x + 6.9, TRAIN_Y, 0]

            def body_right_at(center_pos):
                return np.array(center_pos) + RIGHT * (1.8 / 2)

            def body_left_at(center_pos):
                return np.array(center_pos) + LEFT * (1.8 / 2)

            c0_target = create_beautified_coupler(body_right_at(loco_target_pos), body_left_at(carp_target_pos), GRAY)
            c1_target = create_beautified_coupler(body_right_at(carp_target_pos), body_left_at(cars_target_pos), YELLOW)
            c2_target = create_beautified_coupler(body_right_at(cars_target_pos), body_left_at(carnext_target_pos), YELLOW)

            self.play(
                locomotive.animate.shift(train_car_body_shift_to(locomotive, loco_target_pos)),
                car_p.animate.shift(train_car_body_shift_to(car_p, carp_target_pos)),
                car_s.animate.shift(train_car_body_shift_to(car_s, cars_target_pos)),
                car_next.animate.shift(train_car_body_shift_to(car_next, carnext_target_pos)),
                ReplacementTransform(coupler0, c0_target),
                ReplacementTransform(new_coupler1, c1_target),
                ReplacementTransform(new_coupler2, c2_target),
                run_time=1.5
            )
            self.wait(1.0)

        # 优雅淡出画面火车部分，并同步隐去烟雾
        self.play(
            VGroup(locomotive, car_p, car_next, car_s, coupler0, new_coupler1, new_coupler2, c0_target, c1_target, c2_target).animate.fade(1),
            smoke_opacity_tracker.animate.set_value(0),
            run_time=1.0
        )
        self.remove(locomotive, car_p, car_next, car_s, coupler0, new_coupler1, new_coupler2, c0_target, c1_target, c2_target)
        
        # --- 修改点：火车退出后，清理 updater 以释放运算资源 ---
        smoke_tracker.clear_updaters()

        # ===== PHASE B — INITIALIZATION =====
        self.setup_list_data(SHARED_DATA)

        c_lines = [
            "Status ListInsert(LinkList &L, int i, ElemType e){",
            "    LNode *p = L, *s; int j = 0;",
            "    while (p && j < i - 1) {",
            "        p = p->next; ++j;",
            "    }",
            "    if (!p || j > i - 1) return ERROR;",
            "    s = new LNode;",
            "    s->data = e;",
            "    s->next = p->next;",
            "    p->next = s;",
            "    return OK;",
            "}"
        ]
        
        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ") 
            t = Text(stripped_line, font_size=13, font="Consolas", color=WHITE)
            self.c_texts.append(t)
        
        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        
        SPACE_WIDTH = 0.105 
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
        code_block = VGroup(code_bg, code_group).move_to(RIGHT * 4.2 + UP * 0.4)
        
        input_params = VGroup(
            Text("参数：", font_size=24, color=YELLOW),
            MathTex("i=3, e=20", font_size=26, color=YELLOW)
        ).arrange(RIGHT, buff=0.15).next_to(code_block, DOWN, buff=0.2).align_to(code_block, LEFT)
        
        # ===== CODE HIGHLIGHT HELPER =====
        self.current_line = None
        
        def get_track_anims(new_idx):
            anims = []
            if self.current_line is not None:
                old_idx = self.current_line
                anims.append(self.c_texts[old_idx].animate.set_color(WHITE).scale(1/1.2, about_edge=LEFT))
            
            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW).scale(1.2, about_edge=LEFT))
                
                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.15).rotate(-PI/2)
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

        with self.voiceover(text="首先，假设需要在单链表的第3个位置插入元素20") as tracker:
            self.play(FadeIn(code_block), FadeIn(input_params), run_time=tracker.duration)
        self.wait(1.0)

        with self.voiceover(text="先将p指针指向头结点，变量j设为0") as tracker:
            p_ptr = self.create_pointer(self.nodes[0], "p", color=self.COLOR_CURRENT, direction=DOWN, offset=0.3)
            j_text = MathTex("j = 0", font_size=24, color=WHITE).next_to(p_ptr, DOWN, buff=0.2)
            self.play(*get_track_anims(1), FadeIn(p_ptr), FadeIn(j_text), run_time=tracker.duration)
        self.wait(1.0)

        # ===== PHASE C — MAIN TRACE =====
        with self.voiceover(text="进入循环，寻找插入位置的前驱结点") as tracker:
            self.play(*get_track_anims(2), run_time=tracker.duration)
            
        with self.voiceover(text="第一次循环，将指针向后移动一个位置，指向数据为10的结点，变量j自增为1") as tracker:
            target_p_ptr1 = self.create_pointer(self.nodes[1], "p", color=self.COLOR_CURRENT, direction=DOWN, offset=0.3)
            j_text_new1 = MathTex("j = 1", font_size=24, color=WHITE).next_to(target_p_ptr1, DOWN, buff=0.2)
            
            self.play(
                *get_track_anims(3),
                p_ptr.animate.move_to(target_p_ptr1.get_center()),
                Transform(j_text, j_text_new1),
                run_time=1.0
            )
            self.play(*get_track_anims(2), run_time=0.5)

        with self.voiceover(text="满足条件，继续循环，指针向后移动指向数据为30的结点，变量j自增为2") as tracker:
            target_p_ptr2 = self.create_pointer(self.nodes[2], "p", color=self.COLOR_CURRENT, direction=DOWN, offset=0.3)
            j_text_new2 = MathTex("j = 2", font_size=24, color=WHITE).next_to(target_p_ptr2, DOWN, buff=0.2)
            
            self.play(
                *get_track_anims(3),
                p_ptr.animate.move_to(target_p_ptr2.get_center()),
                Transform(j_text, j_text_new2),
                run_time=1.0
            )
            self.play(*get_track_anims(2), run_time=0.5)
            
        with self.voiceover(text="此时找到了插入位置的前驱结点，循环结束") as tracker:
            self.play(*get_track_anims(None)) 
            self.wait(tracker.duration)

        with self.voiceover(text="检查插入位置是否合法") as tracker:
            self.play(*get_track_anims(5), run_time=tracker.duration)
          
        with self.voiceover(text="接下来创建新结点") as tracker:
            self.play(*get_track_anims(6), run_time=tracker.duration)

        new_node_s = self.create_node(20, color=self.COLOR_INSERT)
        new_node_s.move_to(self.nodes[2].get_center() + DOWN * 2.0 + RIGHT * (self.NODE_SPACING / 2) + RIGHT * 0.2)
        s_ptr = self.create_pointer(new_node_s, "s", color=self.COLOR_INSERT, direction=DOWN, offset=0)
          
        with self.voiceover(text="先在内存中分配空间，将数据域赋值为20") as tracker:
            self.play(*get_track_anims(7), FadeIn(new_node_s), FadeIn(s_ptr), run_time=tracker.duration)
        self.wait(1.0)

        with self.voiceover(text="再将新结点的指针域指向前驱结点的后继结点") as tracker:
            s_arrow = self.create_arrow_between(
                new_node_s, 
                self.nodes[3], 
                color=GREEN,
                end_pos=self.nodes[3].get_bottom() + LEFT * 0.3
            )
            self.play(*get_track_anims(8), GrowArrow(s_arrow))

        with self.voiceover(text="最后将前驱结点的指针域指向新结点") as tracker:
            self.play(*get_track_anims(9), run_time=1.0)
            p_arrow = self.create_arrow_between(
                self.nodes[2], 
                new_node_s, 
                color=YELLOW,
                end_pos=new_node_s.get_top() + LEFT * 0.3
            )
            old_arrow = self.arrows[2]
            self.play(Transform(old_arrow, p_arrow))
            
        with self.voiceover(text="这样就成功将新结点插入进单链表中") as tracker:
            self.nodes.insert(3, new_node_s)
            self.node_mobjects.add(new_node_s)
            
            self.arrows[2] = p_arrow
            self.arrows.insert(3, s_arrow)
            
            # ===== 保持头节点锚定 =====
            anim_group = []
            head_pos = self.nodes[0].get_center()

            for i in range(len(self.nodes)):
                self.nodes[i].generate_target()
                if i == 0:
                    self.nodes[i].target.move_to(head_pos)
                else:
                    self.nodes[i].target.next_to(self.nodes[i-1].target, RIGHT, buff=self.NODE_SPACING - self.NODE_WIDTH)
                anim_group.append(MoveToTarget(self.nodes[i]))

            self.play(*anim_group, run_time=1.5)
            
            arrow_anims = []
            for i in range(len(self.nodes) - 1):
                new_arrow = self.create_arrow_between(self.nodes[i], self.nodes[i+1], color=WHITE)
                arrow_anims.append(Transform(self.arrows[i], new_arrow))
            if arrow_anims:
                self.play(*arrow_anims, run_time=1.0)
                
            self.add_pointer_L()
            
            p_ptr_new = self.create_pointer(self.nodes[2], "p", color=self.COLOR_CURRENT, direction=DOWN)
            s_ptr_new = self.create_pointer(self.nodes[3], "s", color=self.COLOR_INSERT, direction=DOWN)
            j_text_final = MathTex("j = 2", font_size=24, color=WHITE).next_to(p_ptr_new, DOWN, buff=0.2)
            self.play(
                Transform(p_ptr, p_ptr_new),
                Transform(s_ptr, s_ptr_new),
                Transform(j_text, j_text_final)
            )

        with self.voiceover(text="此时可以看到，新元素已顺利插入") as tracker:
            self.wait(tracker.duration)

        # ===== PHASE D — COMPLETION =====
        with self.voiceover(text="算法最后返回成功状态，插入操作结束") as tracker:
            self.play(*get_track_anims(10), run_time=tracker.duration)

        # ===== PHASE E — COMPLEXITY =====
        complexity_panel = VGroup(
            VGroup(Text("时间复杂度：", font_size=24, color=YELLOW), MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1),
            VGroup(Text("空间复杂度：", font_size=24, color=YELLOW), MathTex("O(1)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(LEFT * 3.5 + DOWN * 2)
        
        with self.voiceover(
            text="查找前驱结点需要遍历单链表，所以该算法的时间复杂度为O恩，空间复杂度为常数级别。",
            subcaption="查找前驱结点需要遍历单链表，所以该算法的时间复杂度为O(n)，空间复杂度为常数级别。"
        ) as tracker:
            self.play(*get_track_anims(None), FadeIn(complexity_panel), run_time=tracker.duration)
            
        with self.voiceover(text="这就是单链表插入操作的完整过程。") as tracker:
            self.wait(tracker.duration)
            
        self.wait(2)