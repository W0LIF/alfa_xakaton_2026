from datetime import datetime, timezone
import uuid

from app.agent import llm_client, prompts
from app.core.logging import agent_logger
from app.schemas.insight import (
    Claim, ClientFeatureUsed, ClaimOrigin, RiskOpportunity, SourceRef,
)
from app.services import client_context, news_pipeline, rag, ranking


# ---- Инструменты, делегируемые Person 2 / Person 3 ----

async def get_client_profile(client_id: str) -> dict:
    profile = await client_context.get_profile(client_id)  # TODO Person 2
    if not profile:
        raise ValueError(f"Клиент {client_id} не найден")
    return profile.model_dump()


async def get_candidate_events(client_id: str) -> list[dict]:
    events = await news_pipeline.get_recent_events()       # TODO Person 3
    return [e.model_dump() for e in events]


async def rank_events(profile: dict, events: list[dict]) -> list[dict]:
    return await ranking.rank(profile, events)             # TODO Person 2


async def search_bank_analytics(query: str, profile: dict, k: int = 4) -> list[dict]:
    return await rag.search(query, profile, k=k)           # TODO Person 3


# ---- LLM-шаги (наши) ----

async def generate_insight(event: dict, profile: dict, analytics: list[dict]) -> dict:
    draft = await llm_client.json_call(
        system=prompts.INSIGHT_SYSTEM,
        user=prompts.insight_user(event, profile, analytics),
        schema_hint=prompts.INSIGHT_SCHEMA_HINT,
        tier="universal",
    )
    return _pack_insight(draft, event, profile, analytics)


async def self_check(insight: dict, event: dict, analytics: list[dict]) -> tuple[bool, list[str]]:
    result = await llm_client.json_call(
        system=prompts.SELF_CHECK_SYSTEM,
        user=prompts.self_check_user(insight, event, analytics),
        schema_hint='{"ok": true|false, "notes": ["..."]}',
        tier="reasoning",
    )
    return bool(result.get("ok", False)), list(result.get("notes", []))


# ---- Сборка структуры Insight из свободного ответа LLM ----

def _pack_insight(draft: dict, event: dict, profile: dict, analytics: list[dict]) -> dict:
    # Строим реестр источников: news + analytics
    sources_registry: dict[str, dict] = {
        event["event_id"]: {
            "source_id": event["event_id"],
            "kind": "news",
            "title": event["title"],
            "url": event.get("source_url"),
            "published_at": event["published_at"],
            "excerpt": event.get("summary", "")[:400],
        },
        profile["client_id"]: {
            "source_id": profile["client_id"],
            "kind": "client_data",
            "title": f"Профиль клиента {profile['name']}",
            "url": None,
            "published_at": None,
            "excerpt": f"Отрасль: {profile['industry']}, продукты: {profile['products']}",
        },
    }
    for a in analytics:
        sources_registry[a["fragment_id"]] = {
            "source_id": a["fragment_id"],
            "kind": "bank_analytics",
            "title": a["doc_title"],
            "url": a.get("url"),
            "published_at": None,
            "excerpt": a["excerpt"][:400],
        }

    used_source_ids: set[str] = set()

    def _claims(items: list[dict]) -> list[Claim]:
        out = []
        for it in items or []:
            sids = [s for s in it.get("source_ids", []) if s in sources_registry]
            used_source_ids.update(sids)
            out.append(Claim(
                text=it["text"],
                origin=ClaimOrigin(it.get("origin", "ai_inference")),
                source_ids=sids,
            ))
        return out

    def _risks(items: list[dict]) -> list[RiskOpportunity]:
        out = []
        for it in items or []:
            sids = [s for s in it.get("source_ids", []) if s in sources_registry]
            used_source_ids.update(sids)
            out.append(RiskOpportunity(
                kind=it["kind"],
                text=it["text"],
                severity=it.get("severity", "medium"),
                origin=ClaimOrigin(it.get("origin", "ai_inference")),
                source_ids=sids,
            ))
        return out

    what_happened = _claims(draft.get("what_happened"))
    why_it_matters = _claims(draft.get("why_it_matters"))
    consequences = _risks(draft.get("consequences"))
    actions = _claims(draft.get("actions"))
    bank_view = _claims(draft.get("bank_view"))

    features = [
        ClientFeatureUsed(**f)
        for f in draft.get("client_features_used", [])
    ]

    # based_on — только реально использованные источники
    based_on = [
        SourceRef(**sources_registry[sid])
        for sid in sorted(used_source_ids)
    ]

    return {
        "insight_id": str(uuid.uuid4()),
        "client_id": profile["client_id"],
        "event_id": event["event_id"],
        "title": draft.get("title", event["title"]),
        "what_happened": [c.model_dump() for c in what_happened],
        "why_it_matters": [c.model_dump() for c in why_it_matters],
        "consequences": [c.model_dump() for c in consequences],
        "actions": [c.model_dump() for c in actions],
        "bank_view": [c.model_dump() for c in bank_view],
        "based_on": [s.model_dump() for s in based_on],
        "client_features_used": [f.model_dump() for f in features],
        "relevance_score": event.get("relevance_score", 0.0),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


# ---- Follow-up ----

async def answer_followup(insight: dict, question: str) -> dict:
    return await llm_client.json_call(
        system=prompts.FOLLOWUP_SYSTEM,
        user=prompts.followup_user(insight, question),
        schema_hint='{"answer": "строка", "source_ids": ["..."]}',
        tier="universal",
    )