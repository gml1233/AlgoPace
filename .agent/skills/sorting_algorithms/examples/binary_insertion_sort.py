"""
折半插入排序 (Binary Insertion Sort) - Manim 动画模板

算法思想：
在直接插入排序基础上，用折半查找（二分查找）替代逐个比较，
快速定位待插入元素在有序区中的插入位置，再整体后移元素腾出空间。

时间复杂度：最好O(nlogn)，平均O(n²)，最坏O(n²)
空间复杂度：O(1)
稳定性：稳定
"""

from manim import *
import sys, os
sys.path.append(os.path.dirname(__file__))
from sorting_base import SortingBase


class BinaryInsertionSortScene(SortingBase):
    """折半插入排序动画"""

    def construct(self):
        data = [5, 3, 8, 1, 4]

        self.show_array(data, title="折半插入排序")
        self.wait(0.5)

        info = self.show_complexity_info("O(nlogn)", "O(n²)", "O(n²)", "O(1)", True)

        self.mark_sorted([0])
        step = self.show_step_text("a[0]已在有序区，从a[1]开始折半插入")
        self.wait(self.PHASE_PAUSE)

        n = len(self.array_data)
        for i in range(1, n):
            key = self.array_data[i]
            self.update_step_text(step, f"取出 a[{i}]={key}，折半查找插入位置")
            self.highlight(i, self.COLOR_KEY)
            self.wait(self.STEP_PAUSE)

            # 折半查找过程
            low, high = 0, i - 1

            while low <= high:
                mid = (low + high) // 2
                # 显示 low, mid, high 指针
                self.highlight(mid, self.COLOR_COMPARING, run_time=0.2)
                self.update_step_text(
                    step,
                    f"low={low}, mid={mid}, high={high}  |  a[mid]={self.array_data[mid]} vs {key}"
                )
                self.wait(0.3)

                if self.array_data[mid] > key:
                    self.update_step_text(step, f"a[mid]={self.array_data[mid]} > {key}，high=mid-1={mid - 1}")
                    high = mid - 1
                else:
                    self.update_step_text(step, f"a[mid]={self.array_data[mid]} ≤ {key}，low=mid+1={mid + 1}")
                    low = mid + 1

                self.reset_colors([mid])
                self.mark_sorted(list(range(i)))
                self.wait(0.2)

            # 插入位置为 low
            insert_pos = low
            self.update_step_text(step, f"插入位置={insert_pos}，后移a[{insert_pos}]~a[{i - 1}]")
            self.wait(0.3)

            # 整体后移
            for j in range(i, insert_pos, -1):
                self.array_data[j] = self.array_data[j - 1]
                pos_j = self.boxes[j].get_center()
                pos_prev = self.boxes[j - 1].get_center()
                self.play(
                    self.boxes[j - 1].animate.move_to(pos_j),
                    run_time=0.2
                )
                self.boxes[j - 1], self.boxes[j] = self.boxes[j], self.boxes[j - 1]

            # 插入
            self.array_data[insert_pos] = key
            new_num = Text(str(key), font_size=self.FONT_SIZE, color=WHITE)
            new_num.move_to(self.boxes[insert_pos][1].get_center())
            self.play(Transform(self.boxes[insert_pos][1], new_num), run_time=0.3)

            self.mark_sorted(list(range(i + 1)))
            self.wait(self.STEP_PAUSE)

        self.update_step_text(step, "排序完成！")
        self.show_final_result()
        self.wait(2)
