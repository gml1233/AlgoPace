# coding=utf-8
from manim import *
import sys, os
sys.path.append(os.path.dirname(__file__))
from linked_list_base import LinkedListBase

class GetValueScene(LinkedListBase):
    """单链表的按位置取值"""

    def construct(self):
        data = [10, 20, 30, 40]
        self.setup_list_data(data)
        
        target_index = 3  # 要取的值是链表中第 3 个节点的数值（即 data 的 index 为 2，对应 30）
        target_value = data[target_index - 1]
        
        self.show_step_text(f"我们要找到第 {target_index} 个节点的值：")
        self.wait(1)

        # 1. 建立遍历指针 p 并在头结点初始化
        self.update_step_text("1. 将遍历指针 p 指向头结点的下一个节点：第1个节点。计数器 j = 1")
        p_ptr = self.create_pointer(self.nodes[1], "p", color=self.COLOR_CURRENT, direction=DOWN)
        j_text = Text("j = 1", font_size=self.FONT_SIZE, color=YELLOW).to_corner(UL)
        
        self.play(FadeIn(p_ptr), Write(j_text))
        self.highlight_node(1, color=self.COLOR_CURRENT)
        self.wait(1)

        # 2. 循环遍历直至 j == target_index
        for j in range(1, target_index):
            self.reset_node_color(j)
            
            # 指针后移
            self.update_step_text(f"2. j={j} < {target_index}，继续向后遍历...")
            new_node = self.nodes[j + 1]
            self.move_pointer(p_ptr, new_node, run_time=0.8)
            
            # 更新 j
            new_j_text = Text(f"j = {j + 1}", font_size=self.FONT_SIZE, color=YELLOW).to_corner(UL)
            self.play(Transform(j_text, new_j_text))
            
            self.highlight_node(j + 1, color=self.COLOR_CURRENT)
            self.wait(0.8)

        # 3. 找到目标
        self.update_step_text(f"3. 找到第 {target_index} 个节点！")
        self.highlight_node(target_index, color=self.COLOR_TARGET)
        p_ptr[0].set_color(self.COLOR_TARGET)
        p_ptr[1].set_color(self.COLOR_TARGET)
        self.wait(1)
        
        # 4. 取出数据
        self.update_step_text(f"4. 返回该节点的数据域值：{target_value}。取值结束！")
        target_val_obj = self.nodes[target_index].val_text.copy()
        result_box = Rectangle(width=2, height=1.5, color=WHITE).shift(UP * 2 + RIGHT * 4)
        result_title = Text("结果", font_size=24, color=WHITE).next_to(result_box, UP)
        
        self.play(Create(result_box), Write(result_title))
        self.play(target_val_obj.animate.scale(1.5).move_to(result_box.get_center()).set_color(RED))
        self.wait(2)
