# coding=utf-8
from manim import *


class StackBase(Scene):
    """顺序栈动画公共基类

    数据结构约定：
      - base : 指向栈底（永远指向 boxes[0] 的左侧）
      - top  : 指向"栈顶元素的下一位置"（即下一次入栈写入的索引）
      - stacksize : 栈容量（self.maxsize）
      - 栈空：top == base ；栈满：top - base == stacksize

    布局规定：栈以自下而上的垂直方向堆叠（boxes[0] 在最下，boxes[maxsize-1] 在最上）。
    """

    # ========== 颜色规范 ==========
    COLOR_DEFAULT = BLUE          # 栈中元素默认色
    COLOR_EMPTY = DARK_GRAY       # 空栈格颜色
    COLOR_TOP = YELLOW            # 栈顶元素高亮 / top 指针颜色
    COLOR_PUSH = GREEN            # 新入栈元素颜色
    COLOR_POP = RED               # 即将出栈元素颜色
    COLOR_BASE_PTR = ORANGE       # base 指针颜色
    COLOR_TOP_PTR = YELLOW        # top 指针颜色

    # ========== 布局参数 ==========
    BOX_SIZE = 1.0
    FONT_SIZE = 36
    INDEX_FONT_SIZE = 22
    MAXSIZE_DEFAULT = 6
    PTR_OFFSET = 1.4              # 指针箭头水平偏移量
    POINTER_GAP = 0.6             # 栈空时 top 与 base 上下错位的距离

    # ------------------------------------------------------------------
    # 初始化（带动画 / 瞬时）
    # ------------------------------------------------------------------
    def _build_boxes(self, values):
        """构造垂直堆叠的栈格、文本与索引标签。"""
        self.boxes = VGroup()
        self.texts = VGroup()
        self.indices = VGroup()

        for i in range(self.maxsize):
            color = self.COLOR_DEFAULT if i < self.length else self.COLOR_EMPTY
            box = Square(side_length=self.BOX_SIZE, color=color)
            if i == 0:
                box.move_to(ORIGIN)
            else:
                box.next_to(self.boxes[-1], UP, buff=0)
            self.boxes.add(box)

            val_str = str(values[i]) if i < self.length else ""
            txt = Text(val_str, font_size=self.FONT_SIZE).move_to(box.get_center())
            self.texts.add(txt)

            idx_txt = Text(str(i), font_size=self.INDEX_FONT_SIZE, color=GRAY)
            idx_txt.next_to(box, RIGHT, buff=0.25)
            self.indices.add(idx_txt)

        self.stack_group = VGroup(self.boxes, self.texts, self.indices)
        self.stack_group.move_to(ORIGIN)

    def _build_base_pointer(self):
        """创建 base 指针（始终指向 boxes[0] 的左侧）。"""
        bottom_box = self.boxes[0]
        end_pt = bottom_box.get_left()
        start_pt = end_pt + LEFT * self.PTR_OFFSET
        arrow = Arrow(start=start_pt, end=end_pt, buff=0.1, color=self.COLOR_BASE_PTR)
        label = Text("base", font_size=self.FONT_SIZE - 12, color=self.COLOR_BASE_PTR)
        label.next_to(arrow.get_start(), LEFT, buff=0.1)
        self.base_ptr = VGroup(label, arrow)
        self.base_ptr.label_obj = label
        self.base_ptr.arrow_obj = arrow

    def _top_arrow_target(self, length):
        """根据当前元素个数 length 返回 top 指针箭头的 (start, end) 坐标。"""
        if length <= 0:
            # 栈空：与 base 同高，但稍微向下错位以便区分
            end_pt = self.boxes[0].get_left() + DOWN * self.POINTER_GAP
        elif length >= self.maxsize:
            # 栈满：指向最上方栈格的上方
            end_pt = self.boxes[self.maxsize - 1].get_left() + UP * self.BOX_SIZE
        else:
            # 一般情况：指向第 length 个格子（即下一次入栈写入位置）的左侧
            end_pt = self.boxes[length].get_left()
        start_pt = end_pt + LEFT * self.PTR_OFFSET
        return start_pt, end_pt

    def _build_top_pointer(self, length):
        """构建 top 指针 VGroup，指向第 length 个空格的左侧。"""
        start_pt, end_pt = self._top_arrow_target(length)
        arrow = Arrow(start=start_pt, end=end_pt, buff=0.1, color=self.COLOR_TOP_PTR)
        label = Text("top", font_size=self.FONT_SIZE - 12, color=self.COLOR_TOP_PTR)
        label.next_to(arrow.get_start(), LEFT, buff=0.1)
        ptr = VGroup(label, arrow)
        ptr.label_obj = label
        ptr.arrow_obj = arrow
        return ptr

    def _build_size_text(self):
        self.maxsize_text = Text(
            f"stacksize: {self.maxsize}",
            font_size=self.FONT_SIZE - 14,
            color=WHITE,
        ).next_to(self.stack_group, DOWN, buff=0.6)

    def setup_stack_data(self, values, maxsize=None):
        """初始化顺序栈（带 FadeIn 动画）。

        Args:
            values: 初始入栈数据，从栈底到栈顶（values[0] 在最下）。
            maxsize: 栈容量，默认 max(len(values)+2, 6)。
        """
        self.maxsize = maxsize if maxsize is not None else max(len(values) + 2, self.MAXSIZE_DEFAULT)
        self.length = len(values)

        self._build_boxes(values)
        self._build_base_pointer()
        self.top_ptr = self._build_top_pointer(self.length)
        self._build_size_text()

        self.play(
            FadeIn(self.stack_group),
            FadeIn(self.base_ptr),
            FadeIn(self.top_ptr),
            FadeIn(self.maxsize_text),
        )
        self.wait(0.5)

    def setup_stack_data_instant(self, values, maxsize=None):
        """瞬时（无动画）初始化顺序栈，用于开场场景。"""
        self.maxsize = maxsize if maxsize is not None else max(len(values) + 2, self.MAXSIZE_DEFAULT)
        self.length = len(values)

        self._build_boxes(values)
        self._build_base_pointer()
        self.top_ptr = self._build_top_pointer(self.length)
        self._build_size_text()

        self.add(self.stack_group, self.base_ptr, self.top_ptr, self.maxsize_text)

    # ------------------------------------------------------------------
    # 指针 / 栈格 / 文本 操作
    # ------------------------------------------------------------------
    def move_top_pointer(self, new_length, run_time=0.5):
        """移动 top 指针到 length=new_length 对应的位置。"""
        new_top = self._build_top_pointer(new_length)
        self.play(Transform(self.top_ptr, new_top), run_time=run_time)
        self.length = new_length

    def highlight_box(self, index, color=COLOR_TOP, run_time=0.5):
        """高亮指定索引的栈格。"""
        if 0 <= index < self.maxsize:
            self.play(self.boxes[index].animate.set_color(color), run_time=run_time)

    def reset_box_color(self, index, run_time=0.5):
        """根据 length 把指定栈格颜色还原。"""
        if 0 <= index < self.maxsize:
            color = self.COLOR_DEFAULT if index < self.length else self.COLOR_EMPTY
            self.play(self.boxes[index].animate.set_color(color), run_time=run_time)

    def set_value(self, index, val_str, color=WHITE):
        """设置指定栈格的文字。"""
        if 0 <= index < self.maxsize:
            new_text = Text(str(val_str), font_size=self.FONT_SIZE, color=color)
            new_text.move_to(self.boxes[index].get_center())
            self.play(Transform(self.texts[index], new_text))

    # ------------------------------------------------------------------
    # 高级操作：入栈 / 出栈 / 取栈顶
    # ------------------------------------------------------------------
    def push_element(self, value, run_time=0.6):
        """完整的入栈动画：值从右侧滑入 boxes[length]，再移动 top 指针。

        Returns:
            True 入栈成功；False 栈满未操作。
        """
        if self.length >= self.maxsize:
            return False

        target_box = self.boxes[self.length]
        # 1) 元素从右侧飞入
        flying = Text(str(value), font_size=self.FONT_SIZE, color=self.COLOR_PUSH)
        flying.next_to(target_box, RIGHT, buff=1.5)
        self.play(FadeIn(flying), run_time=0.3)
        self.play(
            flying.animate.move_to(target_box.get_center()),
            target_box.animate.set_color(self.COLOR_PUSH),
            run_time=run_time,
        )

        # 2) 把飞入文字"落实"为正式槽位文字
        new_text = Text(str(value), font_size=self.FONT_SIZE, color=WHITE).move_to(target_box.get_center())
        self.add(new_text)
        self.remove(self.texts[self.length])
        self.texts.remove(self.texts[self.length])
        self.texts.insert(self.length, new_text)
        self.remove(flying)

        # 3) 栈格恢复默认色
        self.play(target_box.animate.set_color(self.COLOR_DEFAULT), run_time=0.3)

        # 4) 移动 top 指针
        self.move_top_pointer(self.length + 1)
        return True

    def pop_element(self, run_time=0.6):
        """完整的出栈动画：移动 top 指针下移，原栈顶元素淡出。

        Returns:
            被弹出的文字内容（字符串），栈空时返回 None。
        """
        if self.length <= 0:
            return None

        idx = self.length - 1
        target_box = self.boxes[idx]
        popped = self.texts[idx].text if hasattr(self.texts[idx], "text") else ""

        # 1) 高亮即将出栈元素
        self.play(target_box.animate.set_color(self.COLOR_POP), run_time=0.3)

        # 2) top 指针先下移
        self.move_top_pointer(self.length - 1)

        # 3) 元素淡出（向右滑动）
        ghost = self.texts[idx].copy()
        self.add(ghost)
        self.play(
            ghost.animate.next_to(target_box, RIGHT, buff=1.5).set_opacity(0.0),
            run_time=run_time,
        )
        self.remove(ghost)

        # 4) 清空槽位文字并恢复颜色
        empty_text = Text("", font_size=self.FONT_SIZE).move_to(target_box.get_center())
        self.remove(self.texts[idx])
        self.texts.remove(self.texts[idx])
        self.texts.insert(idx, empty_text)
        self.add(empty_text)
        self.play(target_box.animate.set_color(self.COLOR_EMPTY), run_time=0.3)
        return popped

    def peek_top(self, run_time=0.5):
        """取栈顶元素的"只读"动画：闪烁高亮 top-1 处，不改变栈状态。

        Returns:
            栈顶元素的文字内容（字符串），栈空时返回 None。
        """
        if self.length <= 0:
            return None

        idx = self.length - 1
        target_box = self.boxes[idx]
        val = self.texts[idx].text if hasattr(self.texts[idx], "text") else ""

        self.play(
            Indicate(target_box, color=self.COLOR_TOP, scale_factor=1.15),
            Indicate(self.texts[idx], color=self.COLOR_TOP, scale_factor=1.15),
            run_time=run_time,
        )
        return val

    # ------------------------------------------------------------------
    # 步骤文字（屏幕上方）
    # ------------------------------------------------------------------
    def show_step_text(self, text_str):
        if hasattr(self, "step_text") and self.step_text in self.mobjects:
            self.remove(self.step_text)
        self.step_text = Text(text_str, font_size=self.FONT_SIZE - 8).to_edge(UP, buff=0.3)
        self.play(FadeIn(self.step_text))

    def update_step_text(self, new_str):
        if not hasattr(self, "step_text"):
            self.show_step_text(new_str)
            return
        new_text = Text(new_str, font_size=self.FONT_SIZE - 8).to_edge(UP, buff=0.3)
        self.play(Transform(self.step_text, new_text))
