"""
tests/test_reporting.py - Unit tests for parent report email generation and Resend API fallback.
"""

import unittest
import os
from pathlib import Path
from agents_app.reporting_agent import generate_html_digest, run_daily_reporting_agent
from core.state import load_state


class TestReporting(unittest.TestCase):

    def test_generate_html_digest_contains_key_elements(self):
        state = {
            "effective_date": "2026-08-05",
            "current_level": 1,
            "sessions_today": 2,
            "minutes_banked": 35,
            "morning_battery_bonus_claimed": True,
            "history": [
                {"correct": 10, "total": 10}
            ]
        }
        usage_data = {
            "categories": {
                "Games": {"total_minutes": 45, "apps": {"Roblox": 30, "Minecraft": 15}},
                "Video": {"total_minutes": 20, "apps": {"YouTube": 20}}
            }
        }
        battery_data = {
            "charge_percent": 85
        }

        html = generate_html_digest(state, usage_data, battery_data)
        
        # Verify content exists in HTML
        self.assertIn("Appreciation of Efforts Math Report", html)
        self.assertIn("Roblox", html)
        self.assertIn("YouTube", html)
        self.assertIn("35 minutes", html)
        self.assertIn("+5 Bonus Minutes Claimed", html)

    def test_run_daily_reporting_agent_saves_locally(self):
        # Trigger report agent
        result = run_daily_reporting_agent()
        
        # Verify it saved a local report file
        self.assertTrue(result["saved_locally"])
        self.assertTrue(Path(result["local_file"]).exists())
        
        # If API keys are missing, Resend delivery should be false
        if not os.getenv("RESEND_API_KEY"):
            self.assertFalse(result["sent_via_resend"])


if __name__ == "__main__":
    unittest.main()
