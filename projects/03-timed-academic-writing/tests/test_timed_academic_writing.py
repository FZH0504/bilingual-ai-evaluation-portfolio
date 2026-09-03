import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "timed_academic_writing.py"
SPEC = importlib.util.spec_from_file_location("timed_writing", MODULE_PATH)
timed_writing = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(timed_writing)


class TimedWritingTests(unittest.TestCase):
    def test_word_count(self):
        self.assertEqual(timed_writing.count_words("A well-tested draft isn't long."), 5)

    def test_timer_format(self):
        self.assertEqual(timed_writing.format_seconds(600), "10:00")
        self.assertEqual(timed_writing.format_seconds(119), "1:59")
        self.assertEqual(timed_writing.format_seconds(-1), "0:00")


if __name__ == "__main__":
    unittest.main()
