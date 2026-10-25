# coding=utf-8
from manim import *
from stack_base import StackBase


class InitStack(StackBase):
    def construct(self):
        # ${visual_contract}
        MAXSIZE = 6
        self.show_step_text("构造一个空的顺序栈 S: InitStack_Sq")
        self.wait(1)

        # 步骤1：为顺序栈分配一个大小为 MAXSIZE 的数组空间，base 指向栈底
        self.update_step_text("S.base = new SElemType[MAXSIZE]; // 分配数组空间")
        self.setup_stack_data([], maxsize=MAXSIZE)
        self.wait(1.0)

        # 步骤2：检查分配是否失败
        self.update_step_text("if (!S.base) exit(OVERFLOW); // 检查存储分配")
        self.play(Indicate(self.base_ptr, color=GREEN))
        self.wait(1.0)

        # 步骤3：栈顶指针 top 与 base 同位置，表示栈空
        self.update_step_text("S.top = S.base; // 栈顶指针 == 栈底指针 → 栈空")
        self.play(Indicate(self.top_ptr, color=YELLOW, scale_factor=1.5))
        self.wait(1.0)

        # 步骤4：设置 stacksize
        self.update_step_text("S.stacksize = MAXSIZE; // 记录栈容量")
        self.play(Indicate(self.maxsize_text, color=WHITE, scale_factor=1.3))
        self.wait(1.0)

        # 完成
        self.update_step_text("return OK; // 顺序栈初始化完成，时间复杂度 O(1)")
        self.wait(1)
