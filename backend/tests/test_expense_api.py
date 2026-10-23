import unittest
from datetime import date, timedelta
from pathlib import Path
import tempfile

from app import create_app
from app.database import dispose_database


class ExpenseApiTests(unittest.TestCase):
    def setUp(self):
        repository_root = Path(__file__).resolve().parents[2]
        self.temp_directory = tempfile.TemporaryDirectory(dir=repository_root)
        self.database_url = (
            f"sqlite:///{(Path(self.temp_directory.name) / 'celebrai-test.sqlite3').as_posix()}"
        )
        self.app = self._create_test_app()
        self.client = self.app.test_client()
        self.event_payload = {
            "event_name": "Graduation celebration",
            "event_type": "community",
            "event_date": (date.today() + timedelta(days=120)).isoformat(),
            "location": "Delhi",
            "guest_count": 60,
            "total_budget": 85000,
        }
        response = self.client.post("/api/events", json=self.event_payload)
        self.event_id = response.get_json()["id"]

    def tearDown(self):
        dispose_database(self.app.extensions["celebrai_engine"])
        self.temp_directory.cleanup()

    def _create_test_app(self):
        return create_app({"TESTING": True, "DATABASE_URL": self.database_url})

    def _record(self, amount, category="Catering", spent_on="2026-06-01"):
        return self.client.post(
            f"/api/events/{self.event_id}/expenses",
            json={"category": category, "amount": amount, "spent_on": spent_on},
        )

    def test_records_and_retrieves_expenses_with_budget_summary(self):
        created = self._record(40000)

        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.get_json()["budget"]["actual_spend"], 40000)
        self.assertEqual(created.get_json()["budget"]["remaining_balance"], 45000)
        self.assertFalse(created.get_json()["budget"]["over_budget"])

        fetched = self.client.get(f"/api/events/{self.event_id}/expenses")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(len(fetched.get_json()["expenses"]), 1)

    def test_summary_groups_categories_and_flags_overspending(self):
        self._record(50000, "Catering")
        self._record(40000, "Venue", "2026-06-02")

        summary = self.client.get(f"/api/events/{self.event_id}/budget").get_json()

        self.assertTrue(summary["over_budget"])
        self.assertEqual(summary["actual_spend"], 90000)
        self.assertEqual(summary["remaining_balance"], -5000)
        self.assertEqual(summary["overspend_amount"], 5000)
        self.assertEqual(summary["category_totals"], {"Catering": 50000, "Venue": 40000})

    def test_empty_expense_list_has_full_remaining_budget(self):
        summary = self.client.get(f"/api/events/{self.event_id}/budget").get_json()

        self.assertEqual(summary["actual_spend"], 0)
        self.assertEqual(summary["remaining_balance"], 85000)
        self.assertEqual(summary["percent_used"], 0)

    def test_invalid_expense_is_not_persisted(self):
        response = self._record(0)

        self.assertEqual(response.status_code, 400)
        self.assertIn("amount", response.get_json()["details"])
        self.assertEqual(
            self.client.get(f"/api/events/{self.event_id}/expenses").get_json()["expenses"], []
        )

    def test_expense_survives_database_recreation(self):
        self._record(12500)
        dispose_database(self.app.extensions["celebrai_engine"])
        self.app = self._create_test_app()
        self.client = self.app.test_client()

        response = self.client.get(f"/api/events/{self.event_id}/expenses")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["expenses"][0]["amount"], 12500)

    def test_missing_event_returns_not_found(self):
        response = self.client.post(
            "/api/events/999/expenses",
            json={"category": "Venue", "amount": 1000, "spent_on": "2026-06-01"},
        )

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
