from fastapi import APIRouter, HTTPException
from app.agent import tools
from app.schemas.news import NewsEvent

router = APIRouter()


@router.get("/{client_id}/feed", response_model=list[NewsEvent])
async def get_feed(client_id: str, limit: int = 20):
    profile = await tools.get_client_profile(client_id)
    events = await tools.get_candidate_events(client_id)
    ranked = await tools.rank_events(profile, events)
    return ranked[:limit]