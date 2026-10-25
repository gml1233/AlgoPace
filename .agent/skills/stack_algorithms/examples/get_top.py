# coding=utf-8
from manim import *
from stack_base import StackBase


class GetTop(StackBase):
    def construct(self):
        # ${visual_contract}
        arr = ${shared_data}
        MAXSIZE = max(len(arr) + 2, 6)
        self.setup_stack_data(arr, maxsize=MAXSIZE)

        self.show_step_text("取栈顶元素 GetTop：读取栈顶元素的值（不出栈）")
        self.wait(1)

        # 步骤1：判空
        self.update_step_text("if (S.top == S.base) return ERROR; // 判栈空")
        if self.length <= 0:
            self.update_step_text("栈空，无栈顶元素可取！")
            self.wait(2)
            return
        self.wait(0.8)

        # 步骤2：定位栈顶元素：top - 1 处
        top_idx = self.length - 1
        self.update_step_text("e = *(S.top - 1); // 栈顶元素位于 top 下方一格")
        # 创建一个辅助指针标注 top-1
        target_box = self.boxes[top_idx]
        marker = Text("S.top - 1", font_size=self.FONT_SIZE - 14, color=self.COLOR_TOP)
        marker_arrow = Arrow(
            start=target_box.get_right() + RIGHT * 1.6,
            end=target_box.get_right(),
            buff=0.1,
            color=self.COLOR_TOP,
        )
        marker.next_to(marker_arrow.get_start(), RIGHT, buff=0.1)
        marker_group = VGroup(marker, marker_arrow)
        self.play(FadeIn(marker_group))
        self.wait(0.8)

        # 步骤3：高亮栈顶元素并取出值
        peek_val = self.peek_top()
        self.wait(0.5)

        info = Text(
            f"栈顶元素: {peek_val}",
            font_size=self.FONT_SIZE - 8,
            color=self.COLOR_TOP,
        ).to_edge(DOWN, buff=0.6)
        self.play(FadeIn(info))
        self.wait(1.0)

        # 步骤4：强调栈状态没有改变
        self.update_step_text("// 注意：GetTop 不修改 S.top，栈结构保持不变")
        self.play(Indicate(self.top_ptr, color=self.COLOR_TOP_PTR, scale_factor=1.3))
        self.wait(0.8)

        # 完成
        self.update_step_text("return OK; // 取栈顶元素完成，时间复杂度 O(1)")
        self.wait(1)

        self.play(FadeOut(marker_group))
