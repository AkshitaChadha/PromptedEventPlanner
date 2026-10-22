import unittest
from datetime import date, datetime

from app.logic.timeline_engine import generate_timeline, reschedule_timeline


class TimelineEngineTests(unittest.TestCase):
    def test_generates_deadlines_relative_to_upcoming_event(self):
        result = generate_timeline("2026-07-30", as_of="2026-05-01")

        self.assertIsNone(result["notice"])
        self.assertEqual(len(result["tasks"]), 8)
        self.assertEqual(result["tasks"][0]["due_date"], "2026-05-01")
        self.assertEqual(result["tasks"][-1]["due_date"], "2026-07-30")
        self.assertTrue(all(task["completed"] is False for task in result["tasks"]))
        self.assertTrue(all(task["system_generated"] for task in result["tasks"]))

    def test_marks_past_deadlines_overdue_for_soon_upcoming_event(self):
        result = generate_timeline("2026-05-10", as_of="2026-05-01")

        self.assertEqual(result["tasks"][0]["status"], "overdue")
        self.assertEqual(result["tasks"][-1]["status"], "pending")

    def test_generates_no_prep_tasks_for_past_event(self):
        result = generate_timeline("2026-04-30", as_of="2026-05-01")

        self.assertEqual(result["tasks"], [])
        self.assertIn("event date has passed", result["notice"])

    def test_accepts_date_objects_and_event_on_today(self):
        result = generate_timeline(date(2026, 5, 1), as_of=date(2026, 5, 1))

        self.assertIsNone(result["notice"])
        self.assertEqual(result["tasks"][-1]["status"], "pending")

    def test_reschedules_pending_tasks_but_preserves_completed_edited_and_custom_tasks(self):
        original = generate_timeline("2026-07-30", as_of="2026-05-01")["tasks"]
        completed = {**original[0], "completed": True, "status": "completed"}
        edited = {**original[1], "title": "Call the venue manager", "user_edited": True}
        untouched = original[2]
        custom = {
            "id": "custom-photo-pickup",
            "title": "Collect printed photos",
            "description": "Pick up prints from the shop.",
            "due_date": "2026-08-01",
            "priority": "low",
            "category": "custom",
            "completed": False,
            "status": "pending",
            "system_generated": False,
            "user_edited": True,
        }

        result = reschedule_timeline(
            [completed, edited, untouched, custom],
            "2026-08-30",
            as_of="2026-05-01",
        )
        updated = {task["id"]: task for task in result["tasks"]}

        self.assertEqual(updated[completed["id"]], completed)
        self.assertEqual(updated[edited["id"]], edited)
        self.assertNotEqual(updated[untouched["id"]]["due_date"], untouched["due_date"])
        self.assertEqual(updated[custom["id"]], custom)

    def test_rescheduling_to_past_date_preserves_existing_tasks(self):
        existing = generate_timeline("2026-07-30", as_of="2026-05-01")["tasks"]

        result = reschedule_timeline(existing, "2026-04-30", as_of="2026-05-01")

        self.assertEqual(result["tasks"], existing)
        self.assertIn("event date has passed", result["notice"])

    def test_rejects_malformed_dates_and_duplicate_task_ids(self):
        with self.assertRaises(ValueError):
            generate_timeline("2026-2-01", as_of="2026-01-01")

        with self.assertRaises(ValueError):
            generate_timeline(datetime(2026, 5, 1), as_of="2026-01-01")

        with self.assertRaises(ValueError):
            reschedule_timeline([{"id": "same"}, {"id": "same"}], "2026-07-30")


if __name__ == "__main__":
    unittest.main()
