# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class HuffmanCodeNoCodeVideo(VoiceoverScene):
    NODE_R = 0.30

    def make_node(self, label, center, weight_str, color=BLUE):
        c = Circle(radius=self.NODE_R, color=color, fill_color=color, fill_opacity=0.15, stroke_width=2.5).move_to(
            center)
        t_weight = Text(str(weight_str), font_size=20, color=WHITE, font="Consolas").move_to(center)
        t_id = Text(f"#{label}", font_size=16, color=GRAY_B, font="Consolas").next_to(c, UP, buff=0.06)
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
        label = Text(label_text, font_size=20, color=YELLOW, font="Consolas").move_to(line.point_from_proportion(0.5))
        # 根据连线方向稍微偏移标签，避免与线重合
        perp_vec = np.array([-u[1], u[0], 0])
        label.shift(perp_vec * 0.25)

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
        algo_title = Text("根据哈夫曼树求哈夫曼编码（无代码跟踪版）", font_size=36, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.3)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(text="本节我们来学习如何基于哈夫曼树求解哈夫曼编码。这里我们主要通过在哈夫曼树上进行回溯来演示其核心思想。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== TREE AND HC TABLE CONSTRUCTION =====
        # =========================================================================

        # 1. 构造哈夫曼树
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
        # 上移并左移哈夫曼树，避免右侧拥挤且不出边界
        tree_group.scale(0.8).move_to(LEFT * 3.5 + UP * 0.5)

        # 2. HC 编码表
        hc_title = Text("HC 编码表", font_size=28, color=BLUE_A, font="Microsoft YaHei")
        hc_boxes = VGroup()
        for i in range(1, 5):
            box = Rectangle(width=2.5, height=0.6, color=GRAY_B)
            label = Text(f"字符 #{i}", font_size=20, color=GRAY, font="Microsoft YaHei").next_to(box, LEFT, buff=0.2)
            hc_boxes.add(VGroup(label, box))
        hc_boxes.arrange(DOWN, buff=0.3)
        hc_group = VGroup(hc_title, hc_boxes).arrange(DOWN, buff=0.5)
        # 缩小 HC 编码表并相对 logo 布局，稍微低于 logo
        hc_group.scale(0.8).next_to(logo, DOWN, buff=0.15).align_to(logo, RIGHT)

        # 3. 临时数组 cd
        cd_title = Text("临时数组 cd", font_size=20, color=YELLOW, font="Microsoft YaHei")
        cd_boxes = VGroup(*[Rectangle(width=0.6, height=0.6, color=YELLOW) for _ in range(4)]).arrange(RIGHT, buff=0)
        cd_group = VGroup(cd_title, cd_boxes).arrange(LEFT, buff=0.3)
        # 相对布局：位于哈夫曼树的右侧，底部对齐并向下偏移避免遮挡
        cd_group.next_to(tree_group, RIGHT, buff=1.0).align_to(tree_group, DOWN).shift(DOWN * 0.5)

        end_char = Text("\\0", font_size=16, color=WHITE, font="Consolas").move_to(cd_boxes[3].get_center())
        cd_group_with_null = VGroup(cd_group, end_char)

        start_pointer = Arrow(start=DOWN, end=UP, color=RED, max_tip_length_to_length_ratio=0.3).scale(0.5)
        start_label = Text("start", font_size=16, color=RED, font="Consolas")
        pointer_group = VGroup(start_pointer, start_label)

        with self.voiceover(text="如图所示，左侧是一棵已经构建好的哈夫曼树。右上方是准备用来存放每个字符编码的编码表。") as tracker:
            self.play(FadeIn(tree_group), run_time=tracker.duration * 0.5)
            self.play(FadeIn(hc_group), run_time=tracker.duration * 0.5)

        with self.voiceover(text="求解哈夫曼编码的过程，是从每个叶子结点出发，沿着树的分支一步步向上回溯，直到根结点。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="如果是从左孩子向上回溯，就记录 0，若是从右孩子向上，就记录 1。") as tracker:
            self.play(Indicate(edges_dict[(7, 1)].label, color=RED, scale_factor=1.5),
                      Indicate(edges_dict[(7, 6)].label, color=RED, scale_factor=1.5), run_time=tracker.duration)

        with self.voiceover(text="为了得到正序的哈夫曼编码，我们引入一个临时数组 cd，从后向前记录每一次回溯的分支值。数组最后一位存放结束符。") as tracker:
            self.play(FadeIn(cd_group_with_null), run_time=tracker.duration)

        with self.voiceover(text="在回溯时，我们用一个指针 start 指向当前记录的位置。每向上一层，start 就向前移动一位。") as tracker:
            # 初始化一下 pointer 示意
            start_pointer.next_to(cd_boxes[3], DOWN, buff=0.1)
            start_label.next_to(start_pointer, DOWN, buff=0.1)
            self.play(FadeIn(pointer_group), run_time=tracker.duration * 0.4)
            self.play(pointer_group.animate.next_to(cd_boxes[2], DOWN, buff=0.1), run_time=tracker.duration * 0.3)
            self.play(pointer_group.animate.next_to(cd_boxes[1], DOWN, buff=0.1), run_time=tracker.duration * 0.3)
            self.play(FadeOut(pointer_group), run_time=0.2)

        # =========================================================================
        # ===== BACKTRACKING TRACE =====
        # =========================================================================

        leaf_paths = {
            1: [(1, 7, '0')],
            2: [(2, 6, '0'), (6, 7, '1')],
            3: [(3, 5, '0'), (5, 6, '1'), (6, 7, '1')],
            4: [(4, 5, '1'), (5, 6, '1'), (6, 7, '1')],
        }

        for i in range(1, 5):
            path = leaf_paths[i]

            with self.voiceover(text=f"现在我们来求解字符 {i} 的哈夫曼编码。首先定位到 {i} 号叶子结点。") as tracker:
                self.play(Indicate(nodes[i].circle, color=RED, scale_factor=1.2), run_time=tracker.duration)

            # 每次新开始，start 指向最后一位 (结束符所在位置)
            start_idx = 3
            start_pointer.next_to(cd_boxes[start_idx], DOWN, buff=0.1)
            start_label.next_to(start_pointer, DOWN, buff=0.1)

            self.play(nodes[i].circle.animate.set_stroke(RED).set_fill(RED, 0.5), FadeIn(pointer_group), run_time=0.5)

            seq_chars = []

            for child_idx, parent_idx, bit in path:
                is_root = (parent_idx == 7)
                parent_name = f"根结点 {parent_idx}" if is_root else f"双亲结点 {parent_idx}"

                if len(path) == 1:
                    vo_text = f"由于结点 {child_idx} 是其双亲的{'左' if bit == '0' else '右'}孩子，直接向上回溯到{parent_name} ，start向左移动，写入 {bit} 。"
                else:
                    if len(seq_chars) == 0:
                        vo_text = f"从结点 {child_idx} 向上回溯到{parent_name} ，经过{'左' if bit == '0' else '右'}分支，start向左移动，写入 {bit} 。"
                    else:
                        vo_text = f"继续向上回溯到{parent_name} ，经过{'左' if bit == '0' else '右'}分支，start向左移动，写入 {bit} 。"

                with self.voiceover(text=vo_text) as tracker:
                    start_idx -= 1
                    edge_g = edges_dict[(parent_idx, child_idx)]

                    bit_char = Text(bit, font_size=28, color=GREEN, font="Consolas").move_to(cd_boxes[start_idx].get_center())

                    self.play(
                        nodes[parent_idx].circle.animate.set_stroke(RED).set_fill(RED, 0.5),
                        Indicate(edge_g.line, color=YELLOW, scale_factor=1.1),
                        Indicate(edge_g.label, color=YELLOW, scale_factor=1.5),
                        pointer_group.animate.next_to(cd_boxes[start_idx], DOWN, buff=0.1),
                        Write(bit_char),
                        run_time=tracker.duration
                    )
                    # 追加到列表，注意这是从右到左填入 cd 的
                    seq_chars.append(bit_char)

            with self.voiceover(text="到达了根结点，回溯结束。") as tracker:
                self.wait(tracker.duration)

            with self.voiceover(text="此时从 start 指向的位置开始，也就是我们写入的序列，就是正确的哈夫曼编码，我们直接把它存入编码表中。") as tracker:
                # seq_chars 中的元素是从最后一位往第一位写的，也就是倒序的
                final_str = "".join([c.text for c in reversed(seq_chars)])
                res_text = Text(final_str, font_size=24, color=YELLOW, font="Consolas").move_to(hc_boxes[i-1][1].get_center())
                
                temp_copy = VGroup(*seq_chars).copy()
                # 倒转一下，使得复制移动时按正向字符顺序排列
                temp_copy.submobjects = list(reversed(temp_copy.submobjects))
                self.play(temp_copy.animate.arrange(RIGHT, buff=0.05).move_to(hc_boxes[i-1][1].get_center()).scale(0.8),
                          run_time=tracker.duration * 0.6)
                self.remove(temp_copy)
                self.add(res_text)
                self.wait(tracker.duration * 0.4)

            # Cleanup for the next iteration
            reset_anims = []
            for n_idx in nodes:
                old_color = BLUE if n_idx <= 4 else GREEN
                reset_anims.append(nodes[n_idx].circle.animate.set_stroke(old_color).set_fill(old_color, 0.15))
            
            if i < 4:
                self.play(
                    FadeOut(pointer_group),
                    *[FadeOut(c) for c in seq_chars], 
                    *reset_anims, 
                    run_time=1.0
                )
            else:
                self.play(
                    FadeOut(pointer_group),
                    *[FadeOut(c) for c in seq_chars], 
                    *reset_anims, 
                    run_time=0.5
                )

        with self.voiceover(text="所有字符编码完毕后，释放临时数组 cd 所占用的空间。") as tracker:
            self.play(FadeOut(cd_group_with_null), run_time=tracker.duration)

        self.wait(1)

        with self.voiceover(
            text="本视频讲解了哈夫曼编码算法的实现思想，如需深入学习该算法的代码实现，请后续观看该算法的代码跟踪版讲解视频。",
            subcaption="本视频讲解了哈夫曼编码算法的实现思想，如需深入学习该算法的代码实现，请后续观看 该算法的代码跟踪版讲解视频。"
        ) as tracker:
            self.wait(tracker.duration)
