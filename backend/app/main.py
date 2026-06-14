import json

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, selectinload

from . import models
from .agent import run_agent
from .database import get_db
from .mode import current_agent_mode
from .schemas import AgentRunOut, AgentStepOut, ChatRequest, ChatResponse, ToolCallOut
from .seed import ensure_seeded, reset_database

app = FastAPI(title="AI Customer Support Refund Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    db = next(get_db())
    try:
        ensure_seeded(db)
    finally:
        db.close()


@app.get("/health")
def health(db: Session = Depends(get_db)):
    ensure_seeded(db)
    mode, notice = _agent_mode()
    return {"status": "ok", "customers": db.query(models.Customer).count(), "agent_mode": mode, "mode_notice": notice}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    ensure_seeded(db)
    run = run_agent(db, payload.session_id, payload.customer_message)
    return ChatResponse(
        run_id=run.id,
        assistant_message=run.assistant_message,
        decision=run.decision,
        model=run.model,
        agent_mode=run.agent_mode,
        mode_notice=run.mode_notice,
    )


@app.get("/api/runs", response_model=list[AgentRunOut])
def list_runs(db: Session = Depends(get_db)):
    runs = (
        db.query(models.AgentRun)
        .options(selectinload(models.AgentRun.steps).selectinload(models.AgentStep.tool_calls))
        .order_by(models.AgentRun.created_at.desc())
        .limit(25)
        .all()
    )
    return [_serialize_run(run, include_steps=False) for run in runs]


@app.get("/api/runs/{run_id}", response_model=AgentRunOut)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = (
        db.query(models.AgentRun)
        .options(selectinload(models.AgentRun.steps).selectinload(models.AgentStep.tool_calls))
        .filter(models.AgentRun.id == run_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return _serialize_run(run, include_steps=True)


@app.get("/api/customers/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(models.Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "loyalty_tier": customer.loyalty_tier,
        "fraud_flag": customer.fraud_flag,
        "orders": [{"id": order.id, "order_date": order.order_date, "total": order.total} for order in customer.orders],
    }


@app.get("/api/orders/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = db.get(models.Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "order_date": order.order_date,
        "total": order.total,
        "items": [
            {
                "id": item.id,
                "sku": item.sku,
                "name": item.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "final_sale": item.final_sale,
            }
            for item in order.items
        ],
    }


@app.post("/api/seed/reset")
def seed_reset(db: Session = Depends(get_db)):
    return reset_database(db)


def _serialize_run(run: models.AgentRun, include_steps: bool) -> AgentRunOut:
    steps = [_serialize_step(step) for step in sorted(run.steps, key=lambda item: item.id)] if include_steps else []
    return AgentRunOut(
        id=run.id,
        session_id=run.session_id,
        customer_message=run.customer_message,
        assistant_message=run.assistant_message,
        decision=run.decision,
        model=run.model,
        agent_mode=run.agent_mode,
        mode_notice=run.mode_notice,
        token_input=run.token_input,
        token_output=run.token_output,
        estimated_cost=run.estimated_cost,
        latency_ms=run.latency_ms,
        created_at=run.created_at,
        steps=steps,
    )


def _serialize_step(step: models.AgentStep) -> AgentStepOut:
    return AgentStepOut(
        id=step.id,
        step_type=step.step_type,
        title=step.title,
        status=step.status,
        summary=step.summary,
        retry_count=step.retry_count,
        latency_ms=step.latency_ms,
        token_input=step.token_input,
        token_output=step.token_output,
        created_at=step.created_at,
        tool_calls=[
            ToolCallOut(
                id=call.id,
                tool_name=call.tool_name,
                arguments=_json(call.arguments_json),
                output=_json(call.output_json),
                error=call.error,
                latency_ms=call.latency_ms,
            )
            for call in step.tool_calls
        ],
    )


def _json(value: str):
    try:
        return json.loads(value)
    except Exception:
        return value


def _agent_mode() -> tuple[str, str]:
    return current_agent_mode()
