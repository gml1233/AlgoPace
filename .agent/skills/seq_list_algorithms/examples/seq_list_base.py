# coding=utf-8
from manim import *

class SeqListBase(Scene):
    """顺序表动画公共基类
    提供统一的顺序表可视化、遍历指针、元素高亮、插入和删除动画方法等。
    """

    COLOR_DEFAULT = BLUE
    COLOR_EMPTY = DARK_GRAY
    COLOR_TARGET = RED
    COLOR_INSERT = GREEN
    COLOR_CURRENT = YELLOW
    
    BOX_SIZE = 1.0
    FONT_SIZE = 36

    def setup_list_data(self, values, capacity=None):
        """初始化一个顺序表"""
        self.capacity = capacity if capacity is not None else max(len(values) + 2, 6)
        self.length = len(values)
        self.boxes = VGroup()
        self.texts = VGroup()
        self.indices = VGroup()
        
        # 建立元素盒子、内容、索引
        for i in range(self.capacity):
            box = Square(side_length=self.BOX_SIZE, color=self.COLOR_DEFAULT if i < self.length else self.COLOR_EMPTY)
            if i > 0:
                box.next_to(self.boxes[-1], RIGHT, buff=0)
            else:
                box.move_to(ORIGIN)
            self.boxes.add(box)
            
            val_str = str(values[i]) if i < self.length else ""
            txt = Text(val_str, font_size=self.FONT_SIZE)
            txt.move_to(box.get_center())
            self.texts.add(txt)
            
            idx_txt = Text(str(i), font_size=self.FONT_SIZE - 12, color=GRAY)
            idx_txt.next_to(box, DOWN, buff=0.2)
            self.indices.add(idx_txt)

        self.seq_group = VGroup(self.boxes, self.texts, self.indices)
        self.seq_group.move_to(DOWN * 1.5)
        
        # 构建 L 结构体 [ elem | length ]
        self.struct_L_label = Text("L", font_size=self.FONT_SIZE, color=YELLOW)
        
        # elem 部分
        self.elem_box = Rectangle(width=2.0, height=self.BOX_SIZE, color=WHITE)
        self.elem_text = Text("elem", font_size=self.FONT_SIZE - 8).move_to(self.elem_box.get_center())
        
        # length 部分
        self.len_box = Rectangle(width=2.0, height=self.BOX_SIZE, color=WHITE)
        self.len_box.next_to(self.elem_box, RIGHT, buff=0)
        self.len_text = Text(f"length:{self.length}", font_size=self.FONT_SIZE - 8, color=YELLOW).move_to(self.len_box.get_center())
        
        self.struct_group = VGroup(self.elem_box, self.elem_text, self.len_box, self.len_text)
        self.struct_group.move_to(UP * 1.5)
        self.struct_L_label.next_to(self.struct_group, LEFT, buff=0.5)
        self.struct_L = VGroup(self.struct_L_label, self.struct_group)
        
        # 指向顺序表数组的指针(箭头)
        start_pt = self.elem_box.get_bottom()
        # 计算整个可容纳数组空间的中心顶部作为箭头终点
        end_pt = VGroup(*self.boxes).get_top()
        self.elem_pointer = Arrow(start=start_pt, end=end_pt, buff=0.1, color=WHITE)
        
        self.play(FadeIn(self.seq_group), FadeIn(self.struct_L), GrowArrow(self.elem_pointer))
        self.wait(0.5)

    def setup_list_data_instant(self, values, capacity=None):
        """瞬时（无动画）初始化并显示顺序表 (数组 + L 结构体 + 指针)。

        用于视频开场（algorithm_intro）场景：完整顺序表直接 `self.add()` 到画面上，
        使视频第一帧即为完整结构。不调用任何 `self.play(...)`。
        """
        self.capacity = capacity if capacity is not None else max(len(values) + 2, 6)
        self.length = len(values)
        self.boxes = VGroup()
        self.texts = VGroup()
        self.indices = VGroup()

        for i in range(self.capacity):
            box = Square(
                side_length=self.BOX_SIZE,
                color=self.COLOR_DEFAULT if i < self.length else self.COLOR_EMPTY,
            )
            if i > 0:
                box.next_to(self.boxes[-1], RIGHT, buff=0)
            else:
                box.move_to(ORIGIN)
            self.boxes.add(box)

            val_str = str(values[i]) if i < self.length else ""
            txt = Text(val_str, font_size=self.FONT_SIZE)
            txt.move_to(box.get_center())
            self.texts.add(txt)

            idx_txt = Text(str(i), font_size=self.FONT_SIZE - 12, color=GRAY)
            idx_txt.next_to(box, DOWN, buff=0.2)
            self.indices.add(idx_txt)

        self.seq_group = VGroup(self.boxes, self.texts, self.indices)
        self.seq_group.move_to(DOWN * 1.5)

        self.struct_L_label = Text("L", font_size=self.FONT_SIZE, color=YELLOW)

        self.elem_box = Rectangle(width=2.0, height=self.BOX_SIZE, color=WHITE)
        self.elem_text = Text("elem", font_size=self.FONT_SIZE - 8).move_to(self.elem_box.get_center())

        self.len_box = Rectangle(width=2.0, height=self.BOX_SIZE, color=WHITE)
        self.len_box.next_to(self.elem_box, RIGHT, buff=0)
        self.len_text = Text(
            f"length:{self.length}", font_size=self.FONT_SIZE - 8, color=YELLOW
        ).move_to(self.len_box.get_center())

        self.struct_group = VGroup(self.elem_box, self.elem_text, self.len_box, self.len_text)
        self.struct_group.move_to(UP * 1.5)
        self.struct_L_label.next_to(self.struct_group, LEFT, buff=0.5)
        self.struct_L = VGroup(self.struct_L_label, self.struct_group)

        start_pt = self.elem_box.get_bottom()
        end_pt = VGroup(*self.boxes).get_top()
        self.elem_pointer = Arrow(start=start_pt, end=end_pt, buff=0.1, color=WHITE)

        self.add(self.seq_group, self.struct_L, self.elem_pointer)

    def update_length(self, new_length):
        """更新顺序表的长度显示"""
        self.length = new_length
        new_len_text = Text(f"length:{self.length}", font_size=self.FONT_SIZE - 8, color=YELLOW)
        new_len_text.move_to(self.len_text.get_center())
        self.play(Transform(self.len_text, new_len_text))

        
        # 更新盒子的颜色
        anims = []
        for i in range(self.capacity):
            color = self.COLOR_DEFAULT if i < self.length else self.COLOR_EMPTY
            anims.append(self.boxes[i].animate.set_color(color))
        if anims:
            self.play(*anims, run_time=0.5)

    def highlight_box(self, index, color=COLOR_TARGET, run_time=0.5):
        """高亮指定元素的盒子"""
        if 0 <= index < self.capacity:
            self.play(self.boxes[index].animate.set_color(color), run_time=run_time)

    def reset_box_color(self, index, run_time=0.5):
        """重置指定盒子的颜色"""
        if 0 <= index < self.capacity:
            color = self.COLOR_DEFAULT if index < self.length else self.COLOR_EMPTY
            self.play(self.boxes[index].animate.set_color(color), run_time=run_time)

    def create_pointer(self, index, label_text="i", color=COLOR_CURRENT):
        """创建一个指向特定索引的指针"""
        if index < 0 or index >= self.capacity:
            return VGroup()
        target_box = self.boxes[index]
        ptr_text = Text(label_text, font_size=self.FONT_SIZE, color=color)
        arrow = Arrow(start=target_box.get_top() + UP * 1.2, end=target_box.get_top(), buff=0.1, color=color)
        ptr_text.next_to(arrow.get_start(), UP, buff=0.1)
        ptr_group = VGroup(ptr_text, arrow)
        ptr_group.text_obj = ptr_text
        ptr_group.arrow_obj = arrow
        return ptr_group

    def move_pointer(self, ptr_group, new_index, run_time=0.5):
        """移动指针到新索引"""
        if new_index < 0 or new_index >= self.capacity:
            return
        target_box = self.boxes[new_index]
        target_arrow = Arrow(start=target_box.get_top() + UP * 1.2, end=target_box.get_top(), buff=0.1)
        target_text = ptr_group.text_obj.copy().next_to(target_arrow.get_start(), UP, buff=0.1)
        target_group = VGroup(target_text, target_arrow)
        self.play(ptr_group.animate.move_to(target_group.get_center()), run_time=run_time)

    def set_value(self, index, val_str, color=WHITE):
        """设置特定索引处的值并更新文字"""
        if 0 <= index < self.capacity:
            new_text = Text(str(val_str), font_size=self.FONT_SIZE, color=color)
            new_text.move_to(self.boxes[index].get_center())
            self.play(Transform(self.texts[index], new_text))

    def show_step_text(self, text_str):
        if hasattr(self, 'step_text'):
            self.remove(self.step_text)
        self.step_text = Text(text_str, font_size=self.FONT_SIZE-8).to_edge(UP, buff=0.3)
        self.play(FadeIn(self.step_text))

    def update_step_text(self, new_str):
        if not hasattr(self, 'step_text'):
            self.show_step_text(new_str)
            return
        new_text = Text(new_str, font_size=self.FONT_SIZE-8).to_edge(UP, buff=0.3)
        self.play(Transform(self.step_text, new_text))
