# coding=utf-8
from manim import *
import sys, os
sys.path.append(os.path.dirname(__file__))
from linked_list_base import LinkedListBase

class InitLinkedListScene(LinkedListBase):
    """单链表的初始化"""

    def construct(self):
        self.show_step_text("单链表的初始化（带头结点）")
        self.wait(0.5)

        # 步骤 1：创建一个新的节点作为头结点
        self.update_step_text("第1步：生成一个新的节点，作为头结点")
        head_node = self.create_node("Head", color=self.COLOR_HEAD)
        head_node.move_to(ORIGIN)
        self.nodes.append(head_node)
        self.node_mobjects.add(head_node)
        self.play(FadeIn(head_node))
        self.wait(1)

        # 步骤 2：头结点的指针域置空
        self.update_step_text("第2步：将头结点的指针域置空（NULL）")
        null_text = Text("^", font_size=self.FONT_SIZE, color=RED)
        null_text.next_to(head_node.dot, RIGHT)
        self.play(Write(null_text))
        self.wait(1)

        # 步骤 3：定义链表 L 指向头结点
        self.update_step_text("第3步：定义单指表指针 L 指向该头结点，初始化完成")
        l_text = Text("L", font_size=self.FONT_SIZE, color=self.COLOR_L_PTR)
        l_arrow = Arrow(
            start=head_node.get_top() + UP * 1.5,
            end=head_node.get_top(),
            buff=0.1,
            color=self.COLOR_L_PTR
        )
        l_text.next_to(l_arrow.get_start(), UP, buff=0.1)
        self.L_pointer = VGroup(l_text, l_arrow)
        self.play(GrowArrow(l_arrow), Write(l_text))
        self.wait(2)
