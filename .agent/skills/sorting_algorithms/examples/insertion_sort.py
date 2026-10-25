"""
直接插入排序 (Insertion Sort) - Manim 动画模板

算法思想：
将数组分为已排序区和未排序区，每次从未排序区取出第一个元素，
在已排序区中从后向前逐个比较，找到合适位置插入。

时间复杂度：最好O(n)，平均O(n²)，最坏O(n²)
空间复杂度：O(1)
稳定性：稳定
"""

from manim import *
import sys, os
sys.path.append(os.path.dirname(__file__))
from sorting_base import SortingBase


class InsertionSortScene(SortingBase):
    """直接插入排序动画"""

    def construct(self):
        data = [5, 3, 8, 1, 4]

        # 显示标题和数组
        self.show_array(data, title="直接插入排序")
        self.wait(0.5)

        # 显示复杂度信息
        info = self.show_complexity_info("O(n)", "O(n²)", "O(n²)", "O(1)", True)

        # 第一个元素默认已排序
        self.mark_sorted([0])
        step = self.show_step_text("a[0]已在有序区，从a[1]开始插入")
        self.wait(self.PHASE_PAUSE)

        n = len(self.array_data)
        for i in range(1, n):
            # 取出待插入元素
            key = self.array_data[i]
            self.update_step_text(step, f"取出 a[{i}]={key}，在有序区中寻找插入位置")
            self.highlight(i, self.COLOR_KEY)
            self.wait(self.STEP_PAUSE)

            # 从后向前比较
            j = i - 1
            while j >= 0 and self.array_data[j] > key:
                self.highlight(j, self.COLOR_COMPARING, run_time=0.2)
                self.update_step_text(step, f"a[{j}]={self.array_data[j]} > {key}，后移")
                self.wait(0.2)

                # 元素后移
                self.array_data[j + 1] = self.array_data[j]
                target_pos = self.boxes[j + 1].get_center()
                old_pos = self.boxes[j].get_center()
                self.play(
                    self.boxes[j].animate.move_to(target_pos),
                    run_time=0.3
                )
                self.boxes[j], self.boxes[j + 1] = self.boxes[j + 1], self.boxes[j]
                j -= 1

            # 插入元素
            self.array_data[j + 1] = key
            insert_idx = j + 1
            self.update_step_text(step, f"插入{key}到位置a[{insert_idx}]")

            # 更新数字显示
            new_num = Text(str(key), font_size=self.FONT_SIZE, color=WHITE)
            new_num.move_to(self.boxes[insert_idx][1].get_center())
            self.play(
                Transform(self.boxes[insert_idx][1], new_num),
                run_time=0.3
            )

            # 标记已排序区
            self.mark_sorted(list(range(i + 1)))
            self.wait(self.STEP_PAUSE)

        # 显示最终结果
        self.update_step_text(step, "排序完成！")
        self.show_final_result()
        self.wait(2)
