from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import session_scope
from app.logic.budget_engine import summarize_actual_spending
from app.logic.expense_validation import validate_expense_payload
from app.models import Event, Expense


expenses_bp = Blueprint("expenses", __name__)


def _expense_response(expense: Expense) -> dict:
    return {
        "id": expense.id,
        "event_id": expense.event_id,
        "category": expense.category,
        "description": expense.description,
        "amount": float(expense.amount),
        "spent_on": expense.spent_on.isoformat(),
        "currency": "INR",
    }


def _budget_response(event: Event, expenses: list[Expense]) -> dict:
    summary = summarize_actual_spending(
        event.total_budget,
        [{"category": expense.category, "amount": expense.amount} for expense in expenses],
    )
    return {
        "event_id": event.id,
        "currency": summary["currency"],
        "total_budget": float(summary["budget"]),
        "actual_spend": float(summary["actual_total"]),
        "category_totals": {
            category: float(amount) for category, amount in summary["category_totals"].items()
        },
        "remaining_balance": float(summary["remaining_balance"]),
        "over_budget": summary["over_budget"],
        "overspend_amount": float(summary["overspend_amount"]),
        "percent_used": float(summary["percent_used"]),
    }


@expenses_bp.post("/<int:event_id>/expenses")
def create_expense(event_id: int):
    payload = request.get_json(silent=True)
    validated, errors = validate_expense_payload(payload)
    if errors:
        return jsonify({"error": "Expense details are invalid.", "details": errors}), 400

    expense_data = dict(validated)
    try:
        with session_scope(current_app) as session:
            event = session.get(Event, event_id)
            if event is None:
                return jsonify({"error": "Event not found."}), 404
            expense = Expense(event_id=event_id, **expense_data)
            session.add(expense)
            session.flush()
            expenses = session.scalars(
                select(Expense).where(Expense.event_id == event_id).order_by(Expense.spent_on, Expense.id)
            ).all()
            response = {
                "expense": _expense_response(expense),
                "budget": _budget_response(event, expenses),
            }
    except SQLAlchemyError:
        current_app.logger.error("Database error while recording expense.")
        return jsonify({"error": "Unable to save this expense."}), 500
    return jsonify(response), 201


@expenses_bp.get("/<int:event_id>/expenses")
def list_expenses(event_id: int):
    try:
        with session_scope(current_app) as session:
            event = session.get(Event, event_id)
            if event is None:
                return jsonify({"error": "Event not found."}), 404
            expenses = session.scalars(
                select(Expense).where(Expense.event_id == event_id).order_by(Expense.spent_on, Expense.id)
            ).all()
            response = {
                "expenses": [_expense_response(expense) for expense in expenses],
                "budget": _budget_response(event, expenses),
            }
    except SQLAlchemyError:
        current_app.logger.error("Database error while loading expenses.")
        return jsonify({"error": "Unable to load expenses."}), 500
    return jsonify(response), 200


@expenses_bp.get("/<int:event_id>/budget")
def get_budget_summary(event_id: int):
    try:
        with session_scope(current_app) as session:
            event = session.get(Event, event_id)
            if event is None:
                return jsonify({"error": "Event not found."}), 404
            expenses = session.scalars(
                select(Expense).where(Expense.event_id == event_id)
            ).all()
            response = _budget_response(event, expenses)
    except SQLAlchemyError:
        current_app.logger.error("Database error while calculating budget summary.")
        return jsonify({"error": "Unable to calculate this budget."}), 500
    return jsonify(response), 200
