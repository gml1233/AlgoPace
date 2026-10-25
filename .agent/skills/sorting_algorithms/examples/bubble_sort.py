"""
冒泡排序 (Bubble Sort) - Manim 动画模板

算法思想：
从头到尾依次比较相邻两个元素，如果前者大于后者则交换，
一轮遍历后最大元素"冒泡"到末尾。重复n-1轮完成排序。
可设置标志位优化：若某轮无交换则提前结束。

时间复杂度：最好O(n)，平均O(n²)，最坏O(n²)
空间复杂度：O(1)
稳定性：稳定
"""

from manim import *
import sys, os
sys.path.append(os.path.dirname(__file__))
from sorting_base import SortingBase


class BubbleSortScene(SortingBase):
    """冒泡排序动画"""

    def construct(self):
        data = [5, 3, 8, 1, 4]

        self.show_array(data, title="冒泡排序")
        self.wait(0.5)

        info = self.show_complexity_info("O(n)", "O(n²)", "O(n²)", "O(1)", True)

        step = self.show_step_text("相邻元素两两比较，大的后移（冒泡）")
        self.wait(self.PHASE_PAUSE)

        n = len(self.array_data)

        for i in range(n - 1):
            self.update_step_text(step, f"第{i + 1}轮：将最大值冒泡到a[{n - 1 - i}]")
            self.wait(0.3)

            swapped = False

            for j in range(n - 1 - i):
                # 高亮比较的两个元素
                self.highlight([j, j + 1], self.COLOR_COMPARING, run_time=0.2)
                self.update_step_text(
                    step,
                    f"比较 a[{j}]={self.array_data[j]} 和 a[{j + 1}]={self.array_data[j + 1]}"
                )
                self.wait(0.2)

                if self.array_data[j] > self.array_data[j + 1]:
                    # 需要交换
                    self.update_step_text(
                        step,
                        f"{self.array_data[j]} > {self.array_data[j + 1]}，交换"
                    )
                    self.swap_elements(j, j + 1)
                    swapped = True
                else:
                    self.update_step_text(
                        step,
                        f"{self.array_data[j]} ≤ {self.array_data[j + 1]}，不交换"
                    )
                    self.reset_colors([j, j + 1])
                    self.wait(0.2)

            # 本轮最大值已就位
            self.mark_sorted([n - 1 - i])
            self.wait(self.STEP_PAUSE)

            # 优化：无交换则提前结束
            if not swapped:
                self.update_step_text(step, f"第{i + 1}轮无交换，排序提前完成！")
                break

        self.update_step_text(step, "排序完成！")
        self.show_final_result()
        self.wait(2)
