# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
class DuLinkListDeleteVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角 Logo
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("双向链表的删除", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        # 彻底移除“第i个”周围的人工空格，使语音合成连续流畅，消除停顿错误
        with self.voiceover(
                text="本节我们来学习双向链表的删除算法。该算法用于删除双向链表中的第i个数据结点，并释放其内存空间。",
                subcaption="本节我们来学习双向链表的删除算法。该算法用于删除双向链表中的第i个数据结点，并释放其内存空间。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== NEW PHASE — LIFE EXAMPLE (双向车厢的解挂) =====
        # =========================================================================
        example_title = Text("生活实例：双向锁扣车厢的解挂", font_size=32, font="Microsoft YaHei", color=YELLOW).to_edge(
            UP, buff=1.4)

        # 引入后插法中带有精美车轮和双车窗的高级车厢渲染引擎
        def create_beautified_train_car(color, text):
            car_w, car_h = 1.8, 1.1
            car_group = VGroup()
            body = RoundedRectangle(
                corner_radius=0.12, width=car_w, height=car_h, color=color,
                fill_color=color, fill_opacity=0.25, stroke_width=3
            )
            car_group.add(body)
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
            label = Text(text, font_size=18, font="Microsoft YaHei", weight=BOLD, color=WHITE).move_to(
                body.get_center() + DOWN * 0.25)
            car_group.add(wheel1, wheel2, w_dot1, w_dot2, label)
            car_group.body = body
            return car_group

        def create_ex_fwd_coupler(start_x, end_x, y_val):
            return Arrow(start=[start_x, y_val, 0], end=[end_x, y_val, 0], buff=0, color=WHITE, tip_length=0.15)

        def create_ex_bwd_coupler(start_x, end_x, y_val):
            return Arrow(start=[start_x, y_val, 0], end=[end_x, y_val, 0], buff=0, color=WHITE, tip_length=0.15)

        # 初始化三节连结的车厢 A, P, B
        carA_g = create_beautified_train_car(BLUE, "车厢 A").move_to(LEFT * 4.6 + DOWN * 0.6)
        carP_g = create_beautified_train_car(RED, "车厢 P").move_to(LEFT * 2.0 + DOWN * 0.6)
        carB_g = create_beautified_train_car(BLUE, "车厢 B").move_to(RIGHT * 0.6 + DOWN * 0.6)

        init_fwd1 = create_ex_fwd_coupler(-3.7, -2.9, -0.5)
        init_bwd1 = create_ex_bwd_coupler(-2.9, -3.7, -0.7)
        init_fwd2 = create_ex_fwd_coupler(-1.1, -0.3, -0.5)
        init_bwd2 = create_ex_bwd_coupler(-0.3, -1.1, -0.7)

        with self.voiceover(text="解挂过程同样可以类比火车。假设我们要拆除中间这节红色的车厢 P。") as tracker:
            self.play(
                FadeIn(example_title), FadeIn(carA_g), FadeIn(carP_g), FadeIn(carB_g),
                Create(init_fwd1), Create(init_bwd1), Create(init_fwd2), Create(init_bwd2),
                run_time=0.6
            )
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(
                text="第一步，我们将车厢 A 向后拉的锁扣越过 P，调整到正上方轨道，扣在后面的车厢 B 上。") as tracker:
            self.play(FadeOut(init_fwd1), run_time=0.2)
            bridge_fwd = Arrow(start=[-3.7, 0.05, 0], end=[-0.3, 0.05, 0], buff=0, color=YELLOW, tip_length=0.15)
            self.play(Create(bridge_fwd), run_time=max(0.1, tracker.duration - 0.2))

        with self.voiceover(
                text="第二步，同理，将车厢 B 向前拉的锁扣也调整到正下方轨道，扣在前面的车厢 A 上。") as tracker:
            self.play(FadeOut(init_bwd2), run_time=0.2)
            bridge_bwd = Arrow(start=[-0.3, -1.25, 0], end=[-3.7, -1.25, 0], buff=0, color=YELLOW, tip_length=0.15)
            self.play(Create(bridge_bwd), run_time=max(0.1, tracker.duration - 0.2))

        with self.voiceover(
                text="此时车厢 P 已经被完全孤立，我们解开它身上剩余的挂钩，并安全地把它从轨道上拖走。") as tracker:
            self.play(FadeOut(init_bwd1), FadeOut(init_fwd2), run_time=0.2)
            self.play(carP_g.animate.shift(UP * 2.0).set_opacity(0), run_time=0.6)

            self.play(
                carB_g.animate.shift(LEFT * 2.6),
                FadeOut(bridge_fwd), FadeOut(bridge_bwd),
                run_time=0.6
            )
            final_fwd = Arrow(start=[-3.7, -0.5, 0], end=[-2.9, -0.5, 0], buff=0, color=GREEN, tip_length=0.15)
            final_bwd = Arrow(start=[-2.9, -0.7, 0], end=[-3.7, -0.7, 0], buff=0, color=GREEN, tip_length=0.15)
            self.add(final_fwd, final_bwd)
            self.wait(max(0.1, tracker.duration - 1.4))

        # 清空实例资产
        self.play(FadeOut(example_title), FadeOut(carA_g), FadeOut(carB_g), FadeOut(final_fwd), FadeOut(final_bwd),
                  run_time=0.5)

        # =========================================================================
        # ===== PHASE B — CODE BLOCK CONFIG =====
        # =========================================================================
        c_lines = [
            "Status ListDelete_DuL(DuLinkList &L, int i) {",
            "    DuLNode *p;",
            "    if (!(p = GetElemP_DuL(L, i)))",
            "        return ERROR;",
            "    p->prior->next = p->next;",
            "    if (p->next)",
            "        p->next->prior = p->prior;",
            "    delete p;",
            "    return OK;",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=13.5, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        SPACE_WIDTH = 0.11
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        bg_width = code_group.get_width() * 1.1 + 0.5
        bg_height = code_group.get_height() + 0.4
        code_bg = RoundedRectangle(corner_radius=0.15, height=bg_height, width=bg_width, color=GRAY, fill_opacity=0.1,
                                   stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.3)
        code_bg.match_y(code_group)

        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.2).to_edge(RIGHT, buff=0.4)

        self.current_lines = []

        def get_track_anims(new_idx):
            if isinstance(new_idx, int):
                new_idx = [new_idx]
            elif new_idx is None:
                new_idx = []
                
            if set(new_idx) == set(self.current_lines): return []
            anims = []
            for idx in self.current_lines:
                if idx not in new_idx:
                    anims.append(self.c_texts[idx].animate.set_color(WHITE).scale(1 / 1.15, about_edge=LEFT))
            
            first_idx = None
            for idx in new_idx:
                if idx not in self.current_lines:
                    anims.append(self.c_texts[idx].animate.set_color(YELLOW).scale(1.15, about_edge=LEFT))
                if first_idx is None or idx < first_idx:
                    first_idx = idx

            if first_idx is not None:
                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.16).rotate(-PI / 2)
                    self.code_pointer.next_to(self.c_texts[first_idx], LEFT, buff=0.2)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.c_texts[first_idx], LEFT, buff=0.2)
                    anims.append(MoveToTarget(self.code_pointer))
            else:
                if hasattr(self, 'code_pointer'):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, 'code_pointer')
                    
            self.current_lines = new_idx
            return anims

        with self.voiceover(text="右侧是双向链表删除算法的代码。我们来拆解底层的指针连结逻辑。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # =========================================================================
        # ===== PHASE C — VISUALIZATION SETUP =====
        # =========================================================================
        def build_node(val_str, is_head=False):
            color = PURPLE if is_head else BLUE
            prior_box = Rectangle(width=0.35, height=0.6, color=color)
            data_box = Rectangle(width=0.8, height=0.6, color=color).next_to(prior_box, RIGHT, buff=0)
            next_box = Rectangle(width=0.35, height=0.6, color=color).next_to(data_box, RIGHT, buff=0)

            node_group = VGroup(prior_box, data_box, next_box)
            prior_dot = Dot(radius=0.04, color=color).move_to(prior_box.get_center())
            prior_null = Text("^", font_size=20, color=color).move_to(prior_box.get_center())
            data_text = Text(val_str, font_size=22, font="Arial", color=WHITE).move_to(data_box.get_center())
            next_dot = Dot(radius=0.04, color=color).move_to(next_box.get_center())
            next_null = Text("^", font_size=20, color=color).move_to(next_box.get_center())

            node_group.add(prior_dot, prior_null, data_text, next_dot, next_null)
            node_group.prior_dot = prior_dot
            node_group.prior_null = prior_null
            node_group.next_dot = next_dot
            node_group.next_null = next_null
            node_group.prior_box = prior_box
            node_group.data_box = data_box
            node_group.next_box = next_box

            prior_dot.set_opacity(1)
            prior_null.set_opacity(0)
            next_dot.set_opacity(1)
            next_null.set_opacity(0)
            return node_group

        def get_ptr(label, target_mobj, color=GREEN, direction=UP):
            if np.array_equal(direction, UP):
                arrow = Arrow(start=target_mobj.get_top() + UP * 0.7, end=target_mobj.get_top(), buff=0.05, color=color)
                txt = Text(label, font_size=18, font="Arial", color=color).next_to(arrow, UP, buff=0.05)
            else:
                arrow = Arrow(start=target_mobj.get_bottom() + DOWN * 0.7, end=target_mobj.get_bottom(), buff=0.05,
                              color=color)
                txt = Text(label, font_size=18, font="Arial", color=color).next_to(arrow, DOWN, buff=0.05)
            return VGroup(arrow, txt)

        # 初始化位置
        head = build_node("L", is_head=True).move_to(LEFT * 5.8 + UP * 0.5)
        set_null = lambda node, field, is_null: (
            getattr(node, f"{field}_dot").set_opacity(0 if is_null else 1),
            getattr(node, f"{field}_null").set_opacity(1 if is_null else 0)
        )
        set_null(head, "prior", True)

        n1 = build_node("10").move_to(LEFT * 3.4 + UP * 0.5)
        n2 = build_node("20").move_to(LEFT * 1.0 + UP * 0.5)
        n3 = build_node("30").move_to(RIGHT * 1.4 + UP * 0.5)
        set_null(n3, "next", True)

        a_h_fwd = Arrow(start=[-5.225, 0.65, 0], end=[-4.15, 0.65, 0], buff=0, color=WHITE, tip_length=0.12)
        a_1_bwd = Arrow(start=[-3.975, 0.35, 0], end=[-5.05, 0.35, 0], buff=0, color=WHITE, tip_length=0.12)

        a_1_fwd = Arrow(start=[-2.825, 0.65, 0], end=[-1.75, 0.65, 0], buff=0, color=WHITE, tip_length=0.12)
        a_2_bwd = Arrow(start=[-1.575, 0.35, 0], end=[-2.65, 0.35, 0], buff=0, color=WHITE, tip_length=0.12)

        a_2_fwd = Arrow(start=[-0.425, 0.65, 0], end=[0.65, 0.65, 0], buff=0, color=WHITE, tip_length=0.12)
        a_3_bwd = Arrow(start=[0.825, 0.35, 0], end=[-0.25, 0.35, 0], buff=0, color=WHITE, tip_length=0.12)

        l_ptr = get_ptr("L", head, ORANGE, direction=UP)

        with self.voiceover(text="假设当前双向链表包含三个有效数据结点 10、20 和 30。") as tracker:
            self.play(
                FadeIn(head, n1, n2, n3),
                GrowArrow(a_h_fwd), GrowArrow(a_1_bwd), GrowArrow(a_1_fwd), GrowArrow(a_2_bwd), GrowArrow(a_2_fwd),
                GrowArrow(a_3_bwd),
                FadeIn(l_ptr),
                run_time=tracker.duration
            )

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW =====
        # =========================================================================

        # 第一步：查找确定被删结点指针 p
        with self.voiceover(text="第一步，通过位置查找到待删除的第二个数据结点，让指针 p 精准指向数据结点 20。",
                            subcaption="第一步，通过位置查找到待删除的第2个数据结点，让指针p精准指向数据结点20。") as tracker:
            self.play(*get_track_anims(2), run_time=0.4)
            p_ptr = get_ptr("p", n2, GREEN, direction=DOWN)
            self.play(FadeIn(p_ptr), run_time=max(0.2, tracker.duration - 0.4))

        # 第二步：p->prior->next = p->next; (前驱指向后继)
        with self.voiceover(
                text="第二步：修改被删结点前驱的后继指针。让结点 10 的后继域跨过 20，直接指向 30。") as tracker:
            self.play(*get_track_anims(4), run_time=0.4)
            self.play(FadeOut(a_1_fwd), run_time=0.2)

            # 【修改点】效仿范例代码的 CurvedArrow 逻辑，设置 angle=-TAU/3 使弧线向上弯曲绕过 20 结点
            n1_to_n3 = CurvedArrow(
                [-2.825, 0.65, 0],
                [0.65, 0.65, 0],
                angle=-TAU / 3,
                color=YELLOW
            )
            self.play(Create(n1_to_n3), run_time=max(0.2, tracker.duration - 0.6))

        # 第三步：p->next->prior = p->prior; (后继指向前驱)
        with self.voiceover(
                text="第三步：判断待删结点是否有后继结点，这里 20 不是尾结点，继续修改其后继结点的前驱指针。让右侧结点 30 的前驱域也跨过 20。") as tracker:
            self.play(*get_track_anims([5, 6]), run_time=0.4)
            self.play(FadeOut(a_3_bwd), run_time=0.2)

            # 【修改点】使用 CurvedArrow 控制反向连线，angle=-TAU/3 配合右向左绘制，能生成完美的下凹对称弧线
            n3_to_n1 = CurvedArrow(
                [0.825, 0.35, 0],
                [-2.65, 0.35, 0],
                angle=-TAU / 3,
                color=YELLOW
            )
            self.play(Create(n3_to_n1), run_time=max(0.2, tracker.duration - 0.6))

        # 第四步：delete p; (释放空间)
        with self.voiceover(
                text="第四步：此时结点 20 已经脱离链表结构。我们调用 delete 释放其内存空间。") as tracker:
            self.play(*get_track_anims(7), run_time=0.4)
            self.play(FadeOut(n2), FadeOut(p_ptr), FadeOut(a_2_bwd), FadeOut(a_2_fwd),
                      run_time=max(0.5, tracker.duration - 0.4))

        # 第五步：一维同轴平滑补位与曲线回归直线
        with self.voiceover(
                text="最后，结点20删除完毕。") as tracker:
            self.play(*get_track_anims(8), run_time=0.3)

            # 回归后标准水平绿色直线连线目标
            final_fwd_line = Arrow(start=[-2.825, 0.65, 0], end=[-1.75, 0.65, 0], buff=0, color=GREEN, tip_length=0.12)
            final_bwd_line = Arrow(start=[-1.575, 0.35, 0], end=[-2.65, 0.35, 0], buff=0, color=GREEN, tip_length=0.12)

            # Transform 会完美、圆滑地将上下的 CurvedArrow 压平并缩短，恢复为直连形态
            self.play(
                n3.animate.move_to(LEFT * 1.0 + UP * 0.5),
                Transform(n1_to_n3, final_fwd_line),
                Transform(n3_to_n1, final_bwd_line),
                run_time=max(1.0, tracker.duration)
            )

        # =========================================================================
        # ===== NEW PHASE — COMPACT PANEL CONFIG =====
        # =========================================================================
        res_text = VGroup(
            Text("结果：", font_size=20, font="Microsoft YaHei", color=GREEN),
            Text("删除成功，返回 OK", font_size=18, font="Microsoft YaHei", color=GREEN)
        ).arrange(RIGHT, buff=0.1)

        time_text = VGroup(
            Text("时间复杂度：", font_size=18, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(n)", font_size=18, color=YELLOW)
        ).arrange(RIGHT, buff=0.1)

        space_text = VGroup(
            Text("空间复杂度：", font_size=18, font="Microsoft YaHei", color=YELLOW),
            MathTex("O(1)", font_size=18, color=YELLOW)
        ).arrange(RIGHT, buff=0.1)

        info_panel = VGroup(res_text, time_text, space_text).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        info_panel.next_to(l_ptr, DOWN, buff=2.2).align_to(head, LEFT)

        with self.voiceover(text="算法成功返回 OK 状态。") as tracker:
            self.play(Write(info_panel[0]), run_time=tracker.duration)

        self.play(*get_track_anims(None), run_time=0.5)

        # ===== PHASE E — COMPLEXITY =====
        with self.voiceover(
                text="为了确定删除位置，算法需要从前向后扫描查找第i个数据结点，因此时间复杂度为 O(n)。",
                subcaption="为了确定删除位置，算法需要从前向后扫描查找第 i 个结点，因此时间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(info_panel[1]), run_time=tracker.duration)

        with self.voiceover(
                text="删除操作仅释放了指定结点的物理内存，空间复杂度为 O(1)。",
                subcaption="删除操作仅释放了指定结点的物理内存，空间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(info_panel[2]), run_time=tracker.duration)

        with self.voiceover(text="以上就是双向链表删除算法的完整演示。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)