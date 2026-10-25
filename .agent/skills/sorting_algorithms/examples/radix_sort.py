"""
基数排序 (Radix Sort) - Manim 动画模板

算法思想：
将整数按位数（个位→十位→百位）切割，对每个位数进行计数排序（桶分配+收集）。
从最低位开始，逐位排序，直到最高位处理完毕，数组即有序。
本质是多关键字排序，利用了计数排序的稳定性保证正确性。

时间复杂度：O(d·n)，d为最大位数
空间复杂度：O(n) 需要桶空间
稳定性：稳定
"""

from manim import *
import sys, os
sys.path.append(os.path.dirname(__file__))
from sorting_base import SortingBase


class RadixSortScene(SortingBase):
    """基数排序动画"""

    BUCKET_COLORS = [
        RED, ORANGE, YELLOW, GREEN, TEAL,
        BLUE, PURPLE, PINK, GOLD, MAROON
    ]

    def construct(self):
        data = [170, 45, 75, 90, 802, 24, 2, 66]

        # 基数排序需要更小的元素
        self.BOX_SIZE = 0.7
        self.FONT_SIZE = 24

        self.show_array(data, title="基数排序")
        self.wait(0.5)

        step = self.show_step_text("按位分配收集：个位→十位→百位")
        self.wait(self.PHASE_PAUSE)

        # 找到最大位数
        max_val = max(self.array_data)
        max_digits = len(str(max_val))

        exp = 1  # 位权值：1=个位, 10=十位, 100=百位
        digit_names = ["个位", "十位", "百位", "千位"]

        for d in range(max_digits):
            digit_name = digit_names[d] if d < len(digit_names) else f"第{d + 1}位"

            self.update_step_text(step, f"第{d + 1}轮：按{digit_name}分配到桶")
            self.wait(0.5)

            # ========== 分配阶段 ==========
            # 创建 0-9 号桶的标签
            buckets_label = VGroup()
            for b in range(10):
                label = Text(f"桶{b}", font_size=18, color=self.BUCKET_COLORS[b])
                buckets_label.add(label)
            buckets_label.arrange(RIGHT, buff=0.5)
            buckets_label.next_to(self.boxes, DOWN, buff=1.0)
            self.clip_to_safe_zone(buckets_label)
            self.play(FadeIn(buckets_label), run_time=0.3)

            # 将元素按当前位数分配到桶
            buckets = [[] for _ in range(10)]
            for i, val in enumerate(self.array_data):
                digit = (val // exp) % 10
                buckets[digit].append(val)

                # 高亮当前元素，显示其当前位的值
                self.highlight(i, self.BUCKET_COLORS[digit], run_time=0.15)
                self.update_step_text(
                    step,
                    f"{val} 的{digit_name}={digit} → 放入桶{digit}"
                )
                self.wait(0.2)

            self.wait(0.5)

            # ========== 收集阶段 ==========
            self.update_step_text(step, f"从桶0到桶9依次收集")
            self.wait(0.3)

            # 从桶中按顺序收集
            sorted_data = []
            for b in range(10):
                for val in buckets[b]:
                    sorted_data.append(val)

            # 更新数组显示
            for idx, val in enumerate(sorted_data):
                self.array_data[idx] = val
                new_num = Text(str(val), font_size=self.FONT_SIZE, color=WHITE)
                new_num.move_to(self.boxes[idx][1].get_center())
                self.play(
                    Transform(self.boxes[idx][1], new_num),
                    run_time=0.15
                )

            # 恢复颜色
            self.reset_colors()

            # 移除桶标签
            self.play(FadeOut(buckets_label), run_time=0.3)

            self.update_step_text(
                step,
                f"第{d + 1}轮({digit_name})结果：{self.array_data}"
            )
            self.wait(self.PHASE_PAUSE)

            exp *= 10

        self.update_step_text(step, "排序完成！")
        self.show_final_result()
        self.wait(2)
