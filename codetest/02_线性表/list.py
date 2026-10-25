# ========== AlgoT2V 生成的 Manim 动画源代码 (前插法防遮挡与第0帧修复版) ==========
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)

from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
from contextlib import contextmanager

@contextmanager
def subtitle_voiceover(scene, text):
    subtitle = Text(text, font_size=24, color=WHITE).to_edge(DOWN, buff=0.5)
    scene.add(subtitle)
    with scene.voiceover(text=text) as tracker:
        yield tracker
    scene.remove(subtitle)


# ========== 场景 1: Scene1Initialization (ID: scene1_initialization) ==========
class Scene1Initialization(VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 【修复2】：第0帧直接呈现标题，不使用 Write 动画
        title_text = Text("前插法创建单链表", font_size=40, color=WHITE).to_edge(UP)
        self.add(title_text)

        with subtitle_voiceover(self, "同学们好，欢迎来到算法课堂。今天我们来学习如何使用前插法创建一个单链表。") as tracker:
            self.wait(tracker.duration)

        # 初始化代码块 (缩小字号，紧贴右上角防遮挡)
        code_l1 = Text("L = new LNode;", font_size=18, color=WHITE)
        code_l2 = Text("L->next = NULL;", font_size=18, color=WHITE)
        code_group = VGroup(code_l1, code_l2).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        code_bg = SurroundingRectangle(code_group, color=GRAY, buff=0.2, fill_opacity=0.1)
        code_block = VGroup(code_bg, code_group).to_corner(UR).shift(DOWN * 0.1 + LEFT * 0.1)

        # 蓝色双舱头节点 (【修复1】：主链表Y轴回退至 UP * 0.5)
        data_box = Rectangle(width=1.2, height=0.8, color=BLUE)
        ptr_box = Rectangle(width=0.4, height=0.8, color=BLUE).next_to(data_box, RIGHT, buff=0)
        ptr_dot = Dot(radius=0.06, color=BLUE).move_to(ptr_box.get_center())
        tail_marker = Text("^", font_size=24, color=BLUE).move_to(ptr_box.get_center())
        
        ptr_dot.set_opacity(0)
        tail_marker.set_opacity(1)
        
        head_node_L = VGroup(data_box, ptr_box, ptr_dot, tail_marker).move_to(LEFT * 5.0 + UP * 0.5)
        label_head = Text("头结点", font_size=22, color=WHITE).next_to(data_box, DOWN, buff=0.3)

        # L 指针
        l_arrow = Arrow(start=data_box.get_left() + LEFT * 1.0, end=data_box.get_left(), buff=0.1, color=WHITE)
        l_text = Text("L", font_size=36, color=WHITE).next_to(l_arrow.get_start(), LEFT, buff=0.1)
        l_pointer = VGroup(l_arrow, l_text)

        with subtitle_voiceover(self, "首先，我们需要在内存中初始化一个带头结点的空链表。这个头结点就像是一个火车头，用来牵引后面的车厢。") as tracker:
            self.play(FadeIn(code_block),
                      FadeIn(head_node_L),
                      FadeIn(label_head),
                      Write(l_pointer), code_l1.animate.set_color(YELLOW),
                      code_l1.animate.set_color(WHITE),
                      code_l2.animate.set_color(YELLOW), run_time=tracker.duration)

        # 输入序列保持底部
        queue_label = Text("输入序列:", font_size=24, color=WHITE).move_to(DOWN * 2.0 + LEFT * 2.5)
        q_box_1 = Square(side_length=0.8, color=WHITE)
        q_box_2 = Square(side_length=0.8, color=WHITE)
        q_box_3 = Square(side_length=0.8, color=WHITE)
        queue_boxes = VGroup(q_box_1, q_box_2, q_box_3).arrange(RIGHT, buff=0.3).next_to(queue_label, RIGHT, buff=0.4)

        q_val_1 = Text("10", font_size=24, color=WHITE).move_to(q_box_1.get_center())
        q_val_2 = Text("20", font_size=24, color=WHITE).move_to(q_box_2.get_center())
        q_val_3 = Text("30", font_size=24, color=WHITE).move_to(q_box_3.get_center())
        queue_texts = VGroup(q_val_1, q_val_2, q_val_3)

        with subtitle_voiceover(self, "假设我们要存入链表的数据序列是：10、20、30。") as tracker:
            self.play(
                code_l2.animate.set_color(WHITE),
                FadeIn(queue_label), FadeIn(queue_boxes), FadeIn(queue_texts),
                run_time=tracker.duration
            )
        self.wait(2)


# ========== 场景 2: Scene2FirstInsertion (ID: scene2_first_insertion) ==========
class Scene2FirstInsertion(VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 全局坐标系声明
        pos_head = LEFT * 5.0 + UP * 0.5
        pos_p = LEFT * 2.6 + UP * 0.5
        pos_n10 = LEFT * 0.2 + UP * 0.5
        pos_spawn = LEFT * 2.6 + DOWN * 0.8  # 新结点在 UP 0.5 和 DOWN 2.0 的安全夹层生成

        # 恢复上一场景资产
        data_box = Rectangle(width=1.2, height=0.8, color=BLUE)
        ptr_box = Rectangle(width=0.4, height=0.8, color=BLUE).next_to(data_box, RIGHT, buff=0)
        ptr_dot = Dot(radius=0.06, color=BLUE).move_to(ptr_box.get_center())
        tail_marker = Text("^", font_size=24, color=BLUE).move_to(ptr_box.get_center())
        ptr_dot.set_opacity(0)
        tail_marker.set_opacity(1)
        
        head_node_L = VGroup(data_box, ptr_box, ptr_dot, tail_marker).move_to(pos_head)
        label_head = Text("头结点", font_size=22, color=WHITE).next_to(data_box, DOWN, buff=0.3)
        l_arrow = Arrow(start=data_box.get_left() + LEFT * 1.0, end=data_box.get_left(), buff=0.1, color=WHITE)
        l_text = Text("L", font_size=36, color=WHITE).next_to(l_arrow.get_start(), LEFT, buff=0.1)
        l_pointer = VGroup(l_arrow, l_text)

        queue_label = Text("输入序列:", font_size=24, color=WHITE).move_to(DOWN * 2.0 + LEFT * 2.5)
        q_box_1 = Square(side_length=0.8, color=WHITE)
        q_box_2 = Square(side_length=0.8, color=WHITE)
        q_box_3 = Square(side_length=0.8, color=WHITE)
        queue_boxes = VGroup(q_box_1, q_box_2, q_box_3).arrange(RIGHT, buff=0.3).next_to(queue_label, RIGHT, buff=0.4)
        q_val_1 = Text("10", font_size=24, color=WHITE).move_to(q_box_1.get_center())
        q_val_2 = Text("20", font_size=24, color=WHITE).move_to(q_box_2.get_center())
        q_val_3 = Text("30", font_size=24, color=WHITE).move_to(q_box_3.get_center())

        # 【修复1】：缩小代码块并贴近右上角
        code_l1 = Text("p = new LNode;", font_size=16, color=WHITE)
        code_l2 = Text("cin >> p->data;", font_size=16, color=WHITE)
        code_l3 = Text("p->next = L->next;", font_size=16, color=WHITE)
        code_l4 = Text("L->next = p;", font_size=16, color=WHITE)
        code_group = VGroup(code_l1, code_l2, code_l3, code_l4).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        code_bg = SurroundingRectangle(code_group, color=GRAY, buff=0.2, fill_opacity=0.1)
        code_block = VGroup(code_bg, code_group).to_corner(UR).shift(DOWN * 0.1 + LEFT * 0.1)

        self.add(head_node_L, label_head, l_pointer, queue_label, queue_boxes, q_val_1,
                 q_val_2, q_val_3, code_block)

        title_text = Text("第一次插入操作", font_size=40, color=WHITE).to_edge(UP)
        with subtitle_voiceover(self, "接下来，我们看如何将第一个元素10插入到链表中。") as tracker:
            self.play(Write(title_text), run_time=tracker.duration)

        p_data_box = Rectangle(width=1.2, height=0.8, color=WHITE)
        p_ptr_box = Rectangle(width=0.4, height=0.8, color=WHITE).next_to(p_data_box, RIGHT, buff=0)
        p_ptr_dot = Dot(radius=0.06, color=WHITE).move_to(p_ptr_box.get_center())
        p_tail_marker = Text("^", font_size=24, color=WHITE).move_to(p_ptr_box.get_center())
        p_ptr_dot.set_opacity(0)
        p_tail_marker.set_opacity(0) # Initially empty pointer field
        
        new_node_p = VGroup(p_data_box, p_ptr_box, p_ptr_dot, p_tail_marker).move_to(pos_spawn)
        p_label = Text("p", font_size=24, color=GREEN).next_to(p_data_box, UP, buff=0.3)

        with subtitle_voiceover(self, "首先，系统分配一块新的内存空间，生成一个新结点，我们用指针p来指向它。") as tracker:
            self.play(FadeIn(new_node_p), FadeIn(p_label), code_l1.animate.set_color(YELLOW), run_time=tracker.duration)

        with subtitle_voiceover(self, "然后，将要存入的数据10，放入新结点p的数据域中。") as tracker:
            self.play(
                q_val_1.animate.move_to(p_data_box.get_center()),
                code_l1.animate.set_color(WHITE), code_l2.animate.set_color(YELLOW),
                run_time=tracker.duration
            )
            new_node_p.add(q_val_1)

        with subtitle_voiceover(self, "前插法的关键第一步，是让新结点的next指针，指向头结点当前的后继结点。现在链表为空，所以指向NULL。") as tracker:
            self.play(
                p_tail_marker.animate.set_opacity(1),
                code_l2.animate.set_color(WHITE), code_l3.animate.set_color(YELLOW),
                run_time=tracker.duration
            )

        arrow_l_to_p = always_redraw(lambda: Arrow(ptr_dot.get_center(), p_data_box.get_left(), buff=0.1, color=RED))
        with subtitle_voiceover(self, "第二步，修改头结点的指针，使其指向我们的新结点p。这样，结点10就成功挂在头结点后面了。") as tracker:
            self.play(
                ptr_dot.animate.set_opacity(1), tail_marker.animate.set_opacity(0),
                Create(arrow_l_to_p),
                code_l3.animate.set_color(WHITE), code_l4.animate.set_color(YELLOW),
                run_time=tracker.duration
            )

        with subtitle_voiceover(self, "现在，第一次插入操作就完成了。") as tracker:
            self.play(
                new_node_p.animate.move_to(pos_p),
                p_label.animate.move_to(pos_p + UP * 0.7),
                run_time=tracker.duration
            )

        self.play(code_l4.animate.set_color(WHITE), FadeOut(p_label))
        self.wait(1)


# ========== 场景 3: Scene3SubsequentInsertions (ID: scene3_subsequent_insertions) ==========
class Scene3SubsequentInsertions(VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        pos_head = LEFT * 5.0 + UP * 0.5
        pos_p = LEFT * 2.6 + UP * 0.5
        pos_n10 = LEFT * 0.2 + UP * 0.5
        pos_n20 = RIGHT * 2.2 + UP * 0.5
        pos_null = RIGHT * 4.6 + UP * 0.5
        pos_spawn = LEFT * 2.6 + DOWN * 0.8

        title_text = Text("后续插入：逆位序效果", font_size=40, color=WHITE).to_edge(UP)

        # 恢复状态
        h_data = Rectangle(width=1.2, height=0.8, color=BLUE)
        h_ptr = Rectangle(width=0.4, height=0.8, color=BLUE).next_to(h_data, RIGHT, buff=0)
        h_dot = Dot(radius=0.06, color=BLUE).move_to(h_ptr.get_center())
        head_node_L = VGroup(h_data, h_ptr, h_dot).move_to(pos_head)
        label_head = Text("头结点", font_size=22, color=WHITE).next_to(h_data, DOWN, buff=0.3)
        l_arrow = Arrow(start=h_data.get_left() + LEFT * 1.0, end=h_data.get_left(), buff=0.1, color=WHITE)
        l_text = Text("L", font_size=36, color=WHITE).next_to(l_arrow.get_start(), LEFT, buff=0.1)
        l_pointer = VGroup(l_arrow, l_text)

        n10_data = Rectangle(width=1.2, height=0.8, color=WHITE)
        n10_ptr = Rectangle(width=0.4, height=0.8, color=WHITE).next_to(n10_data, RIGHT, buff=0)
        n10_dot = Dot(radius=0.06, color=WHITE).move_to(n10_ptr.get_center())
        n10_tail_marker = Text("^", font_size=24, color=WHITE).move_to(n10_ptr.get_center())
        n10_dot.set_opacity(0)
        n10_tail_marker.set_opacity(1)
        q_val_1 = Text("10", font_size=24, color=WHITE).move_to(n10_data.get_center())
        node_10 = VGroup(n10_data, n10_ptr, n10_dot, n10_tail_marker, q_val_1).move_to(pos_p)

        arrow_l_to_10 = always_redraw(lambda: Arrow(h_dot.get_center(), n10_data.get_left(), buff=0.1, color=RED))

        queue_label = Text("输入序列:", font_size=24, color=WHITE).move_to(DOWN * 2.0 + LEFT * 2.5)
        q_box_1 = Square(side_length=0.8, color=WHITE)
        q_box_2 = Square(side_length=0.8, color=WHITE)
        q_box_3 = Square(side_length=0.8, color=WHITE)
        queue_boxes = VGroup(q_box_1, q_box_2, q_box_3).arrange(RIGHT, buff=0.3).next_to(queue_label, RIGHT, buff=0.4)
        q_val_2 = Text("20", font_size=24, color=WHITE).move_to(q_box_2.get_center())
        q_val_3 = Text("30", font_size=24, color=WHITE).move_to(q_box_3.get_center())

        code_l1 = Text("p = new LNode;", font_size=16, color=WHITE)
        code_l2 = Text("cin >> p->data;", font_size=16, color=WHITE)
        code_l3 = Text("p->next = L->next;", font_size=16, color=WHITE)
        code_l4 = Text("L->next = p;", font_size=16, color=WHITE)
        code_group = VGroup(code_l1, code_l2, code_l3, code_l4).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        code_bg = SurroundingRectangle(code_group, color=GRAY, buff=0.2, fill_opacity=0.1)
        code_block = VGroup(code_bg, code_group).to_corner(UR).shift(DOWN * 0.1 + LEFT * 0.1)

        self.add(title_text, head_node_L, label_head, l_pointer, node_10, arrow_l_to_10,
                 queue_label, queue_boxes, q_val_2, q_val_3, code_block)

        with subtitle_voiceover(self, "前插法，顾名思义，就是始终将新结点插入到头结点的紧后面。") as tracker:
            self.wait(tracker.duration)

        # ==================== 插入节点 20 ====================
        p2_data = Rectangle(width=1.2, height=0.8, color=WHITE)
        p2_ptr = Rectangle(width=0.4, height=0.8, color=WHITE).next_to(p2_data, RIGHT, buff=0)
        p2_dot = Dot(radius=0.06, color=WHITE).move_to(p2_ptr.get_center())
        new_node_p2 = VGroup(p2_data, p2_ptr, p2_dot).move_to(pos_spawn)
        p_label_2 = Text("p", font_size=24, color=GREEN).next_to(p2_data, UP, buff=0.3)

        with subtitle_voiceover(self, "接下来插入元素20。同理，生成一个新结点p，并将20存入它的数据域。") as tracker:
            self.play(FadeIn(new_node_p2), FadeIn(p_label_2), code_l1.animate.set_color(YELLOW),
                      run_time=tracker.duration / 2)
            self.play(
                q_val_2.animate.move_to(p2_data.get_center()),
                code_l1.animate.set_color(WHITE), code_l2.animate.set_color(YELLOW),
                run_time=tracker.duration / 2
            )
            new_node_p2.add(q_val_2)

        arrow_20_to_10 = always_redraw(lambda: Arrow(p2_dot.get_center(), n10_data.get_left(), buff=0.1, color=RED))
        with subtitle_voiceover(self, "同样地，先让新结点的next指针，指向头结点当前的后继结点，也就是刚才插入的10。") as tracker:
            self.play(Create(arrow_20_to_10), code_l2.animate.set_color(WHITE), code_l3.animate.set_color(YELLOW),
                      run_time=tracker.duration)

        arrow_l_to_20 = always_redraw(lambda: Arrow(h_dot.get_center(), p2_data.get_left(), buff=0.1, color=RED))
        with subtitle_voiceover(self, "然后再修改头结点的指针，使其指向新结点p。大家看，由于每次都在头部插入，后插入的元素反而排在了前面，这就形成了逆序的效果。") as tracker:
            arrow_l_to_10.clear_updaters()
            self.play(FadeOut(arrow_l_to_10), Create(arrow_l_to_20), code_l3.animate.set_color(WHITE),
                      code_l4.animate.set_color(YELLOW), run_time=tracker.duration / 2)
            self.play(node_10.animate.move_to(pos_n10),
                      new_node_p2.animate.move_to(pos_p),
                      p_label_2.animate.move_to(pos_p + UP * 0.7), run_time=tracker.duration / 2)

        self.play(code_l4.animate.set_color(WHITE), FadeOut(p_label_2))

        # ==================== 插入节点 30 ====================
        p3_data = Rectangle(width=1.2, height=0.8, color=WHITE)
        p3_ptr = Rectangle(width=0.4, height=0.8, color=WHITE).next_to(p3_data, RIGHT, buff=0)
        p3_dot = Dot(radius=0.06, color=WHITE).move_to(p3_ptr.get_center())
        new_node_p3 = VGroup(p3_data, p3_ptr, p3_dot).move_to(pos_spawn)
        p_label_3 = Text("p", font_size=24, color=GREEN).next_to(p3_data, UP, buff=0.3)

        with subtitle_voiceover(self, "以此类推，我们继续将元素30插入链表。") as tracker:
            self.play(FadeIn(new_node_p3), FadeIn(p_label_3), code_l1.animate.set_color(YELLOW),
                      run_time=tracker.duration / 2)
            self.play(
                q_val_3.animate.move_to(p3_data.get_center()),
                code_l1.animate.set_color(WHITE), code_l2.animate.set_color(YELLOW),
                run_time=tracker.duration / 2
            )
            new_node_p3.add(q_val_3)

        arrow_30_to_20 = always_redraw(lambda: Arrow(p3_dot.get_center(), p2_data.get_left(), buff=0.1, color=RED))
        with subtitle_voiceover(self, "新结点的next指针指向头结点的当前后继结点20。") as tracker:
            self.play(Create(arrow_30_to_20), code_l2.animate.set_color(WHITE), code_l3.animate.set_color(YELLOW),
                      run_time=tracker.duration)

        arrow_l_to_30 = always_redraw(lambda: Arrow(h_dot.get_center(), p3_data.get_left(), buff=0.1, color=RED))
        with subtitle_voiceover(self, "头结点更新指针，指向新结点30。前插法创建单链表就全部完成了！") as tracker:
            arrow_l_to_20.clear_updaters()
            self.play(FadeOut(arrow_l_to_20), Create(arrow_l_to_30), code_l3.animate.set_color(WHITE),
                      code_l4.animate.set_color(YELLOW), run_time=tracker.duration / 2)
            self.play(new_node_p2.animate.move_to(pos_n10),
                      node_10.animate.move_to(pos_n20),
                      new_node_p3.animate.move_to(pos_p),
                      p_label_3.animate.move_to(pos_p + UP * 0.7), run_time=tracker.duration / 2)
        self.play(code_l4.animate.set_color(WHITE), FadeOut(p_label_3), run_time=1.0)


        self.wait(2.0)


# ========== 场景 4: Scene4CompletionAndComplexityFixed (ID: completion_and_complexity_fixed) ==========
class Scene4CompletionAndComplexityFixed(VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        TitleText_group = VGroup()
        TitleText = Text("复杂度分析", font_size=40, color=WHITE).to_edge(UP)
        TitleText_group.add(TitleText)

        pos_head = LEFT * 5.0 + UP * 0.5
        pos_30 = LEFT * 2.6 + UP * 0.5
        pos_20 = LEFT * 0.2 + UP * 0.5
        pos_10 = RIGHT * 2.2 + UP * 0.5
        pos_null = RIGHT * 4.6 + UP * 0.5

        h_data = Rectangle(width=1.2, height=0.8, color=BLUE)
        h_ptr = Rectangle(width=0.4, height=0.8, color=BLUE).next_to(h_data, RIGHT, buff=0)
        h_dot = Dot(radius=0.06, color=BLUE).move_to(h_ptr.get_center())
        head_node_L = VGroup(h_data, h_ptr, h_dot).move_to(pos_head)
        label_head = Text("头结点", font_size=22, color=WHITE).next_to(h_data, DOWN, buff=0.3)

        l_arrow = Arrow(start=h_data.get_left() + LEFT * 1.0, end=h_data.get_left(), buff=0.1, color=WHITE)
        l_text = Text("L", font_size=36, color=WHITE).next_to(l_arrow.get_start(), LEFT, buff=0.1)
        l_pointer = VGroup(l_arrow, l_text)

        p3_d = Rectangle(width=1.2, height=0.8, color=WHITE)
        p3_p = Rectangle(width=0.4, height=0.8, color=WHITE).next_to(p3_d, RIGHT, buff=0)
        p3_o = Dot(radius=0.06, color=WHITE).move_to(p3_p.get_center())
        n30 = VGroup(p3_d, p3_p, p3_o).move_to(pos_30)
        t30 = Text("30", font_size=24, color=WHITE).move_to(p3_d.get_center())
        n30.add(t30)

        p2_d = Rectangle(width=1.2, height=0.8, color=WHITE)
        p2_p = Rectangle(width=0.4, height=0.8, color=WHITE).next_to(p2_d, RIGHT, buff=0)
        p2_o = Dot(radius=0.06, color=WHITE).move_to(p2_p.get_center())
        n20 = VGroup(p2_d, p2_p, p2_o).move_to(pos_20)
        t20 = Text("20", font_size=24, color=WHITE).move_to(p2_d.get_center())
        n20.add(t20)

        p1_d = Rectangle(width=1.2, height=0.8, color=WHITE)
        p1_p = Rectangle(width=0.4, height=0.8, color=WHITE).next_to(p1_d, RIGHT, buff=0)
        p1_o = Dot(radius=0.06, color=WHITE).move_to(p1_p.get_center())
        p1_tail = Text("^", font_size=24, color=WHITE).move_to(p1_p.get_center())
        p1_o.set_opacity(0)
        p1_tail.set_opacity(1)
        n10 = VGroup(p1_d, p1_p, p1_o, p1_tail).move_to(pos_10)
        t10 = Text("10", font_size=24, color=WHITE).move_to(p1_d.get_center())
        n10.add(t10)

        arr1 = Arrow(h_dot.get_center(), p3_d.get_left(), buff=0.1, color=RED)
        arr2 = Arrow(p3_o.get_center(), p2_d.get_left(), buff=0.1, color=RED)
        arr3 = Arrow(p2_o.get_center(), p1_d.get_left(), buff=0.1, color=RED)

        list_full = VGroup(head_node_L, label_head, l_pointer, n30, n20, n10, arr1, arr2, arr3)
        list_full.move_to(ORIGIN + UP * 0.5)

        self.play(FadeIn(TitleText), FadeIn(list_full), run_time=1)

        time_text = Text("时间复杂度: ", color=BLUE, font_size=30)
        time_math = MathTex("O(n)", color=BLUE, font_size=30)
        time_complexity = VGroup(time_text, time_math).arrange(RIGHT, buff=0.1)

        space_text = Text("空间复杂度: ", color=GREEN, font_size=30)
        space_math = MathTex("O(1)", color=GREEN, font_size=30)
        space_complexity = VGroup(space_text, space_math).arrange(RIGHT, buff=0.1)

        complexities = VGroup(time_complexity, space_complexity).arrange(RIGHT, buff=1.5).move_to(DOWN * 1.5)

        with subtitle_voiceover(self, "我们来分析一下复杂度。如果有n个元素，由于每一个结点只需要处理一次插入操作，所以整体的时间复杂度为O(n)。") as tracker:
            self.play(Write(time_complexity), run_time=tracker.duration)

        with subtitle_voiceover(self, "在插入过程中，除了为结点本身分配空间外，只需要常数级别的额外空间（如指针p），因此空间复杂度为O(1)。") as tracker:
            self.play(Write(space_complexity), run_time=tracker.duration)

        self.wait(2)
