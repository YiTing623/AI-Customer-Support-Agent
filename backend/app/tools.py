import json
import time

from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import models
from .policy import evaluate_refund_rules


def lookup_customer(db: Session, email_or_customer_id: str) -> dict:
    value = email_or_customer_id.strip().lower()
    customer = (
        db.query(models.Customer)
        .filter(or_(models.Customer.id == email_or_customer_id.strip(), models.Customer.email == value))
        .first()
    )
    if not customer:
        raise ValueError("Customer not found")
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "loyalty_tier": customer.loyalty_tier,
        "fraud_flag": customer.fraud_flag,
        "notes": customer.notes,
        "orders": [{"id": order.id, "order_date": order.order_date, "total": order.total} for order in customer.orders],
    }


def lookup_order(db: Session, order_id: str, customer_id: str | None = None) -> dict:
    query = db.query(models.Order).filter(models.Order.id == order_id.strip().upper())
    if customer_id:
        query = query.filter(models.Order.customer_id == customer_id)
    order = query.first()
    if not order:
        raise ValueError("Order not found")
    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "order_date": order.order_date,
        "status": order.status,
        "total": order.total,
        "items": [
            {
                "id": item.id,
                "sku": item.sku,
                "name": item.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "final_sale": item.final_sale,
                "returned": item.returned,
            }
            for item in order.items
        ],
    }


def get_refund_policy(db: Session) -> dict:
    policy = db.query(models.PolicyDocument).first()
    if not policy:
        raise ValueError("Refund policy not seeded")
    return {"title": policy.title, "version": policy.version, "body": policy.body}


def create_refund_decision(
    db: Session,
    request_id: int,
    decision: str,
    amount: float,
    reason: str,
    escalation_required: bool,
    customer_id: str | None = None,
    order_id: str | None = None,
) -> dict:
    request = db.get(models.RefundRequest, request_id)
    if not request:
        raise ValueError("Refund request not found")
    request.decision = decision
    request.amount = amount
    request.reason = reason
    request.escalation_required = escalation_required
    request.customer_id = customer_id
    request.order_id = order_id
    db.commit()
    return {
        "request_id": request.id,
        "decision": request.decision,
        "amount": request.amount,
        "reason": request.reason,
        "escalation_required": request.escalation_required,
    }


def call_tool(db: Session, name: str, arguments: dict) -> dict:
    if name == "lookup_customer":
        return lookup_customer(db, arguments["email_or_customer_id"])
    if name == "lookup_order":
        return lookup_order(db, arguments["order_id"], arguments.get("customer_id"))
    if name == "get_refund_policy":
        return get_refund_policy(db)
    if name == "evaluate_refund_rules":
        return evaluate_refund_rules(db, arguments["order_id"], arguments.get("item_ids"), arguments.get("reason", ""))
    if name == "create_refund_decision":
        return create_refund_decision(db, **arguments)
    raise ValueError(f"Unknown tool: {name}")


def log_tool_call(db: Session, step: models.AgentStep, name: str, arguments: dict, fn):
    started = time.perf_counter()
    try:
        output = fn()
        latency = int((time.perf_counter() - started) * 1000)
        call = models.ToolCall(
            step_id=step.id,
            tool_name=name,
            arguments_json=json.dumps(arguments, indent=2, sort_keys=True),
            output_json=json.dumps(output, indent=2, sort_keys=True),
            latency_ms=latency,
        )
        db.add(call)
        step.latency_ms += latency
        db.commit()
        return output
    except Exception as exc:
        latency = int((time.perf_counter() - started) * 1000)
        call = models.ToolCall(
            step_id=step.id,
            tool_name=name,
            arguments_json=json.dumps(arguments, indent=2, sort_keys=True),
            output_json="{}",
            error=str(exc),
            latency_ms=latency,
        )
        step.status = "error"
        step.latency_ms += latency
        db.add(call)
        db.commit()
        raise
