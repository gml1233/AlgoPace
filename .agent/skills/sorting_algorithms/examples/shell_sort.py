"""
希尔排序 (Shell Sort) - Manim 动画模板

算法思想：
将数组按增量d分组，对每组进行直接插入排序；
逐步缩小增量（通常每次减半），直到增量为1时执行最终插入排序。
本质是分组插入排序，通过预排序使数组趋于有序，减少最终排序的移动次数。

时间复杂度：最好O(n^1.3)，平均O(n^1.3)，最坏O(n²)
空间复杂度：O(1)
稳定性：不稳定
"""

from manim import *
import sys, os
sys.path.append(os.path.dirname(__file__))
from sorting_base import SortingBase


class ShellSortScene(SortingBase):
    """希尔排序动画"""

    # 分组颜色
    GROUP_COLORS = [RED, BLUE, GREEN, ORANGE, PURPLE, TEAL, PINK, GOLD]

    def construct(self):
        data = [8, 5, 3, 9, 1, 6, 2, 7, 4]

        self.show_array(data, title="希尔排序")
        self.wait(0.5)

        info = self.show_complexity_info("O(n^1.3)", "O(n^1.3)", "O(n²)", "O(1)", False)

        step = self.show_step_text("按增量d分组，对每组做插入排序")
        self.wait(self.PHASE_PAUSE)

        n = len(self.array_data)
        gap = n // 2  # 初始增量

        round_num = 1
        while gap > 0:
            self.update_step_text(step, f"第{round_num}轮：增量 d={gap}，共{gap}组")
            self.wait(0.5)

            # 用颜色标识不同分组
            for g in range(gap):
                color = self.GROUP_COLORS[g % len(self.GROUP_COLORS)]
                group_indices = list(range(g, n, gap))
                self.highlight(group_indices, color, run_time=0.3)

            self.wait(0.5)

            # 对每组进行插入排序
            for i in range(gap, n):
                key = self.array_data[i]
                j = i

                group_id = i % gap
                color = self.GROUP_COLORS[group_id % len(self.GROUP_COLORS)]

                self.highlight(i, self.COLOR_KEY, run_time=0.2)

                while j >= gap and self.array_data[j - gap] > key:
                    self.highlight(j - gap, self.COLOR_COMPARING, run_time=0.15)

                    # 后移
                    self.array_data[j] = self.array_data[j - gap]
                    pos_j = self.boxes[j].get_center()
                    pos_prev = self.boxes[j - gap].get_center()
                    self.play(
                        self.boxes[j - gap].animate.move_to(pos_j),
                        run_time=0.25
                    )
                    self.boxes[j - gap], self.boxes[j] = self.boxes[j], self.boxes[j - gap]
                    j -= gap

                self.array_data[j] = key
                new_num = Text(str(key), font_size=self.FONT_SIZE, color=WHITE)
                new_num.move_to(self.boxes[j][1].get_center())
                self.play(Transform(self.boxes[j][1], new_num), run_time=0.2)

            # 本轮结束，显示当前状态
            self.reset_colors()
            self.update_step_text(
                step,
                f"第{round_num}轮完成 (d={gap})：{self.array_data}"
            )
            self.wait(self.PHASE_PAUSE)

            gap //= 2
            round_num += 1

        self.update_step_text(step, "排序完成！")
        self.show_final_result()
        self.wait(2)
