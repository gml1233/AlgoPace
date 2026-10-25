# coding=utf-8
from manim import *
from tree_base import TreeBase

class CalculateDepth(TreeBase):
    def construct(self):
        title = Text("计算二叉树的深度", font_size=36).to_edge(UP)
        self.play(Write(title))

        data = {
            'v': 'A',
            'l': {'v': 'B', 'l': {'v': 'C'}, 'r': {'v': 'D', 'l': {'v': 'E'}}},
            'r': {'v': 'F', 'r': {'v': 'G'}}
        }
        root = self.build_tree_from_dict(data)
        self.compute_positions(root, x=0, y=1.5)
        self.draw_tree(root)
        self.play(FadeIn(self.edges), FadeIn(self.tree_mobjects))

        self.pointer = self.create_pointer("节点")
        self.pointer.move_to(root.mobject.get_center() + UP)
        self.play(FadeIn(self.pointer))

        depth = self.calc_depth(root)

        final_text = Text(f"该二叉树的深度为: {depth}", font_size=32, color=YELLOW).to_edge(DOWN)
        self.play(Write(final_text))
        self.wait(2)

    def calc_depth(self, node):
        if not node:
            return 0

        self.move_pointer(self.pointer, node)
        self.highlight_node(node, color=self.COLOR_VISITED)

        if node.edge_left:
            self.highlight_edge(node.edge_left)
        left_depth = self.calc_depth(node.left)
        
        self.move_pointer(self.pointer, node)

        if node.edge_right:
            self.highlight_edge(node.edge_right)
        right_depth = self.calc_depth(node.right)
        
        self.move_pointer(self.pointer, node)
        
        current_depth = max(left_depth, right_depth) + 1
        
        # 显示计算得到的深度
        depth_tag = Text(str(current_depth), font_size=20, color=GREEN).next_to(node.mobject, RIGHT, buff=0.1)
        self.play(Write(depth_tag), node.mobject.circle.animate.set_fill(self.COLOR_TARGET), run_time=0.6)
        
        if node.edge_left:
            self.play(node.edge_left.animate.set_color(WHITE), run_time=0.1)
        if node.edge_right:
            self.play(node.edge_right.animate.set_color(WHITE), run_time=0.1)

        return current_depth
