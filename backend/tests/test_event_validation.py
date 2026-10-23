import unittest

from app.logic.event_validation import validate_event_payload


VALID_EVENT = {
    "event_name": "Mira's birthday",
    "event_type": "birthday",
    "event_date": "2027-05-10",
    "location": "Pune",
    "guest_count": 20,
    "total_budget": 15000,
}


class EventValidationTests(unittest.TestCase):
    def test_accepts_valid_event_and_fills_optional_fields(self):
        event, errors = validate_event_payload(VALID_EVENT)

        self.assertEqual(errors, {})
        self.assertEqual(event["event_name"], "Mira's birthday")
        self.assertEqual(event["total_budget"], 15000)
        self.assertEqual(event["user_preferences"], [])
        self.assertEqual(event["preferred_theme"], "")

    def test_reports_all_missing_required_fields(self):
        event, errors = validate_event_payload({})

        self.assertIsNone(event)
        for field in ("event_name", "event_type", "event_date", "location", "guest_count", "total_budget"):
            self.assertIn(field, errors)

    def test_rejects_non_iso_or_impossible_date(self):
        for invalid_date in ("2027-02-29", "10/05/2027", "2027-5-10"):
            with self.subTest(invalid_date=invalid_date):
                event, errors = validate_event_payload({**VALID_EVENT, "event_date": invalid_date})
                self.assertIsNone(event)
                self.assertIn("event_date", errors)

    def test_accepts_past_event_date_for_later_timeline_handling(self):
        event, errors = validate_event_payload({**VALID_EVENT, "event_date": "2020-01-01"})

        self.assertEqual(errors, {})
        self.assertEqual(event["event_date"], "2020-01-01")

    def test_rejects_invalid_guest_counts(self):
        for guest_count in (0, -2, 2.5, True, "20"):
            with self.subTest(guest_count=guest_count):
                event, errors = validate_event_payload({**VALID_EVENT, "guest_count": guest_count})
                self.assertIsNone(event)
                self.assertIn("guest_count", errors)

    def test_rejects_invalid_budgets(self):
        for total_budget in (
            0,
            -1,
            float("inf"),
            float("nan"),
            10**10000,
            True,
            "15000",
            15000.123,
            10**20,
        ):
            with self.subTest(total_budget=total_budget):
                event, errors = validate_event_payload({**VALID_EVENT, "total_budget": total_budget})
                self.assertIsNone(event)
                self.assertIn("total_budget", errors)

    def test_normalizes_event_type_and_list_fields(self):
        event, errors = validate_event_payload(
            {
                **VALID_EVENT,
                "event_type": " Wedding ",
                "user_preferences": ["  vegetarian food  "],
            }
        )

        self.assertEqual(errors, {})
        self.assertEqual(event["event_type"], "wedding")
        self.assertEqual(event["user_preferences"], ["vegetarian food"])

    def test_rejects_unsupported_event_type_and_malformed_lists(self):
        event, errors = validate_event_payload(
            {**VALID_EVENT, "event_type": "conference", "things_to_avoid": "noise"}
        )

        self.assertIsNone(event)
        self.assertIn("event_type", errors)
        self.assertIn("things_to_avoid", errors)

    def test_rejects_non_object_body(self):
        event, errors = validate_event_payload(["not", "an", "object"])

        self.assertIsNone(event)
        self.assertIn("_", errors)


if __name__ == "__main__":
    unittest.main()
