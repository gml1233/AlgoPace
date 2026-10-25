# coding=utf-8
from manim import *
from tree_base import TreeBase

class InorderThreading(TreeBase):
    def construct(self):
        title = Text("二叉树的中序线索化", font_size=36).to_edge(UP)
        self.play(Write(title))

        data = {
            'v': 'A',
            'l': {'v': 'B', 'l': {'v': 'D'}, 'r': {'v': 'E'}},
            'r': {'v': 'C', 'r': {'v': 'F'}}
        }
        root = self.build_tree_from_dict(data)
        self.compute_positions(root, x=0, y=2.0)
        self.draw_tree(root)
        self.play(FadeIn(self.edges), FadeIn(self.tree_mobjects))

        self.pre_node = None
        
        self.pointer_p = self.create_pointer("p", color=BLUE)
        self.pointer_pre = self.create_pointer("pre", color=RED)
        
        # 将指针放在初始位置上空
        self.pointer_p.move_to(root.mobject.get_center() + UP)
        self.pointer_pre.move_to([-5, 3, 0])
        
        self.play(FadeIn(self.pointer_p), FadeIn(self.pointer_pre))
        
        self.inorder_thread(root)
        
        # 处理最后一个结点的右线索
        if self.pre_node and not self.pre_node.right:
            self.move_pointer(self.pointer_pre, self.pre_node)
            right_thread = DashedLine(
                self.pre_node.mobject.get_right(),
                self.pre_node.mobject.get_right() + RIGHT * 0.8,
                color=RED
            ).add_tip()
            self.play(Create(right_thread))
            
        self.wait(2)

    def inorder_thread(self, p):
        if not p:
            return

        self.move_pointer(self.pointer_p, p)
        
        # 1. 递归线索化左子树
        self.inorder_thread(p.left)
        
        self.move_pointer(self.pointer_p, p)
        self.highlight_node(p, color=self.COLOR_VISITED)
        
        # 2. 处理当前结点的线索
        if not p.left:
            # 建立当前结点的前驱线索
            ThreadLeft = None
            if self.pre_node:
                # 指向 pre_node
                ThreadLeft = DashedLine(
                    p.mobject.get_left(),
                    self.pre_node.mobject.get_right(),
                    color=YELLOW
                ).add_tip()
            else:
                # 悬空
                ThreadLeft = DashedLine(
                    p.mobject.get_left(),
                    p.mobject.get_left() + LEFT * 0.8,
                    color=YELLOW
                ).add_tip()
            self.play(Create(ThreadLeft), run_time=0.6)
            
        if self.pre_node and not self.pre_node.right:
            # 建立前驱结点的后继线索
            self.move_pointer(self.pointer_pre, self.pre_node)
            ThreadRight = DashedLine(
                self.pre_node.mobject.get_right(),
                p.mobject.get_left(),
                color=RED
            ).add_tip()
            self.play(Create(ThreadRight), run_time=0.6)
            
        # pre = p
        self.pre_node = p
        self.move_pointer(self.pointer_pre, self.pre_node)
        
        # 3. 递归线索化右子树
        self.inorder_thread(p.right)
        
        self.move_pointer(self.pointer_p, p)
        self.play(p.mobject.circle.animate.set_fill(self.COLOR_DEFAULT), run_time=0.2)
