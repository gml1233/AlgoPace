# coding=utf-8
from manim import *
from stack_base import StackBase


class PopStack(StackBase):
    def construct(self):
        # ${visual_contract}
        arr = ${shared_data}
        MAXSIZE = max(len(arr) + 2, 6)
        self.setup_stack_data(arr, maxsize=MAXSIZE)

        self.show_step_text("出栈操作 Pop：弹出栈顶元素")
        self.wait(1)

        # 步骤1：判空
        self.update_step_text("if (S.top == S.base) return ERROR; // 判栈空")
        if self.length <= 0:
            self.update_step_text("栈空，无法出栈！")
            self.wait(2)
            return
        self.wait(0.8)

        # 步骤2：top 指针下移一格
        top_idx = self.length - 1
        self.update_step_text("--S.top; // 栈顶指针下移一格")
        # 提前高亮原栈顶
        self.highlight_box(top_idx, color=self.COLOR_POP)
        self.wait(0.5)

        # 步骤3：取出原栈顶位置的值
        self.update_step_text("e = *S.top; // 取出原栈顶元素的值")
        popped = self.pop_element()
        self.wait(0.8)

        # 显示弹出元素信息
        info = Text(
            f"弹出元素: {popped}",
            font_size=self.FONT_SIZE - 8,
            color=self.COLOR_POP,
        ).to_edge(DOWN, buff=0.6)
        self.play(FadeIn(info))
        self.wait(1.0)

        # 完成
        self.update_step_text("return OK; // 出栈完成，时间复杂度 O(1)")
        self.wait(1)
