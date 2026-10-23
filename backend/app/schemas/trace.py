from pydantic import BaseModel, Field


class AgentStep(BaseModel):
    step: int
    action: str
    input: dict = {}
    output_summary: str = ""
    duration_ms: int = 0
    sources_touched: list[str] = Field(default_factory=list)


class Trace(BaseModel):
    trace_id: str
    insight_id: str
    client_id: str
    event_id: str
    steps: list[AgentStep]
    self_check_passed: bool
    self_check_notes: list[str] = Field(default_factory=list)
    llm_tokens_used: int = 0