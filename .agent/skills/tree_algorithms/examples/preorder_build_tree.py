# coding=utf-8
from manim import *
from tree_base import TreeBase, TreeNodeObj

class PreorderBuildTree(TreeBase):
    def construct(self):
        title = Text("先序遍历序列建立二叉链表", font_size=36).to_edge(UP)
        self.play(Write(title))

        self.seq_str = "AB#D##C#F##"
        seq_text = Text(f"输入序列: {self.seq_str}", font_size=28).next_to(title, DOWN)
        self.play(Write(seq_text))

        self.idx = 0
        self.pointer = self.create_pointer("建树中", color=self.COLOR_TARGET)
        self.play(FadeIn(self.pointer))

        # Placeholder to help compute exact positions if fully built
        # But we do it dynamically, so we can pre-compute positions, 
        # but only render them progressively
        
        # PRE-COMPUTE coordinates to make dynamic building stable
        dummy_data = {
            'v': 'A',
            'l': {'v': 'B', 'r': {'v': 'D'}},
            'r': {'v': 'C', 'r': {'v': 'F'}}
        }
        dummy_root = self.build_tree_from_dict(dummy_data)
        self.compute_positions(dummy_root, x=0, y=1.5)
        
        self.dummy_map = {}
        def map_coords(node):
            if not node: return
            self.dummy_map[node.value] = (node.x, node.y)
            map_coords(node.left)
            map_coords(node.right)
        map_coords(dummy_root)

        root = self.build_tree(x=0, y=1.5, h_sep=2.0)
        self.wait(2)

    def build_tree(self, x, y, h_sep):
        if self.idx >= len(self.seq_str):
            return None
        
        ch = self.seq_str[self.idx]
        self.idx += 1
        
        if ch == '#':
            # Animation for generating a NULL (optional, standard just returns)
            return None
        
        # Use pre-computed coord if available, else approximate
        cx, cy = self.dummy_map.get(ch, (x, y))
        
        node = TreeNodeObj(ch)
        node.x = cx
        node.y = cy
        node.mobject = self.create_node_mobject(ch, color=self.COLOR_TARGET)
        node.mobject.move_to([cx, cy, 0])
        
        self.move_pointer(self.pointer, node)
        self.play(FadeIn(node.mobject), run_time=0.6)
        self.tree_mobjects.add(node.mobject)
        
        # 构建左子树
        node.left = self.build_tree(cx - h_sep, cy - self.VERTICAL_SPACING, h_sep * 0.5)
        if node.left:
            edge = Line([node.x, node.y, 0], [node.left.x, node.left.y, 0], color=WHITE)
            node.edge_left = edge
            self.edges.add(edge)
            self.play(FadeIn(edge), run_time=0.4)
            # Push circle to front
            self.bring_to_front(node.mobject)
            self.bring_to_front(node.left.mobject)

        # 构建右子树
        node.right = self.build_tree(cx + h_sep, cy - self.VERTICAL_SPACING, h_sep * 0.5)
        if node.right:
            edge = Line([node.x, node.y, 0], [node.right.x, node.right.y, 0], color=WHITE)
            node.edge_right = edge
            self.edges.add(edge)
            self.play(FadeIn(edge), run_time=0.4)
            self.bring_to_front(node.mobject)
            self.bring_to_front(node.right.mobject)

        # 变回普通颜色
        self.play(node.mobject.circle.animate.set_fill(self.COLOR_DEFAULT), run_time=0.4)
        return node
