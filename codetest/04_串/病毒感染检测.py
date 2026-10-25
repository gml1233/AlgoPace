# coding=utf-8
from manim import *
import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
from manim_voiceover import VoiceoverScene
from generation.tts.edge_service import EdgeTTSService

class VirusDetectionVideo(VoiceoverScene):
    def construct(self):
        # 初始化语音服务
        self.set_speech_service(EdgeTTSService(voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%", pitch="+0Hz"))

        logo = ImageMobject(r"resource\Pitcure\front.png").scale_to_fit_height(2.0).to_corner(UR, buff=0.05).shift(UP * 0.1)
        self.add(logo)

        # ===== PHASE A — TITLE =====
        algo_title = Text("病毒感染检测", font_size=48, font="Microsoft YaHei", weight=BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(algo_title), run_time=0.8)

        with self.voiceover(text="本节我们将学习如何利用 B F 算法来实现环状病毒的感染检测。") as tracker:
            self.wait(tracker.duration)

        # ===== PHASE B — CODE BLOCK CONFIG =====
        c_lines = [
            "void Virus_detection()",
            "{//利用BF算法实现病毒检测",
            "    ifstream inFile(\"病毒感染检测输入数据.txt\");",
            "    ofstream outFile(\"病毒感染检测输出结果.txt\");",
            "    inFile>>num;\n        //读取待检测的任务数",
            "    while(num--)\n        //依次检测每对病毒DNA和人的DNA是否匹配",
            "    {",
            "        inFile>>Virus.ch+1;\n            //读取病毒DNA序列，字符串从下标1开始存放",
            "        inFile>>Person.ch+1;\n            //读取人的DNA序列",
            "        Vir=Virus.ch;\n            //将病毒DNA临时暂存在Vir中，以备输出",
            "        flag=0;\n            //用来标识是否匹配，初始为0，匹配后为非0",
            "        m=Virus.length;\n            //病毒DNA序列的长度是m",
            "        for(i=m+1,j=1;j<=m;j++)",
            "            Virus.ch[i++]=Virus.ch[j];\n            //将病毒字符串的长度扩大2倍",
            "        Virus.ch[2*m+1]='\\0';\n            //添加结束符号",
            "        for(i=0;i<m;i++)\n            //依次取得每个长度为m的病毒DNA环状字符串temp",
            "        {",
            "            for(j=1;j<=m;j++)\n                temp.ch[j]=Virus.ch[i+j];",
            "            temp.ch[m+1]='\\0';\n                //添加结束符号",
            "            flag=Index_BF(Person,temp,1);\n                //模式匹配",
            "            if(flag) break;\n                //匹配即可退出循环",
            "        }      //for",
            "        if(flag) outFile<<Vir+1<<\" \"<<Person.ch+1\n            <<\" \"<<\"YES\"<<endl;",
            "        else outFile<<Vir+1<<\" \"<<Person.ch+1\n            <<\" \"<<\"NO\"<<endl;",
            "    }      //while",
            "}"
        ]

        self.c_texts = []
        for line in c_lines:
            stripped_line = line.lstrip(" ")
            t = Text(stripped_line, font_size=7.2, font="Microsoft YaHei", color=WHITE)
            self.c_texts.append(t)

        code_group = VGroup(*self.c_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        SPACE_WIDTH = 0.04
        for i, line in enumerate(c_lines):
            indent_count = len(line) - len(line.lstrip(" "))
            self.c_texts[i].shift(RIGHT * indent_count * SPACE_WIDTH)

        if code_group.width > 6.35:
            code_group.scale_to_fit_width(6.35)
        if code_group.height > 5.75:
            code_group.scale_to_fit_height(5.75)
        bg_width = code_group.get_width() + 0.7
        bg_height = code_group.get_height() + 0.5
        code_bg = RoundedRectangle(corner_radius=0.12, height=bg_height, width=bg_width, color=GRAY, fill_opacity=0.1, stroke_width=1)
        code_bg.move_to(code_group, aligned_edge=LEFT).shift(LEFT * 0.4)
        code_bg.match_y(code_group)
        
        code_block = VGroup(code_bg, code_group).next_to(logo, DOWN, buff=0.15).to_edge(RIGHT, buff=0.18)

        self.current_line = None

        def get_track_anims(new_idx):
            if new_idx == self.current_line: return [Wait(0.001)]
            anims = []
            if self.current_line is not None:
                anims.append(self.c_texts[self.current_line].animate.set_color(WHITE).scale(1 / 1.08, about_edge=LEFT))
            if new_idx is not None:
                anims.append(self.c_texts[new_idx].animate.set_color(YELLOW).scale(1.08, about_edge=LEFT))
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

        with self.voiceover(text="右侧是病毒感染检测的完整算法代码。") as tracker:
            self.play(FadeIn(code_block), run_time=tracker.duration)

        # ===== PHASE C — VISUALIZATION SETUP =====
        def build_string_array(s_str, label_text, color=BLUE):
            boxes = VGroup()
            texts = VGroup()
            indices = VGroup()
            for idx, ch in enumerate(s_str):
                box = Square(side_length=0.7, color=color)
                txt = Text(ch, font_size=32, color=WHITE)
                idx_txt = Text(str(idx + 1), font_size=18, color=GRAY)
                if idx > 0:
                    box.next_to(boxes[-1], RIGHT, buff=0.08)
                txt.move_to(box.get_center())
                idx_txt.next_to(box, UP if label_text == "Person" else DOWN, buff=0.1)
                boxes.add(box)
                texts.add(txt)
                indices.add(idx_txt)
            res = VGroup(boxes, texts, indices)
            label = Text(label_text, font_size=28, color=color, weight=BOLD).next_to(res, LEFT, buff=0.5)
            return VGroup(label, res), boxes, texts, label

        P_str = "cbbad"
        V_str = "bab"
        
        P_full, P_boxes, P_texts, P_label = build_string_array(P_str, "Person", color=BLUE)
        P_full.to_edge(LEFT, buff=1.0).shift(UP * 2.0)
        
        V_full, V_boxes, V_texts, V_label = build_string_array(V_str, "Virus", color=ORANGE)
        V_full.move_to(P_full).shift(DOWN * 3.5)
        # 对齐第一个 box
        diff_x = P_boxes[0].get_center()[0] - V_boxes[0].get_center()[0]
        V_full.shift(RIGHT * diff_x)

        with self.voiceover(
            text="假设人的 D N A 序列为 C B B A D，是一条线性链；而病毒的 D N A 为 B A B，它的结构其实是环状的。",
            subcaption="假设人的 DNA 序列为 cbbad，是一条线性链；而病毒的 DNA 为 bab，它的结构其实是环状的。"
        ) as tracker:
            self.play(FadeIn(P_full), FadeIn(V_full), run_time=tracker.duration)

        with self.voiceover(
            text="因为病毒序列是环状的，所以它可以从任意一个字母开始读取，这就意味着 B A B 实际上对应着三种可能的线性组合。",
            subcaption="因为病毒序列是环状的，所以它可以从任意一个字母开始读取，这就意味着 bab 实际上对应着三种可能的线性组合。"
        ) as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="在算法中，为了方便处理这种环状结构，我们使用了一个非常巧妙的方法。") as tracker:
            self.play(*get_track_anims(12), run_time=tracker.duration/2)
            self.play(*get_track_anims(13), run_time=tracker.duration/2)
            
        with self.voiceover(text="那就是将原病毒序列复制一份，直接拼接在末尾，使得病毒数组的长度扩大为原来的两倍。") as tracker:
            new_boxes = VGroup()
            new_texts = VGroup()
            new_indices = VGroup()
            for idx, ch in enumerate(V_str):
                box = Square(side_length=0.7, color=ORANGE)
                txt = Text(ch, font_size=32, color=WHITE)
                idx_txt = Text(str(idx + 4), font_size=18, color=GRAY)
                box.next_to(V_boxes[-1] if idx == 0 else new_boxes[-1], RIGHT, buff=0.08)
                txt.move_to(box.get_center())
                idx_txt.next_to(box, DOWN, buff=0.1)
                new_boxes.add(box)
                new_texts.add(txt)
                new_indices.add(idx_txt)
                
            self.play(
                FadeIn(new_boxes), FadeIn(new_texts), FadeIn(new_indices),
                run_time=tracker.duration
            )
            V_boxes.add(*new_boxes)
            V_texts.add(*new_texts)
            V_full[1][0].add(*new_boxes)
            V_full[1][1].add(*new_texts)
            V_full[1][2].add(*new_indices)

        temp_group = None
        def extract_temp(start_idx):
            nonlocal temp_group
            self.play(*get_track_anims(17), run_time=0.4)
            t_boxes = VGroup()
            t_texts = VGroup()
            for i in range(3):
                box = Square(side_length=0.7, color=PURPLE)
                if i == 0:
                    box.move_to(V_boxes[start_idx].get_center())
                else:
                    box.next_to(t_boxes[-1], RIGHT, buff=0.08)
                txt = Text(V_str[(start_idx + i) % 3], font_size=32, color=WHITE).move_to(box.get_center())
                t_boxes.add(box)
                t_texts.add(txt)
                
            label = Text("temp", font_size=24, color=PURPLE, weight=BOLD).next_to(t_boxes, LEFT, buff=0.3)
            tg = VGroup(label, t_boxes, t_texts)
            
            self.play(FadeIn(tg), run_time=0.6)
            
            tg.generate_target()
            tg.target.next_to(P_full, DOWN, buff=0.8)
            dx = P_boxes[0].get_center()[0] - tg.target[1][0].get_center()[0]
            tg.target.shift(RIGHT * dx)
            
            self.play(MoveToTarget(tg), run_time=0.8)
            temp_group = tg
            return t_boxes, t_texts

        def slide_and_match(t_boxes, match_idx):
            self.play(*get_track_anims(19), run_time=0.4)
            for slide_idx in range(5 - 3 + 1): 
                is_match = (slide_idx == match_idx)
                self.play(
                    t_boxes.animate.set_color(GREEN if is_match else RED),
                    P_boxes[slide_idx:slide_idx+3].animate.set_color(GREEN if is_match else RED),
                    run_time=0.3
                )
                if is_match:
                    self.play(
                        t_boxes.animate.set_color(PURPLE),
                        P_boxes[slide_idx:slide_idx+3].animate.set_color(BLUE),
                        run_time=0.3
                    )
                    return True
                
                self.play(
                    t_boxes.animate.set_color(PURPLE),
                    P_boxes[slide_idx:slide_idx+3].animate.set_color(BLUE),
                    run_time=0.2
                )
                
                if slide_idx < 2:
                    self.play(temp_group.animate.shift(RIGHT * 0.78), run_time=0.3)
            return False

        with self.voiceover(
            text="接下来，我们依次从扩大后的病毒序列中，截取长度为 3 的片段，并在人的 D N A 中寻找匹配。",
            subcaption="接下来，我们依次从扩大后的病毒序列中，截取长度为 3 的片段，并在人的 DNA 中寻找匹配。"
        ) as tracker:
            self.play(*get_track_anims(15), run_time=tracker.duration)

        # i = 0 (bab)
        with self.voiceover(
            text="首先提取第一种组合：B A B。",
            subcaption="首先提取第一种组合：bab。"
        ) as tracker:
            t_boxes, t_texts = extract_temp(0)
            
        with self.voiceover(text="调用 B F 算法进行模式匹配。经过比较，发现匹配失败。") as tracker:
            slide_and_match(t_boxes, -1)
            self.play(FadeOut(temp_group), run_time=0.3)

        # i = 1 (abb)
        with self.voiceover(
            text="接着循环继续，提取第二种组合：A B B。",
            subcaption="接着循环继续，提取第二种组合：abb。"
        ) as tracker:
            self.play(*get_track_anims(15), run_time=0.3)
            t_boxes, t_texts = extract_temp(1)

        with self.voiceover(text="同样进行 B F 匹配，依然没有在目标序列中找到。") as tracker:
            slide_and_match(t_boxes, -1)
            self.play(FadeOut(temp_group), run_time=0.3)

        # i = 2 (bba)
        with self.voiceover(
            text="循环继续，提取第三种组合：B B A。",
            subcaption="循环继续，提取第三种组合：bba。"
        ) as tracker:
            self.play(*get_track_anims(15), run_time=0.3)
            t_boxes, t_texts = extract_temp(2)

        with self.voiceover(text="再次调用 B F 算法匹配。这一次，在目标序列中找到了对应的片段，匹配成功！") as tracker:
            slide_and_match(t_boxes, 1)

        with self.voiceover(text="此时返回真值，程序跳出循环，判定该人感染了病毒。") as tracker:
            self.play(*get_track_anims(20), run_time=0.5)
            self.play(temp_group.animate.set_color(GREEN), run_time=0.5)
            
            res_box = VGroup(
                Text("结果：检测为感染 (YES)", font_size=24, font="Microsoft YaHei", color=GREEN)
            ).move_to(LEFT * 4.5 + DOWN * 2.3)
            self.play(Write(res_box), run_time=max(0.5, tracker.duration - 1.0))

        self.play(*get_track_anims(None), run_time=0.5)

        # ===== PHASE E — COMPLEXITY =====
        time_box = VGroup(Text("时间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW), Text("O(m^2 × n)", font_size=22, font="Consolas", color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(res_box, RIGHT, buff=0.6)
        space_box = VGroup(Text("空间复杂度：", font_size=22, font="Microsoft YaHei", color=YELLOW), Text("O(m)", font_size=22, font="Consolas", color=YELLOW)).arrange(RIGHT, buff=0.1).next_to(time_box, RIGHT, buff=0.6)

        with self.voiceover(
            text="分析一下复杂度。外层循环执行 M 次，内部生成临时字符串并进行 B F 匹配，最坏情况下总体时间复杂度为 O(M 平方乘以 N)。",
            subcaption="分析一下复杂度。外层循环执行 m 次，内部生成临时字符串并进行 BF 匹配，最坏情况下总体时间复杂度为 O(m² × n)。"
        ) as tracker:
            self.play(FadeIn(time_box), run_time=tracker.duration)

        with self.voiceover(
            text="另外，算法创建了扩展一倍的病毒序列和临时字符串，两者长度均不超过两倍的 M，因此空间复杂度为 O(M)。",
            subcaption="另外，算法创建了扩展一倍的病毒序列和临时字符串，两者长度均不超过 2 倍的 m，因此空间复杂度为 O(m)。"
        ) as tracker:
            self.play(FadeIn(space_box), run_time=tracker.duration)

        with self.voiceover(text="以上就是病毒感染检测算法的完整演示过程。") as tracker:
            self.wait(tracker.duration)
            
        self.wait(2)
