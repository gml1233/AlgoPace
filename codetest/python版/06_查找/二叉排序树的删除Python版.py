# coding=utf-8
from manim import *
import warnings
import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService

from codetest.python版.bst_video_support import PythonCodePanel, method_lines, fit_right

class ElemType:
    def __init__(self, key, otherinfo=""):
        self.key = key  # 关键字域
        self.otherinfo = otherinfo  # 其他域


class BSTree:
    def __init__(self, e=None):
        self.data = e
        self.lchild = None  # 左孩子指针
        self.rchild = None  # 右孩子指针

    def insert_bst(self, e):
        # 当二叉排序树中不存在关键字等于e.key的数据元素时，则插入该元素
        if self.data is None:  # 如果当前树为空，即找插入位置
            self.data = e  # 当前树结点的数据域置为e
            self.lchild = None  # 左子树置为空
            self.rchild = None  # 右子树置为空
        elif e.key < self.data.key:  # e的关键字小于当前节点数据域的关键字
            if self.lchild is None:
                self.lchild = BSTree(e)
            else:
                self.lchild.insert_bst(e)  # 插入左子树
        elif e.key > self.data.key:  # e的关键字大于当前节点数据域的关键字
            if self.rchild is None:
                self.rchild = BSTree(e)
            else:
                self.rchild.insert_bst(e)  # 插入右子树

    def create_bst(self, input_values):
        # 依次读入一个关键字为key的结点，将此结点插入二叉排序树中
        for key in input_values:
            e = ElemType(key)
            self.insert_bst(e)

    def delete_bst(self, key):
        # 删除二叉树中的指定结点值的结点
        p = self
        f = None
        # 下面的while循环从根开始查找关键字等于key的结点 * p
        while p is not None and p.data is not None:
            if p.data.key == key:
                break
            f = p
            if p.data.key > key:
                p = p.lchild
            else:
                p = p.rchild
        if p is None or p.data is None:  # 找不到被删结点则返回
            return
        # 处理三种情况：左右子树均不为空、无右子树、无左子树
        if p.lchild is not None and p.rchild is not None:
            # 左右子树均不为空，找到左子树中的最大结点（前驱）
            q = p
            s = p.lchild
            # 在左子树继续查找前驱结点
            while s.rchild is not None:
                q = s
                s = s.rchild
            # 用前驱结点值替换当前结点值
            p.data = s.data
            # 重接右子树
            if q != p:
                # 重接右子树
                q.rchild = s.lchild
            else:
                # 重接左子树
                q.lchild = s.lchild
        else:
            # 无右子树的情况
            if p.rchild is None:
                # 重接其左子树
                child = p.lchild
            # 无左子树的情况
            elif p.lchild is None:
                # 重接其右子树
                child = p.rchild
            # 被删除结点为根结点
            if f is None:
                self.data = child.data if child else None
                self.lchild = child.lchild if child else None
                self.rchild = child.rchild if child else None
            elif f.lchild == p:
                # 挂接到f的左子树
                f.lchild = child
            else:
                # 挂接到f的右子树
                f.rchild = child

    def in_order_traverse(self):
        # 中序遍历二叉树的递归算法
        if self.data is not None:  # 若二叉树非空
            if self.lchild:
                self.lchild.in_order_traverse()  # 中序遍历左子树
            print(self.data.key, end=' ')  # 访问根结点
            if self.rchild:
                self.rchild.in_order_traverse()  # 中序遍历右子树


