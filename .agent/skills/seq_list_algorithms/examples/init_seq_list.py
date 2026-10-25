# coding=utf-8
from manim import *
from seq_list_base import SeqListBase

class InitSeqList(SeqListBase):
    def construct(self):
        self.show_step_text("构造一个空的顺序表L: InitList_Sq")
        self.wait(1)
        
        # 步骤1：为顺序表分配一个大小为MAXSIZE的数组空间
        self.update_step_text("L.elem = new ElemType[MAXSIZE]; // 分配数组空间")
        MAXSIZE = 8
        self.setup_list_data([], capacity=MAXSIZE)
        self.wait(1.5)
        
        # 步骤2：检查分配是否失败
        self.update_step_text("if (!L.elem) exit(OVERFLOW); // 检查存储分配")
        self.play(Indicate(self.elem_pointer, color=GREEN))
        self.wait(1.5)
        
        # 步骤3：设置长度为0
        self.update_step_text("L.length = 0; // 空表长度为0")
        # 即使初始已经是0，也可以闪烁一下 length 文本提醒观众
        self.play(Indicate(self.len_text, color=YELLOW, scale_factor=1.5))
        self.wait(1.5)
        
        # 完成
        self.update_step_text("return 0; // 顺序表初始化完成")
        self.wait(1)


