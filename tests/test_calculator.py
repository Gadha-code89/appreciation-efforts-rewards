"""
tests/test_calculator.py - Unit tests for AST evaluation and answer string sanitization.
"""

import unittest
from core.calculator import verify_arithmetic, sanitize_and_evaluate_answer


class TestCalculator(unittest.TestCase):

    def test_verify_arithmetic_valid(self):
        self.assertEqual(verify_arithmetic("19 + 28"), 47.0)
        self.assertEqual(verify_arithmetic("12 * 11"), 132.0)
        self.assertEqual(verify_arithmetic("100 / 4"), 25.0)
        self.assertEqual(verify_arithmetic("(5 * 6) + 10"), 40.0)

    def test_verify_arithmetic_invalid(self):
        with self.assertRaises(Exception):
            verify_arithmetic("import os; os.system('echo hack')")

    def test_sanitize_and_evaluate_answer(self):
        is_correct, val = sanitize_and_evaluate_answer("47", 47.0)
        self.assertTrue(is_correct)
        self.assertEqual(val, 47.0)

        is_correct, val = sanitize_and_evaluate_answer(" 47.0 ", 47.0)
        self.assertTrue(is_correct)

        is_correct, val = sanitize_and_evaluate_answer("47 apples", 47.0)
        self.assertTrue(is_correct)
        self.assertEqual(val, 47.0)

        is_correct, val = sanitize_and_evaluate_answer("50", 47.0)
        self.assertFalse(is_correct)


if __name__ == "__main__":
    unittest.main()
