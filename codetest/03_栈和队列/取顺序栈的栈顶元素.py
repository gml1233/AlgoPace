# coding=utf-8
from manim import *
import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService

class SeqStackGetTopVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        # 右上角 Logo
        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("取顺序栈的栈顶元素", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(text="本节学习取顺序栈栈顶元素的算法。该操作仅读取栈顶的值，而不修改栈内的元素分布和指针位置。") as tracker:
            self.wait(tracker.duration)

        # =========================================================================
        # ===== PHASE B — CODE BLOCK CONFIG =====
        # =========================================================================
        c_lines = [
            "Status GetTop(SqStack S)",
            "{",
            "    if (S.top != S.base)",
            "        return *(S.top - 1);",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=11.5, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        SPACE_WIDTH = 0.095
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        bg_width = code_group.get_width() * 1.2 + 0.8
        bg_height = code_group.get_height() + 0.6
        code_bg = RoundedRectangle(corner_radius=0.2, height=bg_height, width=bg_width, color=GRAY, fill_opacity=0.1, stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.4)
        code_bg.match_y(code_group)
        
        code_block = VGroup(code_bg, code_group).to_edge(RIGHT, buff=0.4).shift(UP * 0.4)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line: return []
            anims = []
            if self.current_line is not None:
                anims.append(self.c_texts[self.current_line].animate.set_color(WHITE).scale(1 / 1.2, about_edge=LEFT))
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

        with self.voiceover(text="右侧是该操作的代码实现。我们来观察它是如何执行的。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # =========================================================================
        # ===== PHASE C — VISUALIZATION SETUP =====
        # =========================================================================
        def build_seq_stack_boxes(max_size=3):
            return VGroup(*[Square(side_length=0.8, color=BLUE) for _ in range(max_size)]).arrange(UP, buff=0)

        def get_ptr(label, target_mobj, color=GREEN, direction=UP):
            if np.array_equal(direction, UP):
                arrow = Arrow(start=target_mobj.get_top() + UP * 0.8, end=target_mobj.get_top(), buff=0.1, color=color)
                txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, UP, buff=0.1)
            elif np.array_equal(direction, DOWN):
                arrow = Arrow(start=target_mobj.get_bottom() + DOWN * 0.8, end=target_mobj.get_bottom(), buff=0.1, color=color)
                txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, DOWN, buff=0.1)
            elif np.array_equal(direction, LEFT):
                arrow = Arrow(start=target_mobj.get_left() + LEFT * 0.8, end=target_mobj.get_left(), buff=0.1, color=color)
                txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, LEFT, buff=0.1)
            else: # RIGHT
                arrow = Arrow(start=target_mobj.get_right() + RIGHT * 0.8, end=target_mobj.get_right(), buff=0.1, color=color)
                txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, RIGHT, buff=0.1)
            return VGroup(arrow, txt)

        # =========================================================================
        # ===== PHASE D — ANIMATION FLOW =====
        # =========================================================================
        MAX_SIZE = 3
        s_boxes = build_seq_stack_boxes(MAX_SIZE).move_to(LEFT * 3.5 + DOWN * 0.5)
        val_10 = Text("10", font_size=26, font="Arial").move_to(s_boxes[0].get_center())
        val_20 = Text("20", font_size=26, font="Arial").move_to(s_boxes[1].get_center())
        s_elements = VGroup(val_10, val_20)
        
        s_base_ptr = get_ptr("S.base", s_boxes[0], ORANGE, direction=RIGHT)
        s_top_ptr = get_ptr("S.top", s_boxes[2], GREEN, direction=LEFT)

        ret_label = VGroup(
            Text("返回值 = ", font_size=22, font="Microsoft YaHei", color=YELLOW),
            Text("?", font_size=22, font="Arial", color=YELLOW)
        ).arrange(RIGHT, buff=0.1).move_to(LEFT * 4.0 + UP * 2.0)

        self.add(s_boxes, s_elements, s_base_ptr, s_top_ptr, ret_label)

        with self.voiceover(text="假设当前栈内装有 10 和 20 两个元素。S.top 指向栈顶元素上方的空闲位置。") as tracker:
            self.play(*get_track_anims(0), run_time=max(0.5, tracker.duration - 0.5))

        with self.voiceover(text="第一步，判断栈顶和栈底指针是否相等。如果不等，说明当前栈非空，存在可以读取的元素。") as tracker:
            self.play(*get_track_anims(2), run_time=0.4)
            # 闪烁指针表示正在进行比较检查
            self.play(s_top_ptr.animate.scale(1.2), s_base_ptr.animate.scale(1.2), run_time=0.3)
            self.play(s_top_ptr.animate.scale(1/1.2), s_base_ptr.animate.scale(1/1.2), run_time=0.3)
            self.wait(max(0.1, tracker.duration - 1.0))

        with self.voiceover(text="由于 S.top 始终指向栈顶元素的下一个空闲位置，所以真正的栈顶元素所在地址为 S.top 减 1 。", subcaption="由于 S.top 始终指向栈顶元素的下一个空闲位置，所以真正的栈顶元素所在地址为 S.top - 1 。") as tracker:
            self.play(*get_track_anims(3), run_time=0.4)
            ghost_ptr = get_ptr("S.top - 1", s_boxes[1], GREEN_B, direction=LEFT)
            ghost_ptr.set_opacity(0.6) # 设置为半透明幽灵指针
            # 虚拟指针从 S.top 衍生出来并移动到目标位置
            self.play(TransformFromCopy(s_top_ptr, ghost_ptr), run_time=max(0.2, tracker.duration - 0.4))

        with self.voiceover(text="我们提取该位置的值作为结果返回。注意，整个过程中栈顶指针 S.top 本身的位置并没有发生任何位移，原有元素也完美保留在栈中。") as tracker:
            copy_val = val_20.copy()
            self.play(copy_val.animate.move_to(ret_label[1].get_center()), run_time=0.8)
            new_ret_val = Text("20", font_size=22, font="Arial", color=YELLOW).move_to(ret_label[1].get_center())
            self.remove(ret_label[1], copy_val)
            ret_label.add(new_ret_val)
            self.wait(max(0.2, tracker.duration - 0.8))

        # 淡出幽灵指针，保持画面整洁
        self.play(FadeOut(ghost_ptr), run_time=0.5)

        self.play(*get_track_anims(None), run_time=0.4)

        # =========================================================================
        # ===== PHASE E — COMPLEXITY =====
        # =========================================================================
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW), MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(code_bg, DOWN, buff=0.6).align_to(code_bg, LEFT)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW), MathTex("O(1)", font_size=22, color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(time_box, DOWN, buff=0.3).align_to(time_box, LEFT)

        with self.voiceover(
            text="由于只是进行了偏移计算和一次内存读取，所以时间复杂度为 O(1)。",
            subcaption="由于只是进行了偏移计算和一次内存读取，所以时间复杂度为 O(1)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
            text="整个操作没有使用依赖数据规模的额外内存消耗，空间复杂度同样为 O(1)。",
            subcaption="整个操作没有使用依赖数据规模的额外内存消耗，空间复杂度同样为 O(1)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是取顺序栈的栈顶元素算法的完整演示过程。") as tracker:
            self.wait(tracker.duration)
            
        self.wait(2)
