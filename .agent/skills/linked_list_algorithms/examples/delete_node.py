# coding=utf-8
from manim import *
import sys, os
sys.path.append(os.path.dirname(__file__))
from linked_list_base import LinkedListBase

class DeleteNodeScene(LinkedListBase):
    """单链表的删除操作"""

    def construct(self):
        data = [10, 20, 30, 40, 50]
        self.setup_list_data(data)
        
        delete_index = 3  # 删除第 3 个数据节点的值 30
        
        self.show_step_text(f"我们要删除第 {delete_index} 个位置的节点：")
        self.wait(1)

        # 1. 查找第 i-1 个节点（前驱节点）
        self.update_step_text(f"1. 找到第 {delete_index - 1} 个节点作为删除节点的前驱 p。")
        p_ptr = self.create_pointer(self.nodes[0], "p", color=self.COLOR_CURRENT, direction=DOWN)
        self.play(FadeIn(p_ptr))
        
        # 遍历到前驱节点
        for i in range(delete_index - 1):
            if i > 0:
                self.reset_node_color(i)
                self.move_pointer(p_ptr, self.nodes[i], run_time=0.5)
            self.highlight_node(i, color=self.COLOR_CURRENT, run_time=0.5)
            self.wait(0.5)

        self.update_step_text(f"2. 已经到达前驱节点 p，即第 {delete_index - 1} 个节点。")
        self.highlight_node(delete_index - 1, color=self.COLOR_TARGET)
        self.wait(1)

        # 2. 定位要删除的节点 q = p->next
        self.update_step_text("3. 定义指针 q 指向 p 的下一个节点，即要被删除的节点。")
        delete_node_q = self.nodes[delete_index]
        q_ptr = self.create_pointer(delete_node_q, "q", color=RED, direction=DOWN)
        
        self.play(FadeIn(q_ptr))
        self.highlight_node(delete_index, color=RED)
        self.wait(1)

        # 3. 跨过要删除的节点 p->next = q->next
        self.update_step_text("4. 删除步骤：将 p 的指针域 next 绕过 q 指向 q 的下一个节点。")
        p_node = self.nodes[delete_index - 1]
        next_node = self.nodes[delete_index + 1] if delete_index + 1 < len(self.nodes) else None
        
        if next_node:
            new_arrow = self.create_arrow_between(p_node, next_node, color=GREEN)
            
            # 删除旧指针
            old_p_arrow = self.arrows[delete_index - 1]
            old_q_arrow = self.arrows[delete_index]
            
            self.play(ReplacementTransform(old_p_arrow, new_arrow), FadeOut(old_q_arrow))
            self.wait(1)
            
            self.update_step_text("5. 释放被删除节点 q 占用的内存空间。")
            self.play(
                FadeOut(delete_node_q), 
                FadeOut(q_ptr)
            )
            self.wait(1)
            
            # 从列表中移除节点和箭头
            self.nodes.pop(delete_index)
            self.node_mobjects.remove(delete_node_q)
            self.arrows.remove(old_p_arrow)
            self.arrows.remove(old_q_arrow)
            self.arrows.insert(delete_index - 1, new_arrow)

        # 4. 重新排列链表
        self.update_step_text("6. 链表重组，删除完成！")
        
        # 避免立即 center，通过 target 坐标排布
        anim_group = []
        
        # 计算新链表占用的总宽度
        total_width = (len(self.nodes) - 1) * self.NODE_SPACING + self.NODE_WIDTH
        start_x = -total_width / 2 + self.NODE_WIDTH / 2

        for i in range(len(self.nodes)):
            if i == 0:
                self.nodes[0].generate_target()
                self.nodes[0].target.move_to([start_x, ORIGIN[1], 0])
                anim_group.append(MoveToTarget(self.nodes[0]))
            else:
                self.nodes[i].generate_target()
                self.nodes[i].target.next_to(self.nodes[i-1].target, RIGHT, buff=self.NODE_SPACING - self.NODE_WIDTH)
                anim_group.append(MoveToTarget(self.nodes[i]))

        self.play(*anim_group)
        
        arrow_anims = []
        for i in range(len(self.nodes) - 1):
            new_arr = self.create_arrow_between(self.nodes[i], self.nodes[i+1], color=WHITE)
            arrow_anims.append(Transform(self.arrows[i], new_arr))

        if arrow_anims:
            self.play(*arrow_anims)
        
        # 重置颜色
        self.reset_node_color(delete_index - 1)
        self.remove(p_ptr)
        self.add_pointer_L()
        self.wait(2)
