# coding=utf-8
from manim import *
from tree_base import TreeBase

class CountNodes(TreeBase):
    def construct(self):
        title = Text("统计二叉树结点个数", font_size=36).to_edge(UP)
        self.play(Write(title))

        data = {
            'v': 'A',
            'l': {'v': 'B', 'l': {'v': 'D'}, 'r': {'v': 'E'}},
            'r': {'v': 'C', 'l': {'v': 'F'}}
        }
        root = self.build_tree_from_dict(data)
        self.compute_positions(root, x=0, y=2.0)
        self.draw_tree(root)
        self.play(FadeIn(self.edges), FadeIn(self.tree_mobjects))

        self.pointer = self.create_pointer("访问")
        self.pointer.move_to(root.mobject.get_center() + UP)
        self.play(FadeIn(self.pointer))

        count = self.count_nodes(root)

        final_text = Text(f"共有结点: {count} 个", font_size=32, color=YELLOW).to_edge(DOWN)
        self.play(Write(final_text))
        self.wait(2)

    def count_nodes(self, node):
        if not node:
            return 0

        self.move_pointer(self.pointer, node)
        self.highlight_node(node, color=self.COLOR_VISITED)

        if node.edge_left:
            self.highlight_edge(node.edge_left)
        left_count = self.count_nodes(node.left)

        self.move_pointer(self.pointer, node)

        if node.edge_right:
            self.highlight_edge(node.edge_right)
        right_count = self.count_nodes(node.right)

        self.move_pointer(self.pointer, node)
        
        total = left_count + right_count + 1
        
        # 标记当前子树的结点数
        count_tag = Text(f"={total}", font_size=20, color=RED).next_to(node.mobject, RIGHT, buff=0.1)
        self.play(Write(count_tag), node.mobject.circle.animate.set_fill(self.COLOR_TARGET), run_time=0.6)

        if node.edge_left:
            self.play(node.edge_left.animate.set_color(WHITE), run_time=0.1)
        if node.edge_right:
            self.play(node.edge_right.animate.set_color(WHITE), run_time=0.1)

        return total
