# coding=utf-8
from manim import *
from seq_list_base import SeqListBase

class DeleteElement(SeqListBase):
    def construct(self):
        # ${visual_contract}
        arr = ${shared_data}
        self.setup_list_data(arr, capacity=max(len(arr)+2, 6))
        
        target_idx = min(1, len(arr) - 1)
        if target_idx < 0:
            self.show_step_text("顺序表为空，无法删除")
            self.wait(1)
            return

        self.show_step_text(f"删除元素：删除索引 {target_idx} 的元素")
        self.wait(1)
        
        # 标红要删除的元素
        self.highlight_box(target_idx, color=self.COLOR_TARGET)
        # 删除它的文字
        self.set_value(target_idx, "")
        self.update_step_text(f"已移除索引 {target_idx} 的值，空出位置")
        self.wait(1)

        ptr = self.create_pointer(target_idx + 1, label_text="i")
        self.play(FadeIn(ptr))
        
        # 依次回移元素
        for i in range(target_idx + 1, self.length):
            self.update_step_text(f"将索引 {i} 的元素前移至 {i - 1}")
            self.move_pointer(ptr, i)
            self.highlight_box(i, color=self.COLOR_CURRENT)
            self.wait(0.5)
            
            # 前移动画
            self.set_value(i - 1, arr[i])
            self.reset_box_color(i - 1)
            self.set_value(i, "")
            self.reset_box_color(i)
            self.wait(1)
            
        self.play(FadeOut(ptr))
        
        self.update_step_text("更新顺序表长度减一")
        self.update_length(self.length - 1)
        self.wait(1)
        
        self.update_step_text("删除操作结束，时间复杂度 O(n)")
        self.wait(1)
