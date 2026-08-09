"""
tests/test_reward.py - Unit tests for growth mission rewards and confirmations.
"""

import unittest
from core.reward import complete_mission, confirm_mission
from core.state import get_default_state


class TestReward(unittest.TestCase):

    def test_complete_mission_changes_status_to_pending(self):
        state = get_default_state()
        self.assertEqual(state["daily_missions"][0]["status"], "Not reported")

        # Mark as completed
        new_state = complete_mission(state["daily_missions"][0]["id"], state)
        self.assertEqual(new_state["daily_missions"][0]["status"], "Pending Confirmation")

    def test_confirm_mission_awards_star_and_sets_praise(self):
        state = get_default_state()
        state["total_stars"] = 5
        
        # Complete & confirm
        state = complete_mission(state["daily_missions"][0]["id"], state)
        new_state = confirm_mission(
            state["daily_missions"][0]["id"], 
            "Amazing room tidying! ✨", 
            state
        )

        self.assertEqual(new_state["daily_missions"][0]["status"], "Completed")
        self.assertEqual(new_state["daily_missions"][0]["praise"], "Amazing room tidying! ✨")
        self.assertEqual(new_state["total_stars"], 6)  # 5 + 1


if __name__ == "__main__":
    unittest.main()
