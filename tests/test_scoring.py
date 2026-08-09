"""
tests/test_scoring.py - Unit tests for diminishing returns scoring formula.
"""

import unittest
from core.scoring import compute_minutes


class TestScoring(unittest.TestCase):

    def test_level_1_full_score(self):
        res = compute_minutes(num_correct=10, num_questions=10, session_number=1, is_practice=False, level=1)
        self.assertEqual(res["minutes"], 5)
        self.assertEqual(res["accuracy"], 1.0)

    def test_level_3_full_score(self):
        res = compute_minutes(num_correct=10, num_questions=10, session_number=1, is_practice=True, level=3)
        self.assertEqual(res["minutes"], 15)
        self.assertEqual(res["accuracy"], 1.0)

    def test_strict_10_10_requirement(self):
        # 9/10 is not perfect -> 0 minutes
        res_fail = compute_minutes(num_correct=9, num_questions=10, session_number=1, is_practice=False, level=1)
        self.assertEqual(res_fail["minutes"], 0)


if __name__ == "__main__":
    unittest.main()
