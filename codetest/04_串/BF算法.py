# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class BFAlgorithmVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        # 优化：标题精简为 "BF算法"
        algo_title = Text("BF算法", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        # “模式”的“模”固定使用第二声同音字“魔”送入 TTS，避免被误读为第四声；
        # 屏幕字幕仍通过 subcaption 保留教材中的规范写法。
        with self.voiceover(
                text="本节学习字符串匹配的最基础算法：BF算法。该算法用于求魔式串T在主串S中第pos个字符之后第一次出现的位置，若不存在则返回0。",
                subcaption="本节学习字符串匹配的最基础算法：BF算法。该算法用于求模式串T在主串S中第pos个字符之后第一次出现的位置，若不存在则返回0。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE B — CODE BLOCK CONFIG =====
        c_lines = [
            "int Index_BF(SString S, SString T, int pos) {",
            "    int i = pos; int j = 1;",
            "    while (i <= S.length && j <= T.length) {",
            "        if (S.ch[i] == T.ch[j]) {",
            "            ++i; ++j;",
            "        } else {",
            "            i = i - j + 2;",
            "            j = 1;",
            "        }",
            "    }",
            "    if (j > T.length)",
            "        return i - T.length;",
            "    else",
            "        return 0;",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            # 优化：代码字号由 11.5 缩小至 9.5
            t = Text(stripped_line, font_size=9.5, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        # 优化：行距由 0.18 紧凑至 0.12
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

        # 优化：布局挂载在 logo 下方，彻底杜绝与标题和 logo 遮挡
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.2).to_edge(RIGHT, buff=0.4)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line: return [Wait(0.001)]
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

        with self.voiceover(text="右侧是 BF 算法的实现代码。接下来我们通过实际演示来了解它的匹配过程。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # ===== PHASE C — VISUALIZATION SETUP =====
        def build_string_array(s_str, label_text, color=BLUE):
            boxes = VGroup()
            texts = VGroup()
            indices = VGroup()
            for idx, ch in enumerate(s_str):
                box = Square(side_length=0.8, color=color)
                txt = Text(ch, font_size=36, color=WHITE)
                idx_txt = Text(str(idx + 1), font_size=20, color=GRAY)

                if idx > 0:
                    # 优化：将 buff 从 0 改为 0.08，防止重合边框导致右侧线框颜色渲染不出
                    box.next_to(boxes[-1], RIGHT, buff=0.08)

                txt.move_to(box.get_center())
                idx_txt.next_to(box, UP if label_text == "S" else DOWN, buff=0.1)

                boxes.add(box)
                texts.add(txt)
                indices.add(idx_txt)

            res = VGroup(boxes, texts, indices)
            label = Text(label_text, font_size=32, color=color, weight=BOLD).next_to(res, LEFT, buff=0.5)
            return VGroup(label, res), boxes, texts

        S_str = "ababc"
        T_str = "abc"

        S_full, S_boxes, S_texts = build_string_array(S_str, "S", color=BLUE)
        S_full.move_to(LEFT * 2.5 + UP * 1.5)

        T_full, T_boxes, T_texts = build_string_array(T_str, "T", color=ORANGE)
        diff_x = S_boxes[0].get_center()[0] - T_boxes[0].get_center()[0]
        T_full.shift(RIGHT * diff_x)
        T_full.match_y(S_full).shift(DOWN * 2.5)

        # 优化：将指针 i 移到 S 的上方（自上往下指），彻底分流，解决重叠遮挡问题
        ptr_i = Arrow(start=S_boxes[0].get_top() + UP * 0.8, end=S_boxes[0].get_top(), buff=0.1, color=YELLOW)
        label_i = Text("i", font_size=24, color=YELLOW).next_to(ptr_i, UP, buff=0.1)
        group_i = VGroup(ptr_i, label_i)

        # 优化：将指针 j 移到 T 的下方（自下往上指）
        ptr_j = Arrow(start=T_boxes[0].get_bottom() + DOWN * 0.8, end=T_boxes[0].get_bottom(), buff=0.1, color=YELLOW)
        label_j = Text("j", font_size=24, color=YELLOW).next_to(ptr_j, DOWN, buff=0.1)
        group_j = VGroup(ptr_j, label_j)

        with self.voiceover(
            text="假设主串 S 为 a b a b c，魔式串 T 为 a b c，初始位置 pos 为 1。",
            subcaption="假设主串 S 为 ababc，模式串 T 为 abc，初始位置 pos 为 1。"
        ) as tracker:
            self.play(FadeIn(S_full), FadeIn(T_full), run_time=tracker.duration)

        with self.voiceover(
            text="首先初始化指针 I 和 J，分别指向主串和魔式串的第一个字符。",
            subcaption="首先初始化指针 i 和 j，分别指向主串和模式串的第一个字符。"
        ) as tracker:
            self.play(*get_track_anims(1), run_time=0.4)
            self.play(FadeIn(group_i), FadeIn(group_j), run_time=max(0.2, tracker.duration - 0.4))

        # Helper functions for animation
        def compare_chars(i_idx, j_idx, is_match):
            self.play(*get_track_anims(3), run_time=0.3)
            self.play(S_boxes[i_idx].animate.set_color(GREEN if is_match else RED),
                      T_boxes[j_idx].animate.set_color(GREEN if is_match else RED), run_time=0.3)

        def move_pointers():
            self.play(*get_track_anims(4), run_time=0.3)
            # 优化：因为增加了 0.08 的 buff，单步位移由 0.8 变更为 0.88
            self.play(
                group_i.animate.shift(RIGHT * 0.88),
                group_j.animate.shift(RIGHT * 0.88),
                run_time=0.4
            )

        def backtrack(i_target_idx, shift_t_by):
            self.play(*get_track_anims(6), run_time=0.4)
            anims = []
            for b in S_boxes:
                anims.append(b.animate.set_color(BLUE))
            for b in T_boxes:
                anims.append(b.animate.set_color(ORANGE))

            i_target_x = S_boxes[i_target_idx].get_center()[0]
            curr_i_x = group_i.get_center()[0]

            self.play(*anims, group_i.animate.shift(RIGHT * (i_target_x - curr_i_x)), run_time=0.6)
            self.play(*get_track_anims(7), run_time=0.4)

            # 优化：滑动位移系数由 0.8 同步调整为 0.88
            t_final_x = T_boxes[0].get_center()[0] + 0.88 * shift_t_by
            curr_j_x = group_j.get_center()[0]
            j_shift = t_final_x - curr_j_x

            self.play(
                T_full.animate.shift(RIGHT * 0.88 * shift_t_by),
                group_j.animate.shift(RIGHT * j_shift),
                run_time=0.6
            )

        # Loop 过程保持一致
        with self.voiceover(
            text="进入循环，逐个比较字符。如果字符相等，则指针 I 和 J 都向后移动一位。",
            subcaption="进入循环，逐个比较字符。如果字符相等，则指针 i 和 j 都向后移动一位。"
        ) as tracker:
            self.play(*get_track_anims(2), run_time=0.3)
            compare_chars(0, 0, True)
            move_pointers()

        with self.voiceover(text="继续比较下一个字符，仍然相等，指针继续后移。") as tracker:
            self.play(*get_track_anims(2), run_time=0.3)
            compare_chars(1, 1, True)
            move_pointers()

        with self.voiceover(
            text="当比较第三个字符时，发现字符 A 和 C 不相等。",
            subcaption="当比较第三个字符时，发现字符 a 和 c 不相等。"
        ) as tracker:
            self.play(*get_track_anims(2), run_time=0.3)
            compare_chars(2, 2, False)

        with self.voiceover(text="此时匹配失败，这就是 BF 算法的核心：指针需要后退重新开始匹配。") as tracker:
            self.play(*get_track_anims(5), run_time=0.4)

        with self.voiceover(
            text="将指针 I 退回到主串上一次开始匹配的下一个位置。并将 J 重置为 1，相当于魔式串 T 整体向右滑动一位。",
            subcaption="将指针 i 退回到主串上一次开始匹配的下一个位置。并将 j 重置为 1，相当于模式串 T 整体向右滑动一位。"
        ) as tracker:
            backtrack(1, 1)

        with self.voiceover(
            text="再次进行比较，发现字符 B 和 A 依旧不相等。",
            subcaption="再次进行比较，发现字符 b 和 a 依旧不相等。"
        ) as tracker:
            self.play(*get_track_anims(2), run_time=0.3)
            compare_chars(1, 0, False)

        with self.voiceover(
                text="匹配又一次失败，魔式串 T 继续向右滑动一位，指针重新复位。",
                subcaption="匹配又一次失败，模式串 T 继续向右滑动一位，指针重新复位。"
        ) as tracker:
            self.play(*get_track_anims(5), run_time=0.3)
            backtrack(2, 1)

        with self.voiceover(text="现在再次比较。字符相等，指针向后移动。") as tracker:
            self.play(*get_track_anims(2), run_time=0.3)
            compare_chars(2, 0, True)
            move_pointers()

        with self.voiceover(text="继续比较，字符依然相等，指针后移。") as tracker:
            self.play(*get_track_anims(2), run_time=0.3)
            compare_chars(3, 1, True)
            move_pointers()

        with self.voiceover(text="最后一个字符也匹配成功，指针继续后移。") as tracker:
            self.play(*get_track_anims(2), run_time=0.3)
            compare_chars(4, 2, True)
            move_pointers()

        with self.voiceover(
            text="此时 J 大于魔式串的长度，说明整个魔式串已经完全匹配成功，跳出循环。",
            subcaption="此时 j 大于模式串的长度，说明整个模式串已经完全匹配成功，跳出循环。"
        ) as tracker:
            self.play(*get_track_anims(2), run_time=0.3)
            self.play(*get_track_anims(10), run_time=0.4)

        with self.voiceover(
                text="最后，算法计算并返回魔式串在主串中的起始位置。",
                subcaption="最后，算法计算并返回模式串在主串中的起始位置。"
        ) as tracker:
            self.play(*get_track_anims(11), run_time=0.4)

            # 优化：脱离右侧，开辟左侧独立的动画下方空间，彻底规避底部字幕和代码块的多重遮挡
            res_box = VGroup(
                Text("结果：起始位置 = 3", font_size=22, font="Microsoft YaHei", color=GREEN)
            ).move_to(LEFT * 4.5 + DOWN * 2.3)
            self.play(Write(res_box), run_time=max(0.5, tracker.duration - 0.4))

        self.play(*get_track_anims(None), FadeOut(group_i), FadeOut(group_j), run_time=0.5)

        # ===== PHASE E — COMPLEXITY =====
        # 同时展示最好和最坏情况，避免把 BF 的时间复杂度只概括成一个结论。
        best_time = VGroup(
            Text("最好：", font_size=20, font="Microsoft YaHei", color=GREEN),
            Text("O(m)", font_size=22, font="Consolas", color=GREEN)
        ).arrange(RIGHT, buff=0.08)
        best_case_note = Text(
            "首个位置一次匹配成功，仅比较 m 个字符",
            font_size=15,
            font="Microsoft YaHei",
            color=GREEN,
        )
        best_case_panel = VGroup(best_time, best_case_note).arrange(
            DOWN, aligned_edge=LEFT, buff=0.1
        )
        worst_time = VGroup(
            Text("最坏：", font_size=20, font="Microsoft YaHei", color=ORANGE),
            Text("O(n × m)", font_size=22, font="Consolas", color=ORANGE)
        ).arrange(RIGHT, buff=0.08)
        time_box = VGroup(
            Text("时间复杂度：", font_size=20, font="Microsoft YaHei", color=YELLOW),
            best_case_panel,
            worst_time
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).next_to(res_box, RIGHT, buff=0.6)
        space_box = VGroup(
            Text("空间复杂度：", font_size=20, font="Microsoft YaHei", color=YELLOW),
            Text("O(1)", font_size=22, font="Consolas", color=YELLOW)
        ).arrange(RIGHT, buff=0.1).next_to(time_box, RIGHT, buff=0.6).align_to(time_box, UP)

        with self.voiceover(
                text="最好情况下，魔式串从当前首位置开始就能完全匹配，只需要比较魔式串的 m 个字符，因此时间复杂度为 O(m)。",
                subcaption="最好情况下，模式串从当前首位置开始就能完全匹配，只需要比较模式串的 m 个字符，因此时间复杂度为 O(m)。"
        ) as tracker:
            self.play(FadeIn(time_box[0]), FadeIn(best_case_panel), run_time=tracker.duration)

        with self.voiceover(
                text="最坏情况下，每个位置都可能先匹配一部分，再发现不相等并回退重试，因此时间复杂度为 O(n 乘 m)。",
                subcaption="最坏情况下，每个位置都可能先匹配一部分，再发现不相等并回退重试，因此时间复杂度为 O(n×m)。"
        ) as tracker:
            self.play(FadeIn(worst_time), run_time=tracker.duration)

        with self.voiceover(
                text="算法仅使用了常数级的辅助指针变量，没有占用额外的空间，空间复杂度为 O(1)。",
                subcaption="算法仅使用了常数级的辅助指针变量，没有占用额外的空间，空间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是 BF 字符串匹配算法的完整演示过程。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)
