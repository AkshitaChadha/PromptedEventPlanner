from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta
from typing import Any


_TASK_TEMPLATES = (
    ("set-budget-priorities", "Set budget and priorities", "Confirm the spending limit and the arrangements that matter most.", 90, "high", "planning"),
    ("shortlist-book-venue", "Shortlist and book a venue", "Compare venue options against guest count, access, and location needs.", 75, "high", "venue"),
    ("build-guest-list", "Build the guest list", "Draft the guest list and identify any accessibility or dietary needs.", 60, "medium", "guests"),
    ("confirm-catering", "Confirm catering approach", "Choose a menu direction and confirm dietary requirements with the caterer.", 45, "high", "catering"),
    ("send-invitations", "Send invitations", "Share invitations and a way for guests to respond.", 30, "medium", "guests"),
    ("confirm-vendors", "Confirm vendor arrangements", "Reconfirm timings, responsibilities, and contact details with vendors.", 21, "high", "vendors"),
    ("final-headcount", "Confirm final headcount", "Update the guest count and share it with the venue and caterer.", 7, "high", "guests"),
    ("event-day-run-sheet", "Prepare the event-day run sheet", "Write down the schedule, key contacts, and day-of responsibilities.", 0, "medium", "coordination"),
)


def _parse_date(value: date | str, field: str) -> date:
    if isinstance(value, datetime):
        raise ValueError(f"{field} must be a calendar date, not a datetime.")
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            raise ValueError(f"{field} must use YYYY-MM-DD format.") from None
        if parsed.isoformat() == value:
            return parsed
    raise ValueError(f"{field} must be a date or use YYYY-MM-DD format.")


def _build_tasks(event_day: date, today: date) -> list[dict[str, Any]]:
    tasks = []
    for task_id, title, description, days_before, priority, category in _TASK_TEMPLATES:
        due_day = event_day - timedelta(days=days_before)
        completed = False
        tasks.append(
            {
                "id": task_id,
                "title": title,
                "description": description,
                "due_date": due_day.isoformat(),
                "priority": priority,
                "category": category,
                "completed": completed,
                "status": "overdue" if due_day < today else "pending",
                "system_generated": True,
                "user_edited": False,
            }
        )
    return tasks


def generate_timeline(
    event_date: date | str,
    as_of: date | str | None = None,
) -> dict[str, Any]:
    """Generate planning tasks relative to an event date.

    No new preparation tasks are created for past events. Supplying ``as_of``
    makes deadline and overdue calculations deterministic in tests and callers.
    """
    event_day = _parse_date(event_date, "event_date")
    today = _parse_date(as_of, "as_of") if as_of is not None else date.today()
    if event_day < today:
        return {
            "event_date": event_day.isoformat(),
            "tasks": [],
            "notice": "The event date has passed; no new planning tasks were generated.",
        }
    return {"event_date": event_day.isoformat(), "tasks": _build_tasks(event_day, today), "notice": None}


def reschedule_timeline(
    existing_tasks: Sequence[Mapping[str, Any]],
    new_event_date: date | str,
    as_of: date | str | None = None,
) -> dict[str, Any]:
    """Recalculate generated pending tasks while retaining completed and edited tasks."""
    if not isinstance(existing_tasks, Sequence) or isinstance(existing_tasks, (str, bytes)):
        raise ValueError("existing_tasks must be a list of task objects.")
    preserved_tasks: list[dict[str, Any]] = []
    existing_by_id: dict[str, dict[str, Any]] = {}
    for task in existing_tasks:
        if not isinstance(task, Mapping):
            raise ValueError("Every existing task must be an object.")
        task_copy = dict(task)
        task_id = task_copy.get("id")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("Every existing task must have a non-empty id.")
        if task_id in existing_by_id:
            raise ValueError(f"Task id '{task_id}' is duplicated.")
        existing_by_id[task_id] = task_copy
        preserved_tasks.append(task_copy)

    generated = generate_timeline(new_event_date, as_of)
    if generated["notice"]:
        return {**generated, "tasks": preserved_tasks}

    updated_tasks: list[dict[str, Any]] = []
    generated_fields = {
        "title",
        "description",
        "due_date",
        "priority",
        "category",
        "completed",
        "status",
        "system_generated",
        "user_edited",
    }
    for new_task in generated["tasks"]:
        previous = existing_by_id.pop(new_task["id"], None)
        if previous is None or previous.get("completed") is True or previous.get("user_edited") is True:
            updated_tasks.append(previous if previous is not None else new_task)
            continue
        updated = dict(previous)
        for field in generated_fields:
            updated[field] = new_task[field]
        updated_tasks.append(updated)

    # Keep custom tasks and any existing tasks from earlier planning versions.
    updated_tasks.extend(existing_by_id.values())
    return {**generated, "tasks": updated_tasks}
