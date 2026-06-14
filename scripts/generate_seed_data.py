"""Generate optional synthetic CRM seed data with an LLM.

The committed fixtures are deterministic and are used by default. This script
is a convenience for regenerating mock data during development when
OPENAI_API_KEY is available.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "backend" / "fixtures" / "seed_data.generated.json"


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. Keeping committed deterministic fixtures.")
        return

    from openai import OpenAI

    client = OpenAI()
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        input=(
            "Generate JSON only for an ecommerce mock CRM with exactly 15 customers. "
            "Each customer needs id, name, email, loyalty_tier, notes, optional fraud_flag, "
            "and 1-2 orders with id, order_date, status, total, and items. Include eligible, "
            "final-sale, over-$500, late, damaged, and fraud-review scenarios."
        ),
        text={"format": {"type": "json_object"}},
    )
    data = json.loads(response.output_text)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
