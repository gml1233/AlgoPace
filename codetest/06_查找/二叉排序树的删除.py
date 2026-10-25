# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class BSTDeleteVideo(VoiceoverScene):
    NODE_R = 0.33
    ROLE_P = RED
    ROLE_F = GREEN
    ROLE_Q = TEAL_B
    ROLE_S = ORANGE

    def make_node(self, label, center, r=None, color=BLUE):
        r = self.NODE_R if r is None else r
        circle = Circle(
            radius=r,
            color=color,
            fill_color=color,
            fill_opacity=0.15,
            stroke_width=2.5,
        ).move_to(center)
        text = Text(str(label), font="Arial", font_size=18, color=WHITE).move_to(center)
        group = VGroup(circle, text)
        group.circle = circle
        group.label = text
        group.radius = r
        return group

    def make_edge(self, p1, p2, r1=None, r2=None, color=GRAY, sw=2.5):
        r1 = self.NODE_R if r1 is None else r1
        r2 = self.NODE_R if r2 is None else r2
        p1 = np.array(p1, dtype=float)
        p2 = np.array(p2, dtype=float)
        u = (p2 - p1) / np.linalg.norm(p2 - p1)
        return Line(p1 + u * r1, p2 - u * r2, color=color, stroke_width=sw)

    def build_demo_tree(self):
        raw_pos = {
            45: np.array([-3.0, 1.55, 0]),
            24: np.array([-4.45, 0.20, 0]),
            53: np.array([-1.55, 0.20, 0]),
            12: np.array([-5.25, -1.20, 0]),
            37: np.array([-3.65, -1.20, 0]),
            93: np.array([-1.10, -1.20, 0]),
        }
        scale_factor = 1.0
        shift_vec = np.array([0, -0.10, 0])

        pos = {}
        for key, pt in raw_pos.items():
            pos[key] = pt * scale_factor + shift_vec

        nodes = {}
        for key, pt in pos.items():
            nodes[key] = self.make_node(key, pt)

        edge_pairs = [
            (45, 24), (45, 53),
            (24, 12), (24, 37),
            (53, 93),
        ]
        edges = {}
        for u, v in edge_pairs:
            edges[(u, v)] = self.make_edge(pos[u], pos[v])

        group = VGroup(*edges.values(), *nodes.values())
        return {"pos": pos, "nodes": nodes, "edges": edges, "group": group}

    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(1.35).to_corner(UR, buff=0.12)
        self.add(logo)

        title = Text("二叉排序树的删除（代码跟踪版）", font_size=34, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.12)
        self.play(FadeIn(title), run_time=0.8)

        code_lines = [
            "void DeleteBST(BSTree &T, int key) {",
            "    BSTree p = T; BSTree f = NULL;",
            "    BSTree q, s;",
            "    while (p) {",
            "        if (p->data.key == key) break;",
            "        f = p;",
            "        if (p->data.key > key) p = p->lchild;",
            "        else p = p->rchild;",
            "    }",
            "    if (!p) return;",
            "    if (p->lchild && p->rchild) {",
            "        q = p; s = p->lchild;",
            "        while (s->rchild) { q = s; s = s->rchild; }",
            "        p->data = s->data;",
            "        if (q != p) q->rchild = s->lchild;",
            "        else q->lchild = s->lchild;",
            "        delete s;",
            "    } else {",
            "        if (!p->rchild) { q = p; p = p->lchild; }",
            "        else if (!p->lchild) { q = p; p = p->rchild; }",
            "        if (!f) T = p;",
            "        else if (q == f->lchild) f->lchild = p;",
            "        else f->rchild = p;",
            "        delete q;",
            "    }",
            "}",
        ]

        line_index = {
            "func": 0,
            "init": 1,
            "declare": 2,
            "while": 3,
            "found": 4,
            "parent": 5,
            "go_left": 6,
            "go_right": 7,
            "not_found": 9,
            "two_children": 10,
            "set_qs": 11,
            "pred_loop": 12,
            "copy": 13,
            "relink_right": 14,
            "relink_left": 15,
            "delete_s": 16,
            "else_block": 17,
            "no_right": 18,
            "no_left": 19,
            "root_case": 20,
            "link_left": 21,
            "link_right": 22,
            "delete_q": 23,
        }

        code_texts = []
        for line in code_lines:
            code_texts.append(Text(line.lstrip(" "), font="Consolas", font_size=11.5, color=WHITE))

        code_group = VGroup(*code_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.07)
        space_width = 0.08
        for i, line in enumerate(code_lines):
            indent = len(line) - len(line.lstrip(" "))
            code_texts[i].shift(RIGHT * indent * space_width)

        code_bg = RoundedRectangle(
            corner_radius=0.16,
            height=code_group.get_height() + 0.35,
            width=code_group.get_width() + 0.35,
            color=GRAY,
            fill_color=BLACK,
            fill_opacity=0.82,
            stroke_width=1.2,
        ).move_to(code_group)
        code_title = Text("DeleteBST 核心代码", font_size=20, color=YELLOW, font="Microsoft YaHei")
        code_block = VGroup(code_title, VGroup(code_bg, code_group)).arrange(DOWN, buff=0.16)
        code_block.next_to(logo, DOWN, buff=0.12).to_edge(RIGHT, buff=0.18)
        self.play(FadeIn(code_block), run_time=0.8)

        var_colors = {
            "key": YELLOW,
            "p": self.ROLE_P,
            "f": self.ROLE_F,
            "q": self.ROLE_Q,
            "s": self.ROLE_S,
        }
        case_text = Text("情况一：叶子 12", font_size=18, color=YELLOW, font="Microsoft YaHei")
        case_text.to_corner(UL, buff=0.18).shift(DOWN * 0.28 + RIGHT * 0.08)
        key_title = Text("待删除关键字", font_size=16, color=YELLOW, font="Microsoft YaHei").next_to(case_text, DOWN, aligned_edge=LEFT, buff=0.12)
        key_text = Text("key = --", font_size=20, color=YELLOW, font="Consolas").next_to(key_title, DOWN, aligned_edge=LEFT, buff=0.08)
        self.play(FadeIn(case_text), FadeIn(key_title), FadeIn(key_text), run_time=0.5)

        current_line = {"idx": None}
        code_pointer = {"mob": None}

        def get_code_anims(new_idx):
            if new_idx == current_line["idx"]:
                return []

            anims = []
            if current_line["idx"] is not None:
                old = code_texts[current_line["idx"]]
                anims.append(old.animate.set_color(WHITE).scale(1 / 1.16, about_edge=LEFT))

            if new_idx is not None:
                cur = code_texts[new_idx]
                anims.append(cur.animate.set_color(YELLOW).scale(1.16, about_edge=LEFT))
                if code_pointer["mob"] is None:
                    pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.12).rotate(-PI / 2)
                    pointer.next_to(cur, LEFT, buff=0.12)
                    code_pointer["mob"] = pointer
                    anims.append(FadeIn(pointer))
                else:
                    code_pointer["mob"].generate_target()
                    code_pointer["mob"].target.next_to(cur, LEFT, buff=0.12)
                    anims.append(MoveToTarget(code_pointer["mob"]))
                current_line["idx"] = new_idx
            else:
                if code_pointer["mob"] is not None:
                    anims.append(FadeOut(code_pointer["mob"]))
                    code_pointer["mob"] = None
                current_line["idx"] = None
            return anims

        current_tree = {"state": None}
        pointer_mobs = {"p": None, "f": None, "q": None, "s": None}
        pointer_dirs = {"p": RIGHT, "f": LEFT, "q": DOWN, "s": UP}

        def make_pointer_marker(name, node, direction, color):
            label = Text(name, font="Consolas", font_size=16, color=color)
            label_bg = RoundedRectangle(
                corner_radius=0.08,
                width=label.width + 0.18,
                height=label.height + 0.14,
                color=color,
                fill_color=BLACK,
                fill_opacity=0.88,
                stroke_width=1.4,
            ).move_to(label)
            tag = VGroup(label_bg, label)
            tag.next_to(node, direction, buff=0.18)

            unit = np.array(direction, dtype=float) / np.linalg.norm(direction)
            arrow = Arrow(
                start=tag.get_edge_center(-unit),
                end=node.get_center() + unit * node.radius,
                buff=0.02,
                color=color,
                stroke_width=2.4,
                max_tip_length_to_length_ratio=0.22,
            )
            return VGroup(tag, arrow)

        def update_vars(**kwargs):
            anims = []
            for name, value in kwargs.items():
                if name == "key":
                    new_text = Text(f"key = {value}", font_size=20, color=YELLOW, font="Consolas").move_to(key_text.get_center()).align_to(key_text, LEFT)
                    anims.append(Transform(key_text, new_text))
                    continue

                mob = pointer_mobs[name]
                if value in {None, "NULL"}:
                    if mob is not None:
                        anims.append(FadeOut(mob))
                        pointer_mobs[name] = None
                    continue

                state = current_tree["state"]
                if state is None:
                    continue
                node = state["nodes"][int(value)]
                target = make_pointer_marker(name, node, pointer_dirs[name], var_colors[name])
                if mob is None:
                    pointer_mobs[name] = target
                    anims.append(FadeIn(target))
                else:
                    anims.append(Transform(mob, target))
            return anims

        def reset_tree_colors(nodes):
            return [node.circle.animate.set_color(BLUE).set_fill(BLUE, 0.15) for node in nodes.values()]

        def set_roles(state, p=None, f=None, q=None, s=None, run_time=0.55):
            nodes = state["nodes"]
            anims = [node.circle.animate.set_color(BLUE).set_fill(BLUE, 0.15) for node in nodes.values()]
            if f is not None and f not in {p, q, s}:
                anims.append(nodes[f].circle.animate.set_color(self.ROLE_F).set_fill(self.ROLE_F, 0.45))
            if q is not None and q not in {p, s}:
                anims.append(nodes[q].circle.animate.set_color(self.ROLE_Q).set_fill(self.ROLE_Q, 0.45))
            if s is not None and s != p:
                anims.append(nodes[s].circle.animate.set_color(self.ROLE_S).set_fill(self.ROLE_S, 0.45))
            if p is not None:
                anims.append(nodes[p].circle.animate.set_color(self.ROLE_P).set_fill(self.ROLE_P, 0.5))
            return AnimationGroup(*anims, run_time=run_time)

        def load_tree():
            state = self.build_demo_tree()
            fade_pointer_anims = []
            for name in pointer_mobs:
                if pointer_mobs[name] is not None:
                    fade_pointer_anims.append(FadeOut(pointer_mobs[name]))
                    pointer_mobs[name] = None
            if current_tree["state"] is not None:
                self.play(FadeOut(current_tree["state"]["group"]), *fade_pointer_anims, run_time=0.4)
            elif fade_pointer_anims:
                self.play(*fade_pointer_anims, run_time=0.3)
            current_tree["state"] = state
            self.play(FadeIn(state["group"]), run_time=0.6)
            return state

        with self.voiceover(text="本节我们来学习二叉排序树的删除算法代码实现。右侧是删除函数 DeleteBST 的核心代码，左侧是一棵示例二叉排序树。") as tracker:
            state = load_tree()
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(text="在讲解过程中，红色表示当前处理的结点 p，绿色表示它的双亲结点 f，青色表示辅助指针 q，橙色表示前驱结点 s。与此同时，画面中的指针标签会直接指向这些结点，让代码变量和树上的位置一一对应。") as tracker:
            self.play(
                set_roles(state, p=45, f=24, q=53, s=37, run_time=1.0),
                *update_vars(key="45", p="45", f="24", q="53", s="37"),
                run_time=1.0,
            )
            self.play(*reset_tree_colors(state["nodes"]), *update_vars(key="NULL", p="NULL", f="NULL", q="NULL", s="NULL"), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 1.8))

        # ===== 示例一：删除叶子结点 12 =====
        with self.voiceover(text="先看第一种情况：删除叶子结点 12。这个例子可以帮助我们理解代码中 while 查找部分，以及 else 分支里无右子树的处理。") as tracker:
            self.play(Transform(case_text, Text("情况一：叶子 12", font_size=18, color=YELLOW, font="Microsoft YaHei").move_to(case_text)))
            self.wait(tracker.duration)

        with self.voiceover(text="函数一开始，先让 p 指向根结点，让 f 为空。这里 key 等于 12，所以一开始 p 指向 45，f 还是空。") as tracker:
            self.play(*get_code_anims(line_index["func"]), run_time=0.3)
            self.play(*get_code_anims(line_index["init"]), *update_vars(key="12", p="45", f="NULL", q="NULL", s="NULL"), set_roles(state, p=45), run_time=tracker.duration)

        with self.voiceover(text="进入 while 循环后，先判断当前 p 所指结点是不是要删除的关键字。45 不等于 12，因此不能退出循环。") as tracker:
            self.play(*get_code_anims(line_index["while"]), run_time=0.3)
            self.play(*get_code_anims(line_index["found"]), Indicate(state["nodes"][45].circle, color=YELLOW), run_time=tracker.duration)

        with self.voiceover(text="接着执行 f 等于 p，把当前结点记为双亲。因为 12 小于 45，所以沿着左孩子继续向下查找。于是 f 变成 45，p 移动到 24。") as tracker:
            self.play(*get_code_anims(line_index["parent"]), run_time=0.3)
            self.play(*get_code_anims(line_index["go_left"]), *update_vars(f="45", p="24"), set_roles(state, p=24, f=45), run_time=tracker.duration)

        with self.voiceover(text="现在 p 来到 24。24 仍然不是目标值，所以继续循环。由于 12 小于 24，这次仍然沿左孩子往下找。") as tracker:
            self.play(*get_code_anims(line_index["while"]), run_time=0.2)
            self.play(*get_code_anims(line_index["found"]), Indicate(state["nodes"][24].circle, color=YELLOW), run_time=0.4)
            self.play(*get_code_anims(line_index["parent"]), run_time=0.2)
            self.play(*get_code_anims(line_index["go_left"]), *update_vars(f="24", p="12"), set_roles(state, p=12, f=24), run_time=max(0.6, tracker.duration - 0.8))

        with self.voiceover(text="这一次 p 指向的正好是 12，条件成立，break 执行，while 查找结束。说明我们已经准确找到了待删除结点。") as tracker:
            self.play(*get_code_anims(line_index["while"]), run_time=0.2)
            self.play(*get_code_anims(line_index["found"]), Indicate(state["nodes"][12].circle, color=YELLOW, scale_factor=1.15), run_time=tracker.duration)

        with self.voiceover(text="找到结点以后，先看 if 非 p return 这一句。现在 p 不是空，所以不会返回，程序继续向下判断删除类型。") as tracker:
            self.play(*get_code_anims(line_index["not_found"]), run_time=tracker.duration)

        with self.voiceover(text="再看 p 的左右子树是否同时存在。结点 12 没有左孩子，也没有右孩子，所以不会进入双子树分支，而是进入后面的 else 分支。") as tracker:
            self.play(*get_code_anims(line_index["two_children"]), run_time=0.5)
            self.play(*get_code_anims(line_index["else_block"]), run_time=max(0.5, tracker.duration - 0.5))

        with self.voiceover(text="在 else 分支中，第一句先判断 p 有没有右子树。由于 12 没有右子树，所以这句成立。代码把 q 指向原来的 p，再让 p 改指向它的左子树。因为 12 连左子树也没有，所以新的 p 变成空。") as tracker:
            self.play(*get_code_anims(line_index["no_right"]), *update_vars(q="12", p="NULL"), run_time=0.3)
            self.play(set_roles(state, f=24, q=12), run_time=max(0.5, tracker.duration - 0.3))

        with self.voiceover(text="接下来判断 q 是不是 f 的左孩子。这里 12 正好就是 24 的左孩子，所以执行这句，把 f 的左孩子改成新的 p，也就是空指针。画面上对应的效果，就是把 24 到 12 的连线断开。") as tracker:
            self.play(*get_code_anims(line_index["link_left"]), FadeOut(state["edges"][(24, 12)]), run_time=tracker.duration)

        with self.voiceover(text="最后执行 delete q，释放原来结点 12 的空间。到这里，叶子结点删除就完成了。") as tracker:
            self.play(*get_code_anims(line_index["delete_q"]), FadeOut(state["nodes"][12]), run_time=tracker.duration)

        self.play(*reset_tree_colors(state["nodes"]), run_time=0.6)

        # ===== 示例二：删除只有一棵子树的结点 53 =====
        with self.voiceover(text="下面看第二种情况：删除只有一棵子树的结点 53。为了让流程更清楚，我们先把示例树恢复到初始状态。") as tracker:
            state = load_tree()
            self.play(Transform(case_text, Text("情况二：单子树 53", font_size=18, color=YELLOW, font="Microsoft YaHei").move_to(case_text)))
            self.play(*update_vars(key="53", p="NULL", f="NULL", q="NULL", s="NULL"), *get_code_anims(line_index["init"]), run_time=max(0.6, tracker.duration - 0.6))

        with self.voiceover(text="初始化后，p 先指向根结点 45。因为 53 大于 45，所以第一次比较之后，f 变成 45，p 转向右孩子 53。") as tracker:
            self.play(*update_vars(p="45", f="NULL"), set_roles(state, p=45), run_time=0.4)
            self.play(*get_code_anims(line_index["while"]), run_time=0.2)
            self.play(*get_code_anims(line_index["found"]), run_time=0.2)
            self.play(*get_code_anims(line_index["parent"]), run_time=0.2)
            self.play(*get_code_anims(line_index["go_right"]), *update_vars(f="45", p="53"), set_roles(state, p=53, f=45), run_time=max(0.7, tracker.duration - 1.0))

        with self.voiceover(text="此时 p 正好指向 53，while 循环 break 退出。接下来开始分析它属于哪一种删除情况。") as tracker:
            self.play(*get_code_anims(line_index["while"]), run_time=0.2)
            self.play(*get_code_anims(line_index["found"]), Indicate(state["nodes"][53].circle, color=YELLOW), run_time=tracker.duration)

        with self.voiceover(
            text="结点五十三仅有右孩子九十三，没有左孩子，因此进入 else 分支。",
            subcaption="结点 53 仅有右孩子 93，没有左孩子，因此进入 else 分支。"
        ) as tracker:
            self.play(*get_code_anims(line_index["two_children"]), run_time=0.3)
            self.play(*get_code_anims(line_index["else_block"]), run_time=max(0.5, tracker.duration - 0.3))

        with self.voiceover(text="先判断 p 有没有右子树。由于 53 有右子树，这句不成立；再判断它有没有左子树。53 没有左子树，所以 q 指向原来的 53，p 改为指向 93。") as tracker:
            self.play(*get_code_anims(line_index["no_right"]), run_time=0.25)
            self.play(*get_code_anims(line_index["no_left"]), *update_vars(q="53", p="93"), set_roles(state, p=93, f=45, q=53), run_time=max(0.7, tracker.duration - 0.25))

        with self.voiceover(text="接下来判断 q 是否为 f 的左孩子。这里 q 也就是 53，是 45 的右孩子，所以左孩子判断不成立，程序会执行下一句，把 f 的右孩子直接改成新的 p，也就是 93。") as tracker:
            new_edge_45_93 = self.make_edge(state["pos"][45], state["pos"][53])
            self.play(*get_code_anims(line_index["link_left"]), run_time=0.25)
            self.play(
                *get_code_anims(line_index["link_right"]),
                FadeOut(state["edges"][(45, 53)]),
                FadeOut(state["edges"][(53, 93)]),
                state["nodes"][93].animate.move_to(state["pos"][53]),
                Create(new_edge_45_93),
                run_time=tracker.duration,
            )
            state["group"].add(new_edge_45_93)

        with self.voiceover(text="最后 delete q，释放原来结点 53 的空间。你可以看到，这种情况的本质就是让 p 的唯一子树越过原结点，直接接到双亲下面。") as tracker:
            self.play(*get_code_anims(line_index["delete_q"]), FadeOut(state["nodes"][53]), run_time=tracker.duration)

        self.play(*reset_tree_colors(state["nodes"]), run_time=0.6)

        # ===== 示例三：删除左右子树都存在的结点 45 =====
        with self.voiceover(text="最后看第三种，也是最关键的一种：删除左右子树都存在的结点 45。这个例子会完整用到前驱结点 s，以及辅助指针 q。") as tracker:
            state = load_tree()
            self.play(Transform(case_text, Text("情况三：双子树 45", font_size=18, color=YELLOW, font="Microsoft YaHei").move_to(case_text)))
            self.play(*update_vars(key="45", p="NULL", f="NULL", q="NULL", s="NULL"), run_time=max(0.5, tracker.duration - 0.5))

        with self.voiceover(text="按照同样的初始化方式，先让 p 指向根结点 45。由于 key 也等于 45，所以一进入循环就能命中待删结点，此时 f 仍然为空。") as tracker:
            self.play(*get_code_anims(line_index["init"]), *update_vars(p="45", f="NULL"), set_roles(state, p=45), run_time=0.4)
            self.play(*get_code_anims(line_index["while"]), run_time=0.15)
            self.play(*get_code_anims(line_index["found"]), Indicate(state["nodes"][45].circle, color=YELLOW), run_time=max(0.7, tracker.duration - 0.55))

        with self.voiceover(text="while 查找结束以后，先判断 p 是否为空。现在 p 指向根结点 45，显然不是空，所以继续向下分析删除类型。") as tracker:
            self.play(*get_code_anims(line_index["not_found"]), run_time=tracker.duration)

        with self.voiceover(text="这次 45 同时有左子树和右子树，因此会进入双子树分支。算法的核心思想是：找到它的直接前驱，用前驱的数据覆盖当前结点，再删除那个前驱结点。") as tracker:
            self.play(*get_code_anims(line_index["two_children"]), run_time=tracker.duration)

        with self.voiceover(text="进入分支后，先让 q 指向 p 本身，再让 s 指向 p 的左孩子。此时 q 指向 45，s 指向 24。") as tracker:
            self.play(*get_code_anims(line_index["set_qs"]), *update_vars(q="45", s="24"), set_roles(state, p=45, s=24), run_time=tracker.duration)

        with self.voiceover(text="接下来执行 while s 的右孩子。这个循环的作用，是在 p 的左子树中一路向右，找到最大的那个结点，也就是直接前驱。") as tracker:
            self.play(*get_code_anims(line_index["pred_loop"]), Indicate(state["nodes"][24].circle, color=YELLOW), run_time=tracker.duration)

        with self.voiceover(text="第一次进入循环时，q 更新为当前的 s，也就是 24；然后 s 再沿右孩子向下走到 37。现在 q 是 24，s 是 37。") as tracker:
            self.play(*get_code_anims(line_index["pred_loop"]), *update_vars(q="24", s="37"), set_roles(state, p=45, q=24, s=37), run_time=tracker.duration)

        with self.voiceover(text="再检查一次 while 条件。由于 37 已经没有右孩子了，所以循环结束。这就说明 37 正是结点 45 的直接前驱。") as tracker:
            self.play(*get_code_anims(line_index["pred_loop"]), Indicate(state["nodes"][37].circle, color=YELLOW, scale_factor=1.15), run_time=tracker.duration)

        with self.voiceover(text="找到前驱以后，执行 p 的数据等于 s 的数据。注意这一句并没有真正移动结点，只是把 37 这个关键字复制到原来 45 的位置上。") as tracker:
            self.play(
                *get_code_anims(line_index["copy"]),
                state["nodes"][45].label.animate.become(
                    Text("37", font="Arial", font_size=18, color=WHITE).move_to(state["nodes"][45].label.get_center())
                ),
                run_time=tracker.duration,
            )

        with self.voiceover(text="接下来判断 q 是否不等于 p。这里 q 是 24，p 是原来的 45，所以条件成立。于是程序执行 q 的右孩子等于 s 的左孩子。由于 37 没有左孩子，24 的右孩子会被改为空。") as tracker:
            self.play(*get_code_anims(line_index["relink_right"]), run_time=0.2)
            self.play(
                FadeOut(state["edges"][(24, 37)]),
                set_roles(state, p=45, q=24, s=37, run_time=0.9),
                run_time=max(0.9, tracker.duration - 0.2),
            )

        with self.voiceover(text="最后 delete s，释放原来那个前驱结点 37 的空间。这样一来，树中旧的前驱结点被删掉，而原来 45 的位置则由前驱数据顶替。") as tracker:
            self.play(*get_code_anims(line_index["delete_s"]), FadeOut(state["nodes"][37]), run_time=tracker.duration)

        with self.voiceover(text="这里顺便补充一句：如果前驱结点恰好就是 p 的左孩子，那么 q 会一直等于 p，这时就不会执行刚才那句重新连接 q 的右子树，而会执行下面这句，把 q 的左孩子改为 s 的左孩子。") as tracker:
            self.play(*get_code_anims(line_index["relink_left"]), run_time=tracker.duration)

        with self.voiceover(
            text="另外，else 分支中的根结点判断，专门处理删除树根的情况。如果根结点的左、右孩子中仅有一个非空，删除根结点后，就让这个孩子成为新的树根。",
            subcaption="else 分支中的 if (!f) T = p 专门处理删除树根。根结点仅有一棵子树时，删除后让这棵子树的根成为新树根。"
        ) as tracker:
            self.play(*get_code_anims(line_index["root_case"]), Indicate(state["nodes"][45].circle, color=YELLOW), run_time=tracker.duration)

        # ===== 总结与复杂度 =====
        with self.voiceover(text="总结一下，这段删除代码可以分成两大阶段：先用 while 循环找到待删结点 p，再根据 p 的孩子情况进入不同分支，重新连接结点。") as tracker:
            self.play(*reset_tree_colors(state["nodes"]), *update_vars(key="45", p="45", f="NULL", q="24", s="37"), run_time=max(0.8, tracker.duration))

        self.play(
            FadeOut(state["group"]),
            FadeOut(case_text),
            FadeOut(key_title),
            FadeOut(key_text),
            *update_vars(p="NULL", f="NULL", q="NULL", s="NULL"),
            *get_code_anims(None),
            run_time=0.6,
        )

        complexity_title = Text("复杂度分析", font_size=28, color=YELLOW, font="Microsoft YaHei")
        time_box = VGroup(
            Text("时间复杂度：", font_size=24, color=WHITE, font="Microsoft YaHei"),
            MathTex("O(h)", font_size=28, color=YELLOW),
        ).arrange(RIGHT, buff=0.12)
        worst_box = VGroup(
            Text("最坏情况：", font_size=24, color=WHITE, font="Microsoft YaHei"),
            MathTex("O(n)", font_size=28, color=YELLOW),
        ).arrange(RIGHT, buff=0.12)
        space_box = VGroup(
            Text("空间复杂度：", font_size=24, color=WHITE, font="Microsoft YaHei"),
            MathTex("O(1)", font_size=28, color=YELLOW),
        ).arrange(RIGHT, buff=0.12)
        summary_group = VGroup(complexity_title, time_box, worst_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        summary_group.to_edge(LEFT, buff=1.0).shift(DOWN * 0.5)

        with self.voiceover(
            text="删除时，需要查找目标结点；必要时还要寻找前驱。总时间复杂度与树高成正比，记为欧艾尺。",
            subcaption="查找目标结点及前驱的时间与树高 h 成正比，总时间复杂度为 O(h)。"
        ) as tracker:
            self.play(FadeIn(summary_group), run_time=tracker.duration)

        with self.voiceover(
            text="树比较平衡时，树高是对数级。若树退化成单链表，最坏时间复杂度为欧恩。",
            subcaption="树较平衡时，h 为对数级；退化成单链表时，最坏时间复杂度为 O(n)。"
        ) as tracker:
            self.wait(tracker.duration)

        with self.voiceover(
            text="这份代码采用非递归写法，仅使用几个辅助指针。额外空间为常数级，记为欧一。",
            subcaption="非递归写法仅使用 p、f、q、s 几个辅助指针，额外空间复杂度为 O(1)。"
        ) as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="以上就是二叉排序树删除算法的完整代码跟踪演示。接下来如果你再回头看这段代码，就能更容易把每一条语句和树形变化对应起来。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)
