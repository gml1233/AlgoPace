"""
堆排序 (Heap Sort) - Manim 动画模板

算法思想：
1. 将数组构建为大顶堆（父节点 ≥ 子节点）
2. 将堆顶（最大值）与末尾元素交换，堆大小减1
3. 对堆顶重新调整（下沉），恢复堆性质
4. 重复步骤2-3，直到堆中只剩1个元素

时间复杂度：最好O(nlogn)，平均O(nlogn)，最坏O(nlogn)
空间复杂度：O(1)
稳定性：不稳定
"""

from manim import *
import sys, os
sys.path.append(os.path.dirname(__file__))
from sorting_base import SortingBase


class HeapSortScene(SortingBase):
    """堆排序动画"""

    def construct(self):
        data = [4, 6, 8, 5, 9, 1, 3]

        self.show_array(data, title="堆排序")
        self.wait(0.5)

        info = self.show_complexity_info("O(nlogn)", "O(nlogn)", "O(nlogn)", "O(1)", False)

        step = self.show_step_text("步骤1：建立大顶堆")
        self.wait(self.PHASE_PAUSE)

        n = len(self.array_data)

        # ========== 建堆过程 ==========
        # 从最后一个非叶子节点开始，向前调整
        for i in range(n // 2 - 1, -1, -1):
            self.update_step_text(step, f"调整节点 a[{i}]={self.array_data[i]}，使子树满足大顶堆")
            self._sift_down(i, n, step)

        self.update_step_text(step, f"大顶堆建立完成：{self.array_data}")
        self.wait(self.PHASE_PAUSE)

        # ========== 排序过程 ==========
        self.update_step_text(step, "步骤2：依次取出堆顶最大值")
        self.wait(0.5)

        for i in range(n - 1, 0, -1):
            # 堆顶元素与末尾交换
            self.update_step_text(
                step,
                f"堆顶 a[0]={self.array_data[0]} 与 a[{i}]={self.array_data[i]} 交换"
            )
            self.swap_elements(0, i)

            # 末尾元素就位
            self.mark_sorted([i])
            self.wait(0.3)

            # 对堆顶下沉调整
            self.update_step_text(step, f"调整堆顶 a[0]={self.array_data[0]}，恢复堆性质")
            self._sift_down(0, i, step)
            self.wait(self.STEP_PAUSE)

        # 第一个元素自动就位
        self.mark_sorted([0])

        self.update_step_text(step, "排序完成！")
        self.show_final_result()
        self.wait(2)

    def _sift_down(self, parent, heap_size, step):
        """下沉调整（维护大顶堆性质）"""
        while True:
            largest = parent
            left = 2 * parent + 1
            right = 2 * parent + 2

            # 高亮当前父节点
            self.highlight(parent, self.COLOR_PIVOT, run_time=0.15)

            # 比较左子节点
            if left < heap_size:
                self.highlight(left, self.COLOR_COMPARING, run_time=0.15)
                if self.array_data[left] > self.array_data[largest]:
                    largest = left

            # 比较右子节点
            if right < heap_size:
                self.highlight(right, self.COLOR_COMPARING, run_time=0.15)
                if self.array_data[right] > self.array_data[largest]:
                    largest = right

            self.wait(0.15)

            # 需要交换
            if largest != parent:
                self.update_step_text(
                    step,
                    f"a[{parent}]={self.array_data[parent]} < a[{largest}]={self.array_data[largest]}，下沉"
                )
                self.swap_elements(parent, largest)
                parent = largest
            else:
                # 恢复颜色
                to_reset = [idx for idx in [parent, left, right] if 0 <= idx < heap_size]
                self.reset_colors(to_reset)
                break
