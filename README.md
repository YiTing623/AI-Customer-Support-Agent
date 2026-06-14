# AI Customer Support Refund Agent

A local full-stack demo of an AI refund support agent for e-commerce. The app has:

- FastAPI backend with SQLite persistence
- Raw OpenAI Responses API function-calling loop when `OPENAI_API_KEY` is configured
- Deterministic demo mode when `OPENAI_API_KEY` is missing, with explicit API/UI mode notices
- React/Vite customer chat and admin trace dashboard
- Seeded synthetic CRM with 15 customers, order histories, refund policy, and edge-case scenarios

## Project Structure

```text
backend/
  app/                  FastAPI app, agent loop, tools, policy rules
  fixtures/             Deterministic CRM data and refund policy
  tests/                Backend acceptance tests
frontend/
  src/                  React SPA
scripts/
  generate_seed_data.py Optional LLM seed-data generator
```

## Run Locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=your_key_here
uvicorn app.main:app --reload --port 8000
```

`OPENAI_API_KEY` is optional for local demos.

- If `OPENAI_API_KEY` is present, the backend uses the OpenAI Responses API tool-calling agent.
- If `OPENAI_API_KEY` is missing, the backend still starts and the app still works end to end in deterministic demo mode.
- In deterministic demo mode, `/health`, `/api/chat`, run details, the chat UI, and the admin trace all clearly indicate that LLM mode is disabled.

The same `/api/chat` and trace APIs are used in both OpenAI mode and deterministic demo mode, so reviewers can inspect the full product flow without an API key.

Reset seed data:

```bash
curl -X POST http://127.0.0.1:8000/api/seed/reset
```

Run tests:

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Demo Scenarios

Use the preset buttons in the chat:

- `Approve`: eligible refund inside the 30-day window
- `Final sale`: prompt-injection attempt against a final sale item
- `Over $500`: high-value refund escalated to a human
- `Late`: order outside the refund window
- `Retry trace`: missing order number causes a failed lookup, then retry via email/order history

## Loom Walkthrough Script

Keep it under 5 minutes:

1. Show the React UI and explain the chat/admin split.
2. Run `Approve` and point out the agent response.
3. Select the trace and show tool I/O: policy lookup, order lookup, rule evaluation, decision persistence.
4. Run `Retry trace`; expand the failed `lookup_order` step and the retry.
5. Run `Final sale`; call out that prompt injection cannot override deterministic policy.
6. Show token usage, latency, retries, and cost fields.
7. Mention production additions: authentication, payment-provider integration, PII redaction, durable observability, rate limits, eval suite, human review queue, and model-cost monitoring.

## API

- `GET /health`
- `POST /api/chat`
- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/customers/{customer_id}`
- `GET /api/orders/{order_id}`
- `POST /api/seed/reset`

## Notes

The LLM can select and call tools, but final refund enforcement lives in deterministic backend code. Final sale, refund window, fraud flag, missing evidence, and over-$500 escalation rules cannot be overridden by customer language.
