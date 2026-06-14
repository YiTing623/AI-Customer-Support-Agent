from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    customer_email: str | None = None
    customer_message: str


class ChatResponse(BaseModel):
    run_id: int
    assistant_message: str
    decision: str
    model: str
    agent_mode: str
    mode_notice: str


class ToolCallOut(BaseModel):
    id: int
    tool_name: str
    arguments: Any
    output: Any
    error: str
    latency_ms: int


class AgentStepOut(BaseModel):
    id: int
    step_type: str
    title: str
    status: str
    summary: str
    retry_count: int
    latency_ms: int
    token_input: int
    token_output: int
    created_at: datetime
    tool_calls: list[ToolCallOut]


class AgentRunOut(BaseModel):
    id: int
    session_id: str
    customer_message: str
    assistant_message: str
    decision: str
    model: str
    agent_mode: str
    mode_notice: str
    token_input: int
    token_output: int
    estimated_cost: float
    latency_ms: int
    created_at: datetime
    steps: list[AgentStepOut] = []
