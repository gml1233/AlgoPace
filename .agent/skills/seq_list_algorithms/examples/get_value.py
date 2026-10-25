# coding=utf-8
from manim import *
from seq_list_base import SeqListBase

class GetValue(SeqListBase):
    def construct(self):
        # ${visual_contract}
        arr = ${shared_data}
        self.setup_list_data(arr, capacity=max(len(arr)+2, 6))
        
        target_idx = min(2, len(arr) - 1)
        if target_idx < 0:
            self.show_step_text("顺序表为空，无法取值")
            self.wait(1)
            return

        self.show_step_text(f"开始取值：获取索引 {target_idx} 处的元素")
        self.wait(1)
        
        self.update_step_text("随机访问特性，直接定位")
        ptr = self.create_pointer(target_idx, label_text="i")
        self.play(FadeIn(ptr))
        self.wait(1)
        
        self.highlight_box(target_idx, color=self.COLOR_TARGET)
        self.update_step_text(f"返回索引 {target_idx} 的元素值 {arr[target_idx]}")
        self.wait(2)
        
        self.play(FadeOut(ptr))
        self.reset_box_color(target_idx)
        self.update_step_text("取值操作完成，时间复杂度 O(1)")
        self.wait(1)
