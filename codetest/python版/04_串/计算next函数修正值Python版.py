# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService

# =========================================================================
# Python 版定长顺序存储表示（SString）与 get_nextval 算法逻辑
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


def get_nextval(t):
    # 求模式串T的next函数修正值并存入数组nextval
    i = 1
    j = 0
    nextval = [0] * (t.length + 1)
    while i < t.length:
        if j == 0 or t.ch[i] == t.ch[j]:
            i += 1
            j += 1
            if t.ch[i] != t.ch[j]:
                nextval[i] = j
            else:
                nextval[i] = nextval[j]
        else:
            j = nextval[j]
    return nextval


class ContinuousGetNextvalPythonVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("计算next函数修正值（Python版）", font_size=36, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.5).shift(LEFT * 0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        # “模式”的“模”固定使用第二声同音字“魔”送入 TTS，避免被误读为第四声；
        # 屏幕字幕仍通过 subcaption 保留教材中的规范写法。
        with self.voiceover(
            text="本节我们使用 Python 语言，学习 KMP 算法的关键进阶优化：计算 next 函数修正值。该算法在确定回退位置的同时，排除了注定再次失配的无效比对。",
            subcaption="本节我们使用 Python 语言，学习 KMP 算法的关键进阶优化：计算 next 函数修正值。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== PHASE B — 例子引入（为什么需要修正值）=====
        with self.voiceover(text="在看代码之前，我们先通过一个直观的例子，了解为什么需要对 next 数组进行修正。") as tracker:
            self.wait(tracker.duration)

        demo_boxes = VGroup()
        for k, ch in enumerate("aba"):
            box = Square(side_length=0.7, color=ORANGE)
            txt = Text(ch, font_size=28, color=WHITE).move_to(box.get_center())
            idx = Text(str(k + 1), font_size=18, color=GRAY).next_to(box, UP, buff=0.1)
            if k > 0:
                box.next_to(demo_boxes[-1][0], RIGHT, buff=0.15)
                txt.move_to(box.get_center())
                idx.next_to(box, UP, buff=0.1)
            demo_boxes.add(VGroup(box, txt, idx))
        demo_boxes.move_to(UP * 0.9 + LEFT * 0.8)

        demo_label = Text("魔式串：", font_size=22, font="Microsoft YaHei", color=ORANGE).next_to(demo_boxes, LEFT, buff=0.3)

        with self.voiceover(
            text="假设魔式串为 a b a。当主串字符在第 3 个位置 a 发生失配时，按照原始的 next 数组，next 3 等于 1，指针需要回退到第 1 个字符继续比对。",
            subcaption="假设模式串为 aba。当主串字符在第 3 个位置 a 失配时，按原始 next[3]=1，指针回退到第 1 个字符。"
        ) as tracker:
            self.play(FadeIn(demo_boxes), FadeIn(demo_label), run_time=tracker.duration * 0.5)
            # 高亮第 3 个字符失配
            self.play(demo_boxes[2][0].animate.set_color(RED), run_time=tracker.duration * 0.5)

        # 弧线两端下移，弧顶也留在字符格下方，避免穿过中间的 b。
        back_arrow = CurvedArrow(demo_boxes[2][0].get_bottom() + DOWN * 0.65,
                                 demo_boxes[0][0].get_bottom() + DOWN * 0.65,
                                 color=RED, angle=TAU / 4)
        note_text = Text("第1个字符也是a，注定再次失配！", font_size=20, font="Microsoft YaHei", color=RED).next_to(back_arrow, DOWN, buff=0.2)

        with self.voiceover(
            text="但是，第 1 个字符本身也是 a！既然刚才和 a 比较已经失败了，回退后再次和 a 比较必然还是失败，这就是一次注定无效的多余比对。",
            subcaption="但是第 1 个字符也是 a，刚才与 a 比较已失败，回退后与 a 比对必然再次失败！"
        ) as tracker:
            self.play(Create(back_arrow), FadeIn(note_text), demo_boxes[0][0].animate.set_color(RED), run_time=tracker.duration)

        correct_text = Text("直接修正为 nextval[3] = nextval[1] = 0", font_size=22, font="Microsoft YaHei", color=GREEN).next_to(note_text, DOWN, buff=0.2)
        with self.voiceover(
            text="nextval 的修正思想正是：若回退后的字符与当前字符完全相同，则直接继承其修正值，一步回退到位，避免多余的比对。",
            subcaption="nextval 修正思想：若回退后字符与当前字符相同，则直接继承其修正值，避免多余比对。"
        ) as tracker:
            self.play(FadeIn(correct_text), run_time=tracker.duration)

        self.play(FadeOut(demo_boxes), FadeOut(demo_label), FadeOut(back_arrow), FadeOut(note_text), FadeOut(correct_text), run_time=0.6)

        # ===== PHASE C — CODE BLOCK CONFIG =====
        c_lines = [
            "def get_nextval(t):",
            "    i = 1; j = 0",
            "    nextval = [0] * (t.length + 1)",
            "    while i < t.length:",
            "        if j == 0 or t.ch[i] == t.ch[j]:",
            "            i += 1; j += 1",
            "            if t.ch[i] != t.ch[j]:",
            "                nextval[i] = j",
            "            else:",
            "                nextval[i] = nextval[j]",
            "        else:",
            "            j = nextval[j]",
            "    return nextval"
        ]
        # 代码行高亮索引常量
        IDX_DECL = 1        # i = 1; j = 0
        IDX_INIT = 2        # nextval = [0] * (t.length + 1)
        IDX_WHILE = 3       # while i < t.length:
        IDX_IF_MATCH = 4    # if j == 0 or t.ch[i] == t.ch[j]:
        IDX_INC = 5         # i += 1; j += 1
        IDX_IF_DIFF = 6     # if t.ch[i] != t.ch[j]:
        IDX_SET_J = 7       # nextval[i] = j
        IDX_ELSE_DIFF = 8   # else:
        IDX_SET_VAL = 9     # nextval[i] = nextval[j]
        IDX_ELSE = 10       # else:
        IDX_RETREAT = 11    # j = nextval[j]
        IDX_RETURN = 12     # return nextval

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=9.2, font="Consolas", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.11)
        SPACE_WIDTH = 0.08
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        bg_width = code_group.get_width() * 1.2 + 0.8
        bg_height = code_group.get_height() + 0.55
        code_bg = RoundedRectangle(corner_radius=0.2, height=bg_height, width=bg_width, color=GRAY, fill_opacity=0.1,
                                   stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.4)
        code_bg.match_y(code_group)

        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.2).to_edge(RIGHT, buff=0.25)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line:
                return [Wait(0.001)]
            anims = []
            if self.current_line is not None:
                anims.append(self.c_texts[self.current_line].animate.set_color(WHITE).scale(1 / 1.15, about_edge=LEFT))
            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW).scale(1.15, about_edge=LEFT))
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
            text="右侧是计算 next 函数修正值的 Python 代码。它在字符匹配前进时，增加了对当前字符与回退字符是否相等的判断。",
            subcaption="右侧是计算 next 函数修正值的 Python 代码。它增加了对当前字符与回退字符是否相等的判断。"
        ) as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # ===== PHASE C2 — VISUALIZATION SETUP =====
        BOX = 0.6
        BUF = 0.1
        PITCH = BOX + BUF

        T_str = "abaabcac"

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

        slot0_box = Square(side_length=BOX, color=GRAY, stroke_opacity=0.5).move_to(T_boxes[0].get_center() + LEFT * PITCH)
        slot0_lbl = Text("0", font_size=16, color=GRAY).next_to(slot0_box, UP, buff=0.08)
        slot0 = VGroup(slot0_box, slot0_lbl)

        T_label = Text("t", font_size=28, color=ORANGE, weight=BOLD).next_to(slot0_box, LEFT, buff=0.4)
        T_full = VGroup(T_label, T_body)

        ptr_i = Arrow(start=T_boxes[0].get_top() + UP * 0.45, end=T_boxes[0].get_top(), buff=0.06, color=YELLOW,
                      max_tip_length_to_length_ratio=0.45)
        label_i = Text("i", font_size=22, color=YELLOW).next_to(ptr_i, UP, buff=0.05)
        group_i = VGroup(ptr_i, label_i)

        ptr_j = Arrow(start=slot0_box.get_bottom() + DOWN * 0.5, end=slot0_box.get_bottom(), buff=0.06, color=GREEN,
                      max_tip_length_to_length_ratio=0.45)
        label_j = Text("j", font_size=22, color=GREEN).next_to(ptr_j, DOWN, buff=0.05)
        group_j = VGroup(ptr_j, label_j)

        # ----- 表格：j, t[j], nextval[j] -----
        def make_cell(content, w, h, fs, txt_color=WHITE, box_color=GRAY_B):
            rect = Rectangle(width=w, height=h, color=box_color, stroke_width=1.5)
            t = Text(str(content), font_size=fs, color=txt_color, font="Microsoft YaHei")
            t.move_to(rect.get_center())
            return VGroup(rect, t)

        HEAD_W, CELL_W, CELL_H = 1.3, 0.55, 0.5
        row_j = VGroup(make_cell("j", HEAD_W, CELL_H, 18, txt_color=YELLOW))
        row_t = VGroup(make_cell("t[ j ]", HEAD_W, CELL_H, 16, txt_color=ORANGE))
        row_n = VGroup(make_cell("nextval[ j ]", HEAD_W, CELL_H, 13, txt_color=GREEN))
        next_rects = {}
        for k in range(8):
            row_j.add(make_cell(k + 1, CELL_W, CELL_H, 18, txt_color=YELLOW))
            row_t.add(make_cell(T_str[k], CELL_W, CELL_H, 18, txt_color=ORANGE))
            rect = Rectangle(width=CELL_W, height=CELL_H, color=GRAY_B, stroke_width=1.5)
            row_n.add(rect)
            next_rects[k + 1] = rect
        for r in (row_j, row_t, row_n):
            r.arrange(RIGHT, buff=0)
        next_table = VGroup(row_j, row_t, row_n).arrange(DOWN, buff=0)
        next_table.move_to(LEFT * 2.2 + DOWN * 0.85)

        with self.voiceover(
            text="我们依然以模式串 a b a a b c a c 为例，逐步演示 nextval 数组的计算过程。",
            subcaption="以模式串 abaabcac 为例，逐步演示 nextval 数组的计算过程。"
        ) as tracker:
            self.play(FadeIn(T_full), FadeIn(slot0), FadeIn(next_table), run_time=tracker.duration)

        # ===== PHASE D — 计算辅助函数 =====
        state = {'i': 1, 'j': 0}

        def box_x(idx):
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

        def fill_val(pos, val, is_corrected=False, rt=0.5):
            color = TEAL if is_corrected else GREEN
            t = Text(str(val), font_size=18, color=color, font="Microsoft YaHei").move_to(next_rects[pos].get_center())
            self.play(Write(t), Indicate(next_rects[pos], color=color, scale_factor=1.2), run_time=rt)
            self.add(t)

        def step_advance_diff(match_compare):
            # 前进且 t[i] != t[j] -> nextval[i] = j
            self.play(*get_track_anims(IDX_WHILE), run_time=0.25)
            self.play(*get_track_anims(IDX_IF_MATCH), run_time=0.25)
            if match_compare:
                color_pair(True)
            ni, nj = state['i'] + 1, state['j'] + 1
            self.play(*get_track_anims(IDX_INC), run_time=0.25)
            move_ij(ni, nj)
            self.play(*get_track_anims(IDX_IF_DIFF), run_time=0.25)
            self.play(*get_track_anims(IDX_SET_J), run_time=0.25)
            fill_val(ni, nj, is_corrected=False)
            if match_compare:
                reset_boxes()

        def step_advance_same(val_src):
            # 前进且 t[i] == t[j] -> 触发修正 nextval[i] = nextval[j]
            self.play(*get_track_anims(IDX_WHILE), run_time=0.25)
            self.play(*get_track_anims(IDX_IF_MATCH), run_time=0.25)
            color_pair(True)
            ni, nj = state['i'] + 1, state['j'] + 1
            self.play(*get_track_anims(IDX_INC), run_time=0.25)
            move_ij(ni, nj)
            self.play(*get_track_anims(IDX_IF_DIFF), run_time=0.25)
            self.play(*get_track_anims(IDX_ELSE_DIFF), run_time=0.2)
            self.play(*get_track_anims(IDX_SET_VAL), run_time=0.25)
            # 弧线箭头从 nextval[j] 指向 nextval[i] 突出“继承”
            inherit_arrow = CurvedArrow(next_rects[val_src].get_bottom() + DOWN * 0.05,
                                        next_rects[ni].get_bottom() + DOWN * 0.05,
                                        color=YELLOW, angle=-TAU / 4)
            self.play(Create(inherit_arrow), run_time=0.3)
            fill_val(ni, val_src_val(val_src), is_corrected=True)
            self.play(FadeOut(inherit_arrow), run_time=0.25)
            reset_boxes()

        # 记录已填入的值以便继承查表
        computed_nextval = {1: 0}
        def val_src_val(src):
            return computed_nextval[src]

        def step_retreat(new_j):
            self.play(*get_track_anims(IDX_WHILE), run_time=0.25)
            self.play(*get_track_anims(IDX_IF_MATCH), run_time=0.25)
            color_pair(False)
            self.play(*get_track_anims(IDX_ELSE), run_time=0.2)
            self.play(*get_track_anims(IDX_RETREAT), run_time=0.25)
            self.play(Indicate(next_rects[state['j']], color=RED, scale_factor=1.2), run_time=0.4)
            reset_boxes()
            move_j(new_j)

        # ===== PHASE D2 — 初始化 =====
        with self.voiceover(
            text="首先指针 i 指向 1，j 指向 0 号虚拟位。创建并初始化 nextval 数组，第 1 项为 0。",
            subcaption="首先指针 i 指向 1，j 指向 0 号位。初始化 nextval 数组，第 1 项为 0。"
        ) as tracker:
            self.play(*get_track_anims(IDX_DECL), run_time=0.3)
            self.play(FadeIn(group_i), FadeIn(group_j), run_time=0.3)
            self.play(*get_track_anims(IDX_INIT), run_time=0.3)
            fill_val(1, 0)

        # ===== PHASE D3 — 循环计算步骤 =====
        # 步骤 1：i=1, j=0 -> j==0, i=2, j=1. t[2]='b' != t[1]='a' -> nextval[2] = 1
        with self.voiceover(
            text="进入循环。j 等于 0，执行 i 加 1、j 加 1，得到 i 为 2、j 为 1。比较第 2 个字符 b 与第 1 个字符 a，两者不相等，因此 nextval 2 直接等于当前 j 即 1。",
            subcaption="j==0，i、j 加 1 得 i=2, j=1。t[2]='b' != t[1]='a'，nextval[2] = j = 1。"
        ) as tracker:
            step_advance_diff(match_compare=False)
            computed_nextval[2] = 1

        # 步骤 2：i=2, j=1 -> t[2]='b' != t[1]='a' -> j = nextval[1] = 0
        with self.voiceover(
            text="比较字符 b 与 a，不相等，j 回退到 nextval 1 即 0 号位。",
            subcaption="t[2]='b' != t[1]='a'，j 回退到 nextval[1] = 0。"
        ) as tracker:
            step_retreat(0)

        # 步骤 3：i=2, j=0 -> j==0, i=3, j=1. t[3]='a' == t[1]='a' -> 触发修正！nextval[3] = nextval[1] = 0
        with self.voiceover(
            text="j 等于 0，i、j 均加 1，得到 i 为 3、j 为 1。此时发现第 3 个字符 a 与第 1 个字符 a 完全相同！触发修正：nextval 3 直接继承 nextval 1 的值，记为 0！",
            subcaption="i=3, j=1。t[3]='a' == t[1]='a' 相同！触发修正：nextval[3] = nextval[1] = 0！"
        ) as tracker:
            step_advance_same(1)
            computed_nextval[3] = 0

        # 步骤 4：i=3, j=1 -> t[3]='a' == t[1]='a' -> i=4, j=2. t[4]='a' != t[2]='b' -> nextval[4] = 2
        with self.voiceover(
            text="比较第 3 个字符 a 与第 1 个字符 a，相等，i、j 加 1 得 i 为 4、j 为 2。比较第 4 个字符 a 与第 2 个字符 b，不相等，nextval 4 等于 2。",
            subcaption="t[3]==t[1]，i=4, j=2。t[4]='a' != t[2]='b'，nextval[4] = j = 2。"
        ) as tracker:
            step_advance_diff(match_compare=True)
            computed_nextval[4] = 2

        # 步骤 5：i=4, j=2 -> t[4]='a' != t[2]='b' -> j = nextval[2] = 1
        with self.voiceover(
            text="字符 a 与 b 不相等，j 回退到 nextval 2 即 1 号位。",
            subcaption="t[4]='a' != t[2]='b'，j 回退到 nextval[2] = 1。"
        ) as tracker:
            step_retreat(1)

        # 步骤 6：i=4, j=1 -> t[4]='a' == t[1]='a' -> i=5, j=2. t[5]='b' == t[2]='b' -> 再次修正！nextval[5] = nextval[2] = 1
        with self.voiceover(
            text="比较第 4 个字符 a 与第 1 个字符 a 相等，i、j 加 1 得 i 为 5、j 为 2。此时第 5 个字符 b 与第 2 个字符 b 再次相同！触发修正：nextval 5 继承 nextval 2 的值，记为 1！",
            subcaption="i=5, j=2。t[5]='b' == t[2]='b' 再次相同！触发修正：nextval[5] = nextval[2] = 1！"
        ) as tracker:
            step_advance_same(2)
            computed_nextval[5] = 1

        # 步骤 7：i=5, j=2 -> t[5]='b' == t[2]='b' -> i=6, j=3. t[6]='c' != t[3]='a' -> nextval[6] = 3
        with self.voiceover(
            text="字符 b 与 b 相等，i、j 加 1 得 i 为 6、j 为 3。第 6 个字符 c 与第 3 个字符 a 不等，nextval 6 等于 3。",
            subcaption="t[5]==t[2]，i=6, j=3。t[6]='c' != t[3]='a'，nextval[6] = j = 3。"
        ) as tracker:
            step_advance_diff(match_compare=True)
            computed_nextval[6] = 3

        # 步骤 8：i=6, j=3 -> t[6]='c' != t[3]='a' -> j = nextval[3] = 0 （高光点：一步到位回退到0！）
        with self.voiceover(
            text="字符 c 与 a 不相等，此时注意：由于之前对 nextval 3 进行了修正，j 直接一步回退到 0 号位，成功跳过了无效回退！",
            subcaption="t[6] != t[3]，根据修正值 nextval[3]=0，j 直接一步回退到 0 号位！"
        ) as tracker:
            step_retreat(0)

        # 步骤 9：i=6, j=0 -> j==0, i=7, j=1. t[7]='a' == t[1]='a' -> 修正！nextval[7] = nextval[1] = 0
        with self.voiceover(
            text="j 为 0，i、j 加 1 得 i 为 7、j 为 1。第 7 个字符 a 与第 1 个字符 a 相同，触发修正，nextval 7 继承为 0！",
            subcaption="i=7, j=1。t[7]='a' == t[1]='a' 相同！触发修正：nextval[7] = nextval[1] = 0！"
        ) as tracker:
            step_advance_same(1)
            computed_nextval[7] = 0

        # 步骤 10：i=7, j=1 -> t[7]='a' == t[1]='a' -> i=8, j=2. t[8]='c' != t[2]='b' -> nextval[8] = 2
        with self.voiceover(
            text="字符 a 与 a 相等，i、j 加 1 得 i 为 8、j 为 2。第 8 个字符 c 与第 2 个字符 b 不等，nextval 8 等于 2。",
            subcaption="t[7]==t[1]，i=8, j=2。t[8]='c' != t[2]='b'，nextval[8] = j = 2。"
        ) as tracker:
            step_advance_diff(match_compare=True)
            computed_nextval[8] = 2

        # 步骤 11：i=8 -> 循环结束
        with self.voiceover(
            text="此时 i 等于 8，不再小于模式串长度 8，循环结束，最后返回计算完成的 nextval 数组。",
            subcaption="i=8 不再小于 8，循环结束，返回计算好的 nextval 数组。"
        ) as tracker:
            self.play(*get_track_anims(IDX_WHILE), run_time=0.3)
            self.play(Indicate(self.c_texts[IDX_WHILE], color=RED, scale_factor=1.0), run_time=0.3)
            self.play(*get_track_anims(IDX_RETURN), run_time=0.4)

        # ===== PHASE D4 — 结果展示 =====
        self.play(*get_track_anims(None), FadeOut(group_i), FadeOut(group_j), FadeOut(slot0), run_time=0.5)

        with self.voiceover(
            text="最终求得的 nextval 数组为：0、1、0、2、1、3、0、2。相比原始的 next 数组，有效减少了模式匹配中的无效回退。",
            subcaption="最终求得 nextval 数组：0 1 0 2 1 3 0 2，有效消除了模式匹配中的无效回退。"
        ) as tracker:
            self.play(*[next_rects[k].animate.set_color(GREEN) for k in range(1, 9)], run_time=0.6)
            self.wait(max(0.3, tracker.duration - 0.6))

        # ===== PHASE E — COMPLEXITY =====
        done_label = Text("nextval 修正值计算完成", font_size=24, font="Microsoft YaHei", color=GREEN).move_to(
            LEFT * 4.6 + DOWN * 2.35)
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(m)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(
            done_label, RIGHT, buff=0.6)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(1)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(
            time_box, RIGHT, buff=0.6)

        with self.voiceover(text="至此，计算 next 函数修正值的过程演示完毕。") as tracker:
            self.play(Write(done_label), run_time=max(0.5, tracker.duration))

        with self.voiceover(
            text="算法同样只需单向扫描模式串一次，时间复杂度为 O m；只使用了常数级的辅助变量，额外空间复杂度为 O 1。",
            subcaption="算法单向扫描模式串一次，时间复杂度为 O(m)；辅助空间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(time_box), FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是计算 next 函数修正值 Python 版的完整过程。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)


# Alias
GetNextvalPythonVideo = ContinuousGetNextvalPythonVideo
