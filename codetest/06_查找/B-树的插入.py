# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
from codetest.python版.bst_video_support import PythonCodePanel, method_lines
from codetest.python版.btree_model import BTree


class BTreeInsertionVideo(VoiceoverScene):
    def make_btree_node(self, keys, center, color=BLUE, font_name="Consolas", font_size=18, key_w=0.64):
        cells = VGroup()
        key_cells = VGroup()
        texts = VGroup()
        ptr_cells = VGroup()

        key_h = 0.46
        ptr_w = 0.22
        fill_opacity = 0.22 if color != BLUE else 0.15

        for i in range(len(keys) + 1):
            p_rect = Rectangle(
                width=ptr_w,
                height=key_h,
                color=color,
                fill_color=color,
                fill_opacity=0.06,
                stroke_width=2.5,
            )
            dot = Dot(radius=0.03, color=color).move_to(p_rect.get_center())
            p_group = VGroup(p_rect, dot)
            cells.add(p_group)
            ptr_cells.add(p_group)

            if i < len(keys):
                k_rect = Rectangle(
                    width=key_w,
                    height=key_h,
                    color=color,
                    fill_color=color,
                    fill_opacity=fill_opacity,
                    stroke_width=2.5,
                )
                t = Text(str(keys[i]), font=font_name, font_size=font_size, color=WHITE)
                cells.add(k_rect)
                key_cells.add(k_rect)
                texts.add(t)

        cells.arrange(RIGHT, buff=0)
        for i in range(len(keys) + 1):
            ptr_cells[i][1].move_to(ptr_cells[i][0].get_center())
            if i < len(keys):
                texts[i].move_to(key_cells[i].get_center())

        group = VGroup(cells, texts).move_to(center)

        ptrs = []
        for i in range(len(keys) + 1):
            rect = ptr_cells[i][0]
            ptrs.append(np.array([rect.get_center()[0], rect.get_bottom()[1], 0]))

        group.keys = list(keys)
        group.cells = key_cells
        group.texts = texts
        group.ptrs = ptrs
        return group

    def build_tree_visual(self, spec, positions):
        # Allocate horizontal space from actual leaf widths, including the
        # temporary four-key overflow node. Fixed centres make its neighbours
        # overlap as soon as the leaf grows or splits.
        leaf_gap = 0.5
        widths = {node_id: 0.64 * len(info["keys"]) + 0.22 * (len(info["keys"]) + 1)
                  for node_id, info in spec.items()}
        children = {node_id: [child for child in info.get("children", []) if child is not None]
                    for node_id, info in spec.items()}
        child_ids = {child for ids in children.values() for child in ids}
        root_id = next(node_id for node_id in spec if node_id not in child_ids)
        centers = {}

        def place_subtree(node_id, left):
            if not children[node_id]:
                centers[node_id] = left + widths[node_id] / 2
                return left + widths[node_id]
            right = left
            for child in children[node_id]:
                right = place_subtree(child, right) + leaf_gap
            right -= leaf_gap
            centers[node_id] = (left + right) / 2
            return right

        place_subtree(root_id, 0.0)
        nodes = {}
        for node_id, info in spec.items():
            nodes[node_id] = self.make_btree_node(
                info["keys"],
                np.array([centers[node_id], positions[node_id][1], 0.0]),
                color=info.get("color", BLUE),
            )

        edges = VGroup()
        for node_id, info in spec.items():
            for idx, child in enumerate(info.get("children", [])):
                if child is None:
                    continue
                edges.add(
                    Line(
                        nodes[node_id].ptrs[idx],
                        nodes[child].get_top(),
                        color=GRAY,
                        stroke_width=2.5,
                    )
                )

        group = VGroup(edges, *nodes.values())
        # Fixed left column; apply the same transform to boxes, labels and edges.
        group.scale(min(0.82, 6.5 / group.width)).move_to(np.array([-3.45, -0.25, 0]))
        # Keep pointer coordinates consistent with the final display geometry.
        for node in nodes.values():
            node.ptrs = [node[0][2 * i][0].get_bottom().copy() for i in range(len(node.keys) + 1)]
        return group, nodes

    def make_key_badge(self, value):
        label = Text(f"待插入关键字: {value}", font="Microsoft YaHei", font_size=26, color=YELLOW)
        box = SurroundingRectangle(label, color=YELLOW, buff=0.18, corner_radius=0.12)
        return VGroup(box, label)

    def make_insert_token(self, value, color=GREEN):
        rect = RoundedRectangle(
            corner_radius=0.12,
            width=0.7,
            height=0.48,
            color=color,
            fill_color=color,
            fill_opacity=0.25,
            stroke_width=2.5,
        )
        text = Text(str(value), font="Consolas", font_size=22, color=WHITE)
        return VGroup(rect, text)

    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(0.8).to_corner(UR, buff=0.08)
        self.add(logo)

        title = Text("B-树的插入", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(title), run_time=0.8)

        with self.voiceover(
            text="本节我们学习 B 树的插入算法。先通过查找定位到叶子结点，再插入关键字。若插入后的关键字数小于阶数 m，便完成；否则分裂结点，并把指定位置的关键字向父结点提升。",
            subcaption="先通过查找定位叶子结点，再插入关键字。若插入后 keynum 小于 m，便完成；否则分裂结点，并把第 s 个关键字向父结点提升。"
        ) as tracker:
            self.wait(tracker.duration)

        step_title = Text("插入算法步骤", font="Microsoft YaHei", font_size=34, color=YELLOW)
        step_1 = Text("1. 先按查找算法定位插入位置，若已存在则跳过", font="Microsoft YaHei", font_size=22)
        step_2 = Text("2. 把新关键字插入结点，若关键字数不超过 m-1，则结束", font="Microsoft YaHei", font_size=22)
        step_3 = Text("3. 若结点过满，则以中间关键字为分裂点，并把中间关键字上移", font="Microsoft YaHei", font_size=22)
        step_4 = Text("4. 若根也分裂，则创建新根，B-树高度加 1", font="Microsoft YaHei", font_size=22)
        step_group = VGroup(step_title, step_1, step_2, step_3, step_4).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        step_box = RoundedRectangle(
            corner_radius=0.2,
            height=step_group.get_height() + 0.7,
            width=step_group.get_width() + 0.8,
            color=BLUE,
            fill_color=BLACK,
            fill_opacity=0.85,
            stroke_width=2,
        ).move_to(step_group)
        step_panel = VGroup(step_box, step_group).move_to(ORIGIN)

        with self.voiceover(
            text="B 树插入的核心，可以概括成四步。先找位置，再插入；如果结点过满，就分裂并把中间关键字向上提升；如果一直提升到根，就生成新的根结点。",
            subcaption="B-树插入的核心，可以概括成四步。先找位置，再插入；如果结点过满，就分裂并把中间关键字向上提升；如果一直提升到根，就生成新的根结点。"
        ) as tracker:
            self.play(FadeIn(step_panel), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))

        self.play(FadeOut(step_panel), FadeOut(title), run_time=0.6)

        # 直接展示实现中的 Python 方法，按执行阶段分页，避免缩成小字。
        python_lines = method_lines(BTree.insert_btree)
        def line_index(fragment):
            return next(i for i, line in enumerate(python_lines) if fragment in line)

        IDX_FUNC = 0
        IDX_INIT = line_index("x = key")
        IDX_WHILE = line_index("while q and not finished:")
        IDX_INSERT = line_index("self.insert(q, i, x, ap)")
        IDX_DONE = line_index("if q.keynum < self.m:")
        IDX_ELSE = line_index("else:")
        IDX_SPLIT_INDEX = line_index("s = (self.m + 1) // 2")
        IDX_NEW_NODE = line_index("ap = BTNode")
        IDX_SPLIT = line_index("ap = self.split(q, s, ap)")
        IDX_PROMOTE = line_index("x = q.k[s]")
        IDX_PARENT = line_index("q = q.parent")
        IDX_RESEARCH = line_index("i = self.search(q, x)")
        IDX_NEWROOT_CHECK = line_index("if not finished:")

        code_block = PythonCodePanel(
            python_lines, title="Python 插入（m = 4）",
            page_starts=[0, line_index("ap = BTNode")],
        )
        self.play(FadeIn(code_block), run_time=0.8)
        track_code = code_block.track

        # Example 1: insert without split
        pos_a = {
            "R": np.array([-3.25, 1.18, 0]),
            "L": np.array([-5.05, -0.10, 0]),
            "M": np.array([-1.45, -0.10, 0]),
            "A": np.array([-6.05, -1.45, 0]),
            "B": np.array([-4.15, -1.45, 0]),
            "C": np.array([-2.75, -1.45, 0]),
            "D": np.array([-0.80, -1.45, 0]),
            "E": np.array([1.25, -1.45, 0]),
        }
        spec_a0 = {
            "R": {"keys": [35], "children": ["L", "M"]},
            "L": {"keys": [18], "children": ["A", "B"]},
            "M": {"keys": [43, 78], "children": ["C", "D", "E"]},
            "A": {"keys": [11], "children": [None, None]},
            "B": {"keys": [27], "children": [None, None]},
            "C": {"keys": [39], "children": [None, None]},
            "D": {"keys": [47, 53], "children": [None, None, None]},
            "E": {"keys": [99], "children": [None, None]},
        }
        spec_a1 = {
            "R": {"keys": [35], "children": ["L", "M"]},
            "L": {"keys": [18], "children": ["A", "B"]},
            "M": {"keys": [43, 78], "children": ["C", "D", "E"]},
            "A": {"keys": [11], "children": [None, None]},
            "B": {"keys": [27], "children": [None, None]},
            "C": {"keys": [39], "children": [None, None]},
            "D": {"keys": [47, 53, 64], "children": [None, None, None, None]},
            "E": {"keys": [99], "children": [None, None]},
        }

        tree_a, nodes_a = self.build_tree_visual(spec_a0, pos_a)
        case_a = Text("案例一：插入后无需分裂", font="Microsoft YaHei", font_size=26, color=GREEN).to_corner(UL, buff=0.45).shift(DOWN * 0.15 + RIGHT * 0.1)
        badge_a = self.make_key_badge(64).scale(0.88).next_to(case_a, DOWN, aligned_edge=LEFT, buff=0.18)

        with self.voiceover(
            text="先看第一个例子。我们在这棵四阶 B 树中插入关键字六十四，这个例子只会发生普通插入，不会触发分裂。",
            subcaption="先看第一个例子。我们在这棵 4 阶 B-树中插入关键字 64，这个例子只会发生普通插入，不会触发分裂。"
        ) as tracker:
            self.play(FadeIn(case_a), FadeIn(badge_a), FadeIn(tree_a), run_time=tracker.duration)

        cursor = SurroundingRectangle(nodes_a["R"], color=YELLOW, buff=0.06, stroke_width=3.5)
        cursor_label = Text("q", font_size=24, color=YELLOW).next_to(cursor, UP, buff=0.1)
        cursor_group = VGroup(cursor, cursor_label)

        with self.voiceover(
            text="和查找算法一样，我们先定位插入位置。六十四大于根结点三十五，进入右子树；在结点四十三、七十八中，六十四介于二者之间，所以进入中间叶子结点。",
            subcaption="和查找算法一样，我们先定位插入位置。64 大于根结点 35，进入右子树；在结点 [43,78] 中，64 介于二者之间，所以进入中间叶子结点。"
        ) as tracker:
            # search_btree is performed before insert_btree is called.
            self.play(*track_code(None), run_time=0.4)
            self.play(FadeIn(cursor_group), run_time=0.3)
            self.play(cursor.animate.become(SurroundingRectangle(nodes_a["M"], color=YELLOW, buff=0.06, stroke_width=3.5)),
                      cursor_label.animate.next_to(nodes_a["M"], UP, buff=0.15), run_time=0.7)
            self.play(cursor.animate.become(SurroundingRectangle(nodes_a["D"], color=YELLOW, buff=0.06, stroke_width=3.5)),
                      cursor_label.animate.next_to(nodes_a["D"], UP, buff=0.15), run_time=0.7)
            self.wait(max(0.1, tracker.duration - 2.3))

        fail_text = Text("查找失败: q 指向 [47, 53], i = 2, tag = 0", font="Microsoft YaHei", font_size=20, color=YELLOW)
        fail_text.scale_to_fit_width(min(fail_text.width, 6.2))
        fail_text.next_to(badge_a, DOWN, aligned_edge=LEFT, buff=0.18)

        with self.voiceover(
            text="查找失败后，search_btree 返回 Result 对象。这里 q 指向四十七、五十三所在的结点，i 等于二，表示把六十四插在第二个关键字之后。",
            subcaption="search_btree 返回 Result(q, 2, 0)。q 指向 [47,53]，i = 2，因此把 64 插在第 2 个关键字之后。"
        ) as tracker:
            self.play(*track_code(IDX_FUNC), run_time=0.3)
            self.play(FadeIn(fail_text), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        token_64 = self.make_insert_token(64).move_to(badge_a.get_right() + RIGHT * 1.2 + DOWN * 0.05)

        with self.voiceover(
            text="接着执行插入操作。当前结点插入之后有三个关键字，没有超过四阶 B 树允许的上限三，所以插入立即完成。",
            subcaption="接着执行插入操作。当前结点插入之后有 3 个关键字，没有超过 4 阶 B-树允许的上限 3，所以插入立即完成。"
        ) as tracker:
            self.play(*track_code(IDX_INIT), run_time=0.3)
            self.play(*track_code(IDX_WHILE), run_time=0.3)
            self.play(*track_code(IDX_INSERT), run_time=0.3)
            self.play(FadeIn(token_64), run_time=0.4)
            self.play(token_64.animate.move_to(nodes_a["D"].get_center()), run_time=0.8)
            tree_a_after, nodes_a_after = self.build_tree_visual(spec_a1, pos_a)
            self.play(FadeOut(token_64), ReplacementTransform(tree_a, tree_a_after), run_time=0.9)
            tree_a = tree_a_after
            nodes_a = nodes_a_after
            cursor.become(SurroundingRectangle(nodes_a["D"], color=GREEN, buff=0.06, stroke_width=3.5))
            cursor_label.become(Text("完成", font="Microsoft YaHei", font_size=22, color=GREEN).next_to(cursor, UP, buff=0.1))
            self.play(*track_code(IDX_DONE), run_time=0.3)
            self.play(nodes_a["D"].cells[2].animate.set_fill(GREEN, opacity=0.65), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 3.5))

        self.play(
            FadeOut(tree_a),
            FadeOut(cursor_group),
            FadeOut(badge_a),
            FadeOut(case_a),
            FadeOut(fail_text),
            run_time=0.8,
        )
        self.play(*track_code(None), run_time=0.2)

        # Example 2: split a full leaf and promote the middle key
        pos_b0 = {
            "R": np.array([-3.25, 1.18, 0]),
            "L": np.array([-5.05, -0.10, 0]),
            "M": np.array([-1.45, -0.10, 0]),
            "A": np.array([-6.05, -1.45, 0]),
            "B": np.array([-4.15, -1.45, 0]),
            "C": np.array([-2.75, -1.45, 0]),
            "D": np.array([-0.80, -1.45, 0]),
            "E": np.array([1.25, -1.45, 0]),
        }
        spec_b0 = {
            "R": {"keys": [35], "children": ["L", "M"]},
            "L": {"keys": [18], "children": ["A", "B"]},
            "M": {"keys": [43, 78], "children": ["C", "D", "E"]},
            "A": {"keys": [11], "children": [None, None]},
            "B": {"keys": [27], "children": [None, None]},
            "C": {"keys": [39], "children": [None, None]},
            "D": {"keys": [47, 53, 64], "children": [None, None, None, None]},
            "E": {"keys": [99], "children": [None, None]},
        }

        pos_b1 = dict(pos_b0)
        spec_b1 = {
            "R": {"keys": [35], "children": ["L", "M"]},
            "L": {"keys": [18], "children": ["A", "B"]},
            "M": {"keys": [43, 78], "children": ["C", "D", "E"]},
            "A": {"keys": [11], "children": [None, None]},
            "B": {"keys": [27], "children": [None, None]},
            "C": {"keys": [39], "children": [None, None]},
            "D": {"keys": [47, 53, 60, 64], "children": [None, None, None, None, None], "color": RED},
            "E": {"keys": [99], "children": [None, None]},
        }

        pos_b2 = dict(pos_b0)
        pos_b2["D"] = np.array([-1.05, -1.45, 0])
        pos_b2["F"] = np.array([0.35, -1.45, 0])
        pos_b2["E"] = np.array([1.65, -1.45, 0])
        spec_b2 = {
            "R": {"keys": [35], "children": ["L", "M"]},
            "L": {"keys": [18], "children": ["A", "B"]},
            "M": {"keys": [43, 53, 78], "children": ["C", "D", "F", "E"]},
            "A": {"keys": [11], "children": [None, None]},
            "B": {"keys": [27], "children": [None, None]},
            "C": {"keys": [39], "children": [None, None]},
            "D": {"keys": [47], "children": [None, None]},
            "F": {"keys": [60, 64], "children": [None, None, None]},
            "E": {"keys": [99], "children": [None, None]},
        }

        tree_b0, nodes_b0 = self.build_tree_visual(spec_b0, pos_b0)
        case_b = Text("案例二：叶子结点分裂", font="Microsoft YaHei", font_size=24, color=GREEN).to_corner(UL, buff=0.4).shift(DOWN * 0.1)
        badge_b = self.make_key_badge(60).scale(0.82).next_to(case_b, DOWN, aligned_edge=LEFT, buff=0.14)

        with self.voiceover(
            text="第二个例子用图中的完整 B 树作为初始结构。现在插入关键字六十，它会让叶子结点溢出，从而触发一次分裂。",
            subcaption="第二个例子用图中的完整 B-树作为初始结构。现在插入关键字 60，它会让叶子结点溢出，从而触发一次分裂。"
        ) as tracker:
            self.play(FadeIn(case_b), FadeIn(badge_b), FadeIn(tree_b0), run_time=tracker.duration)

        cursor = SurroundingRectangle(nodes_b0["R"], color=YELLOW, buff=0.06, stroke_width=3.5)
        cursor_label = Text("q", font_size=24, color=YELLOW).next_to(cursor, UP, buff=0.1)
        cursor_group = VGroup(cursor, cursor_label)

        with self.voiceover(
            text="先定位插入位置。六十大于三十五，进入右子树；在结点四十三、七十八中，六十位于二者之间，因此下降到中间叶子结点。",
            subcaption="先定位插入位置。60 大于 35，进入右子树；在结点 [43,78] 中，60 位于二者之间，因此下降到中间叶子结点。"
        ) as tracker:
            self.play(FadeIn(cursor_group), run_time=0.3)
            self.play(cursor.animate.become(SurroundingRectangle(nodes_b0["M"], color=YELLOW, buff=0.06, stroke_width=3.5)),
                      cursor_label.animate.next_to(nodes_b0["M"], UP, buff=0.15), run_time=0.7)
            self.play(cursor.animate.become(SurroundingRectangle(nodes_b0["D"], color=YELLOW, buff=0.06, stroke_width=3.5)),
                      cursor_label.animate.next_to(nodes_b0["D"], UP, buff=0.15), run_time=0.7)
            self.wait(max(0.1, tracker.duration - 1.3))

        fail_text = Text("查找失败: q 指向 [47, 53, 64], i = 2, tag = 0", font="Microsoft YaHei", font_size=18, color=YELLOW)
        fail_text.scale_to_fit_width(min(fail_text.width, 6.2))
        fail_text.next_to(badge_b, DOWN, aligned_edge=LEFT, buff=0.14)

        with self.voiceover(
            text="查找失败后，插入点落在五十三之后、六十四之前，也就是这个叶子结点的中间位置。",
            subcaption="查找失败后，插入点落在 53 之后、64 之前，也就是这个叶子结点的中间位置。"
        ) as tracker:
            self.play(FadeIn(fail_text), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 0.6))

        token_60 = self.make_insert_token(60).move_to(badge_b.get_right() + RIGHT * 1.2 + DOWN * 0.05)

        overflow_hint = Text("当前结点溢出", font="Microsoft YaHei", font_size=18, color=RED)
        overflow_hint.next_to(fail_text, DOWN, aligned_edge=LEFT, buff=0.12)

        with self.voiceover(
            text="现在把关键字六十插入进去以后，这个叶子结点里就有了四十七、五十三、六十、六十四这四个关键字。对于四阶 B 树来说，一个结点最多只能保存三个关键字，所以这里已经超出了容量上限，必须马上进入分裂步骤。",
            subcaption="现在把关键字 60 插入进去以后，这个叶子结点里就有了 47、53、60、64 这 4 个关键字。对于 4 阶 B-树来说，一个结点最多只能保存 3 个关键字，所以这里已经超出了容量上限，必须马上进入分裂步骤。"
        ) as tracker:
            self.play(*track_code(IDX_INIT), run_time=0.3)
            self.play(*track_code(IDX_WHILE), run_time=0.3)
            self.play(*track_code(IDX_INSERT), run_time=0.3)
            self.play(FadeIn(token_60), run_time=0.4)
            self.play(token_60.animate.move_to(nodes_b0["D"].get_center()), run_time=0.7)
            tree_b1, nodes_b1 = self.build_tree_visual(spec_b1, pos_b1)
            self.play(FadeOut(token_60), ReplacementTransform(tree_b0, tree_b1), run_time=0.8)
            tree_b0 = tree_b1
            nodes_b0 = nodes_b1
            self.play(FadeOut(cursor_group), run_time=0.2)
            self.play(*track_code(IDX_DONE), run_time=0.2)
            self.play(*track_code(IDX_ELSE), run_time=0.2)
            self.play(FadeIn(overflow_hint), run_time=0.25)
            self.wait(max(0.1, tracker.duration - 2.9))

        split_hint = Text("上移关键字: 53", font="Microsoft YaHei", font_size=18, color=RED)
        split_hint.next_to(overflow_hint, DOWN, aligned_edge=LEFT, buff=0.1)

        with self.voiceover(
            text="按 Python 代码，四阶 B 树的 s 等于二，所以第二个关键字五十三上移。左边原结点留下四十七，右边新结点保存六十和六十四，再将五十三插入父结点。",
            subcaption="按 Python 代码，4 阶 B-树的 s = (m + 1) // 2 = 2，所以第 2 个关键字 53 上移。左结点保留 47，右结点保存 [60,64]，再将 53 插入父结点。"
        ) as tracker:
            self.play(*track_code(IDX_SPLIT_INDEX), run_time=0.3)
            self.play(*track_code(IDX_NEW_NODE), run_time=0.3)
            self.play(*track_code(IDX_SPLIT), run_time=0.3)
            self.play(FadeIn(split_hint), run_time=0.4)
            self.play(Indicate(nodes_b0["D"].texts[1], color=RED, scale_factor=1.2), run_time=0.6)
            tree_b2, nodes_b2 = self.build_tree_visual(spec_b2, pos_b2)
            self.play(ReplacementTransform(tree_b0, tree_b2), run_time=0.9)
            tree_b0 = tree_b2
            nodes_b0 = nodes_b2
            self.play(*track_code(IDX_PROMOTE), run_time=0.3)
            self.play(*track_code(IDX_PARENT), run_time=0.3)
            self.play(*track_code(IDX_RESEARCH), run_time=0.3)
            self.wait(max(0.1, tracker.duration - 3.1))

        with self.voiceover(
            text="上升后的父结点变成四十三、五十三、七十八，一共有三个关键字。对于四阶 B 树来说，这仍然没有超过上限，所以本轮插入在这里结束。",
            subcaption="上升后的父结点变成 [43,53,78]，一共有 3 个关键字。对于 4 阶 B-树来说，这仍然没有超过上限，所以本轮插入在这里结束。"
        ) as tracker:
            self.play(*track_code(IDX_DONE), run_time=0.4)
            self.play(Indicate(nodes_b0["M"], color=GREEN, scale_factor=1.05), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        height_hint = Text("父结点未溢出 -> 插入完成", font="Microsoft YaHei", font_size=24, color=YELLOW)
        height_hint.to_edge(DOWN, buff=1.25).shift(LEFT * 2.0)

        with self.voiceover(
            text="需要注意，如果父结点也因此溢出，分裂才会继续向上进行；如果一路影响到根结点，才需要创建新根。当前例子中父结点没有溢出，所以不需要新建根结点。",
            subcaption="需要注意，如果父结点也因此溢出，分裂才会继续向上进行；如果一路影响到根结点，才需要创建新根。当前例子中父结点没有溢出，所以不需要新建根结点。"
        ) as tracker:
            self.play(*track_code(IDX_NEWROOT_CHECK), run_time=0.3)
            self.play(FadeIn(height_hint), run_time=0.5)
            self.play(Indicate(nodes_b0["R"], color=YELLOW, scale_factor=1.08), run_time=0.6)
            self.wait(max(0.1, tracker.duration - 1.4))

        self.play(*track_code(None), run_time=0.3)
        self.play(FadeOut(code_block), run_time=0.5)

        time_box = VGroup(
            Text("时间复杂度：", font="Microsoft YaHei", font_size=28, color=YELLOW),
            MathTex(r"O(\log_{m} N)", font_size=34, color=YELLOW),
        ).arrange(RIGHT, buff=0.12)
        space_box = VGroup(
            Text("空间复杂度：", font="Microsoft YaHei", font_size=28, color=YELLOW),
            MathTex(r"O(1)", font_size=34, color=YELLOW),
        ).arrange(RIGHT, buff=0.18)
        summary = VGroup(time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.45).to_edge(RIGHT, buff=1.1).shift(DOWN * 1.4)

        with self.voiceover(
            text="总结一下，B 树插入的第一阶段仍然是查找，所以路径长度是对数级别。之后每一层至多做一次分裂，因此整体时间复杂度仍然是对数级别。",
            subcaption="总结一下，B-树插入的第一阶段仍然是查找，所以路径长度是对数级别。之后每一层至多做一次分裂，因此整体时间复杂度仍然是对数级别。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
            text="在这个实现里，我们仅使用当前关键字、辅助指针和查找位置等少量变量。结点数量增加时，这些辅助变量占用的空间不会随之增加，所以额外空间复杂度为常数级，记为欧一。",
            subcaption="在这个实现里，我们只使用了少量辅助变量，比如当前关键字、辅助指针以及查找位置等信息，并没有额外开辟与树规模成比例的存储空间，所以空间复杂度是常数级，也就是 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
            text="这就是 B 树插入算法的完整演示。先按查找过程确定插入位置，再执行插入；如果结点溢出，就从当前结点开始分裂，并把中间关键字逐层向上提升，直到整棵树重新恢复平衡。",
            subcaption="这就是 B-树插入算法的完整演示。先按查找过程确定插入位置，再执行插入；如果结点溢出，就从当前结点开始分裂，并把中间关键字逐层向上提升，直到整棵树重新恢复平衡。"
        ) as tracker:
            self.wait(tracker.duration)

        self.play(
            FadeOut(tree_b0),
            FadeOut(cursor_group),
            FadeOut(badge_b),
            FadeOut(case_b),
            FadeOut(fail_text),
            FadeOut(overflow_hint),
            FadeOut(split_hint),
            FadeOut(height_hint),
            FadeOut(summary),
            run_time=1.0,
        )
        self.wait(1.5)
