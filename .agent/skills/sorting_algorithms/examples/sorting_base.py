"""
排序算法动画公共基类
提供统一的数组可视化、元素高亮、交换动画等公共方法
所有排序算法动画场景都应继承此基类
"""

from manim import *


class SortingBase(Scene):
    """排序算法动画基类"""

    # ========== 字幕安全区 ==========
    # 底部 y ∈ [-4.0, SUBTITLE_SAFE_TOP_Y] 被烧录字幕占用，禁止放置任何可见元素。
    # 对应 config.subtitle_safe_zone_units ≈ 0.67（约画面底部 8%）。
    SUBTITLE_SAFE_TOP_Y = -3.3

    # ========== 颜色规范 ==========
    COLOR_DEFAULT = BLUE           # 默认元素颜色
    COLOR_COMPARING = YELLOW       # 正在比较的元素
    COLOR_SWAPPING = RED           # 正在交换的元素
    COLOR_SORTED = GREEN           # 已排序/已就位的元素
    COLOR_PIVOT = PURPLE           # 枢轴/基准元素
    COLOR_GROUP = ORANGE           # 分组/子序列标识
    COLOR_KEY = TEAL               # 关键元素（如插入排序中的待插入元素）

    # ========== 布局参数 ==========
    BOX_SIZE = 0.8                 # 元素方块边长
    BOX_BUFF = 0.1                 # 元素间距
    FONT_SIZE = 32                 # 元素数字字号
    INDEX_FONT_SIZE = 20           # 索引标签字号
    TITLE_FONT_SIZE = 40           # 标题字号

    # ========== 代码分栏布局（左 30% 代码 + 右 70% 动画） ==========
    SCREEN_SPLIT_X = -2.84
    CODE_PANEL_CENTER_X = -4.97
    CODE_PANEL_MAX_WIDTH = 4.10
    CODE_PANEL_MAX_HEIGHT = 6.40
    ANIM_AREA_CENTER_X = 2.13

    # ========== 动画速度 ==========
    COMPARE_TIME = 0.4             # 比较动画时长
    SWAP_TIME = 0.6                # 交换动画时长
    STEP_PAUSE = 0.3               # 步骤间暂停时长
    PHASE_PAUSE = 1.0              # 阶段间暂停时长

    def setup(self):
        """场景初始化"""
        self.array_data = []       # 存储当前数组数据
        self.boxes = VGroup()      # 存储所有方块对象
        self.labels = VGroup()     # 存储索引标签
        self.title_mob = None      # 标题对象
        self._code_panel_active = False
        self.code_mob = None
        self._code_hl = None
        self.array_center = ORIGIN

    # ==================== 数组创建与显示 ====================

    def create_array(self, data, show_indices=True):
        """
        创建数组可视化

        Args:
            data: 数组数据列表，如 [5, 3, 8, 1, 9]
            show_indices: 是否显示索引标签

        Returns:
            VGroup: 包含所有方块的组
        """
        self.array_data = list(data)
        self.boxes = VGroup()
        self.labels = VGroup()

        for i, val in enumerate(self.array_data):
            # 创建方块
            box = Square(side_length=self.BOX_SIZE, color=self.COLOR_DEFAULT)
            # 创建数字文本
            num = Text(str(val), font_size=self.FONT_SIZE, color=WHITE)
            # 组合方块和数字
            element = VGroup(box, num)
            self.boxes.add(element)

            # 创建索引标签
            if show_indices:
                idx_label = Text(str(i), font_size=self.INDEX_FONT_SIZE, color=GREY)
                self.labels.add(idx_label)

        # 排列方块
        self.boxes.arrange(RIGHT, buff=self.BOX_BUFF)
        self.boxes.move_to(self.array_center)

        # 放置索引标签
        if show_indices:
            for i, label in enumerate(self.labels):
                label.next_to(self.boxes[i], DOWN, buff=0.2)

        return self.boxes

    def _shift_existing_content_to_right(self):
        animated_group = VGroup()
        if len(self.boxes) > 0:
            animated_group.add(self.boxes)
        if len(self.labels) > 0:
            animated_group.add(self.labels)
        if self.title_mob is not None:
            animated_group.add(self.title_mob)
        if len(animated_group) == 0:
            return

        current_center_x = self.boxes.get_center()[0] if len(self.boxes) > 0 else animated_group.get_center()[0]
        dx = self.ANIM_AREA_CENTER_X - current_center_x
        if abs(dx) < 1e-6:
            return
        self.play(animated_group.animate.shift(RIGHT * dx), run_time=0.35)

    def show_array(self, data, title="", show_indices=True):
        """创建并动画显示数组"""
        # 显示标题
        if title:
            self.title_mob = Text(title, font_size=self.TITLE_FONT_SIZE)
            self.title_mob.to_edge(UP, buff=0.5)
            self.play(Write(self.title_mob))

        # 创建数组
        self.create_array(data, show_indices)

        # 动画显示
        self.play(
            LaggedStart(
                *[FadeIn(box, shift=DOWN * 0.3) for box in self.boxes],
                lag_ratio=0.15
            ),
            run_time=1.0
        )

        if show_indices and self.labels:
            self.play(
                LaggedStart(
                    *[FadeIn(label) for label in self.labels],
                    lag_ratio=0.1
                ),
                run_time=0.5
            )

        self.wait(self.STEP_PAUSE)

    def show_array_instant(self, data, title=None, show_indices=True):
        """瞬时（无动画）显示数组与可选标题。

        用于视频开场（algorithm_intro）场景：将完整数组与标题直接 `self.add()`
        到画面上，使视频第一帧即为完整内容（适合作为缩略图）。
        不调用任何 `self.play(...)`。
        """
        if title:
            self.title_mob = Text(title, font_size=self.TITLE_FONT_SIZE)
            self.title_mob.to_edge(UP, buff=0.5)
            self.add(self.title_mob)

        self.create_array(data, show_indices)
        self.add(self.boxes)
        if show_indices and self.labels:
            self.add(self.labels)

    # ==================== 元素高亮 ====================

    def highlight(self, indices, color, run_time=None):
        """
        高亮指定索引的元素

        Args:
            indices: 索引或索引列表
            color: 高亮颜色
            run_time: 动画时长
        """
        if isinstance(indices, int):
            indices = [indices]
        rt = run_time or self.COMPARE_TIME

        animations = []
        for idx in indices:
            if 0 <= idx < len(self.boxes):
                animations.append(self.boxes[idx][0].animate.set_color(color))

        if animations:
            self.play(*animations, run_time=rt)

    def reset_colors(self, indices=None, color=None):
        """重置元素颜色为默认"""
        c = color or self.COLOR_DEFAULT
        if indices is None:
            indices = range(len(self.boxes))
        elif isinstance(indices, int):
            indices = [indices]

        animations = [
            self.boxes[i][0].animate.set_color(c)
            for i in indices if 0 <= i < len(self.boxes)
        ]
        if animations:
            self.play(*animations, run_time=0.2)

    # ==================== 交换动画 ====================

    def swap_elements(self, i, j, highlight_color=None):
        """
        交换两个元素（带动画）

        Args:
            i: 第一个元素索引
            j: 第二个元素索引
            highlight_color: 交换时的高亮颜色
        """
        if i == j:
            return

        color = highlight_color or self.COLOR_SWAPPING

        # 高亮待交换元素
        self.highlight([i, j], color, run_time=0.2)

        # 获取两个元素的位置
        pos_i = self.boxes[i].get_center()
        pos_j = self.boxes[j].get_center()

        # 弧线交换动画
        arc_angle = PI / 3  # 弧度
        self.play(
            self.boxes[i].animate.move_to(pos_j),
            self.boxes[j].animate.move_to(pos_i),
            run_time=self.SWAP_TIME
        )

        # 交换数据和对象引用
        self.array_data[i], self.array_data[j] = self.array_data[j], self.array_data[i]
        self.boxes[i], self.boxes[j] = self.boxes[j], self.boxes[i]

        # 恢复默认颜色
        self.highlight([i, j], self.COLOR_DEFAULT, run_time=0.2)

    # ==================== 元素移动 ====================

    def shift_element_right(self, idx):
        """将元素向右移动一个位置（用于插入排序）"""
        if idx + 1 < len(self.boxes):
            target_pos = self.boxes[idx + 1].get_center()
            self.play(
                self.boxes[idx].animate.move_to(target_pos),
                run_time=0.3
            )
            # 更新数据
            self.array_data[idx + 1] = self.array_data[idx]
            self.boxes[idx], self.boxes[idx + 1] = self.boxes[idx + 1], self.boxes[idx]

    def insert_element(self, from_pos, to_idx, value):
        """将一个元素插入到指定位置"""
        target_pos = self.boxes[to_idx].get_center()
        self.play(
            from_pos.animate.move_to(target_pos),
            run_time=0.4
        )
        self.array_data[to_idx] = value

    # ==================== 标注与说明 ====================

    def clip_to_safe_zone(self, mobj, margin=0.05):
        """确保 mobj 不进入底部字幕安全区（y ≤ SUBTITLE_SAFE_TOP_Y）。

        若底边低于安全区上沿，整体上移到安全位置；否则不动。
        返回 mobj 本身，便于链式调用。
        """
        bottom_y = mobj.get_bottom()[1]
        min_y = self.SUBTITLE_SAFE_TOP_Y + margin
        if bottom_y < min_y:
            mobj.shift(UP * (min_y - bottom_y))
        return mobj

    def show_step_text(self, text, position=DOWN * 2.0, font_size=28):
        """显示步骤说明文字（默认位置位于注释区，避开底部字幕安全带）"""
        step_text = Text(text, font_size=font_size, color=WHITE)
        step_text.move_to(position)
        self.clip_to_safe_zone(step_text)
        self.play(FadeIn(step_text), run_time=0.3)
        return step_text

    def update_step_text(self, old_text, new_text_str, font_size=28):
        """更新步骤说明文字"""
        new_text = Text(new_text_str, font_size=font_size, color=WHITE)
        new_text.move_to(old_text.get_center())
        self.clip_to_safe_zone(new_text)
        self.play(Transform(old_text, new_text), run_time=0.3)
        return old_text

    def show_pointer(self, idx, text="", color=RED, direction=UP):
        """在元素上方或下方显示指示箭头"""
        arrow = Arrow(
            start=direction * 0.8,
            end=ORIGIN,
            color=color,
            buff=0.1
        )
        arrow.next_to(self.boxes[idx], direction, buff=0.15)

        group = VGroup(arrow)
        if text:
            label = Text(text, font_size=self.INDEX_FONT_SIZE, color=color)
            label.next_to(arrow, direction, buff=0.1)
            group.add(label)

        self.play(FadeIn(group), run_time=0.3)
        return group

    def show_code_panel(self, code_str: str, anchor=None):
        anchor = anchor if anchor is not None else np.array([self.CODE_PANEL_CENTER_X, 0.0, 0.0])
        code = Code(
            code_string=code_str,
            language="cpp",
            background="rectangle",
            add_line_numbers=True,
            tab_width=4,
        )
        code.move_to(anchor)
        while code.width > self.CODE_PANEL_MAX_WIDTH or code.height > self.CODE_PANEL_MAX_HEIGHT:
            code.scale(0.9)
            code.move_to(anchor)
        self.clip_to_safe_zone(code)
        self.play(FadeIn(code), run_time=0.3)
        self.code_mob = code

        if not self._code_panel_active:
            self._code_panel_active = True
            self.array_center = np.array([self.ANIM_AREA_CENTER_X, 0.0, 0.0])
            self._shift_existing_content_to_right()
            if self.title_mob is not None:
                self.play(self.title_mob.animate.move_to(np.array([self.ANIM_AREA_CENTER_X, 3.45, 0])), run_time=0.2)
        return code

    def highlight_code_line(self, line_no: int):
        if self.code_mob is None:
            return
        try:
            line = self.code_mob.code_lines[line_no - 1]
        except (IndexError, AttributeError):
            return
        rect = SurroundingRectangle(line, color=self.COLOR_COMPARING, buff=0.04, stroke_width=2)
        if self._code_hl is not None:
            self.play(Transform(self._code_hl, rect), run_time=0.2)
        else:
            self._code_hl = rect
            self.play(Create(rect), run_time=0.25)

    def remove_pointer(self, pointer):
        """移除指示箭头"""
        self.play(FadeOut(pointer), run_time=0.2)

    # ==================== 阶段和结束 ====================

    def mark_sorted(self, indices):
        """标记元素为已排序状态（绿色）"""
        if isinstance(indices, int):
            indices = [indices]
        self.highlight(indices, self.COLOR_SORTED, run_time=0.3)

    def show_final_result(self):
        """显示最终排序结果（全部变绿）"""
        self.mark_sorted(list(range(len(self.boxes))))
        self.wait(self.PHASE_PAUSE)

    def show_complexity_info(self, time_best, time_avg, time_worst, space, stable):
        """显示算法复杂度信息（放置在右上角，避开底部字幕安全带）"""
        info = VGroup(
            Text(f"最好时间：{time_best}", font_size=22),
            Text(f"平均时间：{time_avg}", font_size=22),
            Text(f"最坏时间：{time_worst}", font_size=22),
            Text(f"空间复杂度：{space}", font_size=22),
            Text(f"稳定性：{'稳定' if stable else '不稳定'}", font_size=22),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        info.to_corner(UR, buff=0.5)
        self.play(FadeIn(info), run_time=0.5)
        return info
