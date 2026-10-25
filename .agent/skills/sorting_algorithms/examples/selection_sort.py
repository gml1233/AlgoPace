"""
简单选择排序 (Selection Sort) - Manim 动画模板

算法思想：
每一轮从未排序区中选出最小元素，与未排序区的第一个元素交换。
经过n-1轮后，数组有序。

时间复杂度：最好O(n²)，平均O(n²)，最坏O(n²)
空间复杂度：O(1)
稳定性：不稳定
"""

from manim import *
import sys, os
sys.path.append(os.path.dirname(__file__))
from sorting_base import SortingBase


class SelectionSortScene(SortingBase):
    """简单选择排序动画"""

    def construct(self):
        data = [5, 3, 8, 1, 4]

        self.show_array(data, title="简单选择排序")
        self.wait(0.5)

        info = self.show_complexity_info("O(n²)", "O(n²)", "O(n²)", "O(1)", False)

        step = self.show_step_text("每轮从未排序区选最小值，放到已排序区末尾")
        self.wait(self.PHASE_PAUSE)

        n = len(self.array_data)

        for i in range(n - 1):
            self.update_step_text(step, f"第{i + 1}轮：在a[{i}]~a[{n - 1}]中选最小值")
            self.wait(0.3)

            # 假设当前位置为最小值
            min_idx = i
            self.highlight(min_idx, self.COLOR_KEY, run_time=0.2)
            self.update_step_text(
                step,
                f"假设 a[{min_idx}]={self.array_data[min_idx]} 为最小值"
            )
            self.wait(0.3)

            # 遍历未排序区，寻找真正的最小值
            for j in range(i + 1, n):
                self.highlight(j, self.COLOR_COMPARING, run_time=0.15)
                self.update_step_text(
                    step,
                    f"比较 a[{j}]={self.array_data[j]} vs 当前最小值 a[{min_idx}]={self.array_data[min_idx]}"
                )
                self.wait(0.2)

                if self.array_data[j] < self.array_data[min_idx]:
                    # 发现更小值，更新标记
                    self.reset_colors([min_idx])
                    min_idx = j
                    self.highlight(min_idx, self.COLOR_KEY, run_time=0.15)
                    self.update_step_text(
                        step,
                        f"更新最小值为 a[{min_idx}]={self.array_data[min_idx]}"
                    )
                else:
                    self.reset_colors([j])

                self.wait(0.1)

            # 将最小值与当前位置交换
            if min_idx != i:
                self.update_step_text(
                    step,
                    f"交换 a[{i}]={self.array_data[i]} 和 a[{min_idx}]={self.array_data[min_idx]}"
                )
                self.swap_elements(i, min_idx)
            else:
                self.update_step_text(step, f"a[{i}]已是最小值，无需交换")
                self.wait(0.3)

            # 标记已排序
            self.mark_sorted([i])
            self.wait(self.STEP_PAUSE)

        # 最后一个元素自动就位
        self.mark_sorted([n - 1])

        self.update_step_text(step, "排序完成！")
        self.show_final_result()
        self.wait(2)
