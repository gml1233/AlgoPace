import sys

def main():
    with open('codetest/B-树的查找.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find PHASE A and PHASE B
    phase_b_start = next(i for i, l in enumerate(lines) if 'PHASE B' in l)
    
    # We find make_btree_node manually since its index might have shifted
    make_start = next(i for i, l in enumerate(lines) if 'def make_btree_node' in l)
    # The end of make_btree_node is 'return group\n'
    make_end = next(i for i in range(make_start, len(lines)) if 'return group' in lines[i]) + 1

    # Extract make_btree_node block
    make_btree_node_block = lines[make_start:make_end]

    # Delete make_btree_node from its original position
    del lines[make_start:make_end]
    
    # After deletion, phase_b_start index needs to be recalculated
    phase_b_start = next(i for i, l in enumerate(lines) if 'PHASE B' in l)

    phase_a2 = """        # ===== PHASE A2 — 实例引入 =====
        with self.voiceover(text="为了更好地理解 B-树的查找，我们可以想象一个图书馆的多区间书架系统。") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="在这个系统中，每一层都是一个索引书架，每个书架上摆放的不是真正的书，而是一组分界标签。") as tracker:
            bookshelf = make_btree_node([10, 20, 30], np.array([0, 1.0, 0]))
            bookshelf.scale(1.5)
            # The ptrs must be updated because scaling does not scale the numpy arrays automatically
            ptrs = []
            ptr_cells = [bookshelf[0][i] for i in range(0, 7, 2)]
            for p in ptr_cells:
                ptrs.append(np.array([p[0].get_center()[0], p[0].get_bottom()[1], 0]))
            bookshelf.ptrs = ptrs
            self.play(FadeIn(bookshelf), run_time=tracker.duration)

        with self.voiceover(text="比如这个书架上有 10、20、30 三个标签，它们就将所有的图书编号划分成了四个区间。") as tracker:
            intervals = VGroup(
                Text("(-∞,10)", font_size=20, font="Consolas", color=YELLOW).next_to(bookshelf.ptrs[0], DOWN, buff=0.8),
                Text("(10,20)", font_size=20, font="Consolas", color=YELLOW).next_to(bookshelf.ptrs[1], DOWN, buff=0.8),
                Text("(20,30)", font_size=20, font="Consolas", color=YELLOW).next_to(bookshelf.ptrs[2], DOWN, buff=0.8),
                Text("(30,+∞)", font_size=20, font="Consolas", color=YELLOW).next_to(bookshelf.ptrs[3], DOWN, buff=0.8),
            )
            
            arrows = VGroup(*[
                Arrow(start=bookshelf.ptrs[i], end=intervals[i].get_top(), buff=0.1, color=GRAY, max_tip_length_to_length_ratio=0.15)
                for i in range(4)
            ])
            self.play(FadeIn(intervals), FadeIn(arrows), run_time=tracker.duration)

        with self.voiceover(text="查找的核心思想是：当你要找一本编号为 key 的书时，你不会直接往下冲，而是做三件事：") as tracker:
            self.wait(tracker.duration)

        with self.voiceover(text="第一，先看当前书架的分界标签；") as tracker:
            self.play(Indicate(bookshelf.cells, color=RED), run_time=tracker.duration)

        with self.voiceover(text="第二，判断 key 属于哪个区间；") as tracker:
            self.play(Indicate(intervals, color=GREEN), run_time=tracker.duration)

        with self.voiceover(text="第三，顺着对应的指针通道，进入下一层书架继续查找。") as tracker:
            self.play(*[Indicate(arr, color=YELLOW) for arr in arrows], run_time=tracker.duration)

        self.play(FadeOut(bookshelf), FadeOut(intervals), FadeOut(arrows))

"""

    # Assemble new file
    part1 = lines[:phase_b_start]
    part2 = lines[phase_b_start:]

    new_lines = part1 + make_btree_node_block + ["\n"] + phase_a2.splitlines(True) + ["\n"] + part2

    with open('codetest/B-树的查找.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

if __name__ == '__main__':
    main()
