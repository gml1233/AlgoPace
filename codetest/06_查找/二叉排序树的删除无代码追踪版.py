# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class BSTDeleteNoCodeVideo(VoiceoverScene):
    NODE_R = 0.35

    def make_node(self, label, center, r=None, color=BLUE):
        r = self.NODE_R if r is None else r
        c = Circle(radius=r, color=color, fill_color=color, fill_opacity=0.15, stroke_width=2.5).move_to(center)
        t = Text(str(label), font="Arial", font_size=20, color=WHITE).move_to(center)
        g = VGroup(c, t)
        g.circle = c
        g.label = t
        return g

    def make_edge(self, p1, p2, r1=None, r2=None, color=GRAY, sw=2.5):
        r1 = self.NODE_R if r1 is None else r1
        r2 = self.NODE_R if r2 is None else r2
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        return Line(p1 + u * r1, p2 - u * r2, color=color, stroke_width=sw)

    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(1.5).to_corner(UR, buff=0.15)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("二叉排序树的删除（无代码跟踪版）", font_size=36, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.12)
        self.play(FadeIn(algo_title), run_time=0.8)

        # Setup Tree
        scale_factor = 1.0
        shift_vec = np.array([0, -0.1, 0])

        pos = {
            45: np.array([0.0, 2.05, 0]),
            24: np.array([-1.9, 0.65, 0]),
            53: np.array([1.9, 0.65, 0]),
            12: np.array([-3.0, -0.85, 0]),
            37: np.array([-0.8, -0.85, 0]),
            93: np.array([2.4, -0.85, 0])
        }
        for k in pos:
            pos[k] = pos[k] * scale_factor + shift_vec

        nodes = {}
        for val, p in pos.items():
            nodes[val] = self.make_node(val, p)

        edges_data = [
            (45, 24), (45, 53),
            (24, 12), (24, 37),
            (53, 93)
        ]
        edges = {}
        for u, v in edges_data:
            edges[(u, v)] = self.make_edge(pos[u], pos[v])

        tree_group = VGroup(*nodes.values(), *edges.values())

        # Setup Panel
        panel_title = Text("二叉排序树删除操作", font_size=24, color=YELLOW, font="Microsoft YaHei")
        p1 = Text("① 若待删结点为叶子结点", font_size=18, font="Microsoft YaHei")
        p2 = Text("② 若待删结点只有一棵子树", font_size=18, font="Microsoft YaHei")
        p3 = Text("③ 若待删结点左右子树均不空", font_size=18, font="Microsoft YaHei")
        panel = VGroup(panel_title, p1, p2, p3).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        panel_box = RoundedRectangle(
            corner_radius=0.1,
            height=panel.get_height() + 0.4,
            width=panel.get_width() + 0.4,
            color=GRAY, fill_color=BLACK, fill_opacity=0.6, stroke_width=1.5
        ).move_to(panel)
        panel_group = VGroup(panel_box, panel).scale(0.9).to_corner(UL, buff=0.25).shift(DOWN * 0.45)

        with self.voiceover(text="本节我们来学习二叉排序树的删除操作。该算法是从二叉排序树中删除关键字等于key的结点，具体分为三种情况。") as tracker:
            self.play(FadeIn(tree_group), FadeIn(panel_group), run_time=tracker.duration)

        with self.voiceover(text="实际操作时，第一步总是先查找。我们从根结点开始，按照二叉排序树的比较规则，去寻找关键字为 key 的结点。如果最后没有找到，那么删除操作就结束，原来的树保持不变。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="如果找到了待删结点，我们把它记作 p，把 p 的双亲结点记作 f。接下来，删除操作会根据 p 的孩子情况分成三类，这是学习这个算法最关键的部分。") as tracker:
            self.wait(tracker.duration)

        # ===== CASE 1 =====
        with self.voiceover(text="第一种情况最简单：p 是叶子结点，也就是它既没有左孩子，也没有右孩子。下面以删除结点 12 为例。") as tracker:
            self.play(p1.animate.set_color(RED))
            self.play(nodes[12].circle.animate.set_color(RED).set_fill(RED, 0.5))
            label_p = Text("p", font_size=24, color=RED, font="Consolas").next_to(nodes[12], RIGHT)
            self.play(FadeIn(label_p), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 1.5))

        with self.voiceover(text="因为叶子结点下面没有任何子树，所以删掉它不会影响别的结点的位置。我们只需要找到它的双亲 f，这里就是结点 24。") as tracker:
            self.play(nodes[24].circle.animate.set_color(GREEN).set_fill(GREEN, 0.5))
            label_f = Text("f", font_size=24, color=GREEN, font="Consolas").next_to(nodes[24], LEFT)
            self.play(FadeIn(label_f), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(text="接下来，把双亲 f 中原来指向 p 的那条孩子指针改为空，也就是把这条连线断开。断开以后，结点 12 就可以直接删除了。") as tracker:
            self.play(
                FadeOut(edges[(24, 12)]),
                FadeOut(nodes[12]),
                FadeOut(label_p),
                run_time=1.0
            )
            self.wait(max(0.1, tracker.duration - 1.0))

        self.play(
            nodes[24].circle.animate.set_color(BLUE).set_fill(BLUE, 0.15),
            FadeOut(label_f),
            p1.animate.set_color(WHITE)
        )
        self.play(FadeIn(nodes[12]), Create(edges[(24, 12)]), run_time=0.5)

        # ===== CASE 2 =====
        with self.voiceover(text="第二种情况是：p 只有一棵子树。也就是说，它要么只有左子树，要么只有右子树。下面以删除结点 53 为例。") as tracker:
            self.play(p2.animate.set_color(RED))
            self.play(nodes[53].circle.animate.set_color(RED).set_fill(RED, 0.5))
            label_p = Text("p", font_size=24, color=RED, font="Consolas").next_to(nodes[53], RIGHT)
            self.play(FadeIn(label_p), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 1.5))

        with self.voiceover(text="先看清这个局部结构。结点 53 的双亲 f 是 45，而且 53 只有一棵右子树，也就是结点 93 所在的这棵子树。") as tracker:
            self.play(nodes[45].circle.animate.set_color(GREEN).set_fill(GREEN, 0.5))
            label_f = Text("f", font_size=24, color=GREEN, font="Consolas").next_to(nodes[45], RIGHT)
            self.play(FadeIn(label_f), run_time=0.5)
            self.play(nodes[93].circle.animate.set_color(YELLOW).set_fill(YELLOW, 0.5))
            label_child = Text("p唯一的子树", font_size=18, color=YELLOW, font="Microsoft YaHei").next_to(nodes[93], DOWN, buff=0.15)
            self.play(FadeIn(label_child), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 2.0))

        with self.voiceover(text="这种情况下的核心思想是越过 p。既然 p 只有一条向下的分支，那么我们就让 p 的唯一子树直接接到双亲 f 的原来位置上，然后再删除结点 53。") as tracker:
            self.play(
                FadeOut(edges[(45, 53)]),
                FadeOut(edges[(53, 93)]),
                FadeOut(nodes[53]),
                FadeOut(label_p)
            )
            self.play(
                nodes[93].animate.move_to(pos[53]),
                label_child.animate.next_to(pos[53], DOWN, buff=0.15)
            )
            new_edge_45_93 = self.make_edge(pos[45], pos[53])
            self.play(Create(new_edge_45_93))
            self.wait(max(0.1, tracker.duration - 3.0))

        self.play(
            nodes[45].circle.animate.set_color(BLUE).set_fill(BLUE, 0.15),
            nodes[93].circle.animate.set_color(BLUE).set_fill(BLUE, 0.15),
            FadeOut(label_f),
            FadeOut(label_child),
            p2.animate.set_color(WHITE)
        )

        self.play(
            FadeOut(new_edge_45_93),
            nodes[93].animate.move_to(pos[93]),
            FadeIn(nodes[53]),
            Create(edges[(45, 53)]),
            Create(edges[(53, 93)]),
            run_time=0.8
        )

        # ===== CASE 3 =====
        with self.voiceover(text="第三种情况最复杂：p 的左子树和右子树都不为空。也就是说，p 的下面两边都有内容。下面以删除结点 45 为例。") as tracker:
            self.play(p3.animate.set_color(RED))
            self.play(nodes[45].circle.animate.set_color(RED).set_fill(RED, 0.5))
            label_p = Text("p", font_size=24, color=RED, font="Consolas").next_to(nodes[45], LEFT)
            self.play(FadeIn(label_p), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 1.5))

        with self.voiceover(text="这一类情况之所以难，是因为 p 两边都有子树，不能像前两种情况那样直接删掉。为了在删除后仍然保持二叉排序树的性质，通常有两种处理思路。我们先看第一种。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="方法一是：让 p 的左子树整体上移，直接取代 p。这里 p 本身就是根结点，所以双亲 f 为空，准备上移的是以 24 为根的左子树。") as tracker:
            label_f = Text("f=NULL", font_size=20, color=GREEN, font="Consolas").next_to(nodes[45], UP, buff=0.2)
            self.play(FadeIn(label_f), run_time=0.5)
            self.play(nodes[24].circle.animate.set_color(YELLOW).set_fill(YELLOW, 0.5))
            label_pl = Text("p的左子树", font_size=18, color=YELLOW, font="Microsoft YaHei").next_to(nodes[24], LEFT)
            self.play(FadeIn(label_pl), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 1.5))

        with self.voiceover(text="不过，左子树整体上移之后，p 原来的右子树还不能丢掉。所以我们还要在左子树中找到最大的那个结点，也就是 p 的直接前驱 s。找的方法很简单：从左孩子出发，一直向右走到底，这里找到的是结点 37。") as tracker:
            self.play(nodes[37].circle.animate.set_color(ORANGE).set_fill(ORANGE, 0.5))
            label_s1 = Text("s", font_size=24, color=ORANGE, font="Consolas").next_to(nodes[37], UP, buff=0.15)
            self.play(FadeIn(label_s1), run_time=0.5)
            self.wait(max(0.1, tracker.duration - 0.5))

        with self.voiceover(text="然后，把 p 的右子树接到前驱 s 的右边。这样处理以后，s 左边的值仍然都比它小，右边新接过来的值仍然都比它大，因此整棵树依然满足二叉排序树左小右大的关系。") as tracker:
            self.play(nodes[53].circle.animate.set_color(PURPLE).set_fill(PURPLE, 0.5))
            label_pr = Text("p的右子树", font_size=18, color=PURPLE, font="Microsoft YaHei").next_to(nodes[53], RIGHT)
            self.play(FadeIn(label_pr), run_time=0.5)
            
            # Animate topological change for Method A with proper subtree shifting
            vec_L = pos[45] - pos[24]
            vec_R = (pos[37] + vec_L + np.array([1.0, -0.75, 0])) - pos[53]

            nodes_L = [24, 12, 37]
            edges_L = [(24, 12), (24, 37)]
            nodes_R = [53, 93]
            edges_R = [(53, 93)]

            self.play(
                FadeOut(edges[(45, 24)]),
                FadeOut(edges[(45, 53)]),
                FadeOut(nodes[45]),
                FadeOut(label_p)
            )
            
            anims = []
            for n in nodes_L:
                anims.append(nodes[n].animate.shift(vec_L))
            for e in edges_L:
                anims.append(edges[e].animate.shift(vec_L))
            anims.append(label_pl.animate.shift(vec_L))
            anims.append(label_s1.animate.shift(vec_L))
            
            for n in nodes_R:
                anims.append(nodes[n].animate.shift(vec_R))
            for e in edges_R:
                anims.append(edges[e].animate.shift(vec_R))
            anims.append(label_pr.animate.shift(vec_R))
            
            self.play(*anims, run_time=1.0)
            
            new_edge_37_53 = self.make_edge(pos[37] + vec_L, pos[53] + vec_R)
            self.play(Create(new_edge_37_53))
            self.wait(max(0.1, tracker.duration - 2.5))

        with self.voiceover(text="不过，这种整体拼接的方法虽然直观，但有时会让树的高度增加。所以在实际教学和实现中，更常用第二种方法。下面我们先撤销刚才的演示，再来看更标准的做法。") as tracker:
            # Undo Method A
            self.play(FadeOut(new_edge_37_53))
            
            anims_undo = []
            for n in nodes_L:
                anims_undo.append(nodes[n].animate.shift(-vec_L))
            for e in edges_L:
                anims_undo.append(edges[e].animate.shift(-vec_L))
            anims_undo.append(label_pl.animate.shift(-vec_L))
            anims_undo.append(label_s1.animate.shift(-vec_L))
            
            for n in nodes_R:
                anims_undo.append(nodes[n].animate.shift(-vec_R))
            for e in edges_R:
                anims_undo.append(edges[e].animate.shift(-vec_R))
            anims_undo.append(label_pr.animate.shift(-vec_R))
            
            self.play(*anims_undo, run_time=1.0)

            self.play(
                FadeIn(nodes[45]), FadeIn(label_p),
                Create(edges[(45, 24)]), Create(edges[(45, 53)])
            )
            self.play(
                nodes[45].circle.animate.set_color(BLUE).set_fill(BLUE, 0.15),
                nodes[24].circle.animate.set_color(BLUE).set_fill(BLUE, 0.15),
                nodes[37].circle.animate.set_color(BLUE).set_fill(BLUE, 0.15),
                nodes[53].circle.animate.set_color(BLUE).set_fill(BLUE, 0.15),
                FadeOut(label_f), FadeOut(label_pl), FadeOut(label_s1), FadeOut(label_pr)
            )
            self.wait(max(0.1, tracker.duration - 2.5))

        with self.voiceover(text="方法二是：不用真的把整棵子树大幅搬动，而是让 p 的直接前驱，或者直接后继，来顶替 p。这样做更常见。这里我们以前驱为例。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="先回忆一个结论：在中序遍历序列里，一个结点的直接前驱，就是它左子树中最大的结点。所以从 p 的左子树出发，一直向右走到底，就能找到这个前驱。") as tracker:
            self.play(nodes[24].circle.animate.set_color(YELLOW).set_fill(YELLOW, 0.5))
            self.wait(0.5)
            self.play(
                nodes[24].circle.animate.set_color(BLUE).set_fill(BLUE, 0.15),
                nodes[37].circle.animate.set_color(YELLOW).set_fill(YELLOW, 0.5)
            )
            self.wait(max(0.1, tracker.duration - 1.5))

        with self.voiceover(text="现在我们已经找到了直接前驱 s，也就是结点 37。为了后面改连线更清楚，我们再把 s 的双亲记作 q，这里 q 是结点 24。") as tracker:
            label_s = Text("s（前驱）", font_size=18, color=YELLOW, font="Microsoft YaHei").next_to(nodes[37], UP, buff=0.15)
            self.play(FadeIn(label_s))
            self.play(nodes[24].circle.animate.set_color(GREEN).set_fill(GREEN, 0.5))
            label_q = Text("q", font_size=24, color=GREEN, font="Consolas").next_to(nodes[24], LEFT)
            self.play(FadeIn(label_q))
            self.wait(max(0.1, tracker.duration - 2.0))

        with self.voiceover(text="第一步，不急着删结点，而是先把前驱 s 的关键字复制到 p 的位置上。这样一来，从数值上看，原来的 45 就已经被 37 替代了。") as tracker:
            self.play(
                nodes[45].label.animate.become(Text("37", font="Arial", font_size=20, color=WHITE).move_to(nodes[45].label.get_center()))
            )
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(text="接下来，再去删除原来那个前驱结点 s。为什么这一步更容易呢？因为直接前驱 s 不可能有右子树，它最多只有一棵左子树，所以问题会自动转化成我们刚讲过的第二种情况。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="在这棵树里，前驱 37 没有左子树。因此删去 s 之后，只需要把 q 的右孩子改为空，就完成了这一轮调整。你可以把它理解为：先借值替身，再删除真正多出来的那个结点。") as tracker:
            self.play(
                FadeOut(edges[(24, 37)]),
                FadeOut(nodes[37]),
                FadeOut(label_s)
            )
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(text="这样，第三种情况也完成了。最终树中已经没有原来的结点 45，对应的位置由前驱 37 顶替，同时整棵树依然保持左边小、右边大的二叉排序树性质。") as tracker:
            self.play(
                nodes[45].circle.animate.set_color(BLUE).set_fill(BLUE, 0.15),
                nodes[24].circle.animate.set_color(BLUE).set_fill(BLUE, 0.15),
                FadeOut(label_p),
                FadeOut(label_q),
                p3.animate.set_color(WHITE)
            )
            self.wait(max(0.1, tracker.duration - 1.0))

        # ===== SUMMARY =====
        with self.voiceover(text="总结一下，二叉排序树的删除虽然看起来步骤比较多，但本质上只分为三种情况：删除叶子结点，删除只有一棵子树的结点，以及删除左右子树都存在的结点。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(
            text="本视频重点讲解了二叉排序树删除的整体思路和结构变化。如果你已经理解了这三种情况，再去看代码实现，就会更容易把每一次指针修改和树形变化一一对应起来。",
            subcaption="本视频重点讲解了二叉排序树删除的整体思路和结构变化。如果你已经理解了这三种情况，再去看代码实现，就会更容易把每一次指针修改和树形变化一一对应起来。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)
