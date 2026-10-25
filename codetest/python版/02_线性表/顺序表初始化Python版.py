# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService


class LinkedListBase(VoiceoverScene):
    """动画公共基类，提供高复用的基础组件配置"""
    pass


class ContinuousSeqListInitPythonVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角全局图片 Logo（紧靠右上角且放大一倍，伴随顶部微调）
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(
            UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE & INTRO =====
        algo_title = Text("顺序表的初始化（Python版）", font_size=38, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.5).shift(LEFT * 0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        # 【核心规范】总领句严格置于视频最开头，确立核心概念
        with self.voiceover(text="本节学习顺序表的初始化算法 Python 版。") as tracker:
            self.wait(tracker.duration)
        with self.voiceover(text="该算法用于在 Python 中构造一个空的顺序表对象。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== PHASE B — VIVID ANALOGY (停车场生活实例部分) =====
        # =========================================================================
        with self.voiceover(text="在学习代码前，我们先看一个生活实例：建设停车场。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(
                text="根据预知需要的最大车容量，先划定一排连续的固定数量的停车位。") as tracker:
            # 1. 创建一排连续的停车位（模拟顺序表在物理内存中分配的连续空间 max_size）
            spaces = VGroup(*[Rectangle(width=1.2, height=1.8, color=BLUE, fill_color=BLUE, fill_opacity=0.1) for _ in
                              range(5)]).arrange(RIGHT, buff=0.05)
            spaces.move_to(DOWN * 0.2)

            # 为车位添加编号（P1, P2...）
            space_nums = VGroup(*[Text(f"P{i + 1}", font_size=24, font="Arial", color=WHITE) for i in range(5)])
            for space, num in zip(spaces, space_nums):
                num.move_to(space.get_center())

            lot_group = VGroup(spaces, space_nums)

            # 显示最大容量标签
            maxsize_label = VGroup(
                Text("规划最大车位 (", font_size=20, font="Microsoft YaHei", color=ORANGE),
                Text("max_size", font_size=20, font="Arial", color=ORANGE),
                Text(") = 5", font_size=20, font="Microsoft YaHei", color=ORANGE)
            ).arrange(RIGHT, buff=0.05).next_to(lot_group, UP, buff=0.4)

            self.play(FadeIn(lot_group, shift=UP * 0.2), Write(maxsize_label), run_time=tracker.duration)

        with self.voiceover(
                text="而在停车场刚建好、准备投入使用时，里面一辆车也没有。这就好比顺序表刚初始化时，虽然有了空间，但内部还没有存入有效数据元素，其当前长度为 0。") as tracker:
            # 2. 显示当前车辆数为 0（模拟顺序表的初始化 length = 0）
            length_label = VGroup(
                Text("当前停放车辆 (", font_size=20, font="Microsoft YaHei", color=GREEN),
                Text("length", font_size=20, font="Arial", color=GREEN),
                Text(") = 0", font_size=20, font="Microsoft YaHei", color=GREEN)
            ).arrange(RIGHT, buff=0.05).next_to(lot_group, DOWN, buff=0.4)

            # 高亮展示一下空空如也的车位
            empty_flash = SurroundingRectangle(spaces, color=GREEN, buff=0.1)

            self.play(Write(length_label), run_time=tracker.duration * 0.4)
            self.play(Create(empty_flash), run_time=tracker.duration * 0.3)
            self.play(FadeOut(empty_flash), run_time=tracker.duration * 0.3)

        with self.voiceover(text="一次性开辟连续空间，并将初始有效长度置为零，这就是顺序表初始化的物理本质。") as tracker:
            self.wait(tracker.duration)

        # 优雅淡出，清理全部资产，为后续正式的算法演示和代码块留出空白画面
        self.play(
            FadeOut(lot_group),
            FadeOut(maxsize_label),
            FadeOut(length_label),
            run_time=1.0
        )
        self.wait(0.5)

        # =========================================================================
        # ===== PHASE C — CODE BLOCK CONFIG (算法代码排版部分) =====
        # =========================================================================
        c_lines = [
            "max_size = 100",
            "class SqList:",
            "    def __init__(self):",
            "        self.elem = [None] * max_size  # 为顺序表分配一个大小为max_size的数组空间",
            "        self.length = 0  # 空表长度为0",
            'if __name__ == "__main__":',
            "    l = SqList()",
            '    print("OK")'
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            # 采用 Microsoft YaHei 彻底杜绝中文注释变成白色方块
            t = Text(stripped_line, font_size=11, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        SPACE_WIDTH = 0.095
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        buff_val = 0.25
        radius_val = 0.2

        code_bg = RoundedRectangle(
            corner_radius=radius_val,
            height=code_group.get_height() + 2 * buff_val,
            width=code_group.get_width() + 2 * buff_val,
            color=GRAY,
            fill_opacity=0.1,
            stroke_width=1
        )
        code_bg.move_to(code_group)

        # 长代码块紧贴右侧边缘排布，防遮挡
        code_block = VGroup(code_bg, code_group).to_edge(RIGHT, buff=0.25).shift(UP * 0.1)

        self.current_line = None

        def get_track_anims(new_idx):
            # 防御机制：阻止因重复调用的无限叠加放大变形
            if new_idx == self.current_line:
                return []

            anims = []
            if self.current_line is not None:
                old_idx = self.current_line
                anims.append(self.c_texts[old_idx].animate.set_color(WHITE).scale(1 / 1.2, about_edge=LEFT))

            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW).scale(1.2, about_edge=LEFT))

                if not hasattr(self, 'code_pointer'):
                    self.code_pointer = Triangle(fill_opacity=1, color=YELLOW).scale(0.15).rotate(-PI / 2)
                    self.code_pointer.next_to(self.c_texts[new_idx], LEFT, buff=0.2)
                    anims.append(FadeIn(self.code_pointer))
                else:
                    self.code_pointer.generate_target()
                    self.code_pointer.target.next_to(self.c_texts[new_idx], LEFT, buff=0.2)
                    anims.append(MoveToTarget(self.code_pointer))

                self.current_line = new_idx
            else:
                if hasattr(self, 'code_pointer'):
                    anims.append(FadeOut(self.code_pointer))
                    delattr(self, 'code_pointer')
                self.current_line = None

            return anims

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW (顺序表初始化物理演练) =====
        # =========================================================================
        with self.voiceover(text="现在，我们来看该算法的 Python 代码实现。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        with self.voiceover(text="主程序创建 SqList 类的实例对象 l，调用构造方法进行初始化。") as tracker:
            self.play(*get_track_anims(6), run_time=1.0)
            self.wait(max(0.1, tracker.duration - 1.0))

        # 1. 执行数组空间开辟
        with self.voiceover(text="进入构造方法。首先，为顺序表分配一个大小为 max_size 的列表空间，初始每个位置均为 None。") as tracker:
            self.play(*get_track_anims(3), run_time=1.0)

            # 创建连续的空蓝色内存格子（未放入有效数据，不写任何数值，体现空表本质）
            mem_boxes = VGroup(*[Square(side_length=0.8, color=BLUE) for _ in range(5)]).arrange(RIGHT, buff=0)
            mem_boxes.move_to(LEFT * 3.2 + UP * 0.5)

            # 与 C++ 版本保持一致，同时标出从1开始的位置和从0开始的列表下标
            position_marks = VGroup(
                *[Text(str(index + 1), font_size=18, color=ORANGE, font="Arial") for index in range(5)])
            for box, mark in zip(mem_boxes, position_marks):
                mark.next_to(box, UP, buff=0.12)

            index_marks = VGroup(
                *[Text(str(index), font_size=18, color=TEAL_A, font="Arial") for index in range(5)])
            for box, mark in zip(mem_boxes, index_marks):
                mark.next_to(box, DOWN, buff=0.12)

            position_label = Text("位置", font_size=20, color=ORANGE, font="Microsoft YaHei").next_to(
                position_marks, LEFT, buff=0.3)
            index_label = Text("下标", font_size=20, color=TEAL_A, font="Microsoft YaHei").next_to(
                index_marks, LEFT, buff=0.3)
            annotations = VGroup(position_label, position_marks, index_label, index_marks)

            # 将列表引用放在左侧，避免与下方的下标标注重叠
            elem_arrow = Arrow(LEFT, RIGHT, buff=0.05, tip_length=0.15).scale(0.3).next_to(
                mem_boxes[0], LEFT, buff=0.35)
            elem_arrow.set_color(ORANGE)
            elem_text = Text("self.elem", font_size=16, color=ORANGE, font="Arial").next_to(
                elem_arrow, LEFT, buff=0.02)
            elem_pointer = VGroup(elem_arrow, elem_text)

            maxsize_label = VGroup(
                Text("分配空间：", font_size=18, font="Microsoft YaHei", color=GRAY_A),
                Text("max_size = 5", font_size=18, font="Arial", color=GRAY_A)
            ).arrange(RIGHT, buff=0.1).next_to(position_marks, UP, buff=0.3).align_to(mem_boxes, LEFT)

            self.play(Create(mem_boxes), FadeIn(annotations), FadeIn(elem_pointer), FadeIn(maxsize_label),
                       run_time=max(0.2, tracker.duration - 1.0))
        self.wait(0.2)

        # 2. 初始化长度
        res_panel = VGroup(
            Text("当前状态：", font_size=24, font="Microsoft YaHei", color=GREEN),
            Text("self.length = 0", font_size=22, font="Consolas", color=GREEN)
        ).arrange(RIGHT, buff=0.15).move_to(LEFT * 3.2 + DOWN * 1.5)

        with self.voiceover(
                text="随后，将顺序表的当前长度 self.length 置为 0，代表目前表内还没有存入任何有效的数据元素。") as tracker:
            # 转移并高亮放大长度置零语句行
            self.play(*get_track_anims(4), Write(res_panel), run_time=tracker.duration)
        self.wait(0.2)

        # 3. 成功返回/输出
        with self.voiceover(text="顺序表初始化完成，主程序输出 OK。一个崭新的空顺序表对象就此在内存中构建完毕。") as tracker:
            self.play(*get_track_anims(7), run_time=tracker.duration)

        # 退出高亮状态并隐去部分辅助资产
        self.play(*get_track_anims(None), FadeOut(elem_pointer), run_time=0.5)

        # =========================================================================
        # ===== PHASE E — COMPLEXITY ANALYSIS (时空复杂度分段双重对齐分析) =====
        # =========================================================================
        time_box = VGroup(Text("时间复杂度：", font_size=24, font="Microsoft YaHei", color=YELLOW),
                          Text("O(1)", font_size=24, font="Consolas", color=YELLOW)).arrange(RIGHT, buff=0.1)
        space_box = VGroup(Text("空间复杂度：", font_size=24, font="Microsoft YaHei", color=YELLOW),
                           Text("O(1)", font_size=24, font="Consolas", color=YELLOW)).arrange(RIGHT, buff=0.1)

        complexity_panel = VGroup(time_box, space_box).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(res_panel,
                                                                                                            DOWN,
                                                                                                            buff=0.4).align_to(
            res_panel, LEFT)

        # 第一句：单独讲解时间复杂度，音频与字幕严格字字对齐
        with self.voiceover(
                text="由于分配固定大小的存储空间以及变量赋值操作均为常数级，因此初始化算法的时间复杂度为 O(1)。",
                subcaption="由于分配固定大小的存储空间以及变量赋值操作均为常数级，因此初始化算法的时间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        # 第二句：单独讲解空间复杂度，音频与字幕严格字字对齐
        with self.voiceover(
                text="整个初始化过程在运行期间仅占用常数个控制引用与辅助变量，因此其辅助空间复杂度同样为 O(1)。",
                subcaption="整个初始化过程在运行期间仅占用常数个控制引用与辅助变量，因此其辅助空间复杂度同样为 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        # 第三句：收尾总结
        with self.voiceover(
                text="这就是顺序表初始化算法 Python 版的完整演示过程。",
                subcaption="这就是顺序表初始化算法 Python 版的完整演示过程。"
        ) as tracker:
            self.wait(tracker.duration)

        self.wait(2)


# 兼容类名
class SeqListInitPythonVideo(ContinuousSeqListInitPythonVideo):
    pass
