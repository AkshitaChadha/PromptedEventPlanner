from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


MAX_EXPENSE_AMOUNT = Decimal("9999999999999999.99")
ALLOWED_FIELDS = {"category", "description", "amount", "spent_on"}


def validate_expense_payload(payload: Any) -> tuple[dict[str, Any] | None, dict[str, str]]:
    if not isinstance(payload, dict):
        return None, {"_": "Request body must be a JSON object."}

    errors: dict[str, str] = {}
    extra_fields = set(payload) - ALLOWED_FIELDS
    if extra_fields:
        errors["_"] = "Remove unsupported fields from the request."

    category = payload.get("category")
    if not isinstance(category, str) or not category.strip():
        errors["category"] = "Enter an expense category."
    elif len(category.strip()) > 60:
        errors["category"] = "Enter no more than 60 characters."

    description = payload.get("description", "")
    if not isinstance(description, str):
        errors["description"] = "Enter the expense description as text."
    elif len(description.strip()) > 300:
        errors["description"] = "Enter no more than 300 characters."

    amount = payload.get("amount")
    if isinstance(amount, bool) or not isinstance(amount, (int, float, Decimal)):
        errors["amount"] = "Enter an expense amount greater than zero in INR."
    else:
        try:
            decimal_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            errors["amount"] = "Enter a valid expense amount in INR."
        else:
            if not decimal_amount.is_finite() or decimal_amount <= 0:
                errors["amount"] = "Enter an expense amount greater than zero in INR."
            elif decimal_amount > MAX_EXPENSE_AMOUNT:
                errors["amount"] = "The expense amount exceeds the supported INR limit."
            elif decimal_amount != decimal_amount.quantize(Decimal("0.01")):
                errors["amount"] = "Enter no more than two decimal places for INR amounts."

    spent_on = payload.get("spent_on")
    if not isinstance(spent_on, str):
        errors["spent_on"] = "Enter the expense date in YYYY-MM-DD format."
    else:
        try:
            parsed_date = date.fromisoformat(spent_on)
            if parsed_date.isoformat() != spent_on:
                raise ValueError
        except ValueError:
            errors["spent_on"] = "Enter a valid date in YYYY-MM-DD format."

    if errors:
        return None, errors
    return {
        "category": category.strip(),
        "description": description.strip(),
        "amount": decimal_amount,
        "spent_on": parsed_date,
    }, {}
