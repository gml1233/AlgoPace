# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
from codetest.tree_video_support import TreeVideoScene


# =========================================================================
# Python 版哈夫曼树与求解哈夫曼编码算法逻辑
# =========================================================================
INF = 0x3f3f3f3f


class HuffmanNode:
    def __init__(self, weight=0, parent=0, lchild=0, rchild=0):
        self.weight = weight  # 结点的权值
        self.parent = parent  # 结点的双亲
        self.lchild = lchild  # 结点的左孩子的下标
        self.rchild = rchild  # 结点的右孩子的下标


class HuffmanTree:
    def __init__(self, n, data):
        self.n = n  # 哈夫曼树的全部叶子结点个数
        self.data = data
        self.ht = [HuffmanNode(0, 0, 0, 0) for _ in range(0, 2 * n)]  # 0号单元未用，动态分配2*n个单元
        self.hc = [' ' for _ in range(0, self.n + 1)]  # 分配存储n个字符编码的编码表空间
        for i in range(1, n + 1):  # 初始化前n个单元中叶子结点的权值
            self.ht[i].weight = data[i - 1]

    def select(self, length):
        # 选择两个其双亲域为0且权值最小的结点
        min_val = INF  # 初始化最小值为无穷大
        s1 = 0  # 记录第一个权值最小结点下标
        s2 = 0  # 记录第二个权值最小结点下标
        for i in range(1, length + 1):  # 从1至length顺序查找出权值最小的结点
            if self.ht[i].weight < min_val and self.ht[i].parent == 0:
                min_val = self.ht[i].weight
                s1 = i
        temp = self.ht[s1].weight  # 将原值存放起来，先赋予最大值，防止s1被重复选择
        self.ht[s1].weight = INF
        min_val = INF
        for i in range(1, length + 1):  # 再次顺序查找出第二小的结点
            if self.ht[i].weight < min_val and self.ht[i].parent == 0:
                min_val = self.ht[i].weight
                s2 = i
        self.ht[s1].weight = temp  # 恢复原来的值
        return s1, s2

    def create_huffmantree(self, data=None):
        # 构造哈夫曼树
        if data is None:
            data = self.data
        if self.n <= 1:
            return
        m = 2 * self.n - 1
        for i in range(1, self.n + 1):  # 输入前n个单元中叶子结点的权值
            self.ht[i].weight = data[i - 1]
        for i in range(self.n + 1, m + 1):  # 通过n-1次的选择、删除、合并来创建哈夫曼树
            s_1, s_2 = self.select(i - 1)
            self.ht[s_1].parent = i
            self.ht[s_2].parent = i
            self.ht[i].lchild = s_1
            self.ht[i].rchild = s_2
            self.ht[i].weight = self.ht[s_1].weight + self.ht[s_2].weight

    def create_huffmancode(self):
        # 从叶子到根逆向求每个字符的哈夫曼编码，存储在编码表hc中
        cd = [' ' for _ in range(0, self.n - 1)]  # 分配临时存放每个字符编码的动态数组空间
        for i in range(1, self.n + 1):  # 逐个字符求哈夫曼编码
            start = self.n - 1  # start开始时指向最后，即编码结束符位置
            c = i
            f = self.ht[i].parent  # f指向结点c的双亲结点
            while f != 0:
                start -= 1  # 回溯一次start向前指一个位置
                if self.ht[f].lchild == c:
                    cd[start] = '0'  # 结点c是f的左孩子，则生成代码0
                else:
                    cd[start] = '1'  # 结点c是f的右孩子，则生成代码1
                c = f
                f = self.ht[f].parent  # 继续向上回溯
            self.hc[i] = ''.join(cd[start:])  # 为第i个字符编码分配空间

    def print_haffmancode(self):
        # 输出哈夫曼编码
        for i in range(1, self.n + 1):
            print(self.ht[i].weight, self.hc[i])


