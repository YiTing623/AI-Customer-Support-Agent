# AI Customer Support Refund Agent

A local full-stack demo of an AI-assisted refund support workflow for e-commerce. Customers can chat about refund requests, while an admin trace panel shows the agent's tool calls, retries, policy reasoning, token usage, latency, and final decision.

The app runs in two modes:

- **OpenAI mode** when `OPENAI_API_KEY` is configured. The backend uses the OpenAI Responses API with function calling.
- **Deterministic demo mode** when `OPENAI_API_KEY` is missing or OpenAI mode fails. The same API and UI still work end to end with deterministic refund logic and explicit mode notices.

## Features

- FastAPI backend with SQLite persistence
- React/Vite customer chat and admin trace dashboard
- Seeded synthetic CRM with customers, orders, refund policy, and edge cases
- Tool-backed refund flow for customer lookup, order lookup, and policy retrieval
- Deterministic backend policy enforcement for approvals, denials, and escalations
- Trace history with tool input/output, retries, token usage, estimated cost, and latency
- Prompt-injection resistant demo scenario for final-sale items

## Project Structure

```text
backend/
  app/                  FastAPI app, agent loop, tools, policy rules, database models
  fixtures/             Seed CRM data and refund policy
  tests/                Backend acceptance tests
frontend/
  src/                  React SPA
scripts/
  generate_seed_data.py Optional LLM-assisted seed-data generator
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- Optional: an OpenAI API key for live Responses API tool-calling mode

## Quick Start

Start the backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Start the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5174`.

The frontend proxies API calls to the backend during development. Keep the backend running on `http://127.0.0.1:8000`.

## OpenAI Mode

To use the live OpenAI Responses API agent:

```bash
export OPENAI_API_KEY=your_key_here
uvicorn app.main:app --reload --port 8000
```

Optional environment variables:

```bash
export OPENAI_MODEL=gpt-5.4-mini
export OPENAI_INPUT_COST_PER_1M_TOKENS=0.75
export OPENAI_OUTPUT_COST_PER_1M_TOKENS=4.50
export OPENAI_CACHED_INPUT_COST_PER_1M_TOKENS=0.075
```

The backend requires `openai>=1.88.0,<2` for the Responses API client. If you see an error like `'OpenAI' object has no attribute 'responses'`, reinstall backend dependencies:

```bash
pip install -r requirements.txt
```

## Deterministic Demo Mode

`OPENAI_API_KEY` is optional. Without it, the app still starts and the same chat, trace, and API flows work locally.

In deterministic demo mode:

- `/health`, `/api/chat`, run details, the chat UI, and the admin trace identify that LLM mode is disabled.
- Refund decisions are produced by deterministic backend code.
- Token usage is zero and estimated LLM cost remains `$0.0000`.

This makes the project easy to review without external credentials.

## Demo Scenarios

Use the preset buttons in the chat UI:

- **Approve**: eligible refund inside the 30-day window
- **Final sale**: prompt-injection attempt against a final-sale item
- **Over $500**: high-value refund escalated to a human
- **Late**: order outside the refund window
- **Retry trace**: missing order number causes a failed lookup, then retry via email/order history

Preset scenarios send an explicit customer identity with each `/api/chat` request. Free-form chat uses the currently selected customer identity and goes through the same API path.

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Backend status, seeded customer count, and current agent mode |
| `POST` | `/api/chat` | Run the refund agent for a customer message |
| `GET` | `/api/runs` | List recent agent runs |
| `GET` | `/api/runs/{run_id}` | Get a run with detailed trace steps and tool calls |
| `GET` | `/api/customers/{customer_id}` | Get seeded customer profile and orders |
| `GET` | `/api/orders/{order_id}` | Get seeded order details and line items |
| `POST` | `/api/seed/reset` | Reset the local SQLite database to fixture data |

Example chat request:

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-session-1",
    "customer_email": "mia.chen@example.com",
    "customer_message": "I want a refund for order ORD-1001"
  }'
```

Example response:

```json
{
  "run_id": 1,
  "assistant_message": "Refund approved...",
  "decision": "approved",
  "model": "gpt-5.4-mini",
  "agent_mode": "deterministic_demo",
  "mode_notice": "LLM mode disabled: OPENAI_API_KEY is missing. Running deterministic demo mode."
}
```

`customer_email` is preferred when present. If omitted, the backend preserves demo fallback behavior such as resolving identity from the message text.

## Seed Data

The backend seeds the SQLite database on startup from `backend/fixtures/seed_data.json` and `backend/fixtures/refund_policy.md`.

Reset seed data:

```bash
curl -X POST http://127.0.0.1:8000/api/seed/reset
```

## Tests

Run backend tests:

```bash
cd backend
pytest
```

Build the frontend:

```bash
cd frontend
npm run build
```

## Policy Enforcement

The LLM can request tools and draft responses, but final refund enforcement lives in deterministic backend code. Customer language cannot override final-sale restrictions, refund windows, fraud flags, missing evidence checks, or over-$500 escalation rules.
