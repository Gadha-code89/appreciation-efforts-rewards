"""
tests/integration_test.py - End-to-end programmatic simulation of My Little Wins app flows.
"""

import unittest
from datetime import datetime, timedelta
from core.state import get_default_state, check_and_apply_9am_rollover
from core.reward import complete_mission, confirm_mission
from core.badges import evaluate_badges


class TestMyLittleWinsIntegration(unittest.TestCase):

    def setUp(self):
        # Start with a clean default state
        self.state = get_default_state()

    def test_complete_child_mission_and_parent_confirm_flow(self):
        # 1. Verify default missions exist
        self.assertEqual(len(self.state["daily_missions"]), 4)
        tidy_mission = self.state["daily_missions"][0]
        self.assertEqual(tidy_mission["title"], "🧹 Tidy your room")
        self.assertEqual(tidy_mission["status"], "Not reported")

        # 2. Child completes the mission
        self.state = complete_mission(tidy_mission["id"], self.state)
        self.assertEqual(self.state["daily_missions"][0]["status"], "Pending Confirmation")

        # 3. Parent reviews and confirms with custom praise
        praise_msg = "Wonderful job cleaning your room! ❤️"
        self.state = confirm_mission(tidy_mission["id"], praise_msg, self.state)

        # Verify confirmation updates
        confirmed_mission = self.state["daily_missions"][0]
        self.assertEqual(confirmed_mission["status"], "Completed")
        self.assertEqual(confirmed_mission["praise"], praise_msg)
        self.assertEqual(self.state["total_stars"], 1)

    def test_parent_add_and_delete_custom_missions(self):
        # 1. Add mission without emoji (fallback to Heart emoji ❤️)
        title_val = "Say your prayer"
        if title_val[0].isalnum():
            title_val = f"❤️ {title_val}"

        why_val = "your manifestation"
        if not why_val.startswith("💡"):
            why_val = f"💡 {why_val}"

        self.state["daily_missions"].append({
            "id": "custom_m_1",
            "title": title_val,
            "why": why_val,
            "status": "Not reported",
            "praise": "",
            "category": "helpful"
        })

        # Verify it got added with the correct formatted title and description
        self.assertEqual(self.state["daily_missions"][-1]["title"], "❤️ Say your prayer")
        self.assertEqual(self.state["daily_missions"][-1]["why"], "💡 your manifestation")

        # 2. Delete the custom mission
        self.state["daily_missions"] = [m for m in self.state["daily_missions"] if m["id"] != "custom_m_1"]
        self.assertEqual(len(self.state["daily_missions"]), 4)

    def test_daily_rollover_resets_stars_and_saves_history(self):
        # 1. Complete and confirm two tasks today
        m1 = self.state["daily_missions"][0]
        m2 = self.state["daily_missions"][1]

        self.state = complete_mission(m1["id"], self.state)
        self.state = confirm_mission(m1["id"], "Praise 1", self.state)
        self.state = complete_mission(m2["id"], self.state)
        self.state = confirm_mission(m2["id"], "Praise 2", self.state)

        self.assertEqual(self.state["total_stars"], 2)
        self.assertEqual(self.state["streak"], 0)  # Streak remains 0 during the day

        # 2. Simulate rollover to a new day (set effective date to yesterday)
        self.state["effective_date"] = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        self.state = check_and_apply_9am_rollover(self.state)

        # 3. Verify daily stats are reset
        self.assertEqual(self.state["total_stars"], 2) # Cumulative stars are preserved!
        stars_today = sum(1 for m in self.state["daily_missions"] if m["status"] == "Completed")
        self.assertEqual(stars_today, 0)               # Stars today reset back to 0!
        self.assertEqual(self.state["streak"], 1)       # Streak incremented to 1 after rollover!
        
        # 4. Verify completed tasks moved to My Journey history log
        self.assertEqual(len(self.state["journey"]), 1)
        history_entry = self.state["journey"][0]
        self.assertEqual(history_entry["stars_earned"], 2)
        self.assertIn("🧹 Tidy your room", history_entry["completed_missions"])
        self.assertIn("📚 Read for 20 minutes", history_entry["completed_missions"])


if __name__ == "__main__":
    unittest.main()