# =========================================================================
# Manim 动画场景
# =========================================================================
class HuffmanCodeCreatePythonVideo(TreeVideoScene):
    NODE_R = 0.32

    def make_node(self, label, center, weight_str, color=BLUE):
        c = Circle(radius=self.NODE_R, color=color, fill_opacity=0.15, stroke_width=2.5).move_to(center)
        t_weight = Text(str(weight_str), font_size=18, color=WHITE, font="Consolas").move_to(center)
        t_id = Text(f"#{label}", font_size=13, color=GRAY_B, font="Consolas").next_to(c, UP, buff=0.06)
        g = VGroup(c, t_weight, t_id)
        g.circle = c
        return g

    def make_edge(self, p1, p2, edge_type, color=WHITE):
        """带有 0/1 标签的连线"""
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        start_pt = p1 + u * self.NODE_R
        end_pt = p2 - u * self.NODE_R
        line = Line(start_pt, end_pt, color=color, stroke_width=2.2)

        # 添加 0 或 1 的标签
        label_text = "0" if edge_type == 0 else "1"
        label = Text(label_text, font_size=16, color=YELLOW, font="Consolas").move_to(line.point_from_proportion(0.5))
        perp_vec = np.array([-u[1], u[0], 0])
        label.shift(perp_vec * 0.2)

        g = VGroup(line, label)
        g.line = line
        g.label = label
        return g

    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 缩小右上角标识，避免覆盖标题并给代码块留出空间。
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(1.45).to_corner(UR, buff=0.05).shift(UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("根据哈夫曼树求哈夫曼编码 (Python版)", font_size=40, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.45)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(
            text="本节我们学习根据哈夫曼树求解哈夫曼编码算法的Python实现。我们将重点讲解该算法的代码实现与逐行运行跟踪。",
            subcaption="本节我们学习根据哈夫曼树求解哈夫曼编码算法的Python实现。我们将重点讲解该算法的代码实现与逐行运行跟踪。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== 准备所有 Mobjects =====
        # 1. Code Block
        py_lines = [
            "def create_huffmancode(self):",                      # 0
            "    # hc 分配存储编码表空间",                          # 1  IDX_HC_ALLOC
            "    cd = [' ' for _ in range(self.n - 1)]",          # 2  IDX_CD_ALLOC
            "    for i in range(1, self.n + 1):",                 # 3  IDX_FOR
            "        start = self.n - 1",                         # 4  IDX_START
            "        c = i; f = self.ht[i].parent",               # 5  IDX_CF
            "        while f != 0:",                              # 6  IDX_WHILE
            "            start -= 1",                             # 7  IDX_DECREMENT
            "            if self.ht[f].lchild == c:",             # 8  IDX_LEFT
            "                cd[start] = '0'",                    # 9  IDX_LEFT_VAL
            "            else:",                                  # 10 IDX_RIGHT
            "                cd[start] = '1'",                    # 11 IDX_RIGHT_VAL
            "            c = f; f = self.ht[f].parent",           # 12 IDX_UPDATE
            "        self.hc[i] = ''.join(cd[start:])",           # 13 IDX_HC_COPY
        ]
        IDX_HC_ALLOC = 1
        IDX_CD_ALLOC = 2
        IDX_FOR = 3
        IDX_START = 4
        IDX_CF = 5
        IDX_WHILE = 6
        IDX_DECREMENT = 7
        IDX_LEFT = 8
        IDX_LEFT_VAL = 9
        IDX_RIGHT = 10
        IDX_RIGHT_VAL = 11
        IDX_UPDATE = 12
        IDX_HC_COPY = 13

        self.py_texts = []
        for line in py_lines:
            stripped_line = line.lstrip(" ")
            # Consolas 没有中文字符，中文注释会被渲染成白色方块；
            # 含中文的整行改用系统中文字体，英文代码仍保持等宽字体。
            code_font = "Microsoft YaHei" if any("\u4e00" <= char <= "\u9fff" for char in stripped_line) else "Consolas"
            t = Text(stripped_line, font_size=10.5, font=code_font, color=WHITE)
            self.py_texts.append(t)

        code_group = VGroup(*self.py_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        SPACE_WIDTH = 0.07
        for i, line in enumerate(py_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.py_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 5.2:
            code_group.scale_to_fit_width(5.2)
        if code_group.height > 4.5:
            code_group.scale_to_fit_height(4.5)

        code_bg = RoundedRectangle(corner_radius=0.15, height=code_group.get_height() + 0.35,
                                   width=code_group.get_width() + 0.7, color=GRAY, fill_opacity=0.1, stroke_width=1)
        code_bg.move_to(code_group)
        code_block = VGroup(code_bg, code_group)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line:
                if new_idx is None:
                    return [Wait(0.001)]
                return [self.py_texts[new_idx].animate.set_color(YELLOW)]
            anims = []
            if self.current_line is not None:
                # 仅改变颜色，不放大文字，避免高亮长行溢出代码框。
                anims.append(self.py_texts[self.current_line].animate.set_color(WHITE))
            if new_idx is not None:
                anims.append(self.py_texts[new_idx].animate.set_color(YELLOW))
                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.14).rotate(-PI / 2)
                    self.code_pointer.next_to(self.py_texts[new_idx], LEFT, buff=0.15)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.py_texts[new_idx], LEFT, buff=0.15)
                    anims.append(MoveToTarget(self.code_pointer))
                self.current_line = new_idx
            else:
                if hasattr(self, 'code_pointer'):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, 'code_pointer')
                self.current_line = None
            if not anims:
                anims.append(Wait(0.001))
            return anims

        # 2. 哈夫曼树
        pos = {
            7: np.array([0, 2.0, 0]),
            1: np.array([-1.5, 0.5, 0]),
            6: np.array([1.5, 0.5, 0]),
            2: np.array([0.0, -1.0, 0]),
            5: np.array([3.0, -1.0, 0]),
            3: np.array([1.5, -2.5, 0]),
            4: np.array([4.5, -2.5, 0]),
        }

        nodes = {}
        nodes[1] = self.make_node(1, pos[1], 70, color=BLUE)
        nodes[2] = self.make_node(2, pos[2], 50, color=BLUE)
        nodes[3] = self.make_node(3, pos[3], 20, color=BLUE)
        nodes[4] = self.make_node(4, pos[4], 40, color=BLUE)
        nodes[5] = self.make_node(5, pos[5], 60, color=GREEN)
        nodes[6] = self.make_node(6, pos[6], 110, color=GREEN)
        nodes[7] = self.make_node(7, pos[7], 180, color=GREEN)

        edges = VGroup(
            self.make_edge(pos[7], pos[1], 0, GREEN),
            self.make_edge(pos[7], pos[6], 1, GREEN),
            self.make_edge(pos[6], pos[2], 0, GREEN),
            self.make_edge(pos[6], pos[5], 1, GREEN),
            self.make_edge(pos[5], pos[3], 0, GREEN),
            self.make_edge(pos[5], pos[4], 1, GREEN)
        )
        edges_dict = {
            (7, 1): edges[0], (7, 6): edges[1],
            (6, 2): edges[2], (6, 5): edges[3],
            (5, 3): edges[4], (5, 4): edges[5]
        }
        tree_group = VGroup(*nodes.values(), edges)

        # 3. HT 数组表 (哈夫曼树的存储结构)
        ht_data = [
            ["1", "70", "7", "0", "0"],
            ["2", "50", "6", "0", "0"],
            ["3", "20", "5", "0", "0"],
            ["4", "40", "5", "0", "0"],
            ["5", "60", "6", "3", "4"],
            ["6", "110", "7", "2", "5"],
            ["7", "180", "0", "1", "6"],
        ]
        ht_table = Table(
            ht_data,
            col_labels=[Text(x, font_size=24, font="Consolas") for x in ["i", "weight", "parent", "lchild", "rchild"]],
            element_to_mobject=lambda s: Text(s, font_size=24, font="Consolas"),
            include_outer_lines=True,
            line_config={"stroke_width": 1.5, "color": GRAY},
            v_buff=0.4,
            h_buff=0.5,
        )
        ht_table.scale(0.85)
        ht_title = Text("HT 数组", font_size=26, color=GREEN_B, weight=BOLD)

        # 4. 变量显示区 c 和 f
        var_c_text = Text("c = ?", font_size=18, color=YELLOW, font="Consolas")
        var_f_text = Text("f = ?", font_size=18, color=RED_A, font="Consolas")
        var_group = VGroup(var_c_text, var_f_text).arrange(RIGHT, buff=0.8)

        ht_group = VGroup(ht_title, ht_table, var_group).arrange(DOWN, buff=0.2)

        # 5. HC 编码表
        hc_title = Text("HC 编码表", font_size=16, color=BLUE_A)
        hc_boxes = VGroup()
        for i in range(1, 5):
            box = Rectangle(width=1.5, height=0.4, color=GRAY_B)
            label = Text(f"#{i}", font_size=14, color=GRAY, font="Consolas").next_to(box, LEFT, buff=0.1)
            hc_boxes.add(VGroup(label, box))
        hc_boxes.arrange(DOWN, buff=0.1)
        hc_group = VGroup(hc_title, hc_boxes).arrange(DOWN, buff=0.2)

        # 6. CD 临时数组 (3个数据单元 + 1个结束符位置)
        cd_title = Text("临时数组 cd", font_size=16, color=YELLOW)
        cd_rects = [Rectangle(width=0.6, height=0.6, color=YELLOW) for _ in range(3)]
        cd_end_rect = DashedVMobject(
            Rectangle(width=0.6, height=0.6, color=GRAY_B), num_dashes=12
        )
        cd_boxes = VGroup(*cd_rects, cd_end_rect).arrange(RIGHT, buff=0)
        cd_group = VGroup(cd_title, cd_boxes).arrange(LEFT, buff=0.3)
        end_char = Text("\\0", font_size=15, color=GRAY_A, font="Consolas")

        # ==========================================
        # ===== 相对/绝对混合布局 ==================
        # ==========================================
        SCREEN_BOTTOM = -config.frame_y_radius
        MARGIN = 0.3

        top_y_limit = algo_title.get_bottom()[1] - 0.2
        max_height = top_y_limit - SCREEN_BOTTOM - MARGIN * 2

        # [右侧] 代码块
        if code_block.height > max_height:
            code_block.scale_to_fit_height(max_height)
        if code_block.width > 4.9:
            code_block.scale_to_fit_width(4.9)
        code_block.to_edge(RIGHT, buff=0.25).set_y((top_y_limit + SCREEN_BOTTOM) / 2)

        # [左侧顶部] 哈夫曼树
        if tree_group.height > max_height * 0.6:
            tree_group.scale_to_fit_height(max_height * 0.6)
        tree_group.scale_to_fit_width(3.8)
        tree_group.to_edge(LEFT, buff=0.25)
        tree_group.set_y(top_y_limit - tree_group.height / 2)

        # [左侧下方] HC编码表
        hc_group.next_to(tree_group, DOWN, buff=0.4)
        if hc_group.get_bottom()[1] < SCREEN_BOTTOM + MARGIN:
            shift_hc = (SCREEN_BOTTOM + MARGIN) - hc_group.get_bottom()[1]
            hc_group.shift(UP * shift_hc)

        # [中侧顶部] HT数组
        if ht_group.height > max_height * 0.7:
            ht_group.scale_to_fit_height(max_height * 0.7)
        ht_group.scale_to_fit_width(3.5)
        ht_group.set_x(-1.05)
        ht_group.set_y(top_y_limit - ht_group.height / 2)

        # [中侧下方] CD临时数组
        cd_group.next_to(ht_group, DOWN, buff=0.6)

        # 预先生成 start 指针
        start_idx = 3
        start_pointer = Arrow(start=DOWN, end=UP, color=RED, max_tip_length_to_length_ratio=0.3).scale(0.5)
        start_pointer.next_to(cd_boxes[start_idx], DOWN, buff=0.1)
        start_label = Text("start", font_size=14, color=RED, font="Consolas").next_to(start_pointer, DOWN, buff=0.1)
        pointer_group = VGroup(start_pointer, start_label)

        test_group = VGroup(cd_group, pointer_group)
        if test_group.get_bottom()[1] < SCREEN_BOTTOM + MARGIN:
            shift_up = (SCREEN_BOTTOM + MARGIN) - test_group.get_bottom()[1]
            cd_group.shift(UP * shift_up)
            pointer_group.shift(UP * shift_up)

        end_char.move_to(cd_boxes[3].get_center())
        start_pointer.next_to(cd_boxes[start_idx], DOWN, buff=0.1)
        start_label.next_to(start_pointer, DOWN, buff=0.1)

        # ==========================================
        # ===== 动画序列播放 =======================
        # ==========================================
        self.current_ht_rows = []

        def get_ht_highlight_anim(current_c, current_f):
            anims = []
            for r in self.current_ht_rows:
                anims.append(ht_table.get_rows()[r].animate.set_color(WHITE))
            self.current_ht_rows = []

            if current_c is not None:
                self.current_ht_rows.append(current_c)
                anims.append(ht_table.get_rows()[current_c].animate.set_color(YELLOW))
            if current_f is not None and current_f != 0:
                self.current_ht_rows.append(current_f)
                anims.append(ht_table.get_rows()[current_f].animate.set_color(RED))

            if current_c is not None:
                new_c_text = Text(f"c = {current_c}", font_size=18, color=YELLOW, font="Consolas").move_to(var_c_text)
                anims.append(Transform(var_c_text, new_c_text))
            if current_f is not None:
                new_f_text = Text(f"f = {current_f}", font_size=18, color=RED_A, font="Consolas").move_to(var_f_text)
                anims.append(Transform(var_f_text, new_f_text))

            return anims

        with self.voiceover(text="下面我们结合具体的代码与哈夫曼树，来看看求解哈夫曼编码算法的执行过程。") as tracker:
            self.play(FadeIn(tree_group), FadeIn(ht_group), FadeIn(code_block), run_time=tracker.duration)

        with self.voiceover(text="画面中间的 HT 数组表示哈夫曼树在内存中的存储结构。在接下来的代码执行中，我们将从叶子结点出发，一步步向上回溯寻找双亲结点。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(
            text="第一步，初始化分配存储4个字符编码的编码表空间HC，以及一个长度为n减1的临时列表cd，并将start指针初始指向结束符位置。"
        ) as tracker:
            dur = tracker.duration / 3
            self.play(*get_track_anims(IDX_HC_ALLOC), FadeIn(hc_group), run_time=dur)
            self.play(*get_track_anims(IDX_CD_ALLOC), FadeIn(cd_group), run_time=dur)
            self.play(*get_track_anims(IDX_START), Write(end_char), run_time=dur)

        cd_chars = []
        hc_results = VGroup()  # 将生成的编码与表格一起移动或淡出。

        leaf_paths = {
            1: [(1, 7, '0')],
            2: [(2, 6, '0'), (6, 7, '1')],
            3: [(3, 5, '0'), (5, 6, '1'), (6, 7, '1')],
            4: [(4, 5, '1'), (5, 6, '1'), (6, 7, '1')]
        }
        leaf_codes = {1: "0", 2: "10", 3: "110", 4: "111"}

        with self.voiceover(text="第二步，通过for循环，逐个求解所有n个字符的哈夫曼编码。") as tracker:
            self.play(*get_track_anims(IDX_FOR), run_time=tracker.duration)

        for leaf_i in range(1, 5):
            path = leaf_paths[leaf_i]
            first_f = path[0][1]

            if leaf_i == 1:
                vo_text = f"首先求解第{leaf_i}个结点的编码。设置start记录位置，c指向当前结点，f查询为双亲。同时高亮树与HT数组对应行。"
            else:
                vo_text = f"接着求解第{leaf_i}个结点的编码。初始化start，c指向当前结点，f指向双亲。"

            with self.voiceover(text=vo_text) as tracker:
                self.play(*get_track_anims(IDX_START), run_time=0.2)
                if cd_chars:
                    self.play(*[FadeOut(c) for c in cd_chars], run_time=0.2)
                    cd_chars.clear()

                start_idx = 3
                if leaf_i == 1:
                    self.play(FadeIn(pointer_group), run_time=0.2)
                else:
                    self.play(pointer_group.animate.next_to(cd_boxes[start_idx], DOWN, buff=0.1), run_time=0.2)

                self.play(
                    *get_track_anims(IDX_CF),
                    *get_ht_highlight_anim(leaf_i, first_f),
                    Indicate(nodes[leaf_i].circle, color=RED, scale_factor=1.2),
                    run_time=max(0.1, tracker.duration - 0.6)
                )

            self.play(
                nodes[leaf_i].circle.animate.set_stroke(RED).set_fill(RED, 0.5),
                nodes[first_f].circle.animate.set_stroke(RED).set_fill(RED, 0.5),
                run_time=0.3
            )
            last_cell_box = None

            for child_idx, parent_idx, bit in path:
                if last_cell_box:
                    self.play(FadeOut(last_cell_box), run_time=0.2)
                    last_cell_box = None

                with self.voiceover(
                    text=f"当f没有到达根结点时，循环执行。当前结点{child_idx}号，双亲{parent_idx}号，回溯一次，start向前移动。"
                ) as tracker:
                    self.play(*get_track_anims(IDX_WHILE))
                    start_idx -= 1
                    self.play(*get_track_anims(IDX_DECREMENT), pointer_group.animate.next_to(cd_boxes[start_idx], DOWN, buff=0.1),
                              run_time=tracker.duration)

                with self.voiceover(
                    text=f"结合HT数组的第 {parent_idx} 行，检查结点{child_idx}是左还是右孩子。"
                ) as tracker:
                    self.play(*get_track_anims(IDX_LEFT if bit == '0' else IDX_RIGHT))
                    col = 4 if bit == '0' else 5

                    cell_box = ht_table.get_highlighted_cell((parent_idx + 1, col), color=BLUE)
                    cell_box.set_fill(BLUE, opacity=0.3).set_stroke(BLUE, width=3)

                    cell_box2 = ht_table.get_highlighted_cell((child_idx + 1, 3), color=BLUE)
                    cell_box2.set_fill(BLUE, opacity=0.3).set_stroke(BLUE, width=3)

                    self.play(FadeIn(cell_box), FadeIn(cell_box2), run_time=tracker.duration)
                    last_cell_box = VGroup(cell_box, cell_box2)

                with self.voiceover(
                    text=f"由于是{'左' if bit == '0' else '右'}分支，路径是 {bit}。存入数组 cd 的 start 位置。"
                ) as tracker:
                    edge_g = edges_dict[(parent_idx, child_idx)]
                    bit_char = Text(bit, font_size=20, color=GREEN, font="Consolas").move_to(cd_boxes[start_idx].get_center())
                    cd_chars.append(bit_char)

                    self.play(
                        *get_track_anims(IDX_LEFT_VAL if bit == '0' else IDX_RIGHT_VAL),
                        Indicate(edge_g.line, color=YELLOW, scale_factor=1.1),
                        Indicate(edge_g.label, color=YELLOW, scale_factor=1.5),
                        Write(bit_char),
                        run_time=tracker.duration
                    )

                next_f = 0
                for path_c, path_p, _ in path:
                    if path_c == parent_idx:
                        next_f = path_p

                if next_f != 0:
                    with self.voiceover(text="继续向上回溯，改变c和f的值。") as tracker:
                        old_color = BLUE if child_idx <= 4 else GREEN
                        self.play(
                            *get_track_anims(IDX_UPDATE),
                            *get_ht_highlight_anim(parent_idx, next_f),
                            nodes[child_idx].circle.animate.set_stroke(old_color).set_fill(old_color, 0.15),
                            nodes[parent_idx].circle.animate.set_stroke(RED).set_fill(RED, 0.5),
                            nodes[next_f].circle.animate.set_stroke(RED).set_fill(RED, 0.5),
                            run_time=tracker.duration
                        )
                else:
                    with self.voiceover(text="改变c和f的值。") as tracker:
                        old_color = BLUE if child_idx <= 4 else GREEN
                        self.play(
                            *get_track_anims(IDX_UPDATE),
                            *get_ht_highlight_anim(parent_idx, next_f),
                            nodes[child_idx].circle.animate.set_stroke(old_color).set_fill(old_color, 0.15),
                            nodes[parent_idx].circle.animate.set_stroke(RED).set_fill(RED, 0.5),
                            run_time=tracker.duration
                        )

            if last_cell_box:
                self.play(FadeOut(last_cell_box), run_time=0.2)
                last_cell_box = None

            with self.voiceover(text="当双亲f为零时，查询发现已到达根结点，该结点回溯结束。") as tracker:
                self.play(*get_track_anims(IDX_WHILE), *get_ht_highlight_anim(parent_idx, 0), run_time=tracker.duration)
                self.play(nodes[parent_idx].circle.animate.set_stroke(GREEN).set_fill(GREEN, 0.15), run_time=0.3)

            with self.voiceover(text="利用切片取出从start开始的编码，存入HC表中。") as tracker:
                result_code = leaf_codes[leaf_i]
                res_text = Text(result_code, font_size=18, color=YELLOW, font="Consolas").move_to(
                    hc_boxes[leaf_i - 1][1].get_center())
                temp_copy = VGroup(*cd_chars).copy()
                self.play(*get_track_anims(IDX_HC_COPY), temp_copy.animate.move_to(hc_boxes[leaf_i - 1][1].get_center()).scale(0.8),
                          run_time=tracker.duration)
                self.remove(temp_copy)
                self.add(res_text)
                hc_results.add(res_text)

            self.wait(0.5)

        with self.voiceover(
            text="第三步，循环处理完所有结点后，每个字符的哈夫曼编码均已生成并保存在HC列表中。"
        ) as tracker:
            self.play(*get_track_anims(None), FadeOut(pointer_group), FadeOut(cd_group), FadeOut(end_char), *[FadeOut(c) for c in cd_chars],
                      *get_ht_highlight_anim(None, None),
                      run_time=tracker.duration)

        self.wait(1)

        # ===== 复杂度分析 =====
        # 先完成画面切换，再开始复杂度旁白。
        self.play(FadeOut(tree_group), FadeOut(ht_group), FadeOut(code_block),
                  FadeOut(hc_group), FadeOut(hc_results), run_time=0.6)
        time_box = VGroup(Text("时间复杂度: ", font_size=20, font="Microsoft YaHei", color=YELLOW), MathTex("O(n^2)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度: ", font_size=20, font="Microsoft YaHei", color=YELLOW), MathTex("O(n^2)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        complexity_text = VGroup(time_box, space_box).arrange(RIGHT, buff=0.8)
        complexity_text.move_to(UP * 0.4)

        with self.voiceover(text="最后我们来分析算法的复杂度。最坏情况下哈夫曼树的高度为n，每个叶子结点回溯需要O(n)，n个叶子总时间复杂度为O(n^2)。空间复杂度同样为O(n^2)。") as tracker:
            self.play(FadeIn(complexity_text, shift=UP), run_time=0.6)

        self.wait(2)


ContinuousHuffmanCodeCreatePythonVideo = HuffmanCodeCreatePythonVideo
