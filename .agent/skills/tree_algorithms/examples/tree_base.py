# coding=utf-8
from manim import *

class TreeNodeObj:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right
        self.mobject = None  # VGroup containing Circle and Text
        self.edge_left = None  # Line connecting to left child
        self.edge_right = None # Line connecting to right child
        self.x = 0  # To be calculated
        self.y = 0  # To be calculated

class TreeBase(Scene):
    """二叉树动画公共基类
    提供统一的树结点构建、布局计算、遍历动画辅助方法等
    """

    COLOR_DEFAULT = BLUE
    COLOR_VISITED = YELLOW
    COLOR_TARGET = GREEN
    COLOR_CLONE = TEAL
    COLOR_NULL = GRAY

    NODE_RADIUS = 0.4
    VERTICAL_SPACING = 1.2
    HORIZONTAL_SPACING = 1.5

    def setup(self):
        self.tree_mobjects = VGroup()
        self.edges = VGroup()
        self.nodes = []

    def create_node_mobject(self, value, color=COLOR_DEFAULT, radius=NODE_RADIUS):
        """生成界面上的树结点 Mobject"""
        group = VGroup()
        circle = Circle(radius=radius, color=WHITE, fill_color=color, fill_opacity=0.8)
        text = Text(str(value), font_size=24, color=WHITE)
        group.add(circle, text)
        group.circle = circle
        group.text = text
        return group

    def build_tree_from_dict(self, data):
        """根据嵌套字典格式建立树模型 例如: {'v': 'A', 'l': {'v': 'B'}, 'r': {'v': 'C'}}"""
        if not data:
            return None
        node = TreeNodeObj(data.get('v'))
        if 'l' in data:
            node.left = self.build_tree_from_dict(data['l'])
        if 'r' in data:
            node.right = self.build_tree_from_dict(data['r'])
        return node

    def compute_positions(self, root, x=0, y=3, h_sep=2.0):
        """计算树中所有结点的坐标"""
        if not root:
            return
        root.x = x
        root.y = y
        if root.left:
            self.compute_positions(root.left, x - h_sep, y - self.VERTICAL_SPACING, h_sep * 0.5)
        if root.right:
            self.compute_positions(root.right, x + h_sep, y - self.VERTICAL_SPACING, h_sep * 0.5)

    def draw_tree(self, root):
        """绘制已计算好坐标的整棵树"""
        if not root:
            return
        
        # Draw edges first so they are behind nodes
        if root.left:
            self.draw_tree(root.left)
            edge = Line([root.x, root.y, 0], [root.left.x, root.left.y, 0], color=WHITE)
            root.edge_left = edge
            self.edges.add(edge)
            
        if root.right:
            self.draw_tree(root.right)
            edge = Line([root.x, root.y, 0], [root.right.x, root.right.y, 0], color=WHITE)
            root.edge_right = edge
            self.edges.add(edge)

        # Create the node mobject
        root.mobject = self.create_node_mobject(root.value)
        root.mobject.move_to([root.x, root.y, 0])
        self.tree_mobjects.add(root.mobject)
        self.nodes.append(root)

    def setup_default_tree(self, data):
        """一次性生成并展示整棵树"""
        root = self.build_tree_from_dict(data)
        self.compute_positions(root)
        self.draw_tree(root)
        self.play(FadeIn(self.edges), FadeIn(self.tree_mobjects), run_time=1)
        self.wait(0.5)
        return root

    def setup_default_tree_instant(self, data):
        """瞬时（无动画）绘制整棵树。

        用于视频开场（algorithm_intro）场景：将整棵树直接 `self.add()` 到画面上，
        使视频第一帧即包含完整结构，可作为封面缩略图。不调用任何 `self.play(...)`。
        返回根节点 TreeNodeObj。
        """
        root = self.build_tree_from_dict(data)
        self.compute_positions(root)
        self.draw_tree(root)
        self.add(self.edges, self.tree_mobjects)
        return root

    def highlight_node(self, node, color=COLOR_VISITED):
        """高亮某一结点"""
        if node and node.mobject:
            self.play(node.mobject.circle.animate.set_fill(color), run_time=0.5)

    def highlight_edge(self, edge, color=YELLOW):
        if edge:
            self.play(edge.animate.set_color(color), run_time=0.5)

    def create_pointer(self, text="p", color=YELLOW):
        """创建一个游标"""
        pointer = VGroup()
        arrow = Arrow(UP*0.5, DOWN*0.1, color=color, buff=0)
        label = Text(text, font_size=20, color=color).next_to(arrow, UP, buff=0.1)
        pointer.add(arrow, label)
        return pointer

    def move_pointer(self, pointer, node, direction=UP):
        """移动游标指向结点"""
        if node and node.mobject:
            target_pos = node.mobject.get_center() + direction * (self.NODE_RADIUS + 0.6)
            self.play(pointer.animate.move_to(target_pos), run_time=0.5)
