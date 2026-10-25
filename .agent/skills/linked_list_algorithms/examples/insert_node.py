# coding=utf-8
from manim import *
import sys, os
sys.path.append(os.path.dirname(__file__))
from linked_list_base import LinkedListBase

class InsertNodeScene(LinkedListBase):
    """单链表的插入操作"""

    def construct(self):
        data = [10, 20, 40, 50]
        self.setup_list_data(data)
        
        insert_index = 3  # 在第 3 个位置（即 40 之前，或者原 30 的位置）插入新值 30
        insert_value = 30
        
        self.show_step_text(f"我们要 在第 {insert_index} 个位置插入新值 {insert_value}：")
        self.wait(1)

        # 1. 查找第 i-1 个节点（前驱节点）
        self.update_step_text(f"1. 找到第 {insert_index - 1} 个节点作为插入的前驱节点 p。开始遍历：")
        p_ptr = self.create_pointer(self.nodes[0], "p", color=self.COLOR_CURRENT, direction=DOWN)
        self.play(FadeIn(p_ptr))
        
        for i in range(insert_index - 1):
            self.highlight_node(i, color=self.COLOR_CURRENT)
            self.wait(0.5)
            if i < insert_index - 2:
                self.reset_node_color(i)
                self.move_pointer(p_ptr, self.nodes[i + 1])

        self.update_step_text(f"2. 已经到达前驱节点，即第 {insert_index - 1} 个数据节点。")
        self.highlight_node(insert_index - 1, color=self.COLOR_TARGET)
        self.wait(1)

        # 2. 生成新节点 s
        self.update_step_text("3. 为新插入的数值 30 创建新节点 s。")
        new_node_s = self.create_node(insert_value, color=self.COLOR_INSERT)
        new_node_s.move_to(self.nodes[insert_index - 1].get_center() + DOWN * 2.5 + RIGHT * (self.NODE_SPACING / 2))
        
        s_ptr = self.create_pointer(new_node_s, "s", color=self.COLOR_INSERT, direction=DOWN)
        
        self.play(FadeIn(new_node_s), FadeIn(s_ptr))
        self.wait(1)

        # 3. 执行插入连线： s->next = p->next
        self.update_step_text("4. 插入步骤A：将新节点 s 的指针域 next 指向 p 原本的下一个节点。")
        
        p_node = self.nodes[insert_index - 1]
        p_next_node = self.nodes[insert_index]
        
        # 新箭头从 s 指向 p_next
        s_arrow = self.create_arrow_between(new_node_s, p_next_node, color=GREEN)
        self.play(GrowArrow(s_arrow))
        self.wait(1)

        # 4. 执行插入连线： p->next = s
        self.update_step_text("5. 插入步骤B：将前驱节点 p 的指针域 next 指向新节点 s。")
        p_arrow = self.create_arrow_between(p_node, new_node_s, color=YELLOW)
        
        # 原有的箭头（从 p 到 p_next 的）将被删除或隐藏
        old_arrow = self.arrows[insert_index - 1]
        self.play(Transform(old_arrow, p_arrow))
        self.wait(1)

        # 5. 完成插入：重排列链表动画
        self.update_step_text("6. 链表重新排列以保持平滑显示。插入成功！")
        
        self.nodes.insert(insert_index, new_node_s)
        self.node_mobjects.add(new_node_s)
        
        self.arrows.insert(insert_index, s_arrow)
        
        # 移除立即 center，而是在 target 里排版
        
        # 定义动画列表，让所有的节点和箭头重组
        anim_group = []
        
        # 计算居中所需的起始 x 坐标
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
        
        # 同步更新箭头
        arrow_anims = []
        for i in range(len(self.nodes) - 1):
            # 将老的箭头换为新的
            new_arrow = self.create_arrow_between(self.nodes[i], self.nodes[i+1], color=WHITE)
            arrow_anims.append(Transform(self.arrows[i], new_arrow))

        if arrow_anims:
            self.play(*arrow_anims)
        
        # 更新头指针 L 位置
        self.add_pointer_L()

        self.reset_node_color(insert_index)
        self.reset_node_color(insert_index - 1)
        self.remove(p_ptr, s_ptr)
        self.wait(2)
