"""
tests/test_state.py - Unit tests for shared state management, 9 AM rollover, and streak protection.
"""

import unittest
from datetime import datetime
from core.state import compute_effective_operating_date, check_and_apply_9am_rollover, get_default_state


class TestState(unittest.TestCase):

    def test_effective_operating_date_before_midnight(self):
        # 11:59 PM on 2026-08-05 should count as the operating day of 2026-08-05
        dt = datetime(2026, 8, 5, 23, 59, 59)
        eff_date = compute_effective_operating_date(dt)
        self.assertEqual(eff_date, "2026-08-05")

    def test_effective_operating_date_after_midnight(self):
        # 12:00 AM on 2026-08-06 should count as the operating day of 2026-08-06
        dt = datetime(2026, 8, 6, 0, 0, 1)
        eff_date = compute_effective_operating_date(dt)
        self.assertEqual(eff_date, "2026-08-06")

    def test_rollover_with_completed_missions_increments_streak(self):
        # Create a state representing yesterday
        state = get_default_state()
        state["effective_date"] = "2000-01-01"
        state["streak"] = 2
        state["consecutive_rest_days"] = 0
        state["tomorrow_reward"] = "30 mins of play"
        
        # Complete one mission
        state["daily_missions"][0]["status"] = "Completed"
        completed_title = state["daily_missions"][0]["title"]

        # Run rollover (current date is different from 2000-01-01)
        new_state = check_and_apply_9am_rollover(state)

        # Assert completed mission moved to journey
        self.assertEqual(len(new_state["journey"]), 1)
        self.assertEqual(new_state["journey"][0]["completed_missions"][0], completed_title)

        # Streak should increment to 3
        self.assertEqual(new_state["streak"], 3)
        self.assertEqual(new_state["consecutive_rest_days"], 0)

        # Tomorrow's reward shifts to yesterday's praise
        self.assertEqual(new_state["yesterday_reward_praise"], "Yesterday you earned 30 mins of play! ❤️")
        self.assertEqual(new_state["tomorrow_reward"], "")

        # Daily missions status reset
        self.assertEqual(new_state["daily_missions"][0]["status"], "Not reported")

    def test_rollover_first_rest_day_preserves_streak(self):
        state = get_default_state()
        state["effective_date"] = "2000-01-01"
        state["streak"] = 4
        state["consecutive_rest_days"] = 0

        # No missions completed today -> rest day
        new_state = check_and_apply_9am_rollover(state)

        # Streak should still be 4 (rest day protection)
        self.assertEqual(new_state["streak"], 4)
        self.assertEqual(new_state["consecutive_rest_days"], 1)

    def test_rollover_second_rest_day_resets_streak(self):
        state = get_default_state()
        state["effective_date"] = "2000-01-01"
        state["streak"] = 4
        state["consecutive_rest_days"] = 1

        # No missions completed -> second rest day in a row
        new_state = check_and_apply_9am_rollover(state)

        # Streak should reset to 0
        self.assertEqual(new_state["streak"], 0)
        self.assertEqual(new_state["consecutive_rest_days"], 2)


if __name__ == "__main__":
    unittest.main()
