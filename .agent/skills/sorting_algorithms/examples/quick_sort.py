"""
快速排序 (Quick Sort) - Manim 动画模板

算法思想：
选择一个基准元素（pivot），将数组分为两部分：
左边全部≤pivot，右边全部≥pivot，对两部分递归排序。
分区过程使用双指针（左右扫描交换法）。

时间复杂度：最好O(nlogn)，平均O(nlogn)，最坏O(n²)
空间复杂度：O(logn) 递归栈空间
稳定性：不稳定
"""

from manim import *
import sys, os
sys.path.append(os.path.dirname(__file__))
from sorting_base import SortingBase


class QuickSortScene(SortingBase):
    """快速排序动画"""

    def construct(self):
        data = [5, 3, 8, 1, 9, 2, 7, 4, 6]

        self.show_array(data, title="快速排序")
        self.wait(0.5)

        info = self.show_complexity_info("O(nlogn)", "O(nlogn)", "O(n²)", "O(logn)", False)

        self.step_text = self.show_step_text("选基准，分区，递归排序")
        self.wait(self.PHASE_PAUSE)

        # 执行快速排序
        self._quick_sort(0, len(self.array_data) - 1, depth=0)

        self.update_step_text(self.step_text, "排序完成！")
        self.show_final_result()
        self.wait(2)

    def _quick_sort(self, low, high, depth):
        """递归快速排序"""
        if low >= high:
            if 0 <= low < len(self.boxes):
                self.mark_sorted([low])
            return

        self.update_step_text(
            self.step_text,
            f"分区 [{low}~{high}]，选 a[{low}]={self.array_data[low]} 为基准"
        )

        # 高亮当前处理范围
        for k in range(low, high + 1):
            self.highlight(k, BLUE_B, run_time=0.1)

        # 高亮基准元素
        self.highlight(low, self.COLOR_PIVOT, run_time=0.3)
        self.wait(0.3)

        # 分区过程
        pivot_idx = self._partition(low, high)

        # 基准元素就位
        self.mark_sorted([pivot_idx])
        self.update_step_text(
            self.step_text,
            f"基准 {self.array_data[pivot_idx]} 就位于 a[{pivot_idx}]"
        )
        self.wait(0.5)

        # 递归排序左半部分
        self._quick_sort(low, pivot_idx - 1, depth + 1)
        # 递归排序右半部分
        self._quick_sort(pivot_idx + 1, high, depth + 1)

    def _partition(self, low, high):
        """分区操作（Lomuto分区法）"""
        pivot = self.array_data[low]
        i = low
        j = high

        while i < j:
            # 右指针左移，找到小于pivot的元素
            while i < j and self.array_data[j] >= pivot:
                self.highlight(j, self.COLOR_COMPARING, run_time=0.15)
                self.wait(0.1)
                self.reset_colors([j])
                j -= 1

            if i < j:
                self.update_step_text(
                    self.step_text,
                    f"右侧找到 a[{j}]={self.array_data[j]} < {pivot}，移到左边"
                )
                self.highlight(j, self.COLOR_SWAPPING, run_time=0.15)
                # 将 j 的值放到 i 的位置
                self.array_data[i] = self.array_data[j]
                new_num = Text(str(self.array_data[j]), font_size=self.FONT_SIZE, color=WHITE)
                new_num.move_to(self.boxes[i][1].get_center())
                self.play(Transform(self.boxes[i][1], new_num), run_time=0.3)

            # 左指针右移，找到大于pivot的元素
            while i < j and self.array_data[i] <= pivot:
                self.highlight(i, self.COLOR_COMPARING, run_time=0.15)
                self.wait(0.1)
                self.reset_colors([i])
                i += 1

            if i < j:
                self.update_step_text(
                    self.step_text,
                    f"左侧找到 a[{i}]={self.array_data[i]} > {pivot}，移到右边"
                )
                self.highlight(i, self.COLOR_SWAPPING, run_time=0.15)
                self.array_data[j] = self.array_data[i]
                new_num = Text(str(self.array_data[i]), font_size=self.FONT_SIZE, color=WHITE)
                new_num.move_to(self.boxes[j][1].get_center())
                self.play(Transform(self.boxes[j][1], new_num), run_time=0.3)
                j -= 1

        # 基准归位
        self.array_data[i] = pivot
        new_num = Text(str(pivot), font_size=self.FONT_SIZE, color=WHITE)
        new_num.move_to(self.boxes[i][1].get_center())
        self.play(Transform(self.boxes[i][1], new_num), run_time=0.3)

        return i
