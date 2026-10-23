from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Any


def _money(value: Any, field: str, *, allow_zero: bool = True) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{field} must be a number in INR.")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a valid number in INR.") from None
    if not amount.is_finite() or amount < 0 or (not allow_zero and amount == 0):
        qualifier = "greater than zero" if not allow_zero else "zero or greater"
        raise ValueError(f"{field} must be {qualifier} in INR.")
    return amount


def allocate_budget(
    total_budget: int | float | Decimal,
    category_estimates: Mapping[str, int | float | Decimal],
    priorities: Sequence[str] = (),
    minimums: Mapping[str, int | float | Decimal] | None = None,
) -> dict[str, Any]:
    """Trim lower-priority estimates first and report any impossible minimums.

    Priorities are ordered from highest to lowest. A minimum protects a required
    amount for a category; it may be zero when that category can be removed.
    Monetary arithmetic uses Decimal so reductions and balances remain exact.
    """
    budget = _money(total_budget, "total_budget", allow_zero=False)
    if not isinstance(category_estimates, Mapping):
        raise ValueError("category_estimates must be a mapping of category names to amounts.")
    if not isinstance(priorities, Sequence) or isinstance(priorities, (str, bytes)):
        raise ValueError("priorities must be an ordered list of category names.")
    if minimums is not None and not isinstance(minimums, Mapping):
        raise ValueError("minimums must be a mapping of category names to amounts.")

    estimates: dict[str, Decimal] = {}
    for name, amount in category_estimates.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Every category must have a non-empty name.")
        category = name.strip()
        if category in estimates:
            raise ValueError(f"Category name '{category}' is duplicated after trimming whitespace.")
        estimates[category] = _money(amount, f"estimate for {category}")

    normalized_priorities: list[str] = []
    for name in priorities:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Each priority must be a non-empty category name.")
        category = name.strip()
        if category not in estimates:
            raise ValueError(f"Priority '{category}' does not match an estimated category.")
        if category in normalized_priorities:
            raise ValueError(f"Priority '{category}' is listed more than once.")
        normalized_priorities.append(category)

    normalized_minimums: dict[str, Decimal] = {}
    for name, amount in (minimums or {}).items():
        if not isinstance(name, str) or name.strip() not in estimates:
            raise ValueError(f"Minimum '{name}' does not match an estimated category.")
        category = name.strip()
        minimum = _money(amount, f"minimum for {category}")
        if minimum > estimates[category]:
            raise ValueError(f"Minimum for {category} cannot exceed its estimate.")
        normalized_minimums[category] = minimum

    allocations = dict(estimates)
    minimums_by_category = {
        category: normalized_minimums.get(category, Decimal("0"))
        for category in estimates
    }
    requested_total = sum(estimates.values(), Decimal("0"))
    shortfall = max(Decimal("0"), requested_total - budget)

    prioritized = set(normalized_priorities)
    reduction_order = [category for category in estimates if category not in prioritized]
    reduction_order.extend(reversed(normalized_priorities))
    reductions: dict[str, Decimal] = {}

    for category in reduction_order:
        if shortfall == 0:
            break
        reducible = allocations[category] - minimums_by_category[category]
        reduction = min(reducible, shortfall)
        if reduction > 0:
            allocations[category] -= reduction
            reductions[category] = reduction
            shortfall -= reduction

    allocated_total = sum(allocations.values(), Decimal("0"))
    remaining_balance = budget - allocated_total
    feasible = remaining_balance >= 0
    overspend_amount = max(Decimal("0"), -remaining_balance)

    trade_offs = [
        {
            "category": category,
            "reduction": amount,
            "explanation": "Reduced this estimate before higher-priority categories.",
        }
        for category, amount in reductions.items()
    ]
    if feasible and trade_offs:
        explanation = "Lower-priority estimates were reduced to fit the budget."
    elif feasible:
        explanation = "All estimates fit within the budget."
    else:
        explanation = (
            f"Required minimums exceed the budget by ₹{overspend_amount}. "
            "Reduce a requirement or increase the budget."
        )

    return {
        "currency": "INR",
        "budget": budget,
        "requested_total": requested_total,
        "allocations": allocations,
        "allocated_total": allocated_total,
        "remaining_balance": remaining_balance,
        "reductions": reductions,
        "trade_offs": trade_offs,
        "feasible": feasible,
        "overspend_amount": overspend_amount,
        "explanation": explanation,
    }


def summarize_actual_spending(
    total_budget: int | float | Decimal,
    expenses: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compare persisted actual expenses with an event's total budget."""
    budget = _money(total_budget, "total_budget", allow_zero=False)
    if not isinstance(expenses, Sequence) or isinstance(expenses, (str, bytes)):
        raise ValueError("expenses must be a list of expense objects.")

    category_totals: dict[str, Decimal] = {}
    for expense in expenses:
        if not isinstance(expense, Mapping):
            raise ValueError("Every expense must be an object.")
        category = expense.get("category")
        if not isinstance(category, str) or not category.strip():
            raise ValueError("Every expense must have a category.")
        amount = _money(expense.get("amount"), f"expense for {category}", allow_zero=False)
        category = category.strip()
        category_totals[category] = category_totals.get(category, Decimal("0")) + amount

    actual_total = sum(category_totals.values(), Decimal("0"))
    remaining_balance = budget - actual_total
    return {
        "currency": "INR",
        "budget": budget,
        "actual_total": actual_total,
        "category_totals": category_totals,
        "remaining_balance": remaining_balance,
        "over_budget": remaining_balance < 0,
        "overspend_amount": max(Decimal("0"), -remaining_balance),
        "percent_used": (actual_total / budget * Decimal("100")).quantize(Decimal("0.01")),
    }
