# coding=utf-8
from manim import *
from stack_base import StackBase


class PushStack(StackBase):
    def construct(self):
        # ${visual_contract}
        arr = ${shared_data}
        MAXSIZE = max(len(arr) + 2, 6)
        self.setup_stack_data(arr, maxsize=MAXSIZE)

        push_val = 99
        self.show_step_text(f"入栈操作 Push：将元素 {push_val} 压入栈顶")
        self.wait(1)

        # 步骤1：判满
        self.update_step_text("if (S.top - S.base == S.stacksize) return ERROR; // 判栈满")
        if self.length >= self.maxsize:
            self.update_step_text("栈已满，无法入栈！")
            self.wait(2)
            return
        self.wait(0.8)

        # 步骤2：将元素压入 *S.top
        self.update_step_text(f"*S.top = e; // 把 {push_val} 写入栈顶位置")
        self.push_element(push_val)
        self.wait(0.8)

        # 步骤3：top 指针上移一格（push_element 已自动完成）
        self.update_step_text("++S.top; // 栈顶指针上移")
        self.play(Indicate(self.top_ptr, color=self.COLOR_TOP_PTR, scale_factor=1.4))
        self.wait(0.8)

        # 完成
        self.update_step_text("return OK; // 入栈完成，时间复杂度 O(1)")
        self.wait(1)
