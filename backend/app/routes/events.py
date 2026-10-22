from datetime import date
from decimal import Decimal

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import session_scope
from app.logic.event_validation import validate_event_payload
from app.logic.timeline_engine import generate_timeline
from app.models import Event, Task


events_bp = Blueprint("events", __name__)


def _task_response(task: Task) -> dict:
    today = date.today()
    status = "completed" if task.completed else "overdue" if task.due_date < today else "pending"
    return {
        "id": task.id,
        "key": task.template_key,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date.isoformat(),
        "priority": task.priority,
        "category": task.category,
        "completed": task.completed,
        "status": status,
        "system_generated": task.system_generated,
        "user_edited": task.user_edited,
    }


def _event_response(event: Event) -> dict:
    return {
        "id": event.id,
        "event_name": event.event_name,
        "event_type": event.event_type,
        "event_date": event.event_date.isoformat(),
        "location": event.location,
        "guest_count": event.guest_count,
        "total_budget": float(event.total_budget),
        "currency": "INR",
        "preferred_theme": event.preferred_theme,
        "user_preferences": event.user_preferences,
        "must_have_arrangements": event.must_have_arrangements,
        "things_to_avoid": event.things_to_avoid,
        "budget_priorities": event.budget_priorities,
        "dietary_requirements": event.dietary_requirements,
        "accessibility_requirements": event.accessibility_requirements,
        "tasks": [_task_response(task) for task in event.tasks],
    }


@events_bp.post("")
def create_event():
    payload = request.get_json(silent=True)
    validated, errors = validate_event_payload(payload)
    if errors:
        return jsonify({"error": "Event details are invalid.", "details": errors}), 400

    event_data = dict(validated)
    event_data["event_date"] = date.fromisoformat(event_data["event_date"])
    event_data["total_budget"] = Decimal(str(event_data["total_budget"]))
    try:
        with session_scope(current_app) as session:
            event = Event(**event_data)
            session.add(event)
            session.flush()
            timeline = generate_timeline(event.event_date)
            for task_data in timeline["tasks"]:
                session.add(
                    Task(
                        event_id=event.id,
                        template_key=task_data["id"],
                        title=task_data["title"],
                        description=task_data["description"],
                        due_date=date.fromisoformat(task_data["due_date"]),
                        priority=task_data["priority"],
                        category=task_data["category"],
                        completed=task_data["completed"],
                        system_generated=task_data["system_generated"],
                        user_edited=task_data["user_edited"],
                    )
                )
            session.flush()
            response = _event_response(event)
    except (SQLAlchemyError, ValueError):
        current_app.logger.error("Database error while creating event.")
        return jsonify({"error": "Unable to save this event."}), 500
    return jsonify(response), 201


@events_bp.get("")
def list_events():
    try:
        with session_scope(current_app) as session:
            events = session.scalars(select(Event).order_by(Event.event_date, Event.id)).all()
            response = [_event_response(event) for event in events]
    except SQLAlchemyError:
        current_app.logger.error("Database error while listing events.")
        return jsonify({"error": "Unable to load events."}), 500
    return jsonify({"events": response}), 200


@events_bp.get("/<int:event_id>")
def get_event(event_id: int):
    try:
        with session_scope(current_app) as session:
            event = session.get(Event, event_id)
            if event is None:
                return jsonify({"error": "Event not found."}), 404
            response = _event_response(event)
    except SQLAlchemyError:
        current_app.logger.error("Database error while loading event.")
        return jsonify({"error": "Unable to load this event."}), 500
    return jsonify(response), 200


@events_bp.patch("/<int:event_id>/tasks/<int:task_id>")
def update_task_completion(event_id: int, task_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or set(payload) != {"completed"} or not isinstance(payload["completed"], bool):
        return jsonify({"error": "Provide only a boolean 'completed' value."}), 400
    try:
        with session_scope(current_app) as session:
            task = session.scalar(
                select(Task).where(Task.id == task_id, Task.event_id == event_id)
            )
            if task is None:
                return jsonify({"error": "Task not found for this event."}), 404
            task.completed = payload["completed"]
            response = _task_response(task)
    except SQLAlchemyError:
        current_app.logger.error("Database error while updating task.")
        return jsonify({"error": "Unable to update this task."}), 500
    return jsonify(response), 200
