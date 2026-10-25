# coding=utf-8
from manim import *
from seq_list_base import SeqListBase

class FindValue(SeqListBase):
    def construct(self):
        # ${visual_contract}
        arr = ${shared_data}
        self.setup_list_data(arr, capacity=max(len(arr)+2, 6))
        
        if len(arr) == 0:
            self.show_step_text("顺序表为空，无法查找")
            self.wait(1)
            return

        target_val = arr[min(2, len(arr) - 1)]
        self.show_step_text(f"开始按值查找：寻找值为 {target_val} 的元素")
        self.wait(1)
        
        ptr = self.create_pointer(0, label_text="i")
        self.play(FadeIn(ptr))
        
        for i in range(len(arr)):
            self.move_pointer(ptr, i)
            self.highlight_box(i, color=self.COLOR_CURRENT)
            self.update_step_text(f"当前比较索引为 {i}，值为 {arr[i]}")
            self.wait(1)
            
            if arr[i] == target_val:
                self.update_step_text(f"查找成功！索引 {i} 的值为目标值")
                self.highlight_box(i, color=self.COLOR_TARGET)
                self.wait(2)
                break
            else:
                self.reset_box_color(i)
                
        else:
            self.update_step_text("遍历结束，未找到目标值")
            
        self.wait(1)
        self.play(FadeOut(ptr))
        self.update_step_text("查找操作结束，时间复杂度 O(n)")
        self.wait(1)
