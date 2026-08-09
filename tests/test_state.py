"""
tests/test_state.py - Unit tests for shared state management and 9 AM rollover.
"""

import unittest
from datetime import datetime
from core.state import compute_effective_operating_date, check_and_apply_9am_rollover, get_default_state


class TestState(unittest.TestCase):

    def test_effective_operating_date_before_9am(self):
        # 8:59 AM on 2026-08-06 should count as the operating day of 2026-08-05
        dt = datetime(2026, 8, 6, 8, 59, 59)
        eff_date = compute_effective_operating_date(dt)
        self.assertEqual(eff_date, "2026-08-05")

    def test_effective_operating_date_after_9am(self):
        # 9:01 AM on 2026-08-06 should count as the operating day of 2026-08-06
        dt = datetime(2026, 8, 6, 9, 0, 1)
        eff_date = compute_effective_operating_date(dt)
        self.assertEqual(eff_date, "2026-08-06")

    def test_rollover_resets_daily_counters_but_preserves_level(self):
        # Create a state representing the previous operating day (using a static old date)
        old_state = {
            "effective_date": "2000-01-01",
            "operating_day_start": "2000-01-01T09:00:00",
            "current_level": 4,
            "sessions_today": 3,
            "minutes_banked": 45,
            "total_stars": 150,
            "streak": 5,
            "unlocked_until": "2000-01-01T23:59:00",
            "morning_battery_bonus_claimed": True,
            "history": []
        }

        # Apply rollover check. Since current system time is ahead (2026-08-06 as of today),
        # it should trigger a rollover.
        new_state = check_and_apply_9am_rollover(old_state)

        # Assert daily parameters are reset
        self.assertEqual(new_state["sessions_today"], 0)
        self.assertNotEqual(new_state["effective_date"], "2000-01-01")
        
        # Level should be preserved
        self.assertEqual(new_state["current_level"], 4)

        # Banked minutes, total stars, and streak should be preserved (minutes includes morning battery bonus of +5)
        self.assertEqual(new_state["minutes_banked"], 50)
        self.assertEqual(new_state["total_stars"], 150)
        self.assertEqual(new_state["streak"], 5)


if __name__ == "__main__":
    unittest.main()
