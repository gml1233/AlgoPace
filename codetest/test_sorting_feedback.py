"""运行：python -m unittest codetest.test_sorting_feedback"""
import unittest

from codetest.sorting_support import (
    SortingNarrationMixin, caption_pages, display_caption, spoken_sorting_text,
)


class SortingFeedbackTests(unittest.TestCase):
    def test_long_chinese_caption_keeps_every_character(self):
        text = "在每一个小组内部，我们仍然使用直接插入排序。由于同组记录之间隔着多个位置，所以一次比较就能让记录移动较远距离。" * 4
        pages = caption_pages(text)
        self.assertGreater(len(pages), 2)
        self.assertEqual("".join(pages).replace("\n", ""), text)
        for page in pages:
            self.assertLessEqual(len(page.splitlines()), 2)
            self.assertTrue(all(len(line) <= 24 for line in page.splitlines()))

    def test_numeric_subscripts_and_gap_in_subtitles(self):
        self.assertEqual(display_caption("从 r 一开始，当 d 等于一时完成排序。"),
                         "从 r[1]开始，当 d = 1时完成排序。")
        self.assertEqual(display_caption("r[10] = 04，dk = 1"), "r[10] = 04，dk = 1")

    def test_comparisons_and_increment_are_spoken(self):
        spoken = spoken_sorting_text("low<high，并且r[3]>=49，执行--high和++low；high--，low++。")
        self.assertIn("左边界小于右边界", spoken)
        self.assertIn("第3号单元大于或等于49", spoken)
        self.assertEqual(spoken.count("右边界减一"), 2)
        self.assertEqual(spoken.count("左边界加一"), 2)

    def test_narration_does_not_change_display_text(self):
        class Base:
            def voiceover(self, **kwargs):
                return kwargs
        class Scene(SortingNarrationMixin, Base):
            pass
        original = "low < high，执行 --high"
        result = Scene().voiceover(text=original)
        self.assertEqual(result["subcaption"], original)
        self.assertIn("减一", result["text"])

    def test_pages_cover_audio_without_gaps_or_overlaps(self):
        class Recorder(SortingNarrationMixin):
            def __init__(self):
                self.cues = []
            def add_subcaption(self, text, duration, offset):
                self.cues.append((text, duration, offset))
        scene = Recorder()
        scene.add_wrapped_subcaption("中文没有空格也必须完整显示。" * 15, 17.25)
        end = 0
        for _, duration, offset in scene.cues:
            self.assertAlmostEqual(offset, end)
            self.assertGreater(duration, 0)
            end = offset + duration
        self.assertAlmostEqual(end, 17.25)

    def test_empty_caption(self):
        self.assertEqual(caption_pages(" \n "), [])


if __name__ == "__main__":
    unittest.main()
