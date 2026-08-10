"""
tests/test_db.py - Unit tests for Supabase database operations using mock data.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import date
import core.db as db


class TestSupabaseDatabaseDriver(unittest.TestCase):

    def setUp(self):
        # Create a mock supabase client
        self.mock_client = MagicMock()
        db.supabase = self.mock_client

    def tearDown(self):
        db.supabase = None

    def test_is_db_enabled(self):
        self.assertTrue(db.is_db_enabled())
        db.supabase = None
        self.assertFalse(db.is_db_enabled())

    def test_login_family_success(self):
        # Mock database response
        mock_response = MagicMock()
        mock_response.data = [{"family_id": "fam_123", "username": "smiths", "password_hash": "pass", "parent_pin": "1111"}]
        
        # Setup mock method calls chaining: table().select().eq().execute()
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        family = db.login_family("smiths", "pass")
        self.assertIsNotNone(family)
        self.assertEqual(family["family_id"], "fam_123")
        self.mock_client.table.assert_any_call("families")

    def test_login_family_invalid_password(self):
        mock_response = MagicMock()
        mock_response.data = [{"family_id": "fam_123", "username": "smiths", "password_hash": "pass", "parent_pin": "1111"}]
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        family = db.login_family("smiths", "wrong_pass")
        self.assertNil = self.assertIsNone(family)

    def test_register_family(self):
        mock_response = MagicMock()
        mock_response.data = [{"family_id": "fam_456", "username": "jones", "parent_pin": "9999"}]
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response

        family = db.register_family("jones", "pass123", "9999")
        self.assertIsNotNone(family)
        self.assertEqual(family["family_id"], "fam_456")
        self.mock_client.table.assert_any_call("families")

    def test_update_parent_pin(self):
        mock_response = MagicMock()
        mock_response.data = [{"family_id": "fam_123", "parent_pin": "7777"}]
        self.mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        success = db.update_parent_pin("fam_123", "7777")
        self.assertTrue(success)

    def test_get_children(self):
        mock_response = MagicMock()
        mock_response.data = [{"child_id": "c1", "name": "Alice"}, {"child_id": "c2", "name": "Bob"}]
        self.mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response

        children = db.get_children("fam_123")
        self.assertEqual(len(children), 2)
        self.assertEqual(children[0]["name"], "Alice")

    def test_register_child(self):
        # Mock children name check (doesn't exist)
        mock_exist_res = MagicMock()
        mock_exist_res.data = []
        self.mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_exist_res

        mock_child = [{"child_id": "c_999", "name": "Jerry", "grade_level": 4, "current_level": 2}]
        mock_res1 = MagicMock()
        mock_res1.data = mock_child
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_res1

        child = db.register_child("fam_123", "Jerry", 4, 2)
        self.assertIsNotNone(child)
        self.assertEqual(child["child_id"], "c_999")

    def test_get_daily_missions(self):
        mock_response = MagicMock()
        mock_response.data = [{"mission_id": "m1", "title": "Tidy Room", "status": "Not reported"}]
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        missions = db.get_daily_missions("c_999")
        self.assertEqual(len(missions), 1)
        self.assertEqual(missions[0]["title"], "Tidy Room")

    def test_complete_mission_db(self):
        mock_response = MagicMock()
        mock_response.data = [{"mission_id": "m1", "status": "Pending Confirmation"}]
        self.mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        success = db.complete_mission_db("m1")
        self.assertTrue(success)

    def test_log_book_db(self):
        # Mock book check (doesn't exist)
        mock_exist_res = MagicMock()
        mock_exist_res.data = []
        self.mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_exist_res

        mock_response = MagicMock()
        mock_response.data = [{"book_id": "b1", "title": "Charlotte's Web", "status": "In Progress", "logged_date": "2026-08-10"}]
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response

        book = db.log_book_db("c_999", "Charlotte's Web", "E.B. White", "In Progress")
        self.assertIsNotNone(book)
        self.assertEqual(book["title"], "Charlotte's Web")
        self.assertEqual(book["date"], "2026-08-10")
        self.assertEqual(book["id"], "b1")

    def test_get_reading_logs(self):
        mock_response = MagicMock()
        mock_response.data = [
            {"book_id": "b1", "title": "Charlotte's Web", "status": "In Progress", "logged_date": "2026-08-09"},
            {"book_id": "b2", "title": "Peter Pan", "status": "Completed", "logged_date": "2026-08-08"}
        ]
        self.mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response

        books = db.get_reading_logs("c_999")
        self.assertEqual(len(books), 2)
        self.assertEqual(books[0]["id"], "b1")
        self.assertEqual(books[0]["date"], "2026-08-09")
        self.assertEqual(books[1]["id"], "b2")
        self.assertEqual(books[1]["date"], "2026-08-08")

    def test_get_child_badges(self):
        mock_response = MagicMock()
        mock_response.data = [{"badge_catalog_id": "first_step"}, {"badge_catalog_id": "on_fire"}]
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        badges = db.get_child_badges("c_999")
        self.assertEqual(len(badges), 2)
        self.assertIn("first_step", badges)
        self.assertIn("on_fire", badges)

    def test_log_action_db(self):
        mock_response = MagicMock()
        mock_response.data = [{"log_id": "log_777"}]
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response

        success = db.log_action_db("fam_123", "child", "Alice", "test_action", "details")
        self.assertTrue(success)
        self.mock_client.table.assert_called_with("audit_logs")
    def test_apply_rollover_db_saves_mission_history(self):
        mock_child_response = MagicMock()
        mock_child_response.data = [{"child_id": "c_999", "name": "Alice", "streak": 2, "consecutive_rest_days": 0, "last_login_date": "2026-08-09", "family_id": "fam_123"}]

        mock_missions_response = MagicMock()
        mock_missions_response.data = [
            {"mission_id": "m1", "title": "🗺️ Complete Math Mission", "category": "learning", "status": "Completed", "math_attempts": [10]},
            {"mission_id": "m2", "title": "🧹 Tidy your room", "category": "helpful", "status": "Not reported"}
        ]

        # Mock select calls: get_child_by_id, get_daily_missions, get_child_by_id in log_action_db
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_child_response,
            mock_missions_response,
            mock_child_response
        ]

        mock_insert_response = MagicMock()
        mock_insert_response.data = [{"id": "some_id"}]
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_insert_response

        mock_update_response = MagicMock()
        mock_update_response.data = [{"id": "updated"}]
        self.mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

        success = db.apply_rollover_db("c_999", 1)
        self.assertTrue(success)

        # Verify mission_history was triggered
        self.mock_client.table.assert_any_call("mission_history")
    def test_math_attempts_logging(self):
        # 1. Test start_math_attempt_db
        # Mock active check (no active attempt)
        mock_active_res = MagicMock()
        mock_active_res.data = []
        self.mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_active_res

        # Mock count check (existing attempts)
        mock_select_res = MagicMock()
        mock_select_res.data = [{"attempt_id": "att_1"}, {"attempt_id": "att_2"}]
        self.mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_select_res

        # Mock insert
        mock_insert_res = MagicMock()
        mock_insert_res.data = [{"attempt_id": "att_3"}]
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_insert_res

        attempt_id = db.start_math_attempt_db("c_999", 2)
        self.assertEqual(attempt_id, "att_3")
        self.mock_client.table.assert_any_call("math_attempts_log")

        # 2. Test complete_math_attempt_db (perfect score)
        mock_update_res = MagicMock()
        mock_update_res.data = [{"attempt_id": "att_3", "status": "completed"}]
        self.mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_res

        success = db.complete_math_attempt_db("att_3", 10)
        self.assertTrue(success)

        # 3. Test complete_math_attempt_db (low score)
        mock_update_res_low = MagicMock()
        mock_update_res_low.data = [{"attempt_id": "att_3", "status": "low score"}]
        self.mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_res_low

        success = db.complete_math_attempt_db("att_3", 8)
        self.assertTrue(success)



if __name__ == "__main__":
    unittest.main()
