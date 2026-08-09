"""
tests/test_reporting.py - Unit tests for parent report email generation and Resend API fallback.
"""

import unittest
import os
from pathlib import Path
from agents_app.reporting_agent import generate_html_digest, run_daily_reporting_agent


class TestReporting(unittest.TestCase):

    def test_generate_html_digest_contains_key_elements(self):
        state = {
            "effective_date": "2026-08-05",
            "total_stars": 42,
            "streak": 5,
            "daily_missions": [
                {
                    "title": "🧹 Tidy your room",
                    "status": "Completed",
                    "praise": "Great cleaning! ❤️"
                },
                {
                    "title": "📚 Read for 20 minutes",
                    "status": "Pending Confirmation"
                }
            ]
        }

        html = generate_html_digest(state)
        
        # Verify content exists in HTML
        self.assertIn("Appreciation of Efforts Personal Growth Report", html)
        self.assertIn("Tidy your room", html)
        self.assertIn("Great cleaning!", html)
        self.assertIn("Read for 20 minutes", html)
        self.assertIn("5 Days", html)
        self.assertIn("42", html)

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