class BSTDeletePythonVideo(VoiceoverScene):
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

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(0.72).to_corner(UR, buff=0.14)
        self.add(logo)

        title = Text("二叉排序树的删除（Python版）", font_size=34, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.12)
        self.play(FadeIn(title), run_time=0.8)

        python_lines = method_lines(BSTree.delete_bst)
        # 分屏保留原始缩进；每个高亮对应实际执行方法中的语句。
        code_block = PythonCodePanel(python_lines, title="delete_bst", page_starts=[0, 14, 27])
        def find_line(fragment):
            return next(i for i, line in enumerate(python_lines) if fragment == line.strip())
        line_index = {
            "func": 0, "init": 1,
            "while": find_line("while p is not None and p.data is not None:"),
            "found": find_line("if p.data.key == key:"),
            "parent": find_line("f = p"),
            "go_left": find_line("p = p.lchild"),
            "go_right": find_line("p = p.rchild"),
            "not_found": find_line("if p is None or p.data is None:"),
            "two_children": find_line("if p.lchild is not None and p.rchild is not None:"),
            "set_qs": find_line("s = p.lchild"),
            "pred_loop": find_line("while s.rchild is not None:"),
            "pred_q": find_line("q = s"), "pred_s": find_line("s = s.rchild"),
            "copy": find_line("p.data = s.data"),
            "relink_right": find_line("q.rchild = s.lchild"),
            "relink_left": find_line("q.lchild = s.lchild"),
            "else_block": find_line("if p.rchild is None:"),
            "no_right": find_line("child = p.lchild"),
            "no_left": find_line("child = p.rchild"),
            "root_case": find_line("if f is None:"),
            "link_left": find_line("f.lchild = child"),
            "link_right": find_line("f.rchild = child"),
        }
        self.play(FadeIn(code_block), run_time=0.8)

        var_colors = {
            "key": YELLOW,
            "p": self.ROLE_P,
            "f": self.ROLE_F,
            "q": self.ROLE_Q,
            "s": self.ROLE_S,
            "child": PURPLE_B,
        }
        case_text = Text("情况一：叶子 12", font_size=18, color=YELLOW, font="Microsoft YaHei")
        case_text.to_corner(UL, buff=0.18).shift(DOWN * 0.28 + RIGHT * 0.08)
        key_title = Text("待删除关键字", font_size=16, color=YELLOW, font="Microsoft YaHei").next_to(case_text, DOWN, aligned_edge=LEFT, buff=0.12)
        key_text = Text("key = --", font_size=20, color=YELLOW, font="Consolas").next_to(key_title, DOWN, aligned_edge=LEFT, buff=0.08)
        self.play(FadeIn(case_text), FadeIn(key_title), FadeIn(key_text), run_time=0.5)

        def get_code_anims(new_idx):
            return code_block.track(new_idx)

        current_tree = {"state": None}
        pointer_mobs = {"p": None, "f": None, "q": None, "s": None, "child": None}
        pointer_dirs = {"p": RIGHT, "f": LEFT, "q": DOWN, "s": UP, "child": DOWN}

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
                if value in {None, "None"}:
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
            return [node.circle.animate.set_color(BLUE).set_fill(BLUE, 0.15) for node in nodes.values() if node in current_tree["state"]["group"].submobjects]

        def set_roles(state, p=None, f=None, q=None, s=None, run_time=0.55):
            nodes = state["nodes"]
            anims = [node.circle.animate.set_color(BLUE).set_fill(BLUE, 0.15) for node in nodes.values() if node in current_tree["state"]["group"].submobjects]
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

        with self.voiceover(text="本节我们来学习二叉排序树的删除算法代码实现。右侧是Python 方法 delete_bst 的核心代码，左侧是一棵示例二叉排序树。") as tracker:
            state = load_tree()
            self.wait(max(0.1, tracker.duration - 0.6))

        with self.voiceover(text="本节空孩子直接用 None 表示。循环先检查 p 和 p.data，空树也能安全返回。在讲解过程中，红色表示当前处理的结点 p，绿色表示它的双亲结点 f，青色表示辅助引用 q，橙色表示前驱结点 s。与此同时，画面中的引用标签会直接指向这些结点，让代码变量和树上的位置一一对应。") as tracker:
            self.play(
                set_roles(state, p=45, f=24, q=53, s=37, run_time=1.0),
                *update_vars(key="45", p="45", f="24", q="53", s="37"),
                run_time=1.0,
            )
            self.play(*reset_tree_colors(state["nodes"]), *update_vars(key="None", p="None", f="None", q="None", s="None"), run_time=0.8)
            self.wait(max(0.1, tracker.duration - 1.8))

        # ===== 示例一：删除叶子结点 12 =====
        with self.voiceover(text="先看第一种情况：删除叶子结点 12。这个例子可以帮助我们理解代码中 while 查找部分，以及 else 分支里无右子树的处理。") as tracker:
            self.play(Transform(case_text, Text("情况一：叶子 12", font_size=18, color=YELLOW, font="Microsoft YaHei").move_to(case_text)))
            self.wait(tracker.duration)

        with self.voiceover(text="函数一开始，先让 p 指向根结点，让 f 为空。这里 key 等于 12，所以一开始 p 指向 45，f 还是空。") as tracker:
            self.play(*get_code_anims(line_index["func"]), run_time=0.3)
            self.play(*get_code_anims(line_index["init"]), *update_vars(key="12", p="45", f="None", q="None", s="None"), set_roles(state, p=45), run_time=tracker.duration)

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

        with self.voiceover(text="找到结点以后，先检查 p 是否为 None，或 p.data 是否为 None。现在 p 不是空，所以不会返回，程序继续向下判断删除类型。") as tracker:
            self.play(*get_code_anims(line_index["not_found"]), run_time=tracker.duration)

        with self.voiceover(text="再看 p 的左右子树是否同时存在。结点 12 没有左孩子，也没有右孩子，所以不会进入双子树分支，而是进入后面的 else 分支。") as tracker:
            self.play(*get_code_anims(line_index["two_children"]), run_time=0.5)
            self.play(*get_code_anims(line_index["else_block"]), run_time=max(0.5, tracker.duration - 0.5))

        with self.voiceover(text="在 else 分支中，第一句先判断 p 有没有右子树。由于 12 没有右子树，所以这句成立。执行 child 等于 p.lchild。十二的左孩子也是 None，所以 child 为 None。p 始终指向待删的十二，f 指向二十四。") as tracker:
            self.play(*get_code_anims(line_index["no_right"]), *update_vars(child="None", p="12"), run_time=0.3)
            self.play(set_roles(state, f=24, p=12), run_time=max(0.5, tracker.duration - 0.3))

        with self.voiceover(text="接下来判断 p 是否为 f 的左孩子。十二正是二十四的左孩子，所以把 f.lchild 改为 child，也就是 None。画面上对应的效果，就是把 24 到 12 的连线断开。") as tracker:
            self.play(*get_code_anims(line_index["link_left"]), FadeOut(state["edges"][(24, 12)]), run_time=tracker.duration)

        with self.voiceover(text="父结点已经不再引用十二，叶子删除完成。Python 不需要 delete 语句；函数返回后，不再被引用的对象可由 Python 自动回收。") as tracker:
            self.play(*get_code_anims(None), *update_vars(p="None"), FadeOut(state["nodes"][12]), run_time=tracker.duration)

        state["group"].remove(state["nodes"][12])
        self.play(*reset_tree_colors(state["nodes"]), run_time=0.6)

        # ===== 示例二：删除只有一棵子树的结点 53 =====
        with self.voiceover(text="下面看第二种情况：删除只有一棵子树的结点 53。为了让流程更清楚，我们先把示例树恢复到初始状态。") as tracker:
            state = load_tree()
            self.play(Transform(case_text, Text("情况二：单子树 53", font_size=18, color=YELLOW, font="Microsoft YaHei").move_to(case_text)))
            self.play(*update_vars(key="53", p="None", f="None", q="None", s="None"), *get_code_anims(line_index["init"]), run_time=max(0.6, tracker.duration - 0.6))

        with self.voiceover(text="初始化后，p 先指向根结点 45。因为 53 大于 45，所以第一次比较之后，f 变成 45，p 转向右孩子 53。") as tracker:
            self.play(*update_vars(p="45", f="None"), set_roles(state, p=45), run_time=0.4)
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

        with self.voiceover(text="先判断 p 有没有右子树。由于 53 有右子树，这句不成立；再判断它有没有左子树。53 没有左子树，所以 child 引用九十三，p 仍然引用待删除的五十三。") as tracker:
            self.play(*get_code_anims(line_index["no_right"]), run_time=0.25)
            self.play(*get_code_anims(line_index["no_left"]), *update_vars(child="93", p="53"), set_roles(state, p=53, f=45), run_time=max(0.7, tracker.duration - 0.25))

        with self.voiceover(text="接下来判断 p 是否为 f 的左孩子。五十三是四十五的右孩子，所以执行 f.rchild 等于 child，让九十三直接接到四十五的右侧。") as tracker:
            new_edge_45_93 = self.make_edge(state["pos"][45], state["pos"][53])
            self.play(*get_code_anims(line_index["link_left"]), run_time=0.25)
            self.play(
                *get_code_anims(line_index["link_right"]),
                FadeOut(state["edges"][(45, 53)]),
                FadeOut(state["edges"][(53, 93)]),
                FadeOut(state["nodes"][53]),
                *update_vars(p="None", child="None"),
                state["nodes"][93].animate.move_to(state["pos"][53]),
                Create(new_edge_45_93),
                run_time=tracker.duration,
            )
            state["group"].add(new_edge_45_93)

        with self.voiceover(text="重接引用后，五十三已经从树中移除。这种情况就是让唯一子树越过待删结点，直接接到双亲下面。对象的回收由 Python 管理。") as tracker:
            self.play(*get_code_anims(None), run_time=tracker.duration)

        state["group"].remove(state["nodes"][53])
        self.play(*reset_tree_colors(state["nodes"]), run_time=0.6)

        # ===== 示例三：删除左右子树都存在的结点 45 =====
        with self.voiceover(text="最后看第三种，也是最关键的一种：删除左右子树都存在的结点 45。这个例子会完整用到前驱结点 s，以及辅助引用 q。") as tracker:
            state = load_tree()
            self.play(Transform(case_text, Text("情况三：双子树 45", font_size=18, color=YELLOW, font="Microsoft YaHei").move_to(case_text)))
            self.play(*update_vars(key="45", p="None", f="None", q="None", s="None"), run_time=max(0.5, tracker.duration - 0.5))

        with self.voiceover(text="按照同样的初始化方式，先让 p 指向根结点 45。由于 key 也等于 45，所以一进入循环就能命中待删结点，此时 f 仍然为空。") as tracker:
            self.play(*get_code_anims(line_index["init"]), *update_vars(p="45", f="None"), set_roles(state, p=45), run_time=0.4)
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
            self.play(*get_code_anims(line_index["pred_q"]), run_time=0.3)
            self.play(*get_code_anims(line_index["pred_s"]), *update_vars(q="24", s="37"), set_roles(state, p=45, q=24, s=37), run_time=tracker.duration)

        with self.voiceover(text="再检查一次 while 条件。由于 37 已经没有右孩子了，所以循环结束。这就说明 37 正是结点 45 的直接前驱。") as tracker:
            self.play(*get_code_anims(line_index["pred_loop"]), Indicate(state["nodes"][37].circle, color=YELLOW, scale_factor=1.15), run_time=tracker.duration)

        with self.voiceover(text="找到前驱以后，执行 p 的数据等于 s 的数据。注意这一句并没有真正移动结点，执行 p.data 等于 s.data，让 p 的数据域引用前驱的 ElemType 对象，因此根位置显示三十七，otherinfo 也一同保留。") as tracker:
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

        with self.voiceover(text="重接完成，旧前驱已经从树中移除。函数返回后，局部引用 s 随之释放；数据对象仍被根结点引用，继续保留。这里也不需要显式释放结点。") as tracker:
            self.play(*get_code_anims(None), *update_vars(s="None"), FadeOut(state["nodes"][37]), run_time=tracker.duration)

        state["group"].remove(state["nodes"][37])

        with self.voiceover(text="这里顺便补充一句：如果前驱结点恰好就是 p 的左孩子，那么 q 会一直等于 p，这时就不会执行刚才那句重新连接 q 的右子树，而会执行下面这句，把 q 的左孩子改为 s 的左孩子。") as tracker:
            self.play(*get_code_anims(line_index["relink_left"]), run_time=tracker.duration)

        with self.voiceover(
            text="另外，else 分支中的根结点判断，专门处理删除树根的情况。如果根只有一个孩子，就将 child 的数据和两个孩子引用写回 self，保持根对象身份。若根是叶子，则三个字段都设为 None，变成空树对象。",
            subcaption="f is None：将 child 的字段写回 self；child 为 None 时，将根对象清空。"
        ) as tracker:
            self.play(*get_code_anims(line_index["root_case"]), Indicate(state["nodes"][45].circle, color=YELLOW), run_time=tracker.duration)

        # ===== 总结与复杂度 =====
        with self.voiceover(text="总结一下，这段删除代码可以分成两大阶段：先用 while 循环找到待删结点 p，再根据 p 的孩子情况进入不同分支，重新连接结点。") as tracker:
            self.play(*reset_tree_colors(state["nodes"]), *update_vars(key="45", p="45", f="None", q="None", s="None"), run_time=max(0.8, tracker.duration))

        self.play(
            FadeOut(state["group"]),
            FadeOut(case_text),
            FadeOut(key_title),
            FadeOut(key_text),
            *update_vars(p="None", f="None", q="None", s="None"),
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
            text="这份代码采用非递归写法，仅使用几个辅助引用。额外空间为常数级，记为欧一。",
            subcaption="非递归写法仅使用 p、f、q、s、child 几个辅助引用，额外空间复杂度为 O(1)。"
        ) as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="以上就是二叉排序树删除算法的完整代码跟踪演示。接下来如果你再回头看这段代码，就能更容易把每一条语句和树形变化对应起来。") as tracker:
            self.wait(tracker.duration)

        self.wait(2)
