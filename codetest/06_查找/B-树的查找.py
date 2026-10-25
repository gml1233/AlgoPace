# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService
from codetest.python版.bst_video_support import PythonCodePanel, method_lines
from codetest.python版.btree_model import BTree


class BTreeSearchVideo(VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(0.8).to_corner(UR, buff=0.08)
        self.add(logo)

        # ===== PHASE A — TITLE & INTRO =====
        algo_title = Text("B-树的查找", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(

            text="本节我们学习B树的查找算法。从根结点开始，在当前结点内比较关键字，再沿对应的分支向下查找，直到找到目标或遇到空指针。正式演示使用一棵四阶B树。",

            subcaption="本节学习 B-树的查找。从根结点开始，在结点内比较，再沿相应分支向下，直到命中目标或遇到空指针。正式演示使用 4 阶 B-树。"

        ) as tracker:
            self.wait(tracker.duration)


        def make_btree_node(keys, center, font_name="Consolas", font_size=18, key_w=0.6):
            cells = VGroup()
            key_cells = VGroup()
            texts = VGroup()
            ptr_cells = VGroup()
            
            KEY_W, KEY_H = key_w, 0.45
            PTR_W = 0.22
            
            for i in range(len(keys) + 1):
                p_rect = Rectangle(width=PTR_W, height=KEY_H, color=BLUE, fill_color=BLUE, fill_opacity=0.05, stroke_width=2.5)
                dot = Dot(radius=0.03, color=BLUE)
                dot.move_to(p_rect.get_center())
                p_group = VGroup(p_rect, dot)
                cells.add(p_group)
                ptr_cells.add(p_group)
                
                if i < len(keys):
                    k_rect = Rectangle(width=KEY_W, height=KEY_H, color=BLUE, fill_color=BLUE, fill_opacity=0.15, stroke_width=2.5)
                    t = Text(str(keys[i]), font=font_name, font_size=font_size, color=WHITE)
                    cells.add(k_rect)
                    key_cells.add(k_rect)
                    texts.add(t)
            
            cells.arrange(RIGHT, buff=0)
            
            for i in range(len(keys) + 1):
                ptr_cells[i][1].move_to(ptr_cells[i][0].get_center())
                if i < len(keys):
                    texts[i].move_to(key_cells[i].get_center())
            
            group = VGroup(cells, texts)
            group.move_to(center)
            group.cells = key_cells
            group.texts = texts
            group.keys = keys
            
            ptrs = []
            for i in range(len(keys) + 1):
                ptrs.append(np.array([ptr_cells[i][0].get_center()[0], ptr_cells[i][0].get_bottom()[1], 0]))
            group.ptrs = ptrs
            return group

        # ===== PHASE A2 — 实例引入 =====
        with self.voiceover(
            text="为了更好地理解 B树的查找，我们可以想象一个大型的“鞋靴仓库”。",
            subcaption="为了更好地理解 B-树的查找，我们可以想象一个大型的“鞋靴仓库”。"
        ) as tracker:
            self.wait(tracker.duration)

        with self.voiceover(

            text="在这个仓库中，每一个路口不仅展示着实际的鞋子样品，还划分了通往下一级仓库的通道。",

            subcaption="在这个仓库中，每一个路口不仅展示着实际的鞋子样品，还划分了通往下一级仓库的通道。"

        ) as tracker:
            bookshelf_root = make_btree_node(["38码", "42码"], np.array([0, 1.5, 0]), font_name="Microsoft YaHei", font_size=16, key_w=0.7)
            bookshelf_root.scale(1.2)
            
            # The ptrs must be updated because scaling does not scale the numpy arrays automatically
            r_ptrs = []
            ptr_cells = [bookshelf_root[0][i] for i in range(0, 5, 2)]
            for p in ptr_cells:
                r_ptrs.append(np.array([p[0].get_center()[0], p[0].get_bottom()[1], 0]))
            bookshelf_root.ptrs = r_ptrs
            
            bookshelf_c1 = make_btree_node(["35码"], np.array([-3.5, -1.0, 0]), font_name="Microsoft YaHei", font_size=16, key_w=0.7).scale(1.2)
            bookshelf_c2 = make_btree_node(["40码"], np.array([0, -1.0, 0]), font_name="Microsoft YaHei", font_size=16, key_w=0.7).scale(1.2)
            bookshelf_c3 = make_btree_node(["45码"], np.array([3.5, -1.0, 0]), font_name="Microsoft YaHei", font_size=16, key_w=0.7).scale(1.2)
            
            edges = VGroup(
                Line(bookshelf_root.ptrs[0], bookshelf_c1.get_top(), color=GRAY, stroke_width=2.5),
                Line(bookshelf_root.ptrs[1], bookshelf_c2.get_top(), color=GRAY, stroke_width=2.5),
                Line(bookshelf_root.ptrs[2], bookshelf_c3.get_top(), color=GRAY, stroke_width=2.5)
            )
            
            shelf_group = VGroup(edges, bookshelf_root, bookshelf_c1, bookshelf_c2, bookshelf_c3)
            self.play(FadeIn(shelf_group), run_time=tracker.duration)

        with self.voiceover(

            text="比如入口处摆放着 38码 和 42码 的鞋子。如果你恰好需要它们，直接拿走即可；否则，它们就将剩余的鞋子划分成了三个通道区间。",

            subcaption="比如入口处摆放着 38码 和 42码 的鞋子。如果你恰好需要它们，直接拿走即可；否则，它们就将剩余的鞋子划分成了三个通道区间。"

        ) as tracker:
            intervals = VGroup(
                Text("<38码", font_size=20, font="Microsoft YaHei", color=YELLOW).next_to(bookshelf_root.ptrs[0], DOWN, buff=0.2),
                Text("38-42码", font_size=20, font="Microsoft YaHei", color=YELLOW).next_to(bookshelf_root.ptrs[1], DOWN, buff=0.2),
                Text(">42码", font_size=20, font="Microsoft YaHei", color=YELLOW).next_to(bookshelf_root.ptrs[2], DOWN, buff=0.2)
            )
            self.play(FadeIn(intervals), run_time=tracker.duration)

        with self.voiceover(

            text="当你要找一双 40码 的鞋子时，你只需要做三件事：",

            subcaption="当你要找一双 40码 的鞋子时，你只需要做三件事："

        ) as tracker:
            key_text = Text("目标: 40码", font_size=24, font="Microsoft YaHei", color=YELLOW).to_corner(UL).shift(DOWN * 0.5)
            self.play(FadeIn(key_text))
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(

            text="第一，查看当前路口的鞋子样品，判断是否是你需要的；",

            subcaption="第一，查看当前路口的鞋子样品，判断是否是你需要的；"

        ) as tracker:
            self.play(Indicate(bookshelf_root.cells, color=RED), run_time=tracker.duration)

        with self.voiceover(

            text="第二，若未命中，则判断 40码 属于哪个区间。显然它在 38 到 42 之间；",

            subcaption="第二，若未命中，则判断 40码 属于哪个区间。显然它在 38 到 42 之间；"

        ) as tracker:
            self.play(Indicate(intervals[1], color=GREEN), run_time=tracker.duration)

        with self.voiceover(

            text="第三，顺着对应的中间通道进入下一级仓库继续寻找。在这里，我们顺利找到了 40码 的鞋子。",

            subcaption="第三，顺着对应的中间通道进入下一级仓库继续寻找。在这里，我们顺利找到了 40码 的鞋子。"

        ) as tracker:
            self.play(Indicate(edges[1], color=YELLOW), run_time=0.8)
            
            p_rect = SurroundingRectangle(bookshelf_c2, color=YELLOW, buff=0.1)
            self.play(Create(p_rect), run_time=0.5)
            self.play(bookshelf_c2.cells[0].animate.set_fill(GREEN, opacity=0.8), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 1.8))
            
        with self.voiceover(
            
            text="既能直接命中数据，又能引导向下层查找，这就是 B树的精髓所在。",
            
            subcaption="既能直接命中数据，又能引导向下层查找，这就是 B-树的精髓所在。"
            
        ) as tracker:
            self.play(FadeOut(shelf_group), FadeOut(intervals), FadeOut(key_text), FadeOut(p_rect), run_time=tracker.duration)

        # ===== PHASE A3 — 核心思想 =====
        logic_title = Text("B-树查找核心逻辑", font_size=36, font="Microsoft YaHei", color=YELLOW)
        logic_1 = Text("1. 将给定值与结点内的关键字进行比较", font_size=24, font="Microsoft YaHei")
        logic_2 = Text("2. 若找到目标值，则查找成功", font_size=24, font="Microsoft YaHei")
        logic_3 = Text("3. 若未找到且子树不为空，则进入对应区间的子结点继续查找", font_size=24, font="Microsoft YaHei")
        logic_4 = Text("4. 若直至叶子结点的指针为空仍未找到，则查找失败", font_size=24, font="Microsoft YaHei")

        logic_group = VGroup(logic_title, logic_1, logic_2, logic_3, logic_4).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        logic_box = SurroundingRectangle(logic_group, color=BLUE, buff=0.6, corner_radius=0.2)
        logic_panel = VGroup(logic_box, logic_group).move_to(ORIGIN)

        with self.voiceover(
            text="在正式的 B 树中，我们需要将目标值与当前结点的多个关键字比较。这份 Python 代码通过 search 方法顺序比较，得到最后一个不大于目标值的关键字下标 i。",
            subcaption="在正式的 B-树中，Python 的 search 方法依次比较当前结点的关键字，返回最后一个不大于 key 的下标 i。"
        ) as tracker:
            self.play(FadeIn(logic_box), FadeIn(logic_title), FadeIn(logic_1), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(
            text="如果在自上而下的查找过程中，找到了目标值，则查找成功；如果直到叶子结点都没有找到，并且对应的子树指针为空，则查找失败。",
            subcaption="如果在自上而下的查找过程中，找到了目标值，则查找成功；如果直到叶子结点都没有找到，并且对应的子树指针为空，则查找失败。"
        ) as tracker:
            self.play(FadeIn(logic_2), FadeIn(logic_3), FadeIn(logic_4), run_time=1.5)
            self.wait(max(0.1, tracker.duration - 1.5))

        self.play(FadeOut(logic_panel), FadeOut(algo_title))


        # 展示实际运行的 Python 方法，行号由源码定位，避免讲解与代码脱节。
        helper_lines = method_lines(BTree.search)
        python_lines = helper_lines + method_lines(BTree.search_btree)
        def line_index(fragment):
            return next(i for i, line in enumerate(python_lines) if fragment in line)

        IDX_INIT = line_index("p = t")
        IDX_WHILE = line_index("while p and not found:")
        IDX_SEARCH = line_index("i = self.search(p, key)")
        IDX_CHECK = line_index("if i > 0 and p.k[i] == key:")
        IDX_FOUND = line_index("found = True")
        IDX_ELSE = line_index("else:")
        IDX_MOVE_Q = line_index("q = p")
        IDX_MOVE_P = line_index("p = p.ptr[i]")
        IDX_RET_SUCC = line_index("return Result(p, i, 1)")
        IDX_RET_FAIL = line_index("return Result(q, i, 0)")

        code_block = PythonCodePanel(
            python_lines, title="Python 查找（m = 4）", page_starts=[0, len(helper_lines)]
        )
        get_track_anims = code_block.track

        self.play(FadeIn(code_block), run_time=0.8)
        with self.voiceover(
            text="先看结点内的 search 方法。关键字数组从一开始存放有效值；while 循环逐个比较，只要下一个关键字不大于 key，就把 i 加一。最后 i 也正是向下选择子树指针的下标。",
            subcaption="search 方法按 k[1]、k[2] 依次比较；满足 k[i+1] <= key 时 i 加 1，返回的 i 同时是 ptr[i] 的下标。"
        ) as tracker:
            self.play(*get_track_anims(line_index("while i < p.keynum")), run_time=0.4)
            self.play(*get_track_anims(line_index("i += 1")), run_time=0.4)
            self.play(*get_track_anims(line_index("return i")), run_time=0.4)
            self.wait(max(0.1, tracker.duration - 1.2))

        # ===== PHASE C — 场景初始化 (绘制 B-树) =====

        pos = {
            'N35': np.array([-3.0, 1.2, 0]),
            'N18': np.array([-4.85, -0.25, 0]),
            'N43_78': np.array([-1.15, -0.25, 0]),
            'N11': np.array([-6.0, -1.75, 0]),
            'N27': np.array([-4.10, -1.75, 0]),
            'N39': np.array([-2.55, -1.75, 0]),
            'N47_53_64': np.array([-0.65, -1.75, 0]),
            'N99': np.array([1.45, -1.75, 0]),
        }

        nodes = {}
        for k, p in pos.items():
            keys = [int(x) for x in k[1:].split('_')]
            nodes[k] = make_btree_node(keys, p)

        def btree_edge(p1, p2, color=GRAY, sw=2.5):
            return Line(p1, p2, color=color, stroke_width=sw)

        edges = VGroup(
            btree_edge(nodes['N35'].ptrs[0], nodes['N18'].get_top()),
            btree_edge(nodes['N35'].ptrs[1], nodes['N43_78'].get_top()),
            
            btree_edge(nodes['N18'].ptrs[0], nodes['N11'].get_top()),
            btree_edge(nodes['N18'].ptrs[1], nodes['N27'].get_top()),
            
            btree_edge(nodes['N43_78'].ptrs[0], nodes['N39'].get_top()),
            btree_edge(nodes['N43_78'].ptrs[1], nodes['N47_53_64'].get_top()),
            btree_edge(nodes['N43_78'].ptrs[2], nodes['N99'].get_top()),
        )
        
        tree_group = VGroup(edges, *nodes.values())
        tree_group.scale(min(0.85, 6.5 / tree_group.width)).move_to([-3.45, -0.15, 0])
        for node in nodes.values():
            node.ptrs = [node[0][2 * i][0].get_bottom().copy() for i in range(len(node.keys) + 1)]
        
        with self.voiceover(
        
            text="这是一棵 4 阶 B树，我们已经插入了一些结点，左侧就是它的最终结构。",
        
            subcaption="这是一棵 4 阶 B-树，我们已经插入了一些结点，左侧就是它的最终结构。"
        
        ) as tracker:
            self.play(FadeIn(tree_group), run_time=tracker.duration)

        # ===== PHASE D — 成功查找演示 (53) =====
        with self.voiceover(
            text="我们先来演示查找成功的情况，例如查找关键字 53。",
            subcaption="我们先来演示查找成功的情况，例如查找关键字 53。"
        ) as tracker:
            search_text = VGroup(
                Text("目标值", font="Microsoft YaHei", font_size=26, color=YELLOW),
                Text("key = 53", font="Consolas", font_size=26, color=YELLOW),
            ).arrange(RIGHT, buff=0.15).to_corner(UL, buff=0.8).shift(DOWN * 0.2)
            self.play(FadeIn(search_text))
            
        with self.voiceover(
            
            text="初始化指针 p 指向根结点。",
            
            subcaption="初始化指针 p 指向根结点。"
            
        ) as tracker:
            self.play(*get_track_anims(IDX_INIT), run_time=0.5)
            p_rect = SurroundingRectangle(nodes['N35'], color=YELLOW, buff=0.1, stroke_width=4)
            p_label = Text("p", font_size=24, color=YELLOW).next_to(p_rect, UP, buff=0.1)
            p_group = VGroup(p_rect, p_label)
            self.play(FadeIn(p_group), run_time=0.5)

        with self.voiceover(

            text="当 p 不为空且尚未找到时，进入循环。",

            subcaption="当 p 不为空且尚未找到时，进入循环。"

        ) as tracker:
            self.play(*get_track_anims(IDX_WHILE), run_time=0.5)

        with self.voiceover(

            text="在当前结点内查找给定的 key。对于关键字 35，由于 53 大于 35，我们需要沿着右侧指针继续查找。",

            subcaption="在当前结点内查找给定的 key。对于关键字 35，由于 53 大于 35，我们需要沿着右侧指针继续查找。"

        ) as tracker:
            self.play(*get_track_anims(IDX_SEARCH), run_time=0.5)
            self.play(Indicate(nodes['N35'].cells[0], color=RED), run_time=0.5)
            self.play(*get_track_anims(IDX_CHECK), run_time=0.5)

        with self.voiceover(

            text="没找到 53，进入 else 分支。",

            subcaption="没找到 53，进入 else 分支。"

        ) as tracker:
            self.play(*get_track_anims(IDX_ELSE), run_time=0.5)
            self.play(*get_track_anims(IDX_MOVE_Q), run_time=0.5)

        with self.voiceover(

            text="将 p 更新为它的右子结点。",

            subcaption="将 p 更新为它的右子结点。"

        ) as tracker:
            self.play(*get_track_anims(IDX_MOVE_P), run_time=0.5)
            self.play(p_rect.animate.become(SurroundingRectangle(nodes['N43_78'], color=YELLOW, buff=0.1, stroke_width=4)),
                      p_label.animate.next_to(nodes['N43_78'], UP, buff=0.2), run_time=1.0)
            
        with self.voiceover(
            
            text="开始下一轮循环。",
            
            subcaption="开始下一轮循环。"
            
        ) as tracker:
            self.play(*get_track_anims(IDX_WHILE), run_time=0.5)
            
        with self.voiceover(
            
            text="在当前结点内比较。53 大于 43，且小于 78，因此沿着中间的指针继续向下。",
            
            subcaption="在当前结点内比较。53 大于 43，且小于 78，因此沿着中间的指针继续向下。"
            
        ) as tracker:
            self.play(*get_track_anims(IDX_SEARCH), run_time=0.5)
            self.play(Indicate(nodes['N43_78'].cells[0], color=RED), run_time=0.5)
            self.play(Indicate(nodes['N43_78'].cells[1], color=RED), run_time=0.5)
            
        with self.voiceover(
            
            text="没找到，继续进入 else 分支更新指针 p。",
            
            subcaption="没找到，继续进入 else 分支更新指针 p。"
            
        ) as tracker:
            self.play(*get_track_anims(IDX_CHECK), run_time=0.3)
            self.play(*get_track_anims(IDX_ELSE), run_time=0.3)
            self.play(*get_track_anims(IDX_MOVE_Q), run_time=0.3)
            self.play(*get_track_anims(IDX_MOVE_P), run_time=0.5)
            
            self.play(p_rect.animate.become(SurroundingRectangle(nodes['N47_53_64'], color=YELLOW, buff=0.1, stroke_width=4)),
                      p_label.animate.next_to(nodes['N47_53_64'], UP, buff=0.2), run_time=1.0)
            
        with self.voiceover(
            
            text="继续循环。",
            
            subcaption="继续循环。"
            
        ) as tracker:
            self.play(*get_track_anims(IDX_WHILE), run_time=0.5)
            
        with self.voiceover(
            
            text="在结点内查找，先看到 47，小于目标值 53；继续比较下一个关键字，发现 53 正好等于目标值。",
            
            subcaption="在结点内查找，先看到 47，小于目标值 53；继续比较下一个关键字，发现 53 正好等于目标值。"
            
        ) as tracker:
            self.play(*get_track_anims(IDX_SEARCH), run_time=0.5)
            self.play(Indicate(nodes['N47_53_64'].cells[0], color=RED), run_time=0.5)
            self.play(nodes['N47_53_64'].cells[1].animate.set_fill(GREEN, opacity=0.8), run_time=0.5)
            
        with self.voiceover(
            
            text="此时 Python 的 found 变为 True，查找成功！",
            
            subcaption="此时 Python 的 found 变为 True，查找成功！"
            
        ) as tracker:
            self.play(*get_track_anims(IDX_CHECK), run_time=0.5)
            self.play(*get_track_anims(IDX_FOUND), run_time=0.5)
            
        with self.voiceover(
            
            text="循环结束，返回查找成功的结点指针和位置。",
            
            subcaption="循环结束，返回查找成功的结点指针和位置。"
            
        ) as tracker:
            self.play(*get_track_anims(IDX_WHILE), run_time=0.5)
            self.play(*get_track_anims(IDX_RET_SUCC), run_time=0.5)
            
        self.play(nodes['N47_53_64'].cells[1].animate.set_fill(BLUE, opacity=0.15), FadeOut(p_group), FadeOut(search_text), run_time=1.0)


        # ===== PHASE E — 失败查找演示 (80) =====
        with self.voiceover(
            text="接下来，我们演示查找失败的情况，比如查找 80。",
            subcaption="接下来，我们演示查找失败的情况，比如查找 80。"
        ) as tracker:
            # Consolas distinguishes the digit zero from a lowercase letter o.
            search_text = VGroup(
                Text("目标值", font="Microsoft YaHei", font_size=26, color=YELLOW),
                Text("key = 80", font="Consolas", font_size=26, color=YELLOW),
            ).arrange(RIGHT, buff=0.15).to_corner(UL, buff=0.8).shift(DOWN * 0.2)
            self.play(FadeIn(search_text))
            
        with self.voiceover(
            
            text="同样，从根结点开始搜索。",
            
            subcaption="同样，从根结点开始搜索。"
            
        ) as tracker:
            self.play(*get_track_anims(IDX_INIT), run_time=0.5)
            p_rect.become(SurroundingRectangle(nodes['N35'], color=YELLOW, buff=0.1, stroke_width=4))
            p_label.next_to(p_rect, UP, buff=0.1)
            self.play(FadeIn(p_group), run_time=0.5)
            
        with self.voiceover(
            
            text="80 大于 35，顺着右侧指针向下。",
            
            subcaption="80 大于 35，顺着右侧指针向下。"
            
        ) as tracker:
            self.play(*get_track_anims(IDX_WHILE), run_time=0.2)
            self.play(*get_track_anims(IDX_SEARCH), run_time=0.2)
            self.play(Indicate(nodes['N35'].cells[0], color=RED), run_time=0.5)
            self.play(*get_track_anims(IDX_ELSE), run_time=0.2)
            self.play(*get_track_anims(IDX_MOVE_P), run_time=0.2)
            self.play(p_rect.animate.become(SurroundingRectangle(nodes['N43_78'], color=YELLOW, buff=0.1, stroke_width=4)),
                      p_label.animate.next_to(nodes['N43_78'], UP, buff=0.2), run_time=0.8)
                      
        with self.voiceover(
                      
            text="在当前结点内，80 大于 78，因此沿着最右侧指针继续向下查找。",
                      
            subcaption="在当前结点内，80 大于 78，因此沿着最右侧指针继续向下查找。"
                      
        ) as tracker:
            self.play(*get_track_anims(IDX_WHILE), run_time=0.2)
            self.play(*get_track_anims(IDX_SEARCH), run_time=0.2)
            self.play(Indicate(nodes['N43_78'].cells[1], color=RED), run_time=0.5)
            self.play(*get_track_anims(IDX_ELSE), run_time=0.2)
            self.play(*get_track_anims(IDX_MOVE_P), run_time=0.2)
            self.play(p_rect.animate.become(SurroundingRectangle(nodes['N99'], color=YELLOW, buff=0.1, stroke_width=4)),
                      p_label.animate.next_to(nodes['N99'], UP, buff=0.2), run_time=0.8)
                      
        with self.voiceover(
                      
            text="在结点中，80 小于 99，本应沿着左侧指针向下。但是，这里已经是叶子结点，它的左侧指针为空。",
                      
            subcaption="在结点中，80 小于 99，本应沿着左侧指针向下。但是，这里已经是叶子结点，它的左侧指针为空。"
                      
        ) as tracker:
            self.play(*get_track_anims(IDX_WHILE), run_time=0.2)
            self.play(*get_track_anims(IDX_SEARCH), run_time=0.2)
            self.play(Indicate(nodes['N99'].cells[0], color=RED), run_time=0.5)
            self.play(*get_track_anims(IDX_ELSE), run_time=0.2)
            self.play(*get_track_anims(IDX_MOVE_P), run_time=0.2)
            
            null_pos = nodes['N99'].ptrs[0] + DOWN * 0.6
            self.play(p_rect.animate.become(Rectangle(width=0.6, height=0.45, color=YELLOW, stroke_width=4).move_to(null_pos)),
                      p_label.animate.next_to(null_pos, UP, buff=0.3), run_time=0.8)
            null_text = Text("None", font="Consolas", font_size=20, color=GRAY).move_to(null_pos)
            self.play(FadeIn(null_text))
            
        with self.voiceover(
            
            text="此时指针 p 为空，退出循环。",
            
            subcaption="此时指针 p 为空，退出循环。"
            
        ) as tracker:
            self.play(*get_track_anims(IDX_WHILE), run_time=0.5)
            
        with self.voiceover(
            
            text="Python 返回 Result 对象，其中 pt 是最后访问的结点 q，i 是插入位置之前的关键字下标，tag 等于零，表示查找失败。",
            
            subcaption="返回 Result(q, i, 0)：pt 为最后访问的结点 q，i 为插入位置之前的关键字下标，tag 为 0。"
            
        ) as tracker:
            self.play(*get_track_anims(IDX_RET_FAIL), run_time=0.5)
            
        self.play(FadeOut(p_group), FadeOut(null_text), FadeOut(search_text), run_time=1.0)

        # ===== PHASE F — 复杂度分析 =====
        self.play(*get_track_anims(None), FadeOut(code_block), run_time=0.5)
        
        time_box = VGroup(Text("时间复杂度：", font_size=28, font="Microsoft YaHei", color=YELLOW),
                          MathTex("O(\\log_M N)", font_size=32, color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=28, font="Microsoft YaHei", color=YELLOW),
                           MathTex("O(1)", font_size=32, color=YELLOW)).arrange(RIGHT, buff=0.1)
        asl_box = VGroup(
            Text("平均查找长度：", font_size=25, font="Microsoft YaHei", color=GREEN),
            Text("由树高决定，属于对数级", font_size=22, font="Microsoft YaHei", color=GREEN),
        ).arrange(RIGHT, buff=0.1)
        summary = VGroup(time_box, space_box, asl_box).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        summary.to_edge(RIGHT, buff=1.5)
        
        with self.voiceover(
        
            text="总结一下，在最坏和平均情况下，B树的查找都需要从根结点顺着子树一直查找到叶结点。",
        
            subcaption="总结一下，在最坏和平均情况下，B-树的查找都需要从根结点顺着子树一直查找到叶结点。"
        
        ) as tracker:
            self.wait(tracker.duration)
            
        with self.voiceover(
            
            text="对于 M 阶 B树，如果有 N 个关键字，时间复杂度为 O(log_M N)。",
            
            subcaption="对于 M 阶 B-树，如果有 N 个关键字，时间复杂度为 O(log_M N)。"
            
        ) as tracker:
            self.play(FadeIn(time_box), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))
            
        with self.voiceover(
            
            text="整个查找过程只需要常数级别的辅助指针变量，因此空间复杂度为 O(1)。",
            
            subcaption="整个查找过程只需要常数级别的辅助指针变量，因此空间复杂度为 O(1)。"
            
        ) as tracker:
            self.play(FadeIn(space_box), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
            text="再看平均查找长度。B树查找访问多少个结点，主要取决于从根到目标结点的路径长度，也就是树高。",
            subcaption="再看平均查找长度。B-树查找访问多少个结点，主要取决于从根到目标结点的路径长度，也就是树高。"
        ) as tracker:
            self.play(FadeIn(asl_box), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
            text="m阶B树除根结点外，每个非终端结点至少有约一半的分支，因此随着层数增加，能覆盖的关键字数量会快速增长。",
            subcaption="m 阶 B-树除根结点外，每个非终端结点至少有约一半的分支，因此层数增加时，能覆盖的关键字数量会快速增长。"
        ) as tracker:
            self.play(asl_box.animate.set_color(YELLOW), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
            text="所以，含有 N 个关键字的B树，其查找路径上的结点数有对数级上界。也就是说，平均查找长度通常随 log N 增长。",
            subcaption="所以，含有 N 个关键字的 B-树，其查找路径上的结点数有对数级上界。平均查找长度通常随 log N 增长。"
        ) as tracker:
            self.play(asl_box.animate.set_color(GREEN), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 0.8))

        with self.voiceover(
            
            text="以上就是 B树查找算法的完整演示。",
            
            subcaption="以上就是 B-树查找算法的完整演示。"
            
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)
