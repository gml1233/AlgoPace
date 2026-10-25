# coding=utf-8
from manim import *
from tree_base import TreeBase, TreeNodeObj

class CopyTree(TreeBase):
    def construct(self):
        title = Text("复制二叉树", font_size=36).to_edge(UP)
        self.play(Write(title))

        data = {
            'v': 'A',
            'l': {'v': 'B', 'l': {'v': 'D'}, 'r': {'v': 'E'}},
            'r': {'v': 'C', 'r': {'v': 'F'}}
        }
        root = self.build_tree_from_dict(data)
        self.compute_positions(root, x=-3, y=1.5)
        self.draw_tree(root)
        self.play(FadeIn(self.edges), FadeIn(self.tree_mobjects))

        orig_label = Text("原二叉树", font_size=24).next_to(root.mobject, UP)
        self.play(Write(orig_label))

        self.pointer = self.create_pointer("复制", color=self.COLOR_VISITED)
        self.pointer.move_to(root.mobject.get_center() + UP*1.2)
        self.play(FadeIn(self.pointer))

        new_label = Text("新二叉树", font_size=24).move_to([4, root.y + 0.8, 0])
        self.play(Write(new_label))

        self.OFFSET_X = 7  # 偏移量，复制到右侧
        new_root = self.copy_tree(root)

        self.wait(2)

    def copy_tree(self, node):
        if not node:
            return None

        self.move_pointer(self.pointer, node)
        self.highlight_node(node, color=self.COLOR_VISITED)

        # 创建新结点
        new_node = TreeNodeObj(node.value)
        new_node.x = node.x + self.OFFSET_X
        new_node.y = node.y
        new_node.mobject = self.create_node_mobject(new_node.value, color=self.COLOR_CLONE)
        new_node.mobject.move_to([new_node.x, new_node.y, 0])
        
        self.play(TransformFromCopy(node.mobject, new_node.mobject), run_time=0.8)
        self.tree_mobjects.add(new_node.mobject)

        # 恢复原颜色
        self.play(node.mobject.circle.animate.set_fill(self.COLOR_DEFAULT), run_time=0.3)

        # 递归复制左子树
        if node.edge_left:
            self.highlight_edge(node.edge_left)
        new_node.left = self.copy_tree(node.left)
        if new_node.left:
            edge = Line([new_node.x, new_node.y, 0], [new_node.left.x, new_node.left.y, 0], color=WHITE)
            new_node.edge_left = edge
            self.edges.add(edge)
            self.play(FadeIn(edge), run_time=0.4)
            self.bring_to_front(new_node.mobject)
            self.bring_to_front(new_node.left.mobject)

        self.move_pointer(self.pointer, node)

        # 递归复制右子树
        if node.edge_right:
            self.highlight_edge(node.edge_right)
        new_node.right = self.copy_tree(node.right)
        if new_node.right:
            edge = Line([new_node.x, new_node.y, 0], [new_node.right.x, new_node.right.y, 0], color=WHITE)
            new_node.edge_right = edge
            self.edges.add(edge)
            self.play(FadeIn(edge), run_time=0.4)
            self.bring_to_front(new_node.mobject)
            self.bring_to_front(new_node.right.mobject)

        # 退栈连线恢复
        if node.edge_left:
            self.play(node.edge_left.animate.set_color(WHITE), run_time=0.1)
        if node.edge_right:
            self.play(node.edge_right.animate.set_color(WHITE), run_time=0.1)

        return new_node
