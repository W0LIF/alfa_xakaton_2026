from fastapi import APIRouter, HTTPException
from app.agent import tools
from app.agent.orchestrator import InsightAgent
from app.schemas.insight import (
    FollowUpAnswer, FollowUpRequest, Insight,
)
from app.schemas.trace import Trace
from app.storage import get_insight, get_trace

router = APIRouter()
agent = InsightAgent()


@router.post("/generate", response_model=Insight)
async def generate_insight(client_id: str, event_id: str | None = None):
    try:
        return await agent.run(client_id, event_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{insight_id}", response_model=Insight)
async def get_insight_endpoint(insight_id: str):
    ins = get_insight(insight_id)
    if not ins:
        raise HTTPException(404, "Insight not found")
    return ins


@router.get("/{insight_id}/trace", response_model=Trace)
async def get_trace_endpoint(insight_id: str):
    ins = get_insight(insight_id)
    if not ins:
        raise HTTPException(404, "Insight not found")
    tr = get_trace(ins.trace_id)
    if not tr:
        raise HTTPException(404, "Trace not found")
    return tr


@router.post("/{insight_id}/ask", response_model=FollowUpAnswer)
async def ask(insight_id: str, body: FollowUpRequest):
    ins = get_insight(insight_id)
    if not ins:
        raise HTTPException(404, "Insight not found")
    result = await tools.answer_followup(ins.model_dump(), body.question)
    return FollowUpAnswer(
        insight_id=insight_id,
        question=body.question,
        answer=result["answer"],
        source_ids=[s for s in result.get("source_ids", [])
                    if s in {b.source_id for b in ins.based_on}],
    )