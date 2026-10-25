# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
class DuLinkListInsertVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角 Logo
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("双向链表的插入", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(
                text="本节我们来学习双向链表的插入算法。该算法是在双向链表中第i个位置之前插入元素e。双向链表的结点不仅包含指向后继的指针，还包含指向前驱的指针。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== NEW PHASE — LIFE EXAMPLE (双向车厢的加挂) =====
        # =========================================================================
        example_title = Text("生活实例：双向锁扣车厢的加挂", font_size=32, font="Microsoft YaHei", color=YELLOW).to_edge(
            UP, buff=1.4)

        # 建立复刻后插法的高级精美车厢渲染函数
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

        def create_double_coupler(start_pt, end_pt, color=WHITE):
            arrow1 = Arrow(start=start_pt + UP * 0.08, end=end_pt + UP * 0.08, buff=0, color=color, tip_length=0.15)
            arrow2 = Arrow(start=end_pt + DOWN * 0.08, end=start_pt + DOWN * 0.08, buff=0, color=color, tip_length=0.15)
            return VGroup(arrow1, arrow2)

        # 初始化已有车厢 A 和 B
        carA_g = create_beautified_train_car(BLUE, "车厢 A").move_to(LEFT * 4.6 + DOWN * 0.6)
        carB_g = create_beautified_train_car(BLUE, "车厢 B").move_to(LEFT * 2.0 + DOWN * 0.6)
        init_coupler = create_double_coupler(carA_g.body.get_right(), carB_g.body.get_left())

        with self.voiceover(
                text="我们可以把双向链表想象成一列由双向锁扣连结的火车，车厢之间既有向前拉的钩子，也有向后拉的钩子。") as tracker:
            self.play(FadeIn(example_title), FadeIn(carA_g), FadeIn(carB_g), Create(init_coupler), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(text="要在中间加挂新车厢 S 时，车厢 B 首先向后平移让出位置。") as tracker:
            self.play(
                carB_g.animate.shift(RIGHT * 2.6),
                FadeOut(init_coupler),
                run_time=0.8
            )

        with self.voiceover(text="随后，新车厢 S 从上方稳稳地降落到这个空档当中。") as tracker:
            carS_g = create_beautified_train_car(GREEN, "车厢 S").move_to(LEFT * 2.0 + UP * 1.5)
            self.play(carS_g.animate.shift(DOWN * 2.1), run_time=0.6)

        with self.voiceover(
                text="最后，我们将双向锁扣分别在 A 与 S、S 与 B 之间扣紧，从而安全地完成了车厢加挂。") as tracker:
            coupler_AS = create_double_coupler(carA_g.body.get_right(), carS_g.body.get_left(), color=GREEN)
            coupler_SB = create_double_coupler(carS_g.body.get_right(), carB_g.body.get_left(), color=GREEN)
            self.play(Create(coupler_AS), Create(coupler_SB), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        # 清空生活实例资产
        self.play(FadeOut(example_title), FadeOut(carA_g), FadeOut(carB_g), FadeOut(carS_g), FadeOut(coupler_AS),
                  FadeOut(coupler_SB), run_time=0.5)

        # =========================================================================
        # ===== PHASE B — CODE BLOCK CONFIG =====
        # =========================================================================
        c_lines = [
            "Status ListInsert_DuL(DuLinkList &L, int i, ElemType e) {",
            "    DuLNode *p = GetElemP_DuL(L, i);",
            "     if(!(p=GetElem_DuL(L,i)))",
            "        return ERROR;",
            "    DuLNode *s = new DuLNode;",
            "    s->data = e;",
            "    if (i == L.length + 1 && L.length > 0) {",
            "        p = L;",
            "        while (p->next) p = p->next;",
            "        s->prior = p;",
            "        s->next = NULL;",
            "        p->next = s;",
            "        return OK;",
            "    }",
            "    if (i == 1 && !p) {",
            "        s->prior = L;",
            "        s->next = L->next;",
            "        if (L->next)",
            "            L->next->prior = s;",
            "        L->next = s;",
            "        return OK;",
            "    }",
            "    s->prior = p->prior;",
            "    p->prior->next = s;",
            "    s->next = p;",
            "    p->prior = s;",
            "    return OK;",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=11, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        SPACE_WIDTH = 0.09
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 6.15:
            code_group.scale_to_fit_width(6.15)
        if code_group.height > 5.65:
            code_group.scale_to_fit_height(5.65)

        bg_width = code_group.get_width() + 0.65
        bg_height = code_group.get_height() + 0.5
        code_bg = RoundedRectangle(corner_radius=0.15, height=bg_height, width=bg_width, color=GRAY, fill_opacity=0.1,
                                   stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.3)
        code_bg.match_y(code_group)

        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.1).to_edge(RIGHT, buff=0.2)

        self.current_lines = []

        def get_track_anims(new_idx):
            if isinstance(new_idx, int):
                new_idx = [new_idx]
            elif new_idx is None:
                new_idx = []
                
            if set(new_idx) == set(self.current_lines): return [Wait(0.001)]
            anims = []
            for idx in self.current_lines:
                if idx not in new_idx:
                    anims.append(self.c_texts[idx].animate.set_color(WHITE).scale(1 / 1.08, about_edge=LEFT))
            
            first_idx = None
            for idx in new_idx:
                if idx not in self.current_lines:
                    anims.append(self.c_texts[idx].animate.set_color(YELLOW).scale(1.08, about_edge=LEFT))
                if first_idx is None or idx < first_idx:
                    first_idx = idx

            if first_idx is not None:
                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.12).rotate(-PI / 2)
                    self.code_pointer.next_to(self.c_texts[first_idx], LEFT, buff=0.15)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.c_texts[first_idx], LEFT, buff=0.15)
                    anims.append(MoveToTarget(self.code_pointer))
            else:
                if hasattr(self, 'code_pointer'):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, 'code_pointer')
                    
            self.current_lines = new_idx
            return anims

        with self.voiceover(text="右侧是双向链表插入算法的核心代码。我们来看看算法的执行过程。") as tracker:
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

        def set_null(node, field="next", is_null=True):
            if field == "next":
                node.next_dot.set_opacity(0 if is_null else 1)
                node.next_null.set_opacity(1 if is_null else 0)
            else:
                node.prior_dot.set_opacity(0 if is_null else 1)
                node.prior_null.set_opacity(1 if is_null else 0)

        def get_ptr(label, target_mobj, color=GREEN, direction=UP):
            if np.array_equal(direction, UP):
                arrow = Arrow(start=target_mobj.get_top() + UP * 0.7, end=target_mobj.get_top(), buff=0.05, color=color)
                txt = Text(label, font_size=18, font="Arial", color=color).next_to(arrow, UP, buff=0.05)
            else:
                arrow = Arrow(start=target_mobj.get_bottom() + DOWN * 0.7, end=target_mobj.get_bottom(), buff=0.05,
                              color=color)
                txt = Text(label, font_size=18, font="Arial", color=color).next_to(arrow, DOWN, buff=0.05)
            return VGroup(arrow, txt)

        # 初始化链表
        head = build_node("L", is_head=True).move_to(LEFT * 5.8 + UP * 0.5)
        set_null(head, "prior", True)

        n1 = build_node("10").move_to(LEFT * 3.8 + UP * 0.5)
        n2 = build_node("20").move_to(LEFT * 1.8 + UP * 0.5)
        set_null(n2, "next", True)

        a_h_fwd = Arrow(start=[-5.225, 0.65, 0], end=[-4.55, 0.65, 0], buff=0, color=WHITE)
        a_1_bwd = Arrow(start=[-4.375, 0.35, 0], end=[-5.05, 0.35, 0], buff=0, color=WHITE)

        a_1_fwd = Arrow(start=[-3.225, 0.65, 0], end=[-2.55, 0.65, 0], buff=0, color=WHITE)
        a_2_bwd = Arrow(start=[-2.375, 0.35, 0], end=[-3.05, 0.35, 0], buff=0, color=WHITE)

        l_ptr = get_ptr("L", head, ORANGE, direction=UP)

        with self.voiceover(text="假设当前已经建立了一个带表头结点的双向链表，包含数据元素 10 和 20。") as tracker:
            self.play(
                FadeIn(head, n1, n2),
                GrowArrow(a_h_fwd), GrowArrow(a_1_bwd), GrowArrow(a_1_fwd), GrowArrow(a_2_bwd),
                FadeIn(l_ptr),
                run_time=tracker.duration
            )

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW =====
        # =========================================================================

        # 第一步：查找插入位置
        with self.voiceover(
                text="首先，调用定位函数找到第 2 个位置，此时指针 p 指向数据结点 20。") as tracker:
            self.play(*get_track_anims(1), run_time=0.4)
            p_ptr = get_ptr("p", n2, GREEN, direction=DOWN)
            self.play(FadeIn(p_ptr), run_time=max(0.2, tracker.duration - 0.4))

        # 第二步：合法性检查
        with self.voiceover(
                text="判断插入位置是否合法，此时 p 不为空，继续执行。") as tracker:
            self.play(*get_track_anims([2, 3]), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 0.4))

        # 第三步：生成新节点
        with self.voiceover(
                text="申请新结点 s，把元素 30 写入数据域。") as tracker:
            self.play(*get_track_anims([4, 5]), run_time=0.4)

            # 构造拉伸后的目标长指针位置
            new_a_1_fwd = Arrow(start=[-3.225, 0.65, 0], end=[-0.55, 0.65, 0], buff=0, color=WHITE)
            new_a_2_bwd = Arrow(start=[-0.375, 0.35, 0], end=[-3.05, 0.35, 0], buff=0, color=WHITE)

            self.play(
                VGroup(n2, p_ptr).animate.shift(RIGHT * 2.0),
                Transform(a_1_fwd, new_a_1_fwd),
                Transform(a_2_bwd, new_a_2_bwd),
                run_time=0.6
            )

            # 新节点 s 在主链下方的空档中诞生 (Y轴设为 -1.5)
            s_node = build_node("30").set_color(GREEN).move_to(LEFT * 1.8 + DOWN * 1.5)
            s_ptr = get_ptr("s", s_node, YELLOW, direction=DOWN)
            self.play(FadeIn(s_node), FadeIn(s_ptr), run_time=max(0.2, tracker.duration - 1.0))

        # 第四步：空链表检查
        with self.voiceover(
                text="判断是否为空链表的插入。这里不是空链表，跳过此分支。") as tracker:
            self.play(*get_track_anims(14), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 0.4))

        # 第五步：s->prior = p->prior;（修改点：改为清晰的斜向上指针）
        with self.voiceover(
                text="接下来，将新结点 s 的前驱指针域指向 p 的前驱，也就是结点 10。") as tracker:
            self.play(*get_track_anims(22), run_time=0.4)
            # 从下方 s 的 prior 域，斜向上指向 10 的下轨右边缘
            s_to_n1 = Arrow(start=[-2.375, -1.2, 0], end=[-3.05, 0.35, 0], buff=0, color=YELLOW)
            self.play(GrowArrow(s_to_n1), run_time=max(0.2, tracker.duration - 0.4))

        # 第六步：p->prior->next = s;（修改点：改为清晰的斜向下指针）
        with self.voiceover(text="修改前驱结点 10 的后继指针域，使其指向新结点 s。") as tracker:
            self.play(*get_track_anims(23), run_time=0.4)
            # 从 10 的 upper rail 上轨，斜向下指向 s 的左侧上边缘
            n1_to_s = Arrow(start=[-3.225, 0.65, 0], end=[-2.55, -1.2, 0], buff=0, color=YELLOW)
            self.play(GrowArrow(n1_to_s), FadeOut(a_1_fwd), run_time=max(0.2, tracker.duration - 0.4))

        # 第七步：s->next = p;（修改点：改为清晰的斜向上指针）
        with self.voiceover(text="将新结点 s 的后继指针域指向当前位置的结点 p。") as tracker:
            self.play(*get_track_anims(24), run_time=0.4)
            # 从下方 s 的 next 域，斜向上指向 20 的 upper rail 上轨左边缘
            s_to_n2 = Arrow(start=[-1.225, -1.2, 0], end=[-0.55, 0.65, 0], buff=0, color=YELLOW)
            self.play(GrowArrow(s_to_n2), run_time=max(0.2, tracker.duration - 0.4))

        # 第八步：p->prior = s;（修改点：改为清晰的斜向下指针）
        with self.voiceover(
                text="最后修改结点 p 的前驱指针域，反向水平连结新结点 s。至此双向链表链接完毕。") as tracker:
            self.play(*get_track_anims(25), run_time=0.4)
            # 从 20 的 lower rail 下轨 prior 域，斜向下指向 s 的右侧上边缘
            n2_to_s = Arrow(start=[-0.375, 0.35, 0], end=[-1.05, -1.2, 0], buff=0, color=YELLOW)
            self.play(GrowArrow(n2_to_s), FadeOut(a_2_bwd), run_time=max(0.2, tracker.duration - 0.4))

        # 第九步：平移归位与变绿（修改点：让 s 结点垂直向上平移归位，同时将 4 条斜向连线平滑 Transform 转换回标准水平线）
        with self.voiceover(text="插入核心工作圆满结束。") as tracker:
            # 构造回归到水平线上（y=0.5）后的 4 条原生水平绿色指针标准坐标
            final_s_to_n1 = Arrow(start=[-2.375, 0.35, 0], end=[-3.05, 0.35, 0], buff=0, color=GREEN)
            final_n1_to_s = Arrow(start=[-3.225, 0.65, 0], end=[-2.55, 0.65, 0], buff=0, color=GREEN)
            final_s_to_n2 = Arrow(start=[-1.225, 0.65, 0], end=[-0.55, 0.65, 0], buff=0, color=GREEN)
            final_n2_to_s = Arrow(start=[-0.375, 0.35, 0], end=[-1.05, 0.35, 0], buff=0, color=GREEN)

            self.play(
                s_node.animate.shift(UP * 2.0),
                s_ptr.animate.shift(UP * 2.0),
                Transform(s_to_n1, final_s_to_n1),
                Transform(n1_to_s, final_n1_to_s),
                Transform(s_to_n2, final_s_to_n2),
                Transform(n2_to_s, final_n2_to_s),
                run_time=max(0.6, tracker.duration)
            )

        # =========================================================================
        # ===== NEW PHASE — COMPACT PANEL CONFIG =====
        # =========================================================================
        res_text = VGroup(
            Text("结果：", font_size=20, font="Microsoft YaHei", color=GREEN),
            Text("插入成功，返回 OK", font_size=18, font="Microsoft YaHei", color=GREEN)
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
            self.play(*get_track_anims(26), Write(info_panel[0]), run_time=tracker.duration)

        self.play(*get_track_anims(None), FadeOut(s_ptr), run_time=0.5)

        # ===== BRANCH EXPLANATION =====
        with self.voiceover(
                text="刚才的例子中，定位函数找到了第 2 个结点，所以 p 不为空，程序继续执行插入操作。") as tracker:
            self.play(*get_track_anims([1, 2, 3]), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 0.4))

        with self.voiceover(
                text="如果定位函数没有找到第 i 个结点，p 就是 NULL。这时还要判断 i 是否是首位，或者是否是表长加 1。") as tracker:
            self.play(*get_track_anims([2, 3, 6, 14]), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 0.4))

        with self.voiceover(
                text="如果 p 为空，并且 i 既不是 1，也不是表长加 1，就说明插入位置非法，程序返回 ERROR。") as tracker:
            self.play(*get_track_anims([2, 3]), run_time=0.4)
            self.play(self.c_texts[3].animate.set_color(RED), run_time=max(0.2, tracker.duration - 0.4))

        with self.voiceover(
                text="但要特别注意，i 等于表长加 1 时，虽然 p 也是 NULL，却表示在表尾之后插入，这是合法操作。程序会先让 p 找到尾结点，再把新结点接到尾部。") as tracker:
            self.play(*get_track_anims([6, 7, 8, 9, 10, 11, 12, 13]), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.5))

        with self.voiceover(
                text="只有 i 等于 1 且链表为空时，才执行头部插入分支。这样，三种情况就都处理完整了。") as tracker:
            self.play(*get_track_anims([14, 15, 16, 17, 18, 19, 20]), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.5))

        self.play(*get_track_anims(None), run_time=0.4)

        # ===== PHASE E — COMPLEXITY =====
        with self.voiceover(
                text="在查找插入位置时，算法需要从头结点开始沿后继指针向后扫描，因此时间复杂度为 O(n)。",
                subcaption="在查找插入位置时，算法需要从头结点开始沿后继指针向后扫描，因此时间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(info_panel[1]), run_time=tracker.duration)

        with self.voiceover(
                text="插入操作只涉及常数次辅助指针的修改，因此空间复杂度为 O(1)。",
                subcaption="插入操作只涉及常数次辅助指针的修改，因此空间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(info_panel[2]), run_time=tracker.duration)

        with self.voiceover(text="以上就是双向链表插入算法的完整演示过程。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)
