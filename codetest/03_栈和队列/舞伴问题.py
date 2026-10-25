# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class DancePartnerVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角 Logo
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("舞伴问题", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP,
                                                                                                              buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(text="本节我们将用队列来解决经典的舞伴分配问题。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== PHASE B — CODE BLOCK CONFIG =====
        # =========================================================================
        c_lines = [
            "void DancePartner(Person dancer[],int num)",
            "{//结构数组dancer中存放跳舞的男女姓名，\n//num是跳舞的人数。",
            "    InitQueue(Mdancers);    //男士队列初始化",
            "    InitQueue(Fdancers);    //女士队列初始化",
            "    for(i=0;i<num;i++)\n        //依次将跳舞者根据其性别入队",
            "    {",
            "        p=dancer[i];",
            "        if(p.sex=='F') EnQueue(Fdancers,p);\n            //插入女队",
            "        else EnQueue(Mdancers,p);   //插入男队",
            "    }",
            "    cout<<\"The dancing partners are:\\n\";",
            "    while(!QueueEmpty(Fdancers)\n          &&!QueueEmpty(Mdancers))",
            "    {//依次输出男女舞伴的姓名",
            "        DeQueue(Fdancers,p);\n            //女士出队",
            "        cout<<p.name<<\" \";\n            //输出出队女士姓名",
            "        DeQueue(Mdancers,p);\n            //男士出队",
            "        cout<<p.name<<endl;\n            //输出出队男士姓名",
            "    }",
            "    if(!QueueEmpty(Fdancers))\n        //女士队列非空，输出队头女士的姓名",
            "    {",
            "        p=GetHead(Fdancers);\n            //取女士队头",
            "        cout<<\"The first woman to get a partner is: \"\n            <<p.name<<endl;",
            "    }",
            "    else if(!QueueEmpty(Mdancers))\n        //男士队列非空，输出队头男士的姓名",
            "    {",
            "        p=GetHead(Mdancers);\n            //取男士队头",
            "        cout<<\"The first man to get a partner is: \"\n            <<p.name<<endl;",
            "    }",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=8.2, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.07)
        SPACE_WIDTH = 0.055
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 6.35:
            code_group.scale_to_fit_width(6.35)
        if code_group.height > 5.8:
            code_group.scale_to_fit_height(5.8)
        bg_width = code_group.get_width() + 0.7
        bg_height = code_group.get_height() + 0.5
        code_bg = RoundedRectangle(corner_radius=0.2, height=bg_height, width=bg_width, color=GRAY, fill_opacity=0.1,
                                   stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.3)
        code_bg.match_y(code_group)

        code_block = VGroup(code_bg, code_group).to_edge(RIGHT, buff=0.25).shift(DOWN * 0.15)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line: return [Wait(0.001)]
            anims = []
            if self.current_line is not None:
                anims.append(self.c_texts[self.current_line].animate.set_color(WHITE).scale(1 / 1.08, about_edge=LEFT))
            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW).scale(1.08, about_edge=LEFT))
                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.12).rotate(-PI / 2)
                    self.code_pointer.next_to(self.c_texts[new_idx], LEFT, buff=0.15)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.c_texts[new_idx], LEFT, buff=0.15)
                    anims.append(MoveToTarget(self.code_pointer))
                self.current_line = new_idx
            else:
                if hasattr(self, 'code_pointer'):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, 'code_pointer')
                self.current_line = None
            if not anims: return [FadeIn(VGroup(), run_time=1e-5)]
            return anims

        self.play(FadeIn(code_block), run_time=1.0)

        # =========================================================================
        # ===== PHASE C — VISUALIZATION SETUP =====
        # =========================================================================
        def build_circular_queue_boxes(max_size=4):
            box_side = 0.6
            boxes = VGroup(*[Square(side_length=box_side, color=BLUE) for _ in range(max_size)]).arrange(RIGHT, buff=0)
            indices = VGroup()
            for i, box in enumerate(boxes):
                idx_txt = Text(str(i), font_size=16, color=GRAY).next_to(box, DOWN, buff=0.15)
                indices.add(idx_txt)
            return VGroup(boxes, indices)

        def get_ptr(label, target_mobj, color=GREEN, direction=UP):
            if np.array_equal(direction, UP):
                arrow = Arrow(start=target_mobj.get_top() + UP * 0.3, end=target_mobj.get_top(), buff=0.05, color=color)
                txt = Text(label, font_size=14, font="Arial", color=color).next_to(arrow, UP, buff=0.05)
            elif np.array_equal(direction, DOWN):
                arrow = Arrow(start=target_mobj.get_bottom() + DOWN * 0.3, end=target_mobj.get_bottom(), buff=0.05,
                              color=color)
                txt = Text(label, font_size=14, font="Arial", color=color).next_to(arrow, DOWN, buff=0.05)
            return VGroup(arrow, txt)

        # 拉开两队的垂直间距，避免男队指针遮挡女队下方的索引。
        f_queue = build_circular_queue_boxes(4).move_to(LEFT * 3.8 + UP * 1.9)
        f_label = Text("女队", font_size=20, font="Microsoft YaHei", color=PINK).next_to(f_queue, LEFT, buff=0.4)

        m_queue = build_circular_queue_boxes(4).move_to(LEFT * 3.8 + DOWN * 0.35)
        m_label = Text("男队", font_size=20, font="Microsoft YaHei", color=BLUE_C).next_to(m_queue, LEFT, buff=0.4)

        wait_label = Text("待分配", font_size=18, font="Microsoft YaHei", color=GRAY).to_edge(LEFT, buff=0.4).shift(
            UP * 1.7)
        dancer_names = [("F1", 'F'), ("M1", 'M'), ("M2", 'M'), ("F2", 'F'), ("F3", 'F')]
        dancers = VGroup(
            *[Text(name, font_size=20, color=PINK if sex == 'F' else BLUE_C) for name, sex in dancer_names]).arrange(
            DOWN, buff=0.25).next_to(wait_label, DOWN, buff=0.3)

        pool_label = Text("舞池配对结果：", font_size=18, font="Microsoft YaHei", color=YELLOW).move_to(
            LEFT * 3.8 + DOWN * 1.1).align_to(f_label, LEFT)

        self.play(FadeIn(f_queue), FadeIn(f_label), FadeIn(m_queue), FadeIn(m_label), FadeIn(wait_label),
                  FadeIn(dancers), FadeIn(pool_label), run_time=1.0)

        f_front_idx, f_rear_idx = 0, 0
        m_front_idx, m_rear_idx = 0, 0

        f_front_ptr = get_ptr("front", f_queue[0][0], GREEN, direction=DOWN)
        f_rear_ptr = get_ptr("rear", f_queue[0][0], ORANGE, direction=UP)
        m_front_ptr = get_ptr("front", m_queue[0][0], GREEN, direction=DOWN)
        m_rear_ptr = get_ptr("rear", m_queue[0][0], ORANGE, direction=UP)

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW =====
        # =========================================================================

        # --- 阶段一：初始化与分流入队 ---
        with self.voiceover(text="首先，算法对男队和女队循环队列进行初始化。") as tracker:
            self.play(*get_track_anims(2), run_time=0.4)
            self.play(FadeIn(f_front_ptr), FadeIn(f_rear_ptr), FadeIn(m_front_ptr), FadeIn(m_rear_ptr),
                      run_time=max(0.2, tracker.duration - 0.4))

        with self.voiceover(text="然后遍历所有入场的舞者，根据性别将他们分别排入各自的队伍。") as tracker:
            self.play(*get_track_anims(4), run_time=tracker.duration)

        f_elements = []
        m_elements = []
        for i, (name, sex) in enumerate(dancer_names):
            d_obj = dancers[i]
            if sex == 'F':
                self.play(*get_track_anims(7), run_time=0.4)
                target_pos = f_queue[0][f_rear_idx].get_center()
                self.play(d_obj.animate.move_to(target_pos), run_time=0.6)
                f_elements.append(d_obj)

                f_rear_idx = (f_rear_idx + 1) % 4
                new_f_rear_ptr = get_ptr("rear", f_queue[0][f_rear_idx], ORANGE, direction=UP)
                self.play(Transform(f_rear_ptr, new_f_rear_ptr), run_time=0.4)
            else:
                self.play(*get_track_anims(8), run_time=0.4)
                target_pos = m_queue[0][m_rear_idx].get_center()
                self.play(d_obj.animate.move_to(target_pos), run_time=0.6)
                m_elements.append(d_obj)

                m_rear_idx = (m_rear_idx + 1) % 4
                new_m_rear_ptr = get_ptr("rear", m_queue[0][m_rear_idx], ORANGE, direction=UP)
                self.play(Transform(m_rear_ptr, new_m_rear_ptr), run_time=0.4)

        # --- 阶段二：配对出队 ---
        self.play(FadeOut(wait_label), run_time=0.5)

        with self.voiceover(text="当两队都不为空时，依次从女队和男队的队头各出一人，配成舞伴。") as tracker:
            self.play(*get_track_anims(11), run_time=max(0.5, tracker.duration))

        # 弹出两对
        pool_pairs = VGroup()
        for round_idx in range(2):
            self.play(*get_track_anims(13), run_time=0.25)
            f_p = f_elements[round_idx]
            m_p = m_elements[round_idx]
            f_copy = f_p.copy()
            m_copy = m_p.copy()

            # 指针后移
            f_front_idx = (f_front_idx + 1) % 4
            new_f_front_ptr = get_ptr("front", f_queue[0][f_front_idx], GREEN, direction=DOWN)
            m_front_idx = (m_front_idx + 1) % 4
            new_m_front_ptr = get_ptr("front", m_queue[0][m_front_idx], GREEN, direction=DOWN)

            self.play(Transform(f_front_ptr, new_f_front_ptr), Transform(m_front_ptr, new_m_front_ptr), run_time=0.5)

            # 输出女士姓名，然后再处理男士出队和输出。
            self.play(*get_track_anims(14), run_time=0.2)
            self.play(*get_track_anims(15), run_time=0.2)
            self.play(*get_track_anims(16), run_time=0.2)

            # 输出面板显示配对
            pair_text = Text(f"{dancer_names[round_idx * 2][0]} 💃 - 🕺 {dancer_names[round_idx * 2 + 1][0]}",
                             font_size=18, font="Microsoft YaHei").next_to(pool_label, RIGHT, buff=0.4).shift(
                DOWN * round_idx * 0.35)

            self.play(
                f_copy.animate.move_to(pair_text.get_left() + LEFT * 0.4),
                m_copy.animate.move_to(pair_text.get_right() + RIGHT * 0.4),
                run_time=0.6
            )
            self.play(FadeIn(pair_text), FadeOut(f_copy), FadeOut(m_copy), FadeOut(f_p), FadeOut(m_p), run_time=0.5)
            pool_pairs.add(pair_text)

        # 第三次判断，跳出
        with self.voiceover(text="再次判断时，男队由于没有成员，导致两队都不为空的条件不再满足，跳出循环。") as tracker:
            self.play(*get_track_anims(11), run_time=0.5)
            self.play(m_front_ptr.animate.scale(1.2), m_rear_ptr.animate.scale(1.2), run_time=0.3)
            self.play(m_front_ptr.animate.scale(1 / 1.2), m_rear_ptr.animate.scale(1 / 1.2), run_time=0.3)
            self.wait(max(0.1, tracker.duration - 1.1))

        # --- 阶段三：下一曲提示 ---
        with self.voiceover(
                text="配对结束后，如果某队仍有未配对的人员，我们会取出队头人员的姓名，提示其成为下一首舞曲首位获得舞伴的人。") as tracker:
            self.play(*get_track_anims(18), run_time=0.5)
            self.play(*get_track_anims(20), run_time=max(0.5, tracker.duration - 0.5))

        # 取女队队头 F3
        f_p_head = f_elements[2]
        ghost_f3 = f_p_head.copy()
        rem_text = Text("下一轮首位候补：F3", font_size=18, font="Microsoft YaHei", color=PINK).next_to(pool_pairs, DOWN,
                                                                                                       buff=0.4).align_to(
            pool_label, LEFT)
        self.play(ghost_f3.animate.move_to(rem_text.get_center()), run_time=0.8)
        self.play(FadeIn(rem_text), FadeOut(ghost_f3), run_time=0.5)

        self.play(*get_track_anims(None), run_time=0.5)

        # =========================================================================
        # ===== PHASE E — COMPLEXITY =====
        # =========================================================================
        # 【调整 2：时空复杂度水平排布，精准挂靠在下一轮候补结果的下方】
        time_box = VGroup(Text("时间复杂度：", font_size=18, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(n)", font_size=18, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=18, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(n)", font_size=18, color=YELLOW)).arrange(RIGHT, buff=0.1)

        complexity_group = VGroup(time_box, space_box).arrange(RIGHT, buff=0.6).next_to(rem_text, DOWN,
                                                                                        buff=0.4).align_to(pool_label,
                                                                                                           LEFT)

        with self.voiceover(
                text="由于需要遍历所有舞者进行入队和出队操作，总消耗时间与人数成正比，因此时间复杂度为 O(n)。",
                subcaption="由于需要遍历所有舞者进行入队和出队操作，总消耗时间与人数成正比，因此时间复杂度为 O(n)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
                text="另外，算法借用了两个队列分别存储男性和女性舞者，占用的内存同样与总人数成正比，空间复杂度也是 O(n)。",
                subcaption="另外，算法借用了两个队列分别存储男性和女性舞者，占用的内存同样与总人数成正比，空间复杂度也是 O(n)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="这就是舞伴问题的算法动画演示。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)
