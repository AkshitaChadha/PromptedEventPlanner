import unittest
from datetime import date, timedelta
from pathlib import Path
import tempfile

from app import create_app
from app.database import dispose_database


class EventApiTests(unittest.TestCase):
    def setUp(self):
        repository_root = Path(__file__).resolve().parents[2]
        self.temp_directory = tempfile.TemporaryDirectory(dir=repository_root)
        database_path = Path(self.temp_directory.name) / "celebrai-test.sqlite3"
        self.database_url = f"sqlite:///{database_path.as_posix()}"
        self.app = self._create_test_app()
        self.client = self.app.test_client()
        self.payload = {
            "event_name": "Family celebration",
            "event_type": "anniversary",
            "event_date": (date.today() + timedelta(days=180)).isoformat(),
            "location": "Pune",
            "guest_count": 45,
            "total_budget": 85000,
            "preferred_theme": "Garden evening",
            "user_preferences": ["vegetarian options"],
            "must_have_arrangements": ["step-free access"],
            "things_to_avoid": ["loud fireworks"],
            "budget_priorities": ["Catering", "Venue"],
            "dietary_requirements": ["vegetarian"],
            "accessibility_requirements": ["step-free access"],
        }

    def tearDown(self):
        dispose_database(self.app.extensions["celebrai_engine"])
        self.temp_directory.cleanup()

    def _create_test_app(self):
        return create_app({"TESTING": True, "DATABASE_URL": self.database_url})

    def test_health_endpoint_still_works(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_create_persists_event_and_generated_tasks(self):
        response = self.client.post("/api/events", json=self.payload)

        self.assertEqual(response.status_code, 201)
        created = response.get_json()
        self.assertEqual(created["event_name"], self.payload["event_name"])
        self.assertEqual(created["currency"], "INR")
        self.assertEqual(len(created["tasks"]), 8)
        self.assertEqual(created["tasks"][0]["key"], "set-budget-priorities")

        fetched = self.client.get(f"/api/events/{created['id']}")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.get_json()["event_date"], self.payload["event_date"])
        self.assertEqual(len(fetched.get_json()["tasks"]), 8)

    def test_lists_saved_events(self):
        self.client.post("/api/events", json=self.payload)

        response = self.client.get("/api/events")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()["events"]), 1)

    def test_saved_event_survives_app_recreation(self):
        created = self.client.post("/api/events", json=self.payload).get_json()
        dispose_database(self.app.extensions["celebrai_engine"])
        self.app = self._create_test_app()
        self.client = self.app.test_client()

        response = self.client.get(f"/api/events/{created['id']}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["event_name"], self.payload["event_name"])
        self.assertEqual(len(response.get_json()["tasks"]), 8)

    def test_invalid_payload_returns_field_errors_without_creating_event(self):
        response = self.client.post("/api/events", json={**self.payload, "guest_count": 0})

        self.assertEqual(response.status_code, 400)
        self.assertIn("guest_count", response.get_json()["details"])
        self.assertEqual(self.client.get("/api/events").get_json()["events"], [])

    def test_non_json_request_returns_validation_error(self):
        response = self.client.post("/api/events", data="not-json", content_type="text/plain")

        self.assertEqual(response.status_code, 400)
        self.assertIn("_", response.get_json()["details"])

    def test_task_can_be_completed_and_reopened(self):
        created = self.client.post("/api/events", json=self.payload).get_json()
        task_id = created["tasks"][-1]["id"]

        completed = self.client.patch(
            f"/api/events/{created['id']}/tasks/{task_id}", json={"completed": True}
        )
        reopened = self.client.patch(
            f"/api/events/{created['id']}/tasks/{task_id}", json={"completed": False}
        )

        self.assertEqual(completed.status_code, 200)
        self.assertEqual(completed.get_json()["status"], "completed")
        self.assertFalse(reopened.get_json()["completed"])

    def test_task_update_rejects_extra_or_non_boolean_fields(self):
        created = self.client.post("/api/events", json=self.payload).get_json()
        task_id = created["tasks"][0]["id"]

        response = self.client.patch(
            f"/api/events/{created['id']}/tasks/{task_id}",
            json={"completed": "yes", "title": "Changed"},
        )

        self.assertEqual(response.status_code, 400)

    def test_missing_event_or_task_returns_not_found(self):
        self.assertEqual(self.client.get("/api/events/999").status_code, 404)
        self.assertEqual(
            self.client.patch("/api/events/999/tasks/1", json={"completed": True}).status_code,
            404,
        )


if __name__ == "__main__":
    unittest.main()
