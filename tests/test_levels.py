"""
tests/test_levels.py - Unit tests for level configuration and progression rules.
"""

import unittest
from core.levels import get_level_info, evaluate_level_up


class TestLevels(unittest.TestCase):

    def test_level_info_retrieval(self):
        info = get_level_info(1)
        self.assertEqual(info["level"], 1)
        self.assertIn("Addition", info["name"])

        info_custom = get_level_info(99)
        self.assertEqual(info_custom["level"], 99)

    def test_evaluate_level_up_subtest_progression(self):
        # 10/10 score on Test 1 of Level 1 -> stays at Level 1, advances to Test 2
        level_up, new_level, new_test = evaluate_level_up(score=10, total=10, current_level=1, current_test=1)
        self.assertFalse(level_up)
        self.assertEqual(new_level, 1)
        self.assertEqual(new_test, 2)

    def test_evaluate_level_up_full_level_up(self):
        # 10/10 score on Test 4 of Level 1 -> advances to Level 2, resets to Test 1
        level_up, new_level, new_test = evaluate_level_up(score=10, total=10, current_level=1, current_test=4)
        self.assertTrue(level_up)
        self.assertEqual(new_level, 2)
        self.assertEqual(new_test, 1)

    def test_evaluate_level_up_partial_marks(self):
        # 8/10 score on Test 1 of Level 1 -> no progression, stays at Test 1 of Level 1
        level_up, new_level, new_test = evaluate_level_up(score=8, total=10, current_level=1, current_test=1)
        self.assertFalse(level_up)
        self.assertEqual(new_level, 1)
        self.assertEqual(new_test, 1)


if __name__ == "__main__":
    unittest.main()
