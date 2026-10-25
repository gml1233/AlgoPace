# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
class GetNextVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务（与 KMP 算法视频完全一致的中文男声配置）
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("计算next函数值", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(
            text="本节我们学习 KMP 算法中的关键预处理：计算 next 函数值。该算法求模式串 T 的 next 函数值，并将结果存入数组 next。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE B — 例子引入（生活实例类比：印花彩带的自我比对）=====
        with self.voiceover(text="在看代码之前，先弄清楚 next 数组到底在算什么。") as tracker:
            self.wait(tracker.duration)

        def mini_row(s, color, side=0.55, buff=0.1):
            boxes = VGroup()
            for k, c in enumerate(s):
                b = Square(side_length=side, color=color)
                t = Text(c, font_size=24, color=WHITE)
                if k > 0:
                    b.next_to(boxes[-1], RIGHT, buff=buff)
                t.move_to(b.get_center())
                boxes.add(VGroup(b, t))
            return boxes

        PITCH_MINI = 0.55 + 0.1
        demo_top = mini_row("abab", BLUE).move_to(UP * 0.9 + LEFT * 0.6)
        demo_bot = mini_row("abab", BLUE)
        demo_bot.shift(demo_top[0].get_center() - demo_bot[0].get_center()).shift(DOWN * 1.2)

        top_cap = Text("一条印花彩带（模式串）", font_size=22, font="Microsoft YaHei", color=BLUE).next_to(demo_top, LEFT, buff=0.4)
        bot_cap = Text("复制一份，向右错位", font_size=22, font="Microsoft YaHei", color=BLUE).next_to(demo_bot, LEFT, buff=0.4)

        with self.voiceover(
            text="next 数组刻画的是模式串自身的重复规律。打个比方：把一条印花彩带复制一份，让它向右错开，再叠到自己身上。"
        ) as tracker:
            self.play(FadeIn(demo_top), FadeIn(top_cap), run_time=tracker.duration * 0.5)
            self.play(FadeIn(demo_bot), FadeIn(bot_cap), run_time=tracker.duration * 0.5)

        overlap_label = Text("重合的花纹长度 = 2", font_size=24, font="Microsoft YaHei", color=GREEN).to_edge(DOWN, buff=1.8)
        with self.voiceover(
            text="当上下两条彩带的花纹重新对齐时，能对齐的最长长度，就是这个模式串 开头的一段在后面重复出现的长度，也就是最长相同前后缀。",
            subcaption="当上下两条彩带的花纹重新对齐时，能对齐的最长长度，就是这个模式串开头的一段在后面重复出现的长度，也就是最长相同前后缀。"
        ) as tracker:
            self.play(demo_bot.animate.shift(RIGHT * 2 * PITCH_MINI), run_time=tracker.duration * 0.5)
            # 高亮重合区域：上方第 3、4 块 与 下方第 1、2 块
            self.play(demo_top[2][0].animate.set_color(GREEN), demo_top[3][0].animate.set_color(GREEN),
                      demo_bot[0][0].animate.set_color(GREEN), demo_bot[1][0].animate.set_color(GREEN),
                      FadeIn(overlap_label), run_time=tracker.duration * 0.5)

        with self.voiceover(
            text="next 数组就是预先记下模式串每个位置之前的这个长度。下面我们结合代码，一步步把它算出来。"
        ) as tracker:
            self.wait(tracker.duration)

        self.play(FadeOut(demo_top), FadeOut(demo_bot), FadeOut(top_cap), FadeOut(bot_cap),
                  FadeOut(overlap_label), run_time=0.6)

        # ===== PHASE C — CODE BLOCK CONFIG（与 KMP 算法完全相同的代码板样式）=====
        c_lines = [
            "void get_next(SString T, int next[]) {",
            "    int i = 1, j = 0;",
            "    next[1] = 0;",
            "    while (i < T.length) {",
            "        if (j == 0 || T.ch[i] == T.ch[j]) {",
            "            ++i;  ++j;",
            "            next[i] = j;",
            "        } else {",
            "            j = next[j];",
            "        }",
            "    }",
            "}"
        ]
        # 代码行索引常量（便于追踪高亮）
        IDX_DECL = 1     # int i = 1, j = 0;
        IDX_INIT = 2     # next[1] = 0;
        IDX_WHILE = 3    # while (i < T.length)
        IDX_IF = 4       # if (j == 0 || T.ch[i] == T.ch[j])
        IDX_INC = 5      # ++i; ++j;
        IDX_SETNEXT = 6  # next[i] = j;
        IDX_RETREAT = 8  # j = next[j];

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            # 代码字号 9.5，与 KMP 算法保持一致
            t = Text(stripped_line, font_size=9.5, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        SPACE_WIDTH = 0.08
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        bg_width = code_group.get_width() * 1.2 + 0.8
        bg_height = code_group.get_height() + 0.6
        code_bg = RoundedRectangle(corner_radius=0.2, height=bg_height, width=bg_width, color=GRAY, fill_opacity=0.1,
                                   stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.4)
        code_bg.match_y(code_group)

        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.2).to_edge(RIGHT, buff=0.3)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line:
                return []
            anims = []
            if self.current_line is not None:
                anims.append(self.c_texts[self.current_line].animate.set_color(WHITE).scale(1 / 1.2, about_edge=LEFT))
            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW).scale(1.2, about_edge=LEFT))
                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.13).rotate(-PI / 2)
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
            return anims

        with self.voiceover(
            text="右侧是计算 next 函数值的代码。它使用两个指针：指针i沿着模式串 向后扫描，指针j记录当前匹配上的最长 前后缀长度。",
            subcaption="右侧是计算next函数值的代码。它使用两个指针：指针i沿着模式串向后扫描，指针j记录当前匹配上的最长前后缀长度。"
        ) as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # ===== PHASE C2 — VISUALIZATION SETUP（串与表的样式与 KMP 算法完全一致）=====
        BOX = 0.6
        BUF = 0.1
        PITCH = BOX + BUF

        T_str = "abaabcac"

        # 模式串 T 的单行可视化：i 指针在上方，j 指针在下方
        T_boxes = VGroup()
        T_texts = VGroup()
        T_idxs = VGroup()
        for k, ch in enumerate(T_str):
            box = Square(side_length=BOX, color=ORANGE)
            if k > 0:
                box.next_to(T_boxes[-1], RIGHT, buff=BUF)
            txt = Text(ch, font_size=26, color=WHITE).move_to(box.get_center())
            idx = Text(str(k + 1), font_size=16, color=GRAY).next_to(box, UP, buff=0.08)
            T_boxes.add(box)
            T_texts.add(txt)
            T_idxs.add(idx)
        T_body = VGroup(T_boxes, T_texts, T_idxs)
        T_body.move_to(LEFT * 2.3 + UP * 1.5)

        # j 的“0 号位”：表示空前缀，位于第 1 个方格左侧一格
        slot0_box = Square(side_length=BOX, color=GRAY, stroke_opacity=0.5).move_to(T_boxes[0].get_center() + LEFT * PITCH)
        slot0_lbl = Text("0", font_size=16, color=GRAY).next_to(slot0_box, UP, buff=0.08)
        slot0 = VGroup(slot0_box, slot0_lbl)

        # 标签 T 放在 0 号位左侧，避免与 0 号位方格重叠
        T_label = Text("T", font_size=28, color=ORANGE, weight=BOLD).next_to(slot0_box, LEFT, buff=0.4)
        T_full = VGroup(T_label, T_body)

        # 指针 i 放在 T 上方（自上往下指）
        ptr_i = Arrow(start=T_boxes[0].get_top() + UP * 0.45, end=T_boxes[0].get_top(), buff=0.06, color=YELLOW,
                      max_tip_length_to_length_ratio=0.45)
        label_i = Text("i", font_size=22, color=YELLOW).next_to(ptr_i, UP, buff=0.05)
        group_i = VGroup(ptr_i, label_i)

        # 指针 j 放在 T 下方（自下往上指），初始指向 0 号位
        ptr_j = Arrow(start=slot0_box.get_bottom() + DOWN * 0.5, end=slot0_box.get_bottom(), buff=0.06, color=GREEN,
                      max_tip_length_to_length_ratio=0.45)
        label_j = Text("j", font_size=22, color=GREEN).next_to(ptr_j, DOWN, buff=0.05)
        group_j = VGroup(ptr_j, label_j)

        # ----- next 数组表格（样式与 KMP 算法完全一致；next 行初始为空，随算法填入）-----
        def make_cell(content, w, h, fs, txt_color=WHITE, box_color=GRAY_B):
            rect = Rectangle(width=w, height=h, color=box_color, stroke_width=1.5)
            t = Text(str(content), font_size=fs, color=txt_color, font="Microsoft YaHei")
            t.move_to(rect.get_center())
            return VGroup(rect, t)

        HEAD_W, CELL_W, CELL_H = 1.0, 0.55, 0.5
        row_j = VGroup(make_cell("j", HEAD_W, CELL_H, 18, txt_color=YELLOW))
        row_t = VGroup(make_cell("T[ j ]", HEAD_W, CELL_H, 16, txt_color=ORANGE))
        row_n = VGroup(make_cell("next[ j ]", HEAD_W, CELL_H, 14, txt_color=GREEN))
        next_rects = {}
        for k in range(8):
            row_j.add(make_cell(k + 1, CELL_W, CELL_H, 18, txt_color=YELLOW))
            row_t.add(make_cell(T_str[k], CELL_W, CELL_H, 18, txt_color=ORANGE))
            # next 行先放空白格子，数值随算法运行逐个填入
            rect = Rectangle(width=CELL_W, height=CELL_H, color=GRAY_B, stroke_width=1.5)
            row_n.add(rect)
            next_rects[k + 1] = rect
        for r in (row_j, row_t, row_n):
            r.arrange(RIGHT, buff=0)
        next_table = VGroup(row_j, row_t, row_n).arrange(DOWN, buff=0)
        next_table.move_to(LEFT * 2.2 + DOWN * 0.85)

        with self.voiceover(
            text="假设模式串 T 为 a b a a b c a c，长度为 8。",
            subcaption="假设模式串 T 为 abaabcac，长度为 8。"
        ) as tracker:
            self.play(FadeIn(T_full), FadeIn(slot0), run_time=tracker.duration)

        with self.voiceover(
            text="我们的目标，就是填出下面这张表的最后一杭——每个位置的 next 值。",
            subcaption="我们的目标，就是填出下面这张表的最后一行——每个位置的 next 值。"
        ) as tracker:
            self.play(FadeIn(next_table), run_time=tracker.duration)

        # ===== PHASE D — 计算过程的辅助函数 =====
        state = {'i': 1, 'j': 0}

        def box_x(idx):
            # idx>=1 取对应方格中心 x；idx==0 取 0 号位中心 x
            if idx >= 1:
                return T_boxes[idx - 1].get_center()[0]
            return slot0_box.get_center()[0]

        def move_ij(new_i, new_j, rt=0.45):
            dxi = box_x(new_i) - box_x(state['i'])
            dxj = box_x(new_j) - box_x(state['j'])
            self.play(group_i.animate.shift(RIGHT * dxi),
                      group_j.animate.shift(RIGHT * dxj), run_time=rt)
            state['i'] = new_i
            state['j'] = new_j

        def move_j(new_j, rt=0.5):
            dxj = box_x(new_j) - box_x(state['j'])
            self.play(group_j.animate.shift(RIGHT * dxj), run_time=rt)
            state['j'] = new_j

        def color_pair(is_match, rt=0.3):
            c = GREEN if is_match else RED
            self.play(T_boxes[state['i'] - 1].animate.set_color(c),
                      T_boxes[state['j'] - 1].animate.set_color(c), run_time=rt)

        def reset_boxes(rt=0.25):
            self.play(*[b.animate.set_color(ORANGE) for b in T_boxes], run_time=rt)

        def fill_next(pos, val, rt=0.5):
            t = Text(str(val), font_size=18, color=GREEN, font="Microsoft YaHei").move_to(next_rects[pos].get_center())
            self.play(Write(t), Indicate(next_rects[pos], color=GREEN, scale_factor=1.15), run_time=rt)
            self.add(t)

        def step_advance(match_compare):
            # match_compare=True 表示因字符相等而前进；False 表示因 j==0 而前进（不做字符比较）
            self.play(*get_track_anims(IDX_WHILE), run_time=0.25)
            self.play(*get_track_anims(IDX_IF), run_time=0.25)
            if match_compare:
                color_pair(True)
            ni, nj = state['i'] + 1, state['j'] + 1
            self.play(*get_track_anims(IDX_INC), run_time=0.25)
            move_ij(ni, nj)
            self.play(*get_track_anims(IDX_SETNEXT), run_time=0.25)
            fill_next(ni, nj)
            if match_compare:
                reset_boxes()

        def step_retreat(new_j):
            self.play(*get_track_anims(IDX_WHILE), run_time=0.25)
            self.play(*get_track_anims(IDX_IF), run_time=0.25)
            color_pair(False)
            self.play(*get_track_anims(IDX_RETREAT), run_time=0.25)
            self.play(Indicate(next_rects[state['j']], color=RED, scale_factor=1.2), run_time=0.4)
            reset_boxes()
            move_j(new_j)

        # ===== PHASE D2 — 初始化 =====
        with self.voiceover(
            text="首先初始化：指针i指向第 1 个字符，指针j指向第0个字符，这里的0号位代表空前缀。"
        ) as tracker:
            self.play(*get_track_anims(IDX_DECL), run_time=0.4)
            self.play(FadeIn(group_i), FadeIn(group_j), run_time=max(0.3, tracker.duration - 0.4))

        with self.voiceover(
            text="并规定next数组的第1项为 0，因为第一个字符之前没有任何前缀可以利用。"
        ) as tracker:
            self.play(*get_track_anims(IDX_INIT), run_time=0.4)
            fill_next(1, 0)

        # ===== PHASE D3 — 主循环逐步计算 =====
        # 步骤 1：i=1, j=0 —— j==0，执行 ++i ++j，next[2]=1
        with self.voiceover(
            text="进入循环。此时 j 等于 0，满足条件，执行加加i、加加j，得到i为2、j为1，记录 next数组的第 2 项为 1。",
            subcaption="进入循环。此时j==0，满足条件，执行++i、++j，得到i为2、j为1，记录next数组的第2项为1。"
        ) as tracker:
            step_advance(match_compare=False)

        # 步骤 2：i=2, j=1 —— T[2]=b ≠ T[1]=a，j=next[1]=0
        with self.voiceover(
            text="比较T的第2个字符b与第1个字符a，不相等。next数组的第1项为0，j回退到0"
        ) as tracker:
            step_retreat(0)

        # 步骤 3：i=2, j=0 —— j==0，++i ++j，next[3]=1
        with self.voiceover(
            text="j等于 0，再次执行加加i、加加j，得到i为 3、j 为 1，记录next数组的第3项为1。",
            subcaption="j等于0，再次执行++i、++j，得到i为3、j为1，记录next数组的第3项为1"
        ) as tracker:
            step_advance(match_compare=False)

        # 步骤 4：i=3, j=1 —— T[3]=a = T[1]=a，++i ++j，next[4]=2
        with self.voiceover(
            text="模式串的第3个字符和第1个字符都是a，执行i++、j++，指针i增加为4、j增加为2，记录next数组的第4项为2。",
            subcaption="模式串的第3个字符和第1个字符都是a，执行i++、j++，指针i增加为4、j增加为2，记录next数组的第4项为2。"
        ) as tracker:
            step_advance(match_compare=True)

        # 步骤 5：i=4, j=2 —— T[4]=a ≠ T[2]=b，j=next[2]=1
        with self.voiceover(
            text="比较模式串的第4个字符a和第2个字符b，不相等，j回退到next数组的第2项，也就是1。"
        ) as tracker:
            step_retreat(1)

        # 步骤 6：i=4, j=1 —— T[4]=a = T[1]=a，++i ++j，next[5]=2
        with self.voiceover(
            text="再比较T的第4个字符a与第1个字符a，相等，i 为 5、j 为 2，记录next数组的第5项为2。",
        ) as tracker:
            step_advance(match_compare=True)

        # 步骤 7：i=5, j=2 —— T[5]=b = T[2]=b，++i ++j，next[6]=3
        with self.voiceover(
            text="比较T的第5个字符b与第2个字符b，相等，i为 6、j为 3，记录next数组的第6项为3。"
        ) as tracker:
            step_advance(match_compare=True)

        # 步骤 8：i=6, j=3 —— T[6]=c ≠ T[3]=a，j=next[3]=1
        with self.voiceover(
            text="比较T的第6个字符c与第3个字符a，不相等，next数组的第3项为1，j回退到1。"
        ) as tracker:
            step_retreat(1)

        # 步骤 9：i=6, j=1 —— T[6]=c ≠ T[1]=a，j=next[1]=0
        with self.voiceover(
            text="再比较T的第6个字符c与第1个字符a，仍然不相等，next数组的第1项为0，j回退到0。"
        ) as tracker:
            step_retreat(0)

        # 步骤 10：i=6, j=0 —— j==0，++i ++j，next[7]=1
        with self.voiceover(
            text="j等于0，执行加加i、加加j，得到i为7、j为1，记录next数组的第7项为1。",
            subcaption="j==0，执行++i、++j，得到i为7、j为1，记录next数组的第7项为1。"
        ) as tracker:
            step_advance(match_compare=False)

        # 步骤 11：i=7, j=1 —— T[7]=a = T[1]=a，++i ++j，next[8]=2
        with self.voiceover(
            text="最后比较T的第7个字符a与第1个字符a，相等，i为8、j为2，记录next数组的第8项为2。",
            subcaption="最后比较T的第7个字符a与第1个字符a，相等，i为8、j为2，记录next数组的第8项为2。"
        ) as tracker:
            step_advance(match_compare=True)

        # 步骤 12：i=8 —— 不再小于 T.length，循环结束
        with self.voiceover(
            text="i等于8，不再小于模式串的长度 8，循环结束，next 数组计算完毕。",
            subcaption="i=8 不再小于 T.length=8，循环结束，next 数组计算完毕。"
        ) as tracker:
            self.play(*get_track_anims(IDX_WHILE), run_time=0.3)
            self.play(Indicate(self.c_texts[IDX_WHILE], color=RED, scale_factor=1.0), run_time=0.4)

        # ===== PHASE D4 — 结果展示 =====
        self.play(*get_track_anims(None), FadeOut(group_i), FadeOut(group_j), FadeOut(slot0), run_time=0.5)

        with self.voiceover(
            text="得到的 next 数组为：0、1、1、2、2、3、1、2，用于指导KMP匹配过程中失配时的滑动距离",
            subcaption="得到的next数组为：0 1 1 2 2 3 1 2，用于指导KMP匹配过程中失配时的滑动距离。"
        ) as tracker:
            self.play(*[next_rects[k].animate.set_color(GREEN) for k in range(1, 9)], run_time=0.6)
            self.wait(max(0.3, tracker.duration - 0.6))

        # ===== PHASE E — COMPLEXITY =====
        done_label = Text("next 数组计算完成", font_size=24, font="Microsoft YaHei", color=GREEN).move_to(
            LEFT * 4.6 + DOWN * 2.35)
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(m)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(
            done_label, RIGHT, buff=0.6)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(1)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(
            time_box, RIGHT, buff=0.6)

        with self.voiceover(text="至此，计算 next 函数值的过程结束。") as tracker:
            self.play(Write(done_label), run_time=max(0.5, tracker.duration))

        with self.voiceover(
            text="指针 i 从头到尾扫描模式串 一遍，虽然j偶尔回退，但总的移动次数与模式串 长度m成正比，因此时间复杂度为 O m。",
            subcaption="指针i从头到尾扫描模式串一遍，虽然j偶尔回退，但总的移动次数与模式串长度m成正比，因此时间复杂度为O(m)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
            text="算法只额外使用了 i、j 两个辅助变量，next 数组是要返回的结果本身，所以额外空间复杂度为 O 1。",
            subcaption="算法只额外使用了i、j两个辅助变量，next数组是要返回的结果本身，所以额外空间复杂度为O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是计算 next 函数值的完整过程。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)