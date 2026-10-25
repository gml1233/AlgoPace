"""
归并排序 (Merge Sort) - Manim 动画模板

算法思想：
采用分治思想：将数组递归拆分为两半，直到每部分仅含一个元素，
然后将两个有序子数组合并为一个有序的大数组，自底向上合并完成排序。

时间复杂度：最好O(nlogn)，平均O(nlogn)，最坏O(nlogn)
空间复杂度：O(n) 需要辅助数组
稳定性：稳定
"""

from manim import *
import sys, os
sys.path.append(os.path.dirname(__file__))
from sorting_base import SortingBase


class MergeSortScene(SortingBase):
    """归并排序动画"""

    # 不同递归深度的颜色
    DEPTH_COLORS = [BLUE, GREEN, ORANGE, PURPLE, RED, TEAL]

    def construct(self):
        data = [8, 3, 5, 1, 9, 2, 7, 4]

        self.show_array(data, title="归并排序")
        self.wait(0.5)

        info = self.show_complexity_info("O(nlogn)", "O(nlogn)", "O(nlogn)", "O(n)", True)

        self.step_text = self.show_step_text("分治法：先递归拆分，再合并有序子数组")
        self.wait(self.PHASE_PAUSE)

        # 执行归并排序
        self._merge_sort(0, len(self.array_data) - 1, depth=0)

        self.update_step_text(self.step_text, "排序完成！")
        self.show_final_result()
        self.wait(2)

    def _merge_sort(self, left, right, depth):
        """递归归并排序"""
        if left >= right:
            return

        mid = (left + right) // 2

        # 显示拆分
        color = self.DEPTH_COLORS[depth % len(self.DEPTH_COLORS)]
        self.update_step_text(
            self.step_text,
            f"拆分 [{left}~{right}] → [{left}~{mid}] + [{mid + 1}~{right}]"
        )

        # 标记左半部分
        for i in range(left, mid + 1):
            self.highlight(i, BLUE_C, run_time=0.1)
        # 标记右半部分
        for i in range(mid + 1, right + 1):
            self.highlight(i, ORANGE, run_time=0.1)
        self.wait(0.5)

        # 递归排序左半部分
        self._merge_sort(left, mid, depth + 1)
        # 递归排序右半部分
        self._merge_sort(mid + 1, right, depth + 1)

        # 合并
        self._merge(left, mid, right)

    def _merge(self, left, mid, right):
        """合并两个有序子数组"""
        self.update_step_text(
            self.step_text,
            f"合并 [{left}~{mid}] 和 [{mid + 1}~{right}]"
        )

        # 高亮合并范围
        for i in range(left, mid + 1):
            self.highlight(i, BLUE_C, run_time=0.08)
        for i in range(mid + 1, right + 1):
            self.highlight(i, ORANGE, run_time=0.08)
        self.wait(0.3)

        # 创建临时数组
        temp = []
        i, j = left, mid + 1

        while i <= mid and j <= right:
            # 比较两个子数组的当前元素
            self.highlight([i, j], self.COLOR_COMPARING, run_time=0.15)

            if self.array_data[i] <= self.array_data[j]:
                temp.append(self.array_data[i])
                self.highlight(i, self.COLOR_KEY, run_time=0.1)
                i += 1
            else:
                temp.append(self.array_data[j])
                self.highlight(j, self.COLOR_KEY, run_time=0.1)
                j += 1
            self.wait(0.15)

        # 剩余元素
        while i <= mid:
            temp.append(self.array_data[i])
            i += 1
        while j <= right:
            temp.append(self.array_data[j])
            j += 1

        # 将合并结果写回数组并更新显示
        for idx, val in enumerate(temp):
            actual_idx = left + idx
            self.array_data[actual_idx] = val

            new_num = Text(str(val), font_size=self.FONT_SIZE, color=WHITE)
            new_num.move_to(self.boxes[actual_idx][1].get_center())
            self.play(
                Transform(self.boxes[actual_idx][1], new_num),
                self.boxes[actual_idx][0].animate.set_color(self.COLOR_SORTED),
                run_time=0.2
            )

        self.update_step_text(
            self.step_text,
            f"合并结果 [{left}~{right}]：{self.array_data[left:right + 1]}"
        )
        self.wait(0.5)

        # 恢复默认颜色
        self.reset_colors(list(range(left, right + 1)))
