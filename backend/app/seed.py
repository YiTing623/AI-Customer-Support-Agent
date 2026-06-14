import json
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import text

from . import models
from .database import Base, engine

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def reset_database(db: Session) -> dict:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database(db)
    return {"status": "ok", "customers": db.query(models.Customer).count()}


def seed_database(db: Session) -> None:
    data = json.loads((FIXTURES_DIR / "seed_data.json").read_text())
    policy = (FIXTURES_DIR / "refund_policy.md").read_text()
    db.add(models.PolicyDocument(title="Acme Outfitters Refund Policy", body=policy, version="2026-06"))
    for customer_data in data["customers"]:
        customer = models.Customer(
            id=customer_data["id"],
            name=customer_data["name"],
            email=customer_data["email"],
            loyalty_tier=customer_data["loyalty_tier"],
            fraud_flag=customer_data.get("fraud_flag", False),
            notes=customer_data.get("notes", ""),
        )
        db.add(customer)
        for order_data in customer_data["orders"]:
            order = models.Order(
                id=order_data["id"],
                customer=customer,
                order_date=order_data["order_date"],
                status=order_data.get("status", "delivered"),
                total=order_data["total"],
            )
            db.add(order)
            for item_data in order_data["items"]:
                db.add(
                    models.OrderItem(
                        order=order,
                        sku=item_data["sku"],
                        name=item_data["name"],
                        category=item_data["category"],
                        quantity=item_data.get("quantity", 1),
                        unit_price=item_data["unit_price"],
                        final_sale=item_data.get("final_sale", False),
                    )
                )
    db.commit()


def ensure_seeded(db: Session) -> None:
    Base.metadata.create_all(bind=engine)
    ensure_runtime_schema(db)
    if db.query(models.Customer).count() == 0:
        seed_database(db)


def ensure_runtime_schema(db: Session) -> None:
    columns = {row[1] for row in db.execute(text("PRAGMA table_info(agent_runs)")).fetchall()}
    if columns and "agent_mode" not in columns:
        db.execute(text("ALTER TABLE agent_runs ADD COLUMN agent_mode VARCHAR DEFAULT 'openai'"))
    if columns and "mode_notice" not in columns:
        db.execute(text("ALTER TABLE agent_runs ADD COLUMN mode_notice TEXT DEFAULT ''"))
    db.commit()
