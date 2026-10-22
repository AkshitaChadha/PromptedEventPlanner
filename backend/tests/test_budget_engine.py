import unittest
from decimal import Decimal

from app.logic.budget_engine import allocate_budget


class BudgetEngineTests(unittest.TestCase):
    def test_reduces_low_priority_first_and_preserves_catering(self):
        result = allocate_budget(
            40000,
            {"Catering": 20000, "Decor": 15000, "Entertainment": 10000},
            priorities=["Catering", "Decor", "Entertainment"],
        )

        self.assertTrue(result["feasible"])
        self.assertEqual(result["allocations"]["Catering"], Decimal("20000"))
        self.assertEqual(result["allocations"]["Entertainment"], Decimal("5000"))
        self.assertEqual(result["reductions"], {"Entertainment": Decimal("5000")})
        self.assertEqual(result["allocated_total"], Decimal("40000"))
        self.assertEqual(result["remaining_balance"], Decimal("0"))

    def test_leaves_unused_balance_when_estimates_fit(self):
        result = allocate_budget(50000, {"Catering": 20000, "Decor": 10000})

        self.assertEqual(result["requested_total"], Decimal("30000"))
        self.assertEqual(result["allocated_total"], Decimal("30000"))
        self.assertEqual(result["remaining_balance"], Decimal("20000"))
        self.assertEqual(result["reductions"], {})

    def test_unprioritized_categories_are_reduced_before_prioritized_ones(self):
        result = allocate_budget(
            35000,
            {"Catering": 20000, "Decor": 10000, "Extras": 10000},
            priorities=["Catering", "Decor"],
        )

        self.assertEqual(result["allocations"]["Catering"], Decimal("20000"))
        self.assertEqual(result["allocations"]["Decor"], Decimal("10000"))
        self.assertEqual(result["allocations"]["Extras"], Decimal("5000"))

    def test_category_minimums_are_preserved(self):
        result = allocate_budget(
            40000,
            {"Catering": 20000, "Decor": 15000, "Entertainment": 10000},
            priorities=["Catering", "Decor", "Entertainment"],
            minimums={"Catering": 18000, "Decor": 5000, "Entertainment": 9000},
        )

        self.assertTrue(result["feasible"])
        self.assertEqual(result["allocations"]["Catering"], Decimal("20000"))
        self.assertEqual(result["allocations"]["Decor"], Decimal("11000"))
        self.assertEqual(result["allocations"]["Entertainment"], Decimal("9000"))

    def test_flags_infeasible_minimums_and_reports_overspend(self):
        result = allocate_budget(
            40000,
            {"Catering": 25000, "Venue": 20000},
            priorities=["Catering", "Venue"],
            minimums={"Catering": 25000, "Venue": 20000},
        )

        self.assertFalse(result["feasible"])
        self.assertEqual(result["allocated_total"], Decimal("45000"))
        self.assertEqual(result["overspend_amount"], Decimal("5000"))
        self.assertEqual(result["remaining_balance"], Decimal("-5000"))
        self.assertIn("increase the budget", result["explanation"])

    def test_uses_decimal_arithmetic_for_fractional_amounts(self):
        result = allocate_budget(
            Decimal("10.30"),
            {"A": Decimal("6.10"), "B": Decimal("5.20")},
            priorities=["A", "B"],
        )

        self.assertEqual(result["allocations"]["A"], Decimal("6.10"))
        self.assertEqual(result["allocations"]["B"], Decimal("4.20"))
        self.assertEqual(result["allocated_total"], Decimal("10.30"))

    def test_rejects_invalid_budget_amounts(self):
        for invalid in (0, -1, True, float("inf"), float("nan"), "500"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    allocate_budget(invalid, {"Catering": 10})

    def test_rejects_bad_estimates_and_priorities(self):
        cases = (
            ({"Catering": -1}, ["Catering"], None),
            ({"Catering": True}, ["Catering"], None),
            ({"Catering": 10}, ["Missing"], None),
            ({"Catering": 10}, ["Catering", "Catering"], None),
            ({"Catering": 10}, ["Catering"], {"Catering": 11}),
        )
        for estimates, priorities, minimums in cases:
            with self.subTest(estimates=estimates, priorities=priorities, minimums=minimums):
                with self.assertRaises(ValueError):
                    allocate_budget(20, estimates, priorities, minimums)


if __name__ == "__main__":
    unittest.main()
