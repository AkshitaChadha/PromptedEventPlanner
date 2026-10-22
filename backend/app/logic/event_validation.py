from datetime import date
import math
from typing import Any


SUPPORTED_EVENT_TYPES = {"birthday", "wedding", "anniversary", "community"}
REQUIRED_TEXT_FIELDS = ("event_name", "event_type", "event_date", "location")
OPTIONAL_LIST_FIELDS = (
    "user_preferences",
    "must_have_arrangements",
    "things_to_avoid",
    "budget_priorities",
    "dietary_requirements",
    "accessibility_requirements",
)


def validate_event_payload(payload: Any) -> tuple[dict[str, Any] | None, dict[str, str]]:
    """Validate and normalize an event request without persisting it."""
    if not isinstance(payload, dict):
        return None, {"_": "Request body must be a JSON object."}

    errors: dict[str, str] = {}
    event: dict[str, Any] = {}

    for field in REQUIRED_TEXT_FIELDS:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            errors[field] = "This field is required and must be text."
            continue

        value = value.strip()
        max_length = {"event_name": 160, "location": 200}.get(field)
        if max_length and len(value) > max_length:
            errors[field] = f"Enter no more than {max_length} characters."
            continue
        if field == "event_type":
            value = value.lower()
            if value not in SUPPORTED_EVENT_TYPES:
                errors[field] = "Choose birthday, wedding, anniversary, or community."
                continue
        elif field == "event_date":
            try:
                parsed_date = date.fromisoformat(value)
                if parsed_date.isoformat() != value:
                    raise ValueError
            except ValueError:
                errors[field] = "Enter a valid date in YYYY-MM-DD format."
                continue
        event[field] = value

    guest_count = payload.get("guest_count")
    if isinstance(guest_count, bool) or not isinstance(guest_count, int) or guest_count <= 0:
        errors["guest_count"] = "Enter a whole number of guests greater than zero."
    else:
        event["guest_count"] = guest_count

    total_budget = payload.get("total_budget")
    try:
        valid_budget = (
            not isinstance(total_budget, bool)
            and isinstance(total_budget, (int, float))
            and math.isfinite(total_budget)
            and total_budget > 0
        )
    except OverflowError:
        valid_budget = False
    if not valid_budget:
        errors["total_budget"] = "Enter a budget greater than zero in INR."
    else:
        event["total_budget"] = total_budget

    preferred_theme = payload.get("preferred_theme", "")
    if not isinstance(preferred_theme, str):
        errors["preferred_theme"] = "Enter the preferred theme as text."
    elif len(preferred_theme.strip()) > 200:
        errors["preferred_theme"] = "Enter no more than 200 characters."
    else:
        event["preferred_theme"] = preferred_theme.strip()

    for field in OPTIONAL_LIST_FIELDS:
        value = payload.get(field, [])
        if (
            not isinstance(value, list)
            or any(not isinstance(item, str) or not item.strip() for item in value)
        ):
            errors[field] = "Enter a list of non-empty text items."
        else:
            event[field] = [item.strip() for item in value]

    if errors:
        return None, errors
    return event, {}
