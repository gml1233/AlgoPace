# coding=utf-8
from manim import *
from seq_list_base import SeqListBase

class InsertElement(SeqListBase):
    def construct(self):
        # ${visual_contract}
        arr = ${shared_data}
        self.setup_list_data(arr, capacity=max(len(arr)+2, 6))
        
        insert_idx = 2
        insert_val = 99
        
        self.show_step_text(f"插入元素：在索引 {insert_idx} 位置插入值 {insert_val}")
        self.wait(1)
        
        if self.length >= self.capacity:
            self.update_step_text("顺序表已满，无法插入！")
            self.wait(2)
            return

        ptr = self.create_pointer(self.length - 1, label_text="i")
        self.play(FadeIn(ptr))
        
        # 从后往前移动元素
        for i in range(self.length - 1, insert_idx - 1, -1):
            self.update_step_text(f"将索引 {i} 的元素后移至 {i + 1}")
            self.move_pointer(ptr, i)
            self.highlight_box(i, color=self.COLOR_CURRENT)
            self.wait(0.5)
            
            # 后移操作动画
            self.set_value(i + 1, arr[i])
            self.reset_box_color(i + 1)
            self.set_value(i, "")
            self.reset_box_color(i)
            self.wait(1)

        self.play(FadeOut(ptr))
        
        # 插入新元素
        self.update_step_text(f"在空出的索引 {insert_idx} 处插入值 {insert_val}")
        target_box = self.boxes[insert_idx]
        new_val_text = Text(str(insert_val), font_size=self.FONT_SIZE, color=self.COLOR_INSERT)
        new_val_text.move_to(target_box.get_center())
        self.play(Transform(self.texts[insert_idx], new_val_text), target_box.animate.set_color(self.COLOR_INSERT))
        self.wait(1)
        
        self.update_length(self.length + 1)
        self.update_step_text("插入完成，数组长度加一")
        self.wait(1)
        
        self.reset_box_color(insert_idx)
        self.set_value(insert_idx, insert_val, color=WHITE)
        self.update_step_text("插入操作结束，时间复杂度 O(n)")
        self.wait(1)
