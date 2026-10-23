import unittest
from decimal import Decimal

from app.logic.expense_validation import validate_expense_payload


VALID_EXPENSE = {
    "category": "Catering",
    "description": "Advance payment",
    "amount": 12500,
    "spent_on": "2026-06-01",
}


class ExpenseValidationTests(unittest.TestCase):
    def test_accepts_and_normalizes_valid_expense(self):
        expense, errors = validate_expense_payload(
            {**VALID_EXPENSE, "category": " Catering ", "description": " Advance payment "}
        )

        self.assertEqual(errors, {})
        self.assertEqual(expense["category"], "Catering")
        self.assertEqual(expense["description"], "Advance payment")
        self.assertEqual(expense["amount"], Decimal("12500"))

    def test_rejects_missing_fields_and_invalid_amounts(self):
        expense, errors = validate_expense_payload({})

        self.assertIsNone(expense)
        self.assertTrue({"category", "amount", "spent_on"}.issubset(errors))

        for amount in (0, -1, float("inf"), float("nan"), True, "1200", 10**100, 1.005):
            with self.subTest(amount=amount):
                expense, errors = validate_expense_payload({**VALID_EXPENSE, "amount": amount})
                self.assertIsNone(expense)
                self.assertIn("amount", errors)

    def test_rejects_invalid_dates_and_unsupported_fields(self):
        expense, errors = validate_expense_payload({**VALID_EXPENSE, "spent_on": "2026-2-01"})
        self.assertIsNone(expense)
        self.assertIn("spent_on", errors)

        expense, errors = validate_expense_payload({**VALID_EXPENSE, "vendor_id": 123})
        self.assertIsNone(expense)
        self.assertIn("_", errors)


if __name__ == "__main__":
    unittest.main()
