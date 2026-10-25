"""使用项目 Manim 环境运行：python -m unittest codetest.test_tree_feedback。"""

import ast
import importlib.util
from pathlib import Path
import unittest

import numpy as np
from manim import ImageMobject, Text

from codetest.tree_video_support import TreeVideoScene, fit_tree_title, split_tree_subcaptions


class TreeFeedbackTests(unittest.TestCase):
    def test_chinese_captions_preserve_text_and_use_at_most_two_lines(self):
        text = "路径压缩查找会将查找路径上的元素直接连接到根结点，从而降低后续查找的路径长度。" * 4
        pages = split_tree_subcaptions(text)
        self.assertEqual("".join(pages).replace("\n", ""), text)
        for page in pages:
            self.assertLessEqual(len(page.splitlines()), 2)
            self.assertTrue(all(len(line) <= 21 for line in page.splitlines()))

    def test_names_and_formulas_are_not_split_across_lines(self):
        text = "当前元素的路径需要执行 compression_find 并返回 ufset[3]，最坏时间为 O(n^2)。"
        lines = [line for page in split_tree_subcaptions(text) for line in page.splitlines()]
        for token in ("compression_find", "ufset[3]", "O(n^2)"):
            self.assertTrue(any(token in line for line in lines))

    def test_caption_timeline_covers_the_narration(self):
        class Recorder(TreeVideoScene):
            def __init__(self):
                self.cues = []
            def add_subcaption(self, text, duration, offset):
                self.cues.append((text, duration, offset))
        scene = Recorder()
        scene.add_wrapped_subcaption("合并操作的时间复杂度主要取决于两次查找操作。" * 5, 23.5, subcaption_buff=0)
        end = 0
        for _, duration, offset in scene.cues:
            self.assertAlmostEqual(offset, end)
            self.assertGreater(duration, 0)
            end = offset + duration
        self.assertAlmostEqual(end, 23.5)

    def test_long_titles_fit_to_the_left_of_the_logo(self):
        logo = ImageMobject("resource/Pitcure/front.png").scale_to_fit_height(2).to_corner(np.array([1, 1, 0]), buff=0.05)
        for text in ("以结点p为根的子树中序线索化（Python版）", "带头结点的二叉树中序线索化（Python版）", "表达式树的求值算法 (Python版)"):
            title = fit_tree_title(Text(text, font="Microsoft YaHei", font_size=46), logo)
            self.assertLessEqual(title.get_right()[0], logo.get_left()[0] - 0.29)

    def test_huffman_diagram_matches_actual_left_and_right_children(self):
        source = Path(__file__).parent / "python版/05_树和二叉树/构造哈夫曼树Python版.py"
        spec = importlib.util.spec_from_file_location("tree_feedback_huffman", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tree = module.HuffmanTree(4, [5, 2, 9, 13])
        tree.create_huffmantree()
        syntax = ast.parse(source.read_text(encoding="utf-8"))
        positions = next(node for node in ast.walk(syntax) if isinstance(node, ast.Assign)
                         and any(isinstance(target, ast.Name) and target.id == "pos" for target in node.targets))
        namespace = {"np": np}
        exec(compile(ast.Module(body=[positions], type_ignores=[]), str(source), "exec"), namespace)
        for index in range(5, 8):
            node = tree.ht[index]
            self.assertLess(namespace["pos"][node.lchild][0], namespace["pos"][index][0])
            self.assertGreater(namespace["pos"][node.rchild][0], namespace["pos"][index][0])


if __name__ == "__main__":
    unittest.main()
