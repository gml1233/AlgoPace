# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class HuffmanTreeCreateVideo(VoiceoverScene):
    NODE_R = 0.32

    def make_node(self, label, center, weight_str, color=BLUE):
        """工厂方法：绘制一个哈夫曼树树结点（双层文本：上方为单元号，下方圆圈内为权值）"""
        c = Circle(radius=self.NODE_R, color=color, fill_color=color, fill_opacity=0.15, stroke_width=2.5).move_to(
            center)
        t_weight = Text(str(weight_str), font_size=18, color=WHITE).move_to(center)
        t_id = Text(f"#{label}", font_size=13, color=GRAY_B).next_to(c, UP, buff=0.06)

        g = VGroup(c, t_weight, t_id)
        g.circle = c
        g.t_weight = t_weight
        g.t_id = t_id
        return g

    def make_edge(self, p1, p2, color=WHITE):
        """高精度触边指针连线，防止连线穿透圆圈内部"""
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        return Line(p1 + u * self.NODE_R, p2 - u * self.NODE_R, color=color, stroke_width=2.2)

    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("哈夫曼树的构造算法", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.5)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(
                text="本节我们来学习铪夫曼树的构造算法，该算法是根据给定的 n 个权值，构造一颗哈夫曼树。",
                subcaption="本节我们来学习哈夫曼树的构造算法，该算法是根据给定的 n 个权值，构造一颗哈夫曼树。"
        ) as tracker:
            self.wait(tracker.duration)

        # ===== 生活实例：公司部门合并 =====
        title_analogy = Text("生活实例：公司部门合并", font_size=32, color=BLUE).next_to(algo_title, DOWN, buff=0.3)
        
        # 部门框位置
        d_pos = {
            1: np.array([-3, -2.05, 0]),
            2: np.array([-1, -2.05, 0]),
            3: np.array([1, -2.05, 0]),
            4: np.array([3, -2.05, 0]),
            5: np.array([-2, -0.72, 0]),
            6: np.array([-0.5, 0.52, 0]),
            7: np.array([1.25, 1.72, 0])
        }
        
        def make_dept(label, center, color=GREEN):
            box = RoundedRectangle(corner_radius=0.1, width=1.2, height=0.6, color=color, fill_opacity=0.2).move_to(center)
            txt = Text(f"{label}人", font_size=20, font="Microsoft YaHei").move_to(center)
            return VGroup(box, txt)

        dept_5 = make_dept(5, d_pos[1])
        dept_2 = make_dept(2, d_pos[2])
        dept_9 = make_dept(9, d_pos[3])
        dept_13 = make_dept(13, d_pos[4])
        
        analogy_bg = VGroup(title_analogy, dept_5, dept_2, dept_9, dept_13)

        with self.voiceover(text="哈夫曼树的构造过程，就像是公司内部不同部门的合并重组。") as tracker:
            self.play(FadeIn(title_analogy), run_time=max(0.1, tracker.duration*0.3))
            
        with self.voiceover(text="假设我们有四个独立的小部门，员工人数分别为5、2、9、13。") as tracker:
            self.play(FadeIn(dept_5), FadeIn(dept_2), FadeIn(dept_9), FadeIn(dept_13), run_time=tracker.duration)

        dept_7 = make_dept(7, d_pos[5], color=YELLOW)
        arrow_2_7 = Arrow(dept_2.get_top(), dept_7.get_bottom(), color=WHITE, buff=0.1)
        arrow_5_7 = Arrow(dept_5.get_top(), dept_7.get_bottom(), color=WHITE, buff=0.1)

        with self.voiceover(text="每次我们会挑选人数最少的两个部门进行合并。首先挑选2人和5人的部门，合并成一个7人的新部门。") as tracker:
            self.play(Indicate(dept_2[0], color=YELLOW), Indicate(dept_5[0], color=YELLOW), run_time=max(0.1, tracker.duration*0.3))
            self.play(GrowArrow(arrow_2_7), GrowArrow(arrow_5_7), run_time=max(0.1, tracker.duration*0.3))
            self.play(FadeIn(dept_7, shift=UP*0.2), run_time=max(0.1, tracker.duration*0.4))

        dept_16 = make_dept(16, d_pos[6], color=ORANGE)
        arrow_7_16 = Arrow(dept_7.get_top(), dept_16.get_bottom(), color=WHITE, buff=0.1)
        arrow_9_16 = Arrow(dept_9.get_top(), dept_16.get_bottom(), color=WHITE, buff=0.1)

        with self.voiceover(text="接着在剩余部门中再次挑选人数最少的两个，也就是7和9，合并为16人的大部门。") as tracker:
            self.play(Indicate(dept_7[0], color=ORANGE), Indicate(dept_9[0], color=ORANGE), run_time=max(0.1, tracker.duration*0.3))
            self.play(GrowArrow(arrow_7_16), GrowArrow(arrow_9_16), run_time=max(0.1, tracker.duration*0.3))
            self.play(FadeIn(dept_16, shift=UP*0.2), run_time=max(0.1, tracker.duration*0.4))

        dept_29 = make_dept(29, d_pos[7], color=RED)
        arrow_16_29 = Arrow(dept_16.get_top(), dept_29.get_bottom(), color=WHITE, buff=0.1)
        arrow_13_29 = Arrow(dept_13.get_top(), dept_29.get_bottom(), color=WHITE, buff=0.1)

        with self.voiceover(text="最后将剩下的16和13合并，形成一个29人的总公司。") as tracker:
            self.play(Indicate(dept_16[0], color=RED), Indicate(dept_13[0], color=RED), run_time=max(0.1, tracker.duration*0.3))
            self.play(GrowArrow(arrow_16_29), GrowArrow(arrow_13_29), run_time=max(0.1, tracker.duration*0.3))
            self.play(FadeIn(dept_29, shift=UP*0.2), run_time=max(0.1, tracker.duration*0.4))

        with self.voiceover(text="这种每次挑选最小的两个节点进行合并、自底向上构建的过程，正是哈夫曼树的核心思想。") as tracker:
            self.wait(tracker.duration)

        analogy_group = VGroup(analogy_bg, dept_7, arrow_2_7, arrow_5_7, dept_16, arrow_7_16, arrow_9_16, dept_29, arrow_16_29, arrow_13_29)
        self.play(FadeOut(analogy_group))

        # ===== 核心思想总结 =====
        summary_title = Text("核心思想", font_size=36, color=YELLOW).shift(UP*1.5)
        summary_body = Text(
            "哈夫曼树的构造本质上是一个 贪心策略 的 自底向上 合并过程：\n\n"
            "1. 初始化：将所有结点视为 独立的树\n"
            "2. 贪心选择：每次选出权值 最小 的两棵树\n"
            "3. 合并：生成一个新结点作为它们的 双亲，权值为两者之和\n"
            "4. 重复此过程，直到森林中只剩下 一棵树（即哈夫曼树）",
            font_size=28, font="Microsoft YaHei", line_spacing=1.5,
            t2c={
                "贪心策略": RED,
                "自底向上": RED,
                "独立的树": GREEN,
                "最小": ORANGE,
                "双亲": BLUE,
                "一棵树": GREEN
            }
        ).next_to(summary_title, DOWN, buff=0.8)
        
        summary_box = SurroundingRectangle(summary_body, color=WHITE, buff=0.5, corner_radius=0.2)
        summary_group = VGroup(summary_title, summary_body, summary_box)

        with self.voiceover(text="通过这个实例我们可以总结出，哈夫曼树构造的核心思想，本质上是一个基于贪心策略的自底向上合并过程。") as tracker:
            self.play(FadeIn(summary_title, shift=DOWN), run_time=max(0.1, tracker.duration*0.3))
            self.play(Create(summary_box), run_time=max(0.1, tracker.duration*0.3))
            self.play(Write(summary_body), run_time=max(0.1, tracker.duration*0.4))

        with self.voiceover(text="算法一开始将所有节点视为独立的树，每次贪心地挑选权值最小的两棵树，合并成一棵新树。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="如此循环往复，直到所有节点被合并为一棵完整的哈夫曼树。接下来我们看看具体的代码实现。") as tracker:
            self.play(FadeOut(summary_group), run_time=tracker.duration)


        # ===== PHASE B — CODE BLOCK CONFIG =====
        c_lines = [
            "void CreateHuffmanTree(HuffmanTree &HT,int n)",
            "{//构造哈夫曼树HT",
            "    if(n<=1) return;",
            "    m=2*n-1;",
            "    HT=new HTNode[m+1];       //动态分配m+1个单元，HT[m]为根节点",
            "    for(i=1;i<=m;++i)         //双亲、左右孩子下标初始化为0",
            "    {HT[i].parent=0;HT[i].lchild=0;HT[i].rchild=0;}",
            "    for(i=1;i<=n;++i)         //输入前n个叶子节点的权值",
            "        cin>>HT[i].weight;",
            "    //- - - - 初始化结束，开始创建哈夫曼树 - - - -",
            "    for(i=n+1;i<=m;++i)",
            "    {//通过n-1次选择、合并创建哈夫曼树",
            "        Select(HT,i-1,s1,s2);",
            "        //选择双亲为0且权值最小的两节点s1和s2",
            "        HT[s1].parent=i;HT[s2].parent=i;",
            "        //得到新节点i，s1与s2的双亲设为i",
            "        HT[i].lchild=s1;HT[i].rchild=s2; //s1,s2分别作为左右孩子",
            "        HT[i].weight=HT[s1].weight+HT[s2].weight; //i权值为左右孩子之和",
            "    }       //for",
            "}"
        ]
        IDX_ALLOC = 4
        IDX_INIT = 5
        IDX_INPUT = 7
        IDX_LOOP = 10
        IDX_SELECT = 12
        IDX_PARENT = 14
        IDX_CHILD = 16
        IDX_WEIGHT = 17

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=10.0, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        SPACE_WIDTH = 0.06
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 6.3:
            code_group.scale_to_fit_width(6.3)
        if code_group.height > 4.5:
            code_group.scale_to_fit_height(4.5)

        code_bg = RoundedRectangle(corner_radius=0.12, height=code_group.get_height() + 0.35,
                                   width=code_group.get_width() + 0.5, color=GRAY, fill_opacity=0.1, stroke_width=1)
        code_bg.move_to(code_group)
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.15).to_edge(RIGHT, buff=0.3)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line: return [Wait(0.001)]
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
            else:
                if hasattr(self, 'code_pointer'):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, 'code_pointer')
                self.current_line = None
            return anims

        # ===== PHASE C — 静态表格与拓扑数据图初始化 =====
        pos = {
            2: np.array([-5.4, -0.2, 0]),
            1: np.array([-4.2, -0.2, 0]),
            3: np.array([-2.6, -0.2, 0]),
            4: np.array([-0.6, -0.2, 0]),
            5: np.array([-4.8, 0.7, 0]),
            6: np.array([-3.7, 1.6, 0]),
            7: np.array([-2.15, 2.5, 0]),
        }

        rows, cols = 8, 5
        w_head, w_cell = 0.65, 0.9
        cell_h = 0.27
        table_cells = VGroup()
        grid_data = {}
        grid_boxes = {}

        headers = ["号", "权值", "双亲", "左孩子", "右孩子"]
        for r in range(rows):
            for c in range(cols):
                cell_box = Rectangle(width=w_head if c == 0 else w_cell, height=cell_h, color=GRAY_B, stroke_width=1.5)
                if c == 0:
                    x_pos = -5.7
                else:
                    x_pos = -4.925 + (c - 1) * w_cell

                y_pos = -(0.78 + r * cell_h)
                cell_box.move_to([x_pos, y_pos, 0])

                if r == 0:
                    txt = Text(headers[c], font_size=11, font="Microsoft YaHei", color=YELLOW)
                    txt.move_to(cell_box.get_center())
                    table_cells.add(cell_box, txt)
                elif c == 0:
                    txt = Text(str(r), font_size=11, font="Microsoft YaHei", color=YELLOW)
                    txt.move_to(cell_box.get_center())
                    table_cells.add(cell_box, txt)
                else:
                    txt = Text("0", font_size=11, font="Microsoft YaHei", color=GRAY)
                    txt.move_to(cell_box.get_center())
                    table_cells.add(cell_box, txt)
                    grid_data[(c, r)] = txt
                    grid_boxes[(c, r)] = cell_box

        table_title = Text("HT静态数组存储结构", font_size=16, font="Microsoft YaHei", color=BLUE_A).next_to(
            table_cells, UP, buff=0.15).align_to(table_cells, LEFT)
        table_group = VGroup(table_cells, table_title)

        with self.voiceover(text="右侧是构造算法的核心代码。我们以包含四个叶子结点的森林为例开展演示。") as tracker:
            self.play(FadeIn(code_block), FadeIn(table_group), run_time=tracker.duration)

        # 1. 初始化分配单元
        with self.voiceover(
                text="第一步，初始化。四个叶子结点会产生一共七个单元。") as tracker:
            self.play(*get_track_anims(IDX_ALLOC), run_time=tracker.duration)

        with self.voiceover(
                text="随后，将一到七号所有单元的双亲、左孩子、右孩子下标全部初始化为零。") as tracker:
            self.play(*get_track_anims(IDX_INIT), run_time=tracker.duration)

        # 2. 读入前 n 个叶子结点的权值
        leaf_weights = {1: 5, 2: 2, 3: 9, 4: 13}
        tree_nodes = {}

        with self.voiceover(text="接下来读入前四个单元中叶子结点的原始权值，它们分别是5、2、9、13。") as tracker:
            self.play(*get_track_anims(IDX_INPUT), run_time=0.4)

            spawn_anims = []
            for idx, wt in leaf_weights.items():
                new_txt = Text(str(wt), font_size=13, font="Microsoft YaHei", color=WHITE).move_to(
                    grid_data[(1, idx)].get_center())
                spawn_node = self.make_node(idx, pos[idx], wt)
                tree_nodes[idx] = spawn_node
                spawn_anims.extend([
                    Transform(grid_data[(1, idx)], new_txt),
                    FadeIn(spawn_node, shift=UP * 0.3)
                ])
            self.play(*spawn_anims, run_time=max(0.5, tracker.duration - 0.4))
        self.wait(0.2)

        # ===== PHASE D — 创建哈夫曼树的大循环演示 =====
        def update_grid(r, c, val_str, txt_color=GREEN):
            new_t = Text(str(val_str), font_size=11, font="Microsoft YaHei", color=txt_color).move_to(
                grid_data[(r, c)].get_center())
            return AnimationGroup(
                Transform(grid_data[(r, c)], new_t),
                Indicate(grid_boxes[(r, c)], color=YELLOW, scale_factor=1.08),
            )

        # ---------------- 第一轮合并：i = 5 ----------------
        with self.voiceover(text="第二步，创建哈夫曼树。第一轮，开始构建第一个结点") as tracker:
            self.play(*get_track_anims(IDX_LOOP), run_time=tracker.duration)

        with self.voiceover(
                text="在当前双亲域为零的结点中，挑选出权值最小的两个结点，即2号和1号。") as tracker:
            self.play(*get_track_anims(IDX_SELECT), run_time=0.4)
            self.play(
                Indicate(tree_nodes[2].circle, color=YELLOW, scale_factor=1.2),
                Indicate(tree_nodes[1].circle, color=YELLOW, scale_factor=1.2),
                run_time=max(0.6, tracker.duration - 0.4)
            )

        with self.voiceover(
                text="将这两个被选结点的双亲域下标修改为当前新单元的编号5，标志着它们被从森林中删除并合并。") as tracker:
            self.play(
                *get_track_anims(IDX_PARENT),
                update_grid(2, 1, "5"), update_grid(2, 2, "5"),
                run_time=tracker.duration
            )

        node5 = self.make_node(5, pos[5], 7, color=GREEN)
        tree_nodes[5] = node5
        edge_5_2 = self.make_edge(pos[5], pos[2], color=GREEN)
        edge_5_1 = self.make_edge(pos[5], pos[1], color=GREEN)

        with self.voiceover(text="在5号单元中，记录它的左孩子为2号，右孩子为1号。") as tracker:
            self.play(
                *get_track_anims(IDX_CHILD),
                update_grid(3, 5, "2"), update_grid(4, 5, "1"),
                run_time=tracker.duration
            )

        with self.voiceover(
                text="最后将左右孩子的权值相加，计算出5号新结点的权值为七。") as tracker:
            self.play(
                *get_track_anims(IDX_WEIGHT),
                FadeIn(node5, shift=UP * 0.2), Create(edge_5_2), Create(edge_5_1),
                update_grid(1, 5, "7", txt_color=GREEN),
                run_time=tracker.duration
            )
        self.wait(0.3)

        # ---------------- 第二轮合并：i = 6 ----------------
        with self.voiceover(text="第二轮，构建第二个结点。") as tracker:
            self.play(*get_track_anims(IDX_LOOP), run_time=tracker.duration)

        with self.voiceover(text="在双亲为零的结点中，当前权值最小的两个树根是5号和3号。") as tracker:
            self.play(*get_track_anims(IDX_SELECT), run_time=0.4)
            self.play(
                Indicate(tree_nodes[5].circle, color=YELLOW, scale_factor=1.2),
                Indicate(tree_nodes[3].circle, color=YELLOW, scale_factor=1.2),
                run_time=max(0.6, tracker.duration - 0.4)
            )

        with self.voiceover(text="将5号和3号结点的双亲域下标均由0改为6。") as tracker:
            self.play(
                *get_track_anims(IDX_PARENT),
                update_grid(2, 5, "6"), update_grid(2, 3, "6"),
                run_time=tracker.duration
            )

        node6 = self.make_node(6, pos[6], 16, color=GREEN)
        tree_nodes[6] = node6
        edge_6_5 = self.make_edge(pos[6], pos[5], color=GREEN)
        edge_6_3 = self.make_edge(pos[6], pos[3], color=GREEN)

        with self.voiceover(text="记录6号结点的左孩子为5号，右孩子为3号。") as tracker:
            self.play(
                *get_track_anims(IDX_CHILD),
                update_grid(3, 6, "5"), update_grid(4, 6, "3"),
                run_time=tracker.duration
            )

        with self.voiceover(text="将两者的权值7和9相加，得到6号新结点的权值为16。") as tracker:
            self.play(
                *get_track_anims(IDX_WEIGHT),
                FadeIn(node6, shift=UP * 0.2), Create(edge_6_5), Create(edge_6_3),
                update_grid(1, 6, "16", txt_color=GREEN),
                run_time=tracker.duration
            )
        self.wait(0.3)

        # ---------------- 第三轮合并：i = 7 ----------------
        with self.voiceover(text="最后一轮循环，构建最后一个结点") as tracker:
            self.play(*get_track_anims(IDX_LOOP), run_time=tracker.duration)

        with self.voiceover(text="找出目前森林中唯二双亲为零的两个树根，它们是4号和6号。") as tracker:
            self.play(*get_track_anims(IDX_SELECT), run_time=0.4)
            self.play(
                Indicate(tree_nodes[4].circle, color=YELLOW, scale_factor=1.2),
                Indicate(tree_nodes[6].circle, color=YELLOW, scale_factor=1.2),
                run_time=max(0.6, tracker.duration - 0.4)
            )

        with self.voiceover(text="将4号和6号结点的双亲域下标全部更改为7。") as tracker:
            self.play(
                *get_track_anims(IDX_PARENT),
                update_grid(2, 4, "7"), update_grid(2, 6, "7"),
                run_time=tracker.duration
            )

        node7 = self.make_node(7, pos[7], 29, color=GREEN)
        tree_nodes[7] = node7
        edge_7_4 = self.make_edge(pos[7], pos[4], color=GREEN)
        edge_7_6 = self.make_edge(pos[7], pos[6], color=GREEN)

        with self.voiceover(text="在表格中记录7号结点的左孩子为4号，右孩子为6号。") as tracker:
            self.play(
                *get_track_anims(IDX_CHILD),
                update_grid(3, 7, "4"), update_grid(4, 7, "6"),
                run_time=tracker.duration
            )

        with self.voiceover(text="将权值13和16累加，最终计算出根结点的权值为29。") as tracker:
            self.play(
                *get_track_anims(IDX_WEIGHT),
                FadeIn(node7, shift=UP * 0.2), Create(edge_7_4), Create(edge_7_6),
                update_grid(1, 7, "29", txt_color=GREEN),
                run_time=tracker.duration
            )
        self.wait(0.4)

        # ===== PHASE E — COMPLEXITY ANALYSIS =====
        self.play(*get_track_anims(None), FadeOut(algo_title), run_time=0.4)

        time_box = VGroup(Text("时间复杂度：", font_size=18, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(n^2)", font_size=20, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=18, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(n)", font_size=20, color=YELLOW)).arrange(RIGHT, buff=0.1)

        # 【核心修改点】垂直排列复杂度面板，并通过 next_to 绑定在 table_cells 的右侧安全区
        summary = VGroup(time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        summary.next_to(table_cells, RIGHT, buff=0.6)

        with self.voiceover(
                text="由于每次合并都需要在剩余未处理的结点中遍历搜索最小值，n减一次的选择共耗费平方级的时间，因此时间复杂度为 O(n^2)。") as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
                text="算法存储仅依赖于一个大小为 2n 单元的静态线性结构数组，没有额外的空间开销，辅助空间复杂度为 O(n)。") as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="这就是构造哈夫曼树算法的完整演示过程。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)
