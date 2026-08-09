"""
tests/test_policy.py - Unit tests for morning battery bonus rules.
"""

import unittest
from core.policy import evaluate_morning_battery_bonus


class TestPolicy(unittest.TestCase):

    def test_morning_battery_bonus_eligible(self):
        res = evaluate_morning_battery_bonus(85)
        self.assertTrue(res["eligible"])
        self.assertEqual(res["bonus_minutes"], 5)

    def test_morning_battery_bonus_ineligible(self):
        res = evaluate_morning_battery_bonus(40)
        self.assertFalse(res["eligible"])
        self.assertEqual(res["bonus_minutes"], 0)


if __name__ == "__main__":
    unittest.main()
