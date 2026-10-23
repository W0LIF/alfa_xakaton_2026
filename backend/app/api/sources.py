from fastapi import APIRouter, HTTPException
from app.schemas.insight import SourceRef
from app.storage import store

router = APIRouter()


@router.get("/{source_id}", response_model=SourceRef)
async def get_source(source_id: str):
    # ищем по инсайтам
    for ins in store.insights.values():
        for src in ins.based_on:
            if src.source_id == source_id:
                return src
    # иначе — по сырым данным
    if source_id in store.events:
        e = store.events[source_id]
        return SourceRef(source_id=e.event_id, kind="news", title=e.title,
                         url=e.source_url, published_at=e.published_at,
                         excerpt=e.summary)
    if source_id in store.analytics:
        a = store.analytics[source_id]
        return SourceRef(source_id=a.fragment_id, kind="bank_analytics",
                         title=a.doc_title, url=a.url, excerpt=a.excerpt)
    raise HTTPException(404, "Source not found")