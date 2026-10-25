# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService

# =========================================================================
# Python 版定长顺序存储表示（SString）与 KMP 算法逻辑
# =========================================================================
max_size = 100


class SString:
    def __init__(self):
        # 初始化一个空的串
        self.length = 0  # 串当前长度
        self.ch = [None] * max_size  # 最大长度为max_size的空间

    def str_assign(self, s):
        # 把串的值赋为s
        n = len(s)  # 求串s的长度
        if n > max_size - 1:  # 此处为max_size - 1因为0号单元弃用
            raise Exception('空间已满')
        else:
            self.length = 0  # 把串置为空
            while self.length < n:
                self.length += 1
                self.ch[self.length] = s[self.length - 1]
            return self


def get_next(t):
    # 求模式串t的next函数值并存入数组next
    next = [0] * (t.length + 1)
    i = 1
    j = 0
    while i < t.length:
        if j == 0 or t.ch[i] == t.ch[j]:
            i += 1
            j += 1
            next[i] = j
        else:
            j = next[j]
    return next


def index_kmp(s, t, pos, next):
    # 利用模式串t的next函数求t在主串s中第pos个字符之后的位置的KMP算法
    # 其中，t非空，1<=pos<=s.length
    i = pos
    j = 1
    while i <= s.length and j <= t.length:  # 两个串均未比较到串尾
        if j == 0 or s.ch[i] == t.ch[j]:
            i += 1
            j += 1  # 继续比较后继字符
        else:
            j = next[j]  # 模式串向右移动
    if j > t.length:
        return i - t.length  # 匹配成功
    else:
        return 0  # 匹配失败


class ContinuousKMPAlgorithmPythonVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("KMP算法（Python版）", font_size=38, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.5).shift(LEFT * 0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        # “模式”的“模”固定使用第二声同音字“魔”送入 TTS，避免被误读为第四声；
        # 屏幕字幕仍通过 subcaption 保留教材中的规范写法。
        with self.voiceover(
            text="本节我们使用 Python 语言，学习一种高效的字符串匹配算法：KMP算法。该算法利用魔式串 t 的 next 函数，求 t 在主串 s 中第 pos 个字符之后的位置。",
            subcaption="本节我们使用 Python 语言，学习一种高效的字符串匹配算法：KMP算法。该算法利用模式串 t 的 next 函数，求 t 在主串 s 中第 pos 个字符之后的位置。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE B — 例子引入（生活实例类比：放大镜阅读，目光不回头）=====
        with self.voiceover(text="在学习代码之前，先用一个生活中的例子来理解 KMP 的核心思想。") as tracker:
            self.wait(tracker.duration)

        # 用一行文字瓷砖代表书页上的文字（主串），下方一条短瓷砖代表要找的词（模式串）
        def mini_row(s, color, side=0.6, buff=0.08):
            boxes = VGroup()
            for k, c in enumerate(s):
                b = Square(side_length=side, color=color)
                t = Text(c, font_size=26, color=WHITE)
                if k > 0:
                    b.next_to(boxes[-1], RIGHT, buff=buff)
                t.move_to(b.get_center())
                boxes.add(VGroup(b, t))
            return boxes

        demo_S = mini_row("ababac", BLUE).move_to(UP * 1.1 + LEFT * 0.6)
        demo_T = mini_row("abac", ORANGE)
        # 让 demo_T 的第一个瓷砖对齐到 demo_S 的第一个瓷砖正下方
        demo_T.shift(demo_S[0].get_center() - demo_T[0].get_center()).shift(DOWN * 1.4)

        S_cap = Text("文本（主串）", font_size=22, font="Microsoft YaHei", color=BLUE).next_to(demo_S, LEFT, buff=0.4)
        T_cap = Text("要找的词（模式串）", font_size=22, font="Microsoft YaHei", color=ORANGE).next_to(demo_T, LEFT, buff=0.4)

        # 放大镜：代表“目光 / 扫描位置”
        def make_lens():
            ring = Circle(radius=0.22, color=YELLOW, stroke_width=5)
            handle = Line(ring.get_center() + DOWN * 0.18 + RIGHT * 0.18,
                          ring.get_center() + DOWN * 0.45 + RIGHT * 0.45, color=YELLOW, stroke_width=5)
            return VGroup(ring, handle)

        lens = make_lens().move_to(demo_S[0].get_top() + UP * 0.5)

        with self.voiceover(text="想象在文本中寻找一个词。我们用放大镜代表正在扫描的目光，从左往右逐个核对。") as tracker:
            self.play(FadeIn(demo_S), FadeIn(demo_T), FadeIn(S_cap), FadeIn(T_cap), run_time=tracker.duration * 0.6)
            self.play(FadeIn(lens), run_time=tracker.duration * 0.4)

        with self.voiceover(text="前三个字符 a b a 都对上了，但第四个字符，文本是 b，词是 c，匹配失败。") as tracker:
            for k in range(3):
                self.play(lens.animate.move_to(demo_S[k].get_top() + UP * 0.5),
                          demo_S[k][0].animate.set_color(GREEN), demo_T[k][0].animate.set_color(GREEN), run_time=0.3)
            self.play(lens.animate.move_to(demo_S[3].get_top() + UP * 0.5),
                      demo_S[3][0].animate.set_color(RED), demo_T[3][0].animate.set_color(RED), run_time=0.4)

        # BF 笨办法：目光回退
        bf_tag = Text("", font_size=24, font="Microsoft YaHei", color=RED).to_edge(DOWN, buff=2.0)
        back_arrow = CurvedArrow(demo_S[3].get_top() + UP * 0.5, demo_S[1].get_top() + UP * 0.5, color=RED, angle=-TAU / 4)
        with self.voiceover(text="笨办法是：把目光退回去，从下一个位置重新一个一个地比较，做了很多重复劳动。") as tracker:
            self.play(FadeIn(bf_tag), Create(back_arrow), run_time=tracker.duration * 0.5)
            self.play(lens.animate.move_to(demo_S[1].get_top() + UP * 0.5), run_time=tracker.duration * 0.5)

        # 恢复，准备演示 KMP
        self.play(FadeOut(back_arrow), FadeOut(bf_tag),
                  *[demo_S[k][0].animate.set_color(BLUE) for k in range(len(demo_S))],
                  *[demo_T[k][0].animate.set_color(ORANGE) for k in range(len(demo_T))],
                  lens.animate.move_to(demo_S[3].get_top() + UP * 0.5), run_time=0.6)

        # KMP 聪明办法：目光不回退，模式串向右滑动
        kmp_tag = Text("", font_size=24, font="Microsoft YaHei",
                       color=GREEN).to_edge(DOWN, buff=1.0)
        with self.voiceover(
            text="而 KMP 的聪明之处在于：目光绝不回头。它利用词本身已经匹配过的重复信息，使得魔式串一次性向右滑动到正确位置，跳过那些注定能对上的字符。",
            subcaption="而 KMP 的聪明之处在于：目光绝不回头。它利用词本身已经匹配过的重复信息，使得模式串一次性向右滑动到正确位置，跳过那些注定能对上的字符。"
        ) as tracker:
            # 重新点亮前三个匹配
            self.play(*[demo_S[k][0].animate.set_color(GREEN) for k in range(3)],
                      *[demo_T[k][0].animate.set_color(GREEN) for k in range(3)],
                      demo_S[3][0].animate.set_color(RED), demo_T[3][0].animate.set_color(RED), run_time=0.4)
            self.play(FadeIn(kmp_tag), run_time=0.4)
            # 模式串向右滑动 2 格，目光（放大镜）停在原处不动
            slide_dx = demo_S[2].get_center()[0] - demo_T[0].get_center()[0]
            self.play(*[demo_T[k][0].animate.set_color(ORANGE) for k in range(len(demo_T))],
                      demo_T.animate.shift(RIGHT * slide_dx), run_time=max(0.6, tracker.duration - 0.8))

        with self.voiceover(
            text="这个 “魔式串应该滑动多远” 的信息，正是预先保存在 next 数组里的。",
            subcaption="这个 “模式串应该滑动多远” 的信息，正是预先保存在 next 数组里的。"
        ) as tracker:
            self.wait(tracker.duration)

        # 清场，进入主演示
        self.play(FadeOut(demo_S), FadeOut(demo_T), FadeOut(S_cap), FadeOut(T_cap),
                  FadeOut(lens), FadeOut(kmp_tag), run_time=0.6)

        # ===== PHASE C — CODE BLOCK CONFIG（与 BF 算法完全相同的代码板样式）=====
        c_lines = [
            "def index_kmp(s, t, pos, next):",
            "    i = pos; j = 1",
            "    while i <= s.length and j <= t.length:",
            "        if j == 0 or s.ch[i] == t.ch[j]:",
            "            i += 1; j += 1",
            "        else:",
            "            j = next[j]",
            "    if j > t.length:",
            "        return i - t.length",
            "    else:",
            "        return 0"
        ]
        # 代码行索引常量（便于追踪高亮）
        IDX_DECL = 1
        IDX_WHILE = 2
        IDX_IF = 3
        IDX_INC = 4
        IDX_NEXT = 6
        IDX_RET_IF = 7
        IDX_RET = 8

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
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

        # 布局挂载在 logo 下方，杜绝与标题和 logo 遮挡
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.2).to_edge(RIGHT, buff=0.3)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line:
                return [Wait(0.001)]
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

        with self.voiceover(text="右侧是 KMP 算法的 Python 实现代码，接下来我们通过实际演示来了解它的匹配过程。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # ===== PHASE C2 — VISUALIZATION SETUP（串的样式与 BF 算法完全一致）=====
        BOX = 0.55          # 因主串较长（14 个字符），方格边长适当缩小
        BUF = 0.08
        PITCH = BOX + BUF   # 单步位移 = 边长 + 间距

        def build_string_array(s_str, label_text, color=BLUE):
            boxes = VGroup()
            texts = VGroup()
            indices = VGroup()
            for idx, ch in enumerate(s_str):
                box = Square(side_length=BOX, color=color)
                txt = Text(ch, font_size=24, color=WHITE)
                idx_txt = Text(str(idx + 1), font_size=15, color=GRAY)

                if idx > 0:
                    box.next_to(boxes[-1], RIGHT, buff=BUF)

                txt.move_to(box.get_center())
                idx_txt.next_to(box, UP if label_text == "S" else DOWN, buff=0.08)

                boxes.add(box)
                texts.add(txt)
                indices.add(idx_txt)

            res = VGroup(boxes, texts, indices)
            label = Text(label_text, font_size=28, color=color, weight=BOLD).next_to(res, LEFT, buff=0.35)
            return VGroup(label, res), boxes, texts

        S_str = "acabaabaabcaca"
        T_str = "abaabcac"

        S_full, S_boxes, S_texts = build_string_array(S_str, "S", color=BLUE)
        S_full.move_to(LEFT * 2.15 + UP * 1.75)

        T_full, T_boxes, T_texts = build_string_array(T_str, "T", color=ORANGE)
        diff_x = S_boxes[0].get_center()[0] - T_boxes[0].get_center()[0]
        T_full.shift(RIGHT * diff_x)
        T_full.match_y(S_full).shift(DOWN * 1.6)

        # 指针 i 放在 S 的上方（自上往下指）
        ptr_i = Arrow(start=S_boxes[0].get_top() + UP * 0.45, end=S_boxes[0].get_top(), buff=0.06, color=YELLOW,
                      max_tip_length_to_length_ratio=0.45)
        label_i = Text("i", font_size=22, color=YELLOW).next_to(ptr_i, UP, buff=0.05)
        group_i = VGroup(ptr_i, label_i)

        # 指针 j 放在 T 的下方（自下往上指）
        ptr_j = Arrow(start=T_boxes[0].get_bottom() + DOWN * 0.5, end=T_boxes[0].get_bottom(), buff=0.06, color=YELLOW,
                      max_tip_length_to_length_ratio=0.45)
        label_j = Text("j", font_size=22, color=YELLOW).next_to(ptr_j, DOWN, buff=0.05)
        group_j = VGroup(ptr_j, label_j)

        # ----- next 数组表格 -----
        def make_cell(content, w, h, fs, txt_color=WHITE, box_color=GRAY_B):
            rect = Rectangle(width=w, height=h, color=box_color, stroke_width=1.5)
            t = Text(str(content), font_size=fs, color=txt_color, font="Microsoft YaHei")
            t.move_to(rect.get_center())
            return VGroup(rect, t)

        HEAD_W, CELL_W, CELL_H = 1.0, 0.55, 0.5
        next_list = [0, 1, 1, 2, 2, 3, 1, 2]
        row_j = VGroup(make_cell("j", HEAD_W, CELL_H, 18, txt_color=YELLOW))
        row_t = VGroup(make_cell("t[ j ]", HEAD_W, CELL_H, 16, txt_color=ORANGE))
        row_n = VGroup(make_cell("next[ j ]", HEAD_W, CELL_H, 14, txt_color=GREEN))
        next_cells = {}
        for k in range(8):
            row_j.add(make_cell(k + 1, CELL_W, CELL_H, 18, txt_color=YELLOW))
            row_t.add(make_cell(T_str[k], CELL_W, CELL_H, 18, txt_color=ORANGE))
            ncell = make_cell(next_list[k], CELL_W, CELL_H, 18, txt_color=GREEN)
            row_n.add(ncell)
            next_cells[k + 1] = ncell
        for r in (row_j, row_t, row_n):
            r.arrange(RIGHT, buff=0)
        next_table = VGroup(row_j, row_t, row_n).arrange(DOWN, buff=0)
        next_table.move_to(LEFT * 2.4 + DOWN * 1.75)

        with self.voiceover(
            text="假设主串 s 为 a c a b a a b a a b c a c a，魔式串 t 为 a b a a b c a c，初始位置 pos 为 1。",
            subcaption="假设主串 s 为 acabaabaabcaca，模式串 t 为 abaabcac，初始位置 pos 为 1。"
        ) as tracker:
            self.play(FadeIn(S_full), FadeIn(T_full), run_time=tracker.duration)

        with self.voiceover(
            text="这是预先由 get next 函数计算好的 next 数组。它记录了每个位置失配时，魔式串指针 j 应该回退到的新位置。",
            subcaption="这是预先由 get_next 函数计算好的 next 数组。它记录了每个位置失配时，模式串指针 j 应该回退到的新位置。"
        ) as tracker:
            self.play(FadeIn(next_table), run_time=tracker.duration)

        with self.voiceover(
            text="首先初始化指针 I 和 J，分别指向主串和魔式串的第一个字符。",
            subcaption="首先初始化指针 i 和 j，分别指向主串和模式串的第一个字符。"
        ) as tracker:
            self.play(*get_track_anims(IDX_DECL), run_time=0.4)
            self.play(FadeIn(group_i), FadeIn(group_j), run_time=max(0.2, tracker.duration - 0.4))

        # ===== PHASE D — 匹配过程的辅助动画函数 =====
        def reset_box_colors():
            return [b.animate.set_color(BLUE) for b in S_boxes] + [b.animate.set_color(ORANGE) for b in T_boxes]

        def compare_chars(i_idx, j_idx, is_match, pace=1.0):
            self.play(*get_track_anims(IDX_WHILE), run_time=0.25 * pace)
            self.play(*get_track_anims(IDX_IF), run_time=0.25 * pace)
            self.play(S_boxes[i_idx].animate.set_color(GREEN if is_match else RED),
                      T_boxes[j_idx].animate.set_color(GREEN if is_match else RED), run_time=0.3 * pace)

        def match_move(pace=1.0):
            # 字符相等：i += 1; j += 1; 两指针同时右移一格（模式串 T 不动）
            self.play(*get_track_anims(IDX_INC), run_time=0.25 * pace)
            self.play(group_i.animate.shift(RIGHT * PITCH),
                      group_j.animate.shift(RIGHT * PITCH), run_time=0.4 * pace)

        def narrated_match(i_idx, j_idx):
            # 一次比较对应一句旁白，动画总时长跟随该句语音，不留无声的逐格移动。
            ch = S_str[i_idx]
            with self.voiceover(
                text=f"主串第{i_idx + 1}个字符{ch}与魔式串第{j_idx + 1}个字符{ch}相等，两个指针各向后移动一位。",
                subcaption=f"S[{i_idx + 1}] 与 T[{j_idx + 1}] 都是 {ch}，匹配；i、j 各后移一位。"
            ) as tracker:
                pace = tracker.duration / 1.45
                compare_chars(i_idx, j_idx, True, pace)
                match_move(pace)

        def slide(j_old, j_new, s_idx):
            # 失配：j = next[j]。主串指针 i 不回退，模式串 T 向右滑动，
            # 使 T 的第 j_new 个字符对齐到主串 S_boxes[s_idx] 下方。
            self.play(*get_track_anims(IDX_NEXT), run_time=0.3)
            self.play(*reset_box_colors(),
                      Indicate(next_cells[j_old], color=RED, scale_factor=1.4), run_time=0.6)
            dx_T = S_boxes[s_idx].get_center()[0] - T_boxes[j_new - 1].get_center()[0]
            j_target_x = S_boxes[s_idx].get_center()[0]
            self.play(T_full.animate.shift(RIGHT * dx_T),
                      group_j.animate.shift(RIGHT * (j_target_x - group_j.get_center()[0])), run_time=0.6)

        def retreat_j_to_zero():
            # 失配且 next[j] 为 0 的情形：j = next[1] = 0。
            # 主串指针 i 不动；模式串指针 j 退到 0 号“虚拟”位置（T 第一个字符的左侧一格），
            # 并用一个灰色 “0” 标注当前 j 的取值，使“j 退到 0”这一步在画面上清晰可见。
            self.play(*get_track_anims(IDX_NEXT), run_time=0.3)
            self.play(Indicate(next_cells[1], color=RED, scale_factor=1.4), run_time=0.5)
            slot0_x = T_boxes[0].get_center()[0] - PITCH
            zero_tag_pos = T_boxes[0].get_bottom() + LEFT * PITCH + DOWN * 0.17
            self.j_zero_tag = Text("0", font_size=15, color=GRAY).move_to(zero_tag_pos)
            # j 向左移动一格，明确停在 0 号虚拟位置，并淡入 “0” 标注
            self.play(group_j.animate.shift(RIGHT * (slot0_x - group_j.get_center()[0])),
                      FadeIn(self.j_zero_tag), run_time=0.5)

        def restart_after_zero(s_idx_new):
            # 因 j==0 执行 i += 1; j += 1。为了让“j 先回退 0、再前进到 1”的过程清晰可见，分两步演示：
            #   第一步（j += 1）：j 由 0 号虚拟位置回到指向 T 的第一个字符（即 j 由 0 变为 1），
            #                    同时淡出 “0” 标注，这一步是干净的“向右一格”运动；
            #   第二步（i += 1）：主串指针 i 前进一格，模式串 T 整体右滑使 T[1] 对齐到新的 i 列，
            #                    j 随 T 一同右移，为下一次比较做好对齐。
            self.play(*get_track_anims(IDX_IF), run_time=0.25)
            self.play(*reset_box_colors(), run_time=0.4)

            # —— 第一步：j += 1，j 从 0 回到 1（指向 T 的第一个字符），并淡出 “0” 标注 ——
            self.play(*get_track_anims(IDX_INC), run_time=0.25)
            self.play(FadeOut(self.j_zero_tag),
                      group_j.animate.shift(RIGHT * (T_boxes[0].get_center()[0] - group_j.get_center()[0])),
                      run_time=0.5)

            # —— 第二步：i += 1，i 前进一格；模式串 T 右滑使 T[1] 对齐到新的 i 列；j 随 T 一同右移 ——
            dx_T = S_boxes[s_idx_new].get_center()[0] - T_boxes[0].get_center()[0]
            self.play(group_i.animate.shift(RIGHT * (S_boxes[s_idx_new].get_center()[0] - group_i.get_center()[0])),
                       T_full.animate.shift(RIGHT * dx_T),
                       group_j.animate.shift(RIGHT * dx_T), run_time=0.55)

        # ===== 匹配过程演示 =====
        with self.voiceover(
            text="进入循环逐个比较字符。S的第1个字符与T的第1个字符都是a，指针i和j都向后移动一位。",
            subcaption="进入循环逐个比较字符。S的第1个字符与T的第1个字符都是a，指针i和j都向后移动一位。"
        ) as tracker:
            compare_chars(0, 0, True)
            match_move()

        with self.voiceover(
            text="比较第2个字符，S 的 c 与 T 的 b 不相等，匹配失败。",
            subcaption="比较第二个字符，S的c与T的b不相等，匹配失败。"
        ) as tracker:
            compare_chars(1, 1, False)

        with self.voiceover(
            text="此时主串指针I不回退，next 2 等于 1，j回退到 1",
            subcaption="主串指针i不回退，next[2]=1，j回退到 1"
        ) as tracker:
            slide(2, 1, 1)

        with self.voiceover(
            text="再比较S的第2个字符c与T的第1个字符a，仍然不相等。next 1 等于 0，J 退到 0。",
            subcaption="再比较S的第2个字符c与T的第1个字符a，仍然不相等。next[1]=0，j退到0。"
        ) as tracker:
            compare_chars(1, 0, False)
            retreat_j_to_zero()

        with self.voiceover(
            text="因为J 等于 0，执行 i 加 1、j 加 1，j回到1后，主串指针i前进一格，魔式串重新从头开始比较。",
            subcaption="因为 j==0，执行 i += 1、j += 1：j 先回到 1，i 前进到 s[3]，模式串重新从头比较。"
        ) as tracker:
            restart_after_zero(2)

        for i_idx, j_idx in ((2, 0), (3, 1), (4, 2), (5, 3), (6, 4)):
            narrated_match(i_idx, j_idx)

        with self.voiceover(
            text="比较S的第8个字符a与T的第6个字符c，不相等，匹配失败。",
            subcaption="比较S的第8个字符a与T的第6个字符c，不相等，匹配失败。"
        ) as tracker:
            compare_chars(7, 5, False)

        with self.voiceover(
            text="主串指针 I 依然停在第8位不回退，next 6 等于 3，j回退到3",
            subcaption="主串指针 i 停在第 8 位不回退，next[6]=3，j回退到3"
        ) as tracker:
            slide(6, 3, 7)

        for i_idx, j_idx in ((7, 2), (8, 3), (9, 4), (10, 5), (11, 6), (12, 7)):
            narrated_match(i_idx, j_idx)

        with self.voiceover(
            text="此时 J 大于魔式串的长度，魔式串完全匹配成功，跳出循环。",
            subcaption="此时 j 大于模式串的长度，模式串完全匹配成功，跳出循环。"
        ) as tracker:
            self.play(*get_track_anims(IDX_WHILE), run_time=0.3)
            self.play(*get_track_anims(IDX_RET_IF), run_time=0.4)

        with self.voiceover(
            text="最后算法返回 i 减 t 的长度，等于 14 减 8，结果为 6，魔式串在主串中从第6个字符开始。",
            subcaption="返回 i - t.length = 14 - 8 = 6，模式串在主串中从第6个字符开始。"
        ) as tracker:
            self.play(*get_track_anims(IDX_RET), run_time=0.4)
            # 高亮匹配成功的区段 S[6..13]，并将整条模式串 T 点亮为绿色
            # （其中 T[1]、T[2] 是 KMP 复用的已匹配前缀，无需重新比较）
            self.play(*[S_boxes[k].animate.set_color(GREEN) for k in range(5, 13)],
                      *[b.animate.set_color(GREEN) for b in T_boxes], run_time=0.5)
            self.wait(max(0.2, tracker.duration - 0.9))

        # 淡出指针、代码高亮与 next 表，腾出底部空间展示结论
        self.play(*get_track_anims(None), FadeOut(group_i), FadeOut(group_j), FadeOut(next_table), run_time=0.5)

        res_box = Text("结果：起始位置 = 6", font_size=24, font="Microsoft YaHei", color=GREEN).move_to(
            LEFT * 4.3 + DOWN * 2.6)
        with self.voiceover(
            text="至此，KMP 算法成功在主串中找到了魔式串。",
            subcaption="至此，KMP 算法成功在主串中找到了模式串。"
        ) as tracker:
            self.play(Write(res_box), run_time=max(0.5, tracker.duration))

        # ===== PHASE E — COMPLEXITY =====
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(n + m)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(
            res_box, RIGHT, buff=0.7)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(m)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(
            time_box, RIGHT, buff=0.7)

        with self.voiceover(
            text="计算next数组需要遍历魔式串，匹配时i不回退，算法的时间复杂度为 O n 加 m。",
            subcaption="计算next数组需要遍历模式串，匹配时i不回退，算法的时间复杂度为 O(n+m)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
            text="算法额外申请了大小为 m 的 next 数组，空间复杂度为 O m。",
            subcaption="算法额外申请了大小为 m 的 next 数组，空间复杂度为 O(m)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是 KMP 字符串匹配算法 Python 版的完整演示过程。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)


# Alias
KMPAlgorithmPythonVideo = ContinuousKMPAlgorithmPythonVideo
IndexKMPPythonVideo = ContinuousKMPAlgorithmPythonVideo
