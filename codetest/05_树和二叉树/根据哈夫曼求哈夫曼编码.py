# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class HuffmanCodeCreateVideo(VoiceoverScene):
    NODE_R = 0.32

    def make_node(self, label, center, weight_str, color=BLUE):
        c = Circle(radius=self.NODE_R, color=color, fill_color=color, fill_opacity=0.15, stroke_width=2.5).move_to(
            center)
        t_weight = Text(str(weight_str), font_size=18, color=WHITE, font="Consolas").move_to(center)
        t_id = Text(f"#{label}", font_size=13, color=GRAY_B, font="Consolas").next_to(c, UP, buff=0.06)
        g = VGroup(c, t_weight, t_id)
        g.circle = c
        return g

    def make_edge(self, p1, p2, edge_type, color=WHITE):
        """带有0/1标签的连线"""
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        start_pt = p1 + u * self.NODE_R
        end_pt = p2 - u * self.NODE_R
        line = Line(start_pt, end_pt, color=color, stroke_width=2.2)

        # 添加 0 或 1 的标签
        label_text = "0" if edge_type == 0 else "1"
        label = Text(label_text, font_size=16, color=YELLOW, font="Consolas").move_to(line.point_from_proportion(0.5))
        # 根据连线方向稍微偏移标签，避免与线重合
        perp_vec = np.array([-u[1], u[0], 0])
        label.shift(perp_vec * 0.2)

        g = VGroup(line, label)
        g.line = line
        g.label = label
        return g

    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("根据哈夫曼树求哈夫曼编码（有代码跟踪版）", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.3)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(text="本视频重点讲解哈夫曼编码算法的代码实现与逐行运行跟踪，如尚未掌握该算法的设计思路，建议首先观看 学习该算法的无代码跟踪版讲解视频。") as tracker:
            self.wait(tracker.duration)


        # ===== 准备所有的 Mobjects =====
        # 1. Code Block
        c_lines = [
            "void CreatHuffmanCode(HuffmanTree HT, HuffmanCode &HC, int n)",
            "{//逆向求每个字符的哈夫曼编码，存储在HC中",
            "    HC=new char*[n+1];        //分配字符编码表空间",
            "    cd=new char[n];           //分配临时存放编码的动态数组空间",
            "    cd[n-1]='\\0';             //编码结束符",
            "    for(i=1;i<=n;++i)         //逐个字符求哈夫曼编码",
            "    {",
            "        start=n-1;            //start指向最后结束符位置",
            "        c=i;f=HT[i].parent;   //f指向节点c的双亲节点",
            "        while(f!=0)           //从叶子节点向上回溯到根节点",
            "        {",
            "            --start;          //回溯一次start向前移一位",
            "            if(HT[f].lchild==c) cd[start]='0'; //c是左孩子则生成0",
            "            else cd[start]='1';                //c是右孩子则生成1",
            "            c=f;f=HT[f].parent; //继续向上回溯",
            "        }     //求出第i个字符的编码",
            "        HC[i]=new char[n-start];",
            "        strcpy(HC[i],&cd[start]); //编码从cd复制到HC当前行",
            "    }     //for",
            "    delete cd;    //释放临时空间",
            "}"
        ]
        IDX_HC_ALLOC = 2
        IDX_CD_ALLOC = 3
        IDX_CD_END = 4
        IDX_FOR = 5
        IDX_START = 7
        IDX_CF = 8
        IDX_WHILE = 9
        IDX_DECREMENT = 11
        IDX_LEFT = 12
        IDX_RIGHT = 13
        IDX_UPDATE = 14
        IDX_HC_COPY_ALLOC = 16
        IDX_STRCPY = 17
        IDX_DELETE = 19

        self.c_texts = []
        for line in c_lines:
            t = Text(line.lstrip(" "), font_size=10.0, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        SPACE_WIDTH = 0.06
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 6.0:
            code_group.scale_to_fit_width(6.0)
        if code_group.height > 4.5:
            code_group.scale_to_fit_height(4.5)

        code_bg = RoundedRectangle(corner_radius=0.15, height=code_group.get_height() + 0.35,
                                   width=code_group.get_width() + 0.5, color=GRAY, fill_opacity=0.1, stroke_width=1)
        code_bg.move_to(code_group)
        code_block = VGroup(code_bg, code_group)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line:
                if new_idx is None:
                    return [Wait(0.001)]
                return [self.c_texts[new_idx].animate.set_color(YELLOW)]
            anims = []
            if self.current_line is not None:
                anims.append(self.c_texts[self.current_line].animate.set_color(WHITE).scale(1 / 1.08, about_edge=LEFT))
            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW).scale(1.08, about_edge=LEFT))
                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.14).rotate(-PI / 2)
                    self.code_pointer.next_to(self.c_texts[new_idx], LEFT, buff=0.15)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.c_texts[new_idx], LEFT, buff=0.15)
                    anims.append(MoveToTarget(self.code_pointer))
                self.current_line = new_idx
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

        # 6. CD 临时数组
        cd_title = Text("临时数组 cd", font_size=16, color=YELLOW)
        cd_boxes = VGroup(*[Rectangle(width=0.6, height=0.6, color=YELLOW) for _ in range(4)]).arrange(RIGHT, buff=0)
        cd_group = VGroup(cd_title, cd_boxes).arrange(LEFT, buff=0.3)
        end_char = Text("\\0", font_size=16, color=WHITE, font="Consolas")

        # ==========================================
        # ===== 最新精细化相对/绝对混合布局 ============
        # ==========================================
        SCREEN_TOP = config.frame_y_radius
        SCREEN_BOTTOM = -config.frame_y_radius
        SCREEN_RIGHT = config.frame_x_radius
        SCREEN_LEFT = -config.frame_x_radius
        MARGIN = 0.3
        
        # 安全区域顶部（标题下方一点）
        top_y_limit = algo_title.get_bottom()[1] - 0.2
        max_height = top_y_limit - SCREEN_BOTTOM - MARGIN * 2

        # [右侧] 仅保留代码块。三栏使用明确的宽度和中心位置，避免
        # 长代码块向左侵入 HT 数组（原布局在 16:9 画幅下会发生遮挡）。
        if code_block.height > max_height:
            code_block.scale_to_fit_height(max_height)
        if code_block.width > 4.9:
            code_block.scale_to_fit_width(4.9)
        code_block.to_edge(RIGHT, buff=0.25).set_y((top_y_limit + SCREEN_BOTTOM) / 2)

        # [左侧顶部] 哈夫曼树上移
        if tree_group.height > max_height * 0.6:  
            tree_group.scale_to_fit_height(max_height * 0.6)
        tree_group.scale_to_fit_width(3.8)
        tree_group.to_edge(LEFT, buff=0.25)
        tree_group.set_y(top_y_limit - tree_group.height / 2) 

        # [左侧下方] HC编码表移动到树下面 (相对布局)
        hc_group.next_to(tree_group, DOWN, buff=0.4)
        if hc_group.get_bottom()[1] < SCREEN_BOTTOM + MARGIN:
            shift_hc = (SCREEN_BOTTOM + MARGIN) - hc_group.get_bottom()[1]
            hc_group.shift(UP * shift_hc)

        # [中侧顶部] HT数组上移
        if ht_group.height > max_height * 0.7:  
            ht_group.scale_to_fit_height(max_height * 0.7)
        ht_group.scale_to_fit_width(3.5)
        # Keep the table in its own middle column, with a visible gap from
        # both the tree and the code panel.
        ht_group.set_x(-1.05)
        ht_group.set_y(top_y_limit - ht_group.height / 2)

        # [中侧下方] CD临时数组放在HT数组下面 (相对布局)
        cd_group.next_to(ht_group, DOWN, buff=0.6)
        
        # 预先生成 start 指针进行防越界测试
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
            
        # 确保绑定
        end_char.move_to(cd_boxes[3].get_center())
        start_pointer.next_to(cd_boxes[start_idx], DOWN, buff=0.1)
        start_label.next_to(start_pointer, DOWN, buff=0.1)

        # ==========================================
        # ===== 正式播放动画序列 ====================
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

        with self.voiceover(text="下面我们结合具体的代码与哈夫曼树，来看看算法的执行过程。") as tracker:
            self.play(FadeIn(tree_group), FadeIn(ht_group), FadeIn(code_block), run_time=tracker.duration)

        with self.voiceover(text="画面中间的 HT 数组表示哈夫曼树在内存中的存储结构。在接下来的代码执行中，我们将从叶子结点出发，一步步向上回溯寻找双亲结点。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(
                text="第一步，分配存储4个字符编码的编码表空间HC，以及一个长度为n的临时数组cd，并将cd最后一位设为结束符。") as tracker:
            self.play(*get_track_anims(IDX_HC_ALLOC), FadeIn(hc_group), run_time=tracker.duration / 3)
            self.play(*get_track_anims(IDX_CD_ALLOC), FadeIn(cd_group), run_time=tracker.duration / 3)
            self.play(*get_track_anims(IDX_CD_END), Write(end_char), run_time=tracker.duration / 3)

        cd_chars = []  

        leaf_paths = {
            1: [(1, 7, '0')],
            2: [(2, 6, '0'), (6, 7, '1')],
            3: [(3, 5, '0'), (5, 6, '1'), (6, 7, '1')],
            4: [(4, 5, '1'), (5, 6, '1'), (6, 7, '1')]
        }
        leaf_codes = { 1: "0", 2: "10", 3: "110", 4: "111" }

        with self.voiceover(text="第二步，通过for循环，逐个求解所有n个字符的编码。") as tracker:
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
                        text=f"当f没有到达根结点时，循环执行。当前结点{child_idx}号，双亲{parent_idx}号，回溯一次，start向前移动。") as tracker:
                    self.play(*get_track_anims(IDX_WHILE))
                    start_idx -= 1
                    self.play(*get_track_anims(IDX_DECREMENT), pointer_group.animate.next_to(cd_boxes[start_idx], DOWN, buff=0.1),
                              run_time=tracker.duration)

                with self.voiceover(
                        text=f"结合HT数组的第 {parent_idx} 行，检查结点{child_idx}是左还是右孩子。") as tracker:
                    self.play(*get_track_anims(IDX_LEFT if bit == '0' else IDX_RIGHT))
                    col = 4 if bit == '0' else 5
                    
                    cell_box = ht_table.get_highlighted_cell((parent_idx + 1, col), color=BLUE)
                    cell_box.set_fill(BLUE, opacity=0.3).set_stroke(BLUE, width=3)
                    
                    cell_box2 = ht_table.get_highlighted_cell((child_idx + 1, 3), color=BLUE)
                    cell_box2.set_fill(BLUE, opacity=0.3).set_stroke(BLUE, width=3)
                    
                    self.play(FadeIn(cell_box), FadeIn(cell_box2), run_time=tracker.duration)
                    last_cell_box = VGroup(cell_box, cell_box2)
                with self.voiceover(
                        text=f"由于是{'左' if bit == '0' else '右'}分支，路径是 {bit}。存入数组 cd 的 start 位置。") as tracker:
                    edge_g = edges_dict[(parent_idx, child_idx)]
                    bit_char = Text(bit, font_size=20, color=GREEN, font="Consolas").move_to(cd_boxes[start_idx].get_center())
                    cd_chars.append(bit_char)
                    
                    self.play(
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

            with self.voiceover(text="为该字符分配空间，并将编码复制到HC表中。") as tracker:
                self.play(*get_track_anims(IDX_HC_COPY_ALLOC))

                result_code = leaf_codes[leaf_i]
                res_text = Text(result_code, font_size=18, color=YELLOW, font="Consolas").move_to(
                    hc_boxes[leaf_i - 1][1].get_center()) 
                temp_copy = VGroup(*cd_chars).copy()
                self.play(*get_track_anims(IDX_STRCPY), temp_copy.animate.move_to(hc_boxes[leaf_i - 1][1].get_center()).scale(0.8),
                          run_time=tracker.duration)
                self.remove(temp_copy)
                self.add(res_text)

            self.wait(0.5)

        with self.voiceover(
                text="第三步，循环处理完所有结点后，最后释放临时空间cd即可。") as tracker:
            self.play(*get_track_anims(IDX_DELETE), FadeOut(pointer_group), FadeOut(cd_group), FadeOut(end_char), *[FadeOut(c) for c in cd_chars],
                      *get_ht_highlight_anim(None, None),
                      run_time=tracker.duration)

        self.wait(1)

        # ===== 复杂度分析 =====
        time_box = VGroup(Text("时间复杂度: ", font_size=20, color=YELLOW), MathTex("O(n^2)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度: ", font_size=20, color=YELLOW), MathTex("O(n^2)", font_size=24, color=YELLOW)).arrange(RIGHT, buff=0.1)
        complexity_text = VGroup(time_box, space_box).arrange(RIGHT, buff=0.8)
        # Keep the complexity summary above the reserved subtitle band.
        complexity_text.to_edge(DOWN, buff=1.15)

        with self.voiceover(text="最后我们来分析算法的复杂度。最坏情况下哈夫曼树的高度为n，所以总时间复杂度为O(n^2)。而在空间上，需要存储所有编码，空间复杂度同样为O(n^2)。") as tracker:
            # Clear the dense trace layout before showing the summary so the
            # code panel, HT table and HC table cannot cover one another or
            # the complexity text.
            self.play(
                FadeOut(tree_group), FadeOut(ht_group), FadeOut(code_block),
                FadeOut(hc_group), FadeIn(complexity_text, shift=UP),
                run_time=tracker.duration,
            )

        self.wait(2)
