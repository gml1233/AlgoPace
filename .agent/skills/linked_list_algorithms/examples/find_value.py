# coding=utf-8
from manim import *
import sys, os
sys.path.append(os.path.dirname(__file__))
from linked_list_base import LinkedListBase

class FindValueScene(LinkedListBase):
    """单链表的按值查找"""

    def construct(self):
        data = [15, 25, 35, 45, 55]
        self.setup_list_data(data)
        
        target_value = 35
        
        self.show_step_text(f"我们要找到值为 {target_value} 的节点：")
        self.wait(1)

        # 1. 建立遍历指针 p 从头结点后的第一个节点开始
        self.update_step_text("1. 将遍历指针 p 指向链表的第一个数据节点。")
        p_ptr = self.create_pointer(self.nodes[1], "p", color=self.COLOR_CURRENT, direction=DOWN)
        
        self.play(FadeIn(p_ptr))
        self.highlight_node(1, color=self.COLOR_CURRENT)
        self.wait(1)

        # 2. 循环遍历直至 node.value == target_value
        for node_idx in range(1, len(data) + 1):
            node_val = self.nodes[node_idx].value
            
            if node_val == target_value:
                # 找到目标
                self.update_step_text(f"2. 当前节点值 {node_val} == {target_value}！找到目标！")
                self.highlight_node(node_idx, color=self.COLOR_TARGET)
                p_ptr[0].set_color(self.COLOR_TARGET)
                p_ptr[1].set_color(self.COLOR_TARGET)
                
                # 弹出找到的序号
                result_text = Text(f"值为 {target_value} 的节点在第 {node_idx} 个位置", font_size=self.FONT_SIZE, color=GREEN).to_edge(DOWN)
                self.play(Write(result_text))
                self.wait(2)
                break
                
            else:
                self.update_step_text(f"2. 当前节点值 {node_val} != {target_value}，继续向后遍历...")
                self.reset_node_color(node_idx)
                
                if node_idx < len(self.nodes) - 1:
                    new_node = self.nodes[node_idx + 1]
                    self.move_pointer(p_ptr, new_node, run_time=0.8)
                    self.highlight_node(node_idx + 1, color=self.COLOR_CURRENT)
                self.wait(0.8)
