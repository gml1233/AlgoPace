# coding=utf-8
from manim import *
from tree_base import TreeBase

class InorderNonRecursive(TreeBase):
    def construct(self):
        title = Text("中序遍历的非递归算法", font_size=36).to_edge(UP)
        self.play(Write(title))

        data = {
            'v': 'A',
            'l': {'v': 'B', 'l': {'v': 'D'}, 'r': {'v': 'E'}},
            'r': {'v': 'C', 'r': {'v': 'F'}}
        }
        root = self.build_tree_from_dict(data)
        # 偏右一些，给左边的栈留空间
        self.compute_positions(root, x=2, y=2.0)
        self.draw_tree(root)
        self.play(FadeIn(self.edges), FadeIn(self.tree_mobjects))

        # 栈结构可视化
        stack_title = Text("栈(Stack)", font_size=24).to_corner(DL).shift(UP*4 + RIGHT)
        self.play(Write(stack_title))
        
        stack_box = VGroup()
        for i in range(5):
            rect = Rectangle(width=1.5, height=0.6, color=WHITE).next_to(stack_title, DOWN, buff=0.1 + i*0.6)
            stack_box.add(rect)
        self.play(FadeIn(stack_box))
        
        result_text = Text("遍历序列: ", font_size=28).to_edge(DOWN)
        self.play(Write(result_text))
        self.seq_values = []
        
        pointer = self.create_pointer("p")
        pointer.move_to(root.mobject.get_center() + UP)
        self.play(FadeIn(pointer))
        self.wait(0.5)

        stack = []
        stack_vgroups = [] # 用于保存界面上的栈元素
        
        p = root
        
        while p or stack:
            if p:
                self.move_pointer(pointer, p)
                self.highlight_node(p, color=self.COLOR_VISITED)
                
                # 入栈
                stack.append(p)
                val_text = Text(p.value, font_size=24, color=self.COLOR_VISITED)
                # 放在栈底部的对应位置
                idx = len(stack) - 1
                val_text.move_to(stack_box[4 - idx].get_center())
                stack_vgroups.append(val_text)
                
                self.play(Write(val_text), run_time=0.4)
                
                p = p.left
                if p:
                    self.highlight_edge(stack[-1].edge_left)
            else:
                # 出栈
                p = stack.pop()
                popped_text = stack_vgroups.pop()
                self.play(FadeOut(popped_text), run_time=0.4)
                
                self.move_pointer(pointer, p)
                self.highlight_node(p, color=self.COLOR_TARGET)
                
                # 访问
                new_val = Text(p.value, font_size=28, color=self.COLOR_TARGET)
                if not self.seq_values:
                    new_val.next_to(result_text, RIGHT)
                else:
                    new_val.next_to(self.seq_values[-1], RIGHT, buff=0.2)
                self.play(Write(new_val), run_time=0.4)
                self.seq_values.append(new_val)
                
                # 转右子树
                if p.edge_right:
                    self.highlight_edge(p.edge_right)
                p = p.right
                
        self.wait(2)
