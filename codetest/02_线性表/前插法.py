# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import numpy as np
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class LinkedListBase(VoiceoverScene):
    """单链表动画公共基类（带头结点，链表L指向头结点）
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

        # 显式指定 font="Arial" 确保数字基线和高度绝对对齐
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

        # 指针 L 位于头结点的左侧，水平向右指向头结点
        l_arrow = Arrow(
            start=head_node.get_left() + LEFT * 1.0,
            end=head_node.get_left(),
            buff=0,
            color=self.COLOR_L_PTR
        )
        l_text.next_to(l_arrow.get_start(), LEFT, buff=0.2)

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


class ContinuousHeadInsertVideo(LinkedListBase):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角全局图片 Logo（放大一倍至 2.0，紧靠右上角并往上微调）
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — OPENING =====
        algo_title = Text("前插法创建单链表", font_size=48, weight=BOLD).to_edge(UP, buff=0.6)
        self.add(algo_title)

        sentences = [
            "本节我们学习使用前插法创建单链表。",
            "该算法是通过将新结点逐个插入到链表的头部来创建链表"
        ]
        for sentence in sentences:
            with self.voiceover(text=sentence) as tracker:
                self.wait(tracker.duration)

        # ===== NEW PHASE — VIVID ANALOGY (手机通知栏生活实例) =====
        with self.voiceover(
                text="我们来看一个更贴近生活的实例：手机通知栏。手机上每来一条新通知，它都会出现在最上面。") as tracker:

            # 1. 手机外壳 (等比缩小精致版)
            phone_body = RoundedRectangle(corner_radius=0.26, width=3.45, height=5.6, color=GRAY, fill_color=BLACK,
                                          fill_opacity=1, stroke_width=3)
            # 2. 手机屏幕
            phone_screen = RoundedRectangle(corner_radius=0.18, width=3.25, height=5.4, color=DARK_GRAY,
                                            fill_color="#1C1C1E", fill_opacity=1, stroke_width=1.5)
            # 3. 顶部刘海/灵动岛
            notch = RoundedRectangle(corner_radius=0.09, width=0.9, height=0.18, color=BLACK, fill_color=BLACK,
                                     fill_opacity=1, stroke_width=0)
            notch.move_to(phone_screen.get_top() + DOWN * 0.09)
            # 4. 底部 Home 触控条
            home_bar = RoundedRectangle(corner_radius=0.04, width=0.9, height=0.06, color=WHITE, fill_opacity=0.6,
                                        stroke_width=0)
            home_bar.move_to(phone_screen.get_bottom() + UP * 0.15)
            # 5. 侧边实体按键
            btn_power = Rectangle(width=0.05, height=0.45, color=GRAY, fill_color=GRAY, fill_opacity=1).next_to(
                phone_body, RIGHT, buff=0).shift(UP * 0.6)
            btn_vol_up = Rectangle(width=0.05, height=0.3, color=GRAY, fill_color=GRAY, fill_opacity=1).next_to(
                phone_body, LEFT, buff=0).shift(UP * 0.9)
            btn_vol_down = Rectangle(width=0.05, height=0.3, color=GRAY, fill_color=GRAY, fill_opacity=1).next_to(
                phone_body, LEFT, buff=0).shift(UP * 0.45)

            # 组装整台手机并将其放置在画面偏下位置
            phone_group = VGroup(btn_power, btn_vol_up, btn_vol_down, phone_body, phone_screen, notch,
                                 home_bar).move_to(DOWN * 0.2)

            # 通知中心标题，严格锚定在刘海下方，留出防护空隙
            panel_title = Text("通知中心", font_size=15, color=GRAY_A, weight=BOLD).next_to(notch, DOWN, buff=0.15)

            self.play(FadeIn(phone_group, shift=UP * 0.5), FadeIn(panel_title), run_time=1.5)

        # 定义通知卡片（回调并完全还原第一版的视觉样式与透明度，并适配手机宽度）
        def create_notification(app_name, content, color=BLUE):
            notif_w, notif_h = 3.0, 0.75
            box = RoundedRectangle(corner_radius=0.075, width=notif_w, height=notif_h, color=color, fill_color=color,
                                   fill_opacity=0.15, stroke_width=1.5)

            app_text = Text(app_name, font_size=12, weight=BOLD, color=color)
            content_text = Text(content, font_size=10.5, color=WHITE)

            texts = VGroup(app_text, content_text).arrange(DOWN, aligned_edge=LEFT, buff=0.075)
            texts.move_to(box.get_center()).align_to(box, LEFT).shift(RIGHT * 0.225)

            return VGroup(box, texts)

        # 管理场景中的活跃通知集合
        active_notifications = VGroup()
        START_Y = panel_title.get_bottom()[1] - 0.45
        NOTIF_BUFF = 0.86

        with self.voiceover(text="假设现在来了第一条新通知：微信消息。它会直接呈现在通知栏的最上方。") as tracker:
            notif_1 = create_notification("微信", "你收到了一条新消息", BLUE)
            notif_1.move_to([phone_screen.get_center()[0], START_Y, 0])
            self.play(FadeIn(notif_1, shift=DOWN * 0.3), run_time=1.2)
            active_notifications.add(notif_1)

        with self.voiceover(text="接着，又来了一条新通知：系统更新。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(
                text="前插法的核心在于：新到来的通知必须抢占最顶端的位置，而原有的微信通知则被整体向下推一格。") as tracker:
            notif_2 = create_notification("系统更新", "发现新版本，请及时升级", PURPLE)
            notif_2.move_to([phone_screen.get_center()[0], START_Y, 0])

            # 微信通知下移的同时，系统通知抢滩最顶部
            self.play(
                notif_1.animate.shift(DOWN * NOTIF_BUFF),
                FadeIn(notif_2, shift=DOWN * 0.3),
                run_time=1.5
            )
            active_notifications.add(notif_2)

        with self.voiceover(text="以此类推，当第三条通知：支付通知 到来时，它再次插到最前面，也就是最顶端。") as tracker:
            notif_3 = create_notification("支付宝", "成功收款 10.00 元", GREEN)
            notif_3.move_to([phone_screen.get_center()[0], START_Y, 0])

            # 之前的所有通知整体向下顺延
            self.play(
                notif_1.animate.shift(DOWN * NOTIF_BUFF),
                notif_2.animate.shift(DOWN * NOTIF_BUFF),
                FadeIn(notif_3, shift=DOWN * 0.3),
                run_time=1.5
            )
            active_notifications.add(notif_3)

        with self.voiceover(
                text="如果我们把每条通知都看作一个链表的新结点，这种每次都把新元素放到链表最前端的操作，就是前插法创建单链表的本质。") as tracker:
            # 高亮突出最顶端最新插入的通知结点
            highlight_box = SurroundingRectangle(notif_3, color=YELLOW, buff=0.08, corner_radius=0.1)
            self.play(Create(highlight_box), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))
            self.play(FadeOut(highlight_box))

        # 结束时优雅淡出清理整个手机面板资产
        self.play(
            FadeOut(phone_group),
            FadeOut(panel_title),
            FadeOut(active_notifications),
            run_time=1.0
        )

        # ===== PHASE B — CODE BLOCK =====
        c_lines = [
            "void CreateList_H(LinkList &L, int n) {",
            "    LNode *p;",
            "    L = new LNode;",
            "    L->next = NULL;",
            "    for (int i = 0; i < n; ++i) {",
            "        p = new LNode;",
            "        cin>>p->data;",
            "        p->next = L->next;",
            "        L->next = p;",
            "    }",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip("  ")
            t = Text(stripped_line, font_size=13, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.14)

        SPACE_WIDTH = 0.105
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip("  "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 6.25:
            code_group.scale_to_fit_width(6.25)
        if code_group.height > 5.4:
            code_group.scale_to_fit_height(5.4)

        buff_val = 0.32
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

        # 代码块垂直中心位置设定在 UP * 0.0，完美防遮挡
        code_block = VGroup(code_bg, code_group).move_to(RIGHT * 4.2 + UP * 0.0)

        input_params = VGroup(
            Text("参数：", font_size=24, color=YELLOW),
            MathTex("n=3", font_size=26, color=YELLOW)
        ).arrange(RIGHT, buff=0.15).next_to(code_block, DOWN, buff=0.2).align_to(code_block, LEFT)

        self.current_line = None

        def get_track_anims(new_idx):
            anims = []
            if self.current_line is not None:
                old_idx = self.current_line
                anims.append(self.c_texts[old_idx].animate.set_color(WHITE).scale(1 / 1.08, about_edge=LEFT))

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

        with self.voiceover(text="假设我们需要创建包含3个元素的单链表。") as tracker:
            self.play(FadeIn(code_block), FadeIn(input_params), run_time=tracker.duration)
        self.wait(1.0)

        # ===== PHASE C — INITIALIZATION =====
        with self.voiceover(text="首先，在内存中分配一个空结点作为头结点。") as tracker:
            self.play(*get_track_anims(2), run_time=1.0)

            # 链表整体向下平移至 UP * 0.2，留出顶部呼吸空间
            head_node = self.create_node("", color=self.COLOR_HEAD, is_tail=True)
            head_node.move_to(LEFT * 4 + UP * 0.2)
            self.play(FadeIn(head_node))

            self.nodes.append(head_node)
            self.node_mobjects.add(head_node)

            self.add_pointer_L()
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(text="执行初始化，将头结点的指针域置为空。") as tracker:
            self.play(*get_track_anims(3), run_time=tracker.duration)

        # ===== PHASE D — LOOP AND INSERTION =====
        input_values = [10, 20, 30]
        # 输入序列框保持在 DOWN * 1.8 处，水平向左移至 LEFT * 4.5，完美避免与 p 指针或底部字幕产生重叠
        input_queue_box = Rectangle(width=3, height=1, color=WHITE).move_to(DOWN * 1.8 + LEFT * 4.5)
        queue_label = Text("输入序列", font_size=24).next_to(input_queue_box, UP)

        data_texts = VGroup(*[Text(str(val), font_size=30, font="Arial") for val in input_values]).arrange(RIGHT,
                                                                                                           buff=0.5).move_to(
            input_queue_box)

        with self.voiceover(text="准备进入循环，依次读入输入序列中的元素。") as tracker:
            self.play(*get_track_anims(4), FadeIn(input_queue_box), FadeIn(queue_label), FadeIn(data_texts),
                      run_time=tracker.duration)

        for i, val in enumerate(input_values):
            data_text = data_texts[i]

            if i == 0:
                insertion_intro = f"接下来插入第一个结点，数据元素是{val}。"
            elif i == len(input_values) - 1:
                insertion_intro = f"最后，插入第三个结点，数据元素是{val}。"
            else:
                insertion_intro = f"接下来插入第二个结点，数据元素是{val}。"

            with self.voiceover(text=insertion_intro) as tracker:
                self.wait(tracker.duration)

            with self.voiceover(text=f"第一步，生成新结点p。") as tracker:
                self.play(*get_track_anims(5), run_time=1.0)

                # 避开左下角的输入序列框，在宽敞的右下方生成新结点
                new_node = self.create_node("", color=self.COLOR_INSERT, is_tail=False)
                new_node.move_to(LEFT * 1.5 + DOWN * 0.8)

                p_ptr = self.create_pointer(new_node, "p", color=self.COLOR_CURRENT, direction=DOWN, offset=0.0)

                self.play(FadeIn(new_node), FadeIn(p_ptr))
                self.wait(max(0.1, tracker.duration - 1.0))

            with self.voiceover(text=f"第二步，读入数据元素值{val}，赋给新结点的数据域。") as tracker:
                self.play(*get_track_anims(6), run_time=0.5)

                target_val_text = Text(str(val), font_size=self.FONT_SIZE, font="Arial").move_to(
                    new_node.rect.get_center() + LEFT * (self.NODE_WIDTH / 8))
                self.play(data_text.animate.move_to(target_val_text.get_center()), run_time=1.0)

                new_node.val_text.become(target_val_text)
                self.remove(data_text)
                self.wait(max(0.1, tracker.duration - 1.5))

            third_step_text = (
                "第三步，让 p 指向头结点当前后继。第一次前插时 L->next 为空，所以 p 的 next 指针指向 NULL。"
                if len(self.nodes) == 1
                else "第三步，将新结点的指针域，也就是 p 的 next 指针，指向头结点的当前后继结点，也就是原来的第一个数据结点。"
            )
            with self.voiceover(text=third_step_text) as tracker:
                self.play(*get_track_anims(7), run_time=0.5)

                # 创建从新结点 p 指向头结点当前后继结点的临时绿色连线
                if len(self.nodes) == 1:
                    # 此时链表仅有头结点，p 指针域置空，呈现尾标志
                    self.set_tail(new_node, is_tail=True)
                    self.wait(max(0.1, tracker.duration - 0.5))
                    temp_arrow = None
                else:
                    # p 指向原本排在首位的结点（即 self.nodes[1]）
                    self.set_tail(new_node, is_tail=False)
                    temp_arrow = self.create_arrow_between(new_node, self.nodes[1], color=GREEN)
                    self.play(GrowArrow(temp_arrow), run_time=1.0)
                    self.wait(max(0.1, tracker.duration - 1.5))

            with self.voiceover(text="第四步，修改头结点的指针域，使其指向新结点p。") as tracker:
                self.play(*get_track_anims(8), run_time=1.0)

                # 如果存在旧连线（头结点指向原第一结点的连线），将其淡出
                if len(self.arrows) > 0:
                    old_head_arrow = self.arrows[0]
                    self.play(FadeOut(old_head_arrow), run_time=0.5)

                # 建立头结点指向新结点 p 的临时黄色连线
                head_to_p_arrow = self.create_arrow_between(self.nodes[0], new_node, color=YELLOW)
                self.play(GrowArrow(head_to_p_arrow), run_time=0.5)
                self.wait(max(0.1, tracker.duration - 1.0))

            with self.voiceover(text="新结点成功挂载。") as tracker:
                # 正式将新结点插入到链表结构中（紧跟在头结点之后，即索引 1 处）
                self.nodes.insert(1, new_node)
                self.node_mobjects.add(new_node)

                # 清理刚才演练的临时连线，后面交由标准对齐逻辑重新建立
                if temp_arrow is not None:
                    self.remove(temp_arrow)
                self.remove(head_to_p_arrow)

                # 清空旧有的规范连线
                for arrow in self.arrows:
                    self.remove(arrow)
                self.arrows = VGroup()

                # 丝滑地重构整条链表的排列位置，将旧结点平滑地向右推开
                anim_group = []
                for idx in range(len(self.nodes)):
                    self.nodes[idx].generate_target()
                    if idx == 0:
                        self.nodes[idx].target.move_to(LEFT * 4 + UP * 0.2)
                    else:
                        self.nodes[idx].target.next_to(self.nodes[idx - 1].target, RIGHT,
                                                       buff=self.NODE_SPACING - self.NODE_WIDTH)
                    anim_group.append(MoveToTarget(self.nodes[idx]))

                # 指针 p 同步随之重定位到上方主链表中
                target_p_final = self.create_pointer(self.nodes[1], "p", color=self.COLOR_CURRENT, direction=DOWN)
                anim_group.append(Transform(p_ptr, target_p_final))

                self.play(*anim_group, run_time=1.2)

                # 重新生长整条链表的白色标准连线
                arrow_anims = []
                for idx in range(len(self.nodes) - 1):
                    new_arrow = self.create_arrow_between(self.nodes[idx], self.nodes[idx + 1], color=WHITE)
                    self.arrows.add(new_arrow)
                    arrow_anims.append(GrowArrow(new_arrow))
                if arrow_anims:
                    self.play(*arrow_anims, run_time=0.6)

            # 准备退出本次循环，淡出清除指针环境
            self.play(FadeOut(p_ptr), run_time=0.4)
            self.play(*get_track_anims(4), run_time=0.4)
            self.reset_node_color(1, run_time=0.4)

        # ===== 循环结束 =====
        with self.voiceover(text="所有元素处理完毕，退出循环。前插法创建的链表呈现出输入序列的逆序效果。") as tracker:
            self.play(*get_track_anims(None), FadeOut(input_queue_box), FadeOut(queue_label), run_time=tracker.duration)

        # ===== PHASE E — COMPLEXITY =====
        complexity_panel = VGroup(
            VGroup(Text("时间复杂度：", font_size=24, color=YELLOW),
                   MathTex("O(n)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1),
            VGroup(Text("空间复杂度：", font_size=24, color=YELLOW),
                   MathTex("O(1)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(LEFT * 3.5 + DOWN * 2)

        with self.voiceover(
                text="每个结点的插入操作都是常数级。如果有n个元素，总时间复杂度为O(n)。仅使用了辅助指针p，额外空间复杂度为O(1)。",
                subcaption="每个结点的插入操作都是常数级。如果有n个元素，总时间复杂度为O(n)。仅使用了辅助指针p，额外空间复杂度为O(1)。"
        ) as tracker:
            self.play(FadeIn(complexity_panel), run_time=tracker.duration)

        with self.voiceover(text="这就是前插法创建单链表的完整演示。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)
