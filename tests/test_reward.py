"""
tests/test_reward.py - Unit tests for reward engine (apply_reward).
"""

import unittest
from unittest.mock import patch
from core.reward import apply_reward
from core.state import get_default_state


class TestReward(unittest.TestCase):

    @patch('core.reward.load_state')
    @patch('core.reward.save_state')
    def test_practice_session_awards_zero_rewards(self, mock_save, mock_load):
        # Set up default initial state
        mock_load.return_value = get_default_state(effective_date="2026-08-09")
        mock_load.return_value["minutes_banked"] = 10
        mock_load.return_value["total_stars"] = 120

        # Simulate perfect quiz result on level 1
        quiz_result = {
            "level": 1,
            "test_in_level": 1,
            "score": 10,
            "total": 10,
            "passed": True,
            "level_up_occurred": False,
            "new_level": 1,
            "new_test_in_level": 2
        }

        # Apply reward as a practice session
        res = apply_reward(earned_minutes=5, quiz_result=quiz_result, is_practice=True)

        # Assert practice gets 0 minutes and 0 stars
        self.assertEqual(res["earned_minutes"], 0)
        self.assertEqual(res["stars_earned"], 0)
        self.assertEqual(res["total_minutes_banked"], 10)  # Unchanged
        self.assertEqual(res["total_stars"], 120)  # Unchanged

    @patch('core.reward.load_state')
    @patch('core.reward.save_state')
    def test_actual_mission_awards_rewards(self, mock_save, mock_load):
        # Set up default initial state
        mock_load.return_value = get_default_state(effective_date="2026-08-09")
        mock_load.return_value["minutes_banked"] = 10
        mock_load.return_value["total_stars"] = 120

        # Simulate perfect quiz result on level 1
        quiz_result = {
            "level": 1,
            "test_in_level": 1,
            "score": 10,
            "total": 10,
            "passed": True,
            "level_up_occurred": False,
            "new_level": 1,
            "new_test_in_level": 2
        }

        # Apply reward as an actual session
        res = apply_reward(earned_minutes=5, quiz_result=quiz_result, is_practice=False)

        # Assert actual gets rewards (5 minutes, 20 stars)
        self.assertEqual(res["earned_minutes"], 5)
        self.assertEqual(res["stars_earned"], 20)
        self.assertEqual(res["total_minutes_banked"], 15)  # 10 + 5
        self.assertEqual(res["total_stars"], 140)  # 120 + 20


if __name__ == "__main__":
    unittest.main()
