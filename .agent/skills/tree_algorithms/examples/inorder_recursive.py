# coding=utf-8
from manim import *
from tree_base import TreeBase

class InorderRecursiveBase(TreeBase):
    def construct(self):
        title = Text("中序遍历的递归算法", font_size=36).to_edge(UP)
        self.play(Write(title))

        # 构建测试数据
        data = {
            'v': 'A',
            'l': {'v': 'B', 'l': {'v': 'D'}, 'r': {'v': 'E'}},
            'r': {'v': 'C', 'r': {'v': 'F'}}
        }
        root = self.build_tree_from_dict(data)
        self.compute_positions(root, x=0, y=2.0)
        self.draw_tree(root)
        self.play(FadeIn(self.edges), FadeIn(self.tree_mobjects))
        self.wait(1)

        result_text = Text("遍历序列: ", font_size=28).to_edge(DOWN)
        self.play(Write(result_text))
        
        self.seq = VGroup()
        self.seq.next_to(result_text, RIGHT)
        self.seq_values = []

        pointer = self.create_pointer("访问")
        pointer.move_to(root.mobject.get_center() + UP)
        self.play(FadeIn(pointer))

        self.inorder(root, pointer, result_text)
        
        self.wait(2)

    def inorder(self, node, pointer, result_text):
        if not node:
            return

        self.move_pointer(pointer, node)
        
        # 递归左子树
        if node.edge_left:
            self.highlight_edge(node.edge_left, color=self.COLOR_VISITED)
        self.inorder(node.left, pointer, result_text)
        
        # 访问根结点
        self.move_pointer(pointer, node)
        self.highlight_node(node, color=self.COLOR_TARGET)
        
        new_val = Text(node.value, font_size=28, color=self.COLOR_TARGET)
        if not self.seq_values:
            new_val.next_to(result_text, RIGHT)
        else:
            new_val.next_to(self.seq_values[-1], RIGHT, buff=0.2)
        
        self.play(Write(new_val), run_time=0.5)
        self.seq_values.append(new_val)
        self.seq.add(new_val)
        
        # 递归右子树
        if node.edge_right:
            self.highlight_edge(node.edge_right, color=self.COLOR_VISITED)
        self.inorder(node.right, pointer, result_text)
        
        # 退栈，将边恢复
        self.move_pointer(pointer, node)
        if node.edge_left:
            self.play(node.edge_left.animate.set_color(WHITE), run_time=0.2)
        if node.edge_right:
            self.play(node.edge_right.animate.set_color(WHITE), run_time=0.2)
