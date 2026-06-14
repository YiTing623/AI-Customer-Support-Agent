from datetime import date

from sqlalchemy.orm import Session

from . import models

TODAY = date(2026, 6, 9)
REFUND_WINDOW_DAYS = 30
ESCALATION_LIMIT = 500.0


def evaluate_refund_rules(db: Session, order_id: str, item_ids: list[int] | None, reason: str) -> dict:
    order = db.get(models.Order, order_id)
    if not order:
        return _decision("denied", 0, "Order was not found.", "lookup", False)

    customer = db.get(models.Customer, order.customer_id)
    if customer and customer.fraud_flag:
        return _decision("escalated", 0, "Customer account has a fraud review flag.", "fraud_review", True)

    selected_items = order.items
    if item_ids:
        selected_items = [item for item in order.items if item.id in item_ids]
    if not selected_items:
        return _decision("denied", 0, "No refundable order items were found.", "item_lookup", False)

    if any(item.final_sale for item in selected_items):
        return _decision("denied", 0, "Final sale items cannot be refunded.", "final_sale", False)

    order_date = date.fromisoformat(order.order_date)
    age_days = (TODAY - order_date).days
    if age_days > REFUND_WINDOW_DAYS:
        return _decision(
            "denied",
            0,
            f"Order is {age_days} days old, outside the {REFUND_WINDOW_DAYS}-day refund window.",
            "refund_window",
            False,
        )

    lowered = reason.lower()
    amount = round(sum(item.quantity * item.unit_price for item in selected_items), 2)
    if any(word in lowered for word in ["damaged", "broken", "defective"]):
        if not any(word in lowered for word in ["photo", "evidence", "picture", "image"]):
            return _decision(
                "escalated",
                0,
                "Damaged-item refunds require evidence before approval.",
                "damage_evidence",
                True,
            )

    if amount > ESCALATION_LIMIT:
        return _decision(
            "escalated",
            amount,
            "Refunds over $500 require human escalation.",
            "high_value",
            True,
        )

    return _decision("approved", amount, "Refund meets the written policy requirements.", "standard_refund", False)


def _decision(decision: str, amount: float, reason: str, rule: str, escalation_required: bool) -> dict:
    return {
        "decision": decision,
        "amount": round(float(amount), 2),
        "reason": reason,
        "policy_rule": rule,
        "escalation_required": escalation_required,
    }
