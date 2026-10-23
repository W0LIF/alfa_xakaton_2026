import time
import uuid
from dataclasses import dataclass, field

from app.agent import tools
from app.core.logging import agent_logger, trace_logger
from app.schemas.insight import Insight
from app.schemas.trace import AgentStep, Trace
from app.storage import store_trace, store_insight


MAX_ATTEMPTS = 2


@dataclass
class AgentContext:
    client_id: str
    trace_id: str
    requested_event_id: str | None = None
    client_profile: dict | None = None
    candidate_events: list[dict] = field(default_factory=list)
    ranked_events: list[dict] = field(default_factory=list)
    selected_event: dict | None = None
    analytics: list[dict] = field(default_factory=list)
    insight_payload: dict | None = None
    steps: list[AgentStep] = field(default_factory=list)
    last_self_check_ok: bool = False
    self_check_notes: list[str] = field(default_factory=list)


class InsightAgent:
    async def run(self, client_id: str, event_id: str | None = None) -> Insight:
        ctx = AgentContext(client_id=client_id, trace_id=str(uuid.uuid4()),
                           requested_event_id=event_id)

        self._log_step(ctx, "plan", {"client_id": client_id, "event_id": event_id},
                       "план: профиль → кандидаты → ранжирование → аналитика → генерация → проверка")

        ctx.client_profile = await self._run_step(
            ctx, "get_client_profile", {"client_id": client_id},
            lambda: tools.get_client_profile(client_id),
            summary=lambda r: f"отрасль={r['industry']}, продукты={self._enabled(r['products'])}",
            sources=lambda r: [client_id],
        )

        ctx.candidate_events = await self._run_step(
            ctx, "fetch_candidate_events", {"client_id": client_id},
            lambda: tools.get_candidate_events(client_id),
            summary=lambda r: f"кандидатов={len(r)}",
        )

        ctx.ranked_events = await self._run_step(
            ctx, "rank_events", {"count": len(ctx.candidate_events)},
            lambda: tools.rank_events(ctx.client_profile, ctx.candidate_events),
            summary=lambda r: f"топ-3={[e['event_id'] for e in r[:3]]}",
        )

        ctx.selected_event = self._select_event(ctx)
        if not ctx.selected_event:
            raise ValueError("Нет событий, релевантных клиенту")
        self._log_step(
            ctx, "select_event",
            {"requested": ctx.requested_event_id},
            f"выбрано {ctx.selected_event['event_id']}, "
            f"relevance={ctx.selected_event.get('relevance_score')}",
        )

        for attempt in range(1, MAX_ATTEMPTS + 1):
            ctx.analytics = await self._run_step(
                ctx, "retrieve_bank_analytics",
                {"query": ctx.selected_event["title"], "attempt": attempt},
                lambda: tools.search_bank_analytics(
                    ctx.selected_event["title"], ctx.client_profile),
                summary=lambda r: f"фрагментов={len(r)}",
                sources=lambda r: [a["fragment_id"] for a in r],
            )

            if not ctx.analytics and attempt == 1:
                self._log_step(ctx, "adapt", {},
                               "аналитика не найдена, повтор с расширенным запросом")
                ctx.analytics = await self._run_step(
                    ctx, "retrieve_bank_analytics_broad",
                    {"query": " ".join(ctx.selected_event.get("topics", []))},
                    lambda: tools.search_bank_analytics(
                        " ".join(ctx.selected_event.get("topics", [])) or "макроэкономика",
                        ctx.client_profile,
                    ),
                    summary=lambda r: f"фрагментов={len(r)}",
                    sources=lambda r: [a["fragment_id"] for a in r],
                )

            ctx.insight_payload = await self._run_step(
                ctx, "generate_insight", {"attempt": attempt},
                lambda: tools.generate_insight(
                    ctx.selected_event, ctx.client_profile, ctx.analytics),
                summary=lambda r: f"claims="
                    f"{sum(len(r[k]) for k in ['what_happened','why_it_matters','bank_view'])}",
                sources=lambda r: [s["source_id"] for s in r["based_on"]],
            )

            ok, notes = await self._run_step(
                ctx, "self_check", {"attempt": attempt},
                lambda: tools.self_check(
                    ctx.insight_payload, ctx.selected_event, ctx.analytics),
                summary=lambda r: f"ok={r[0]}, notes={len(r[1])}",
            )
            ctx.last_self_check_ok = ok
            ctx.self_check_notes = notes
            if ok:
                break
            agent_logger.warning(f"self_check failed, retry: {notes}")

        insight = self._build_insight(ctx)
        store_insight(insight)

        trace = Trace(
            trace_id=ctx.trace_id,
            insight_id=insight.insight_id,
            client_id=ctx.client_id,
            event_id=insight.event_id,
            steps=ctx.steps,
            self_check_passed=ctx.last_self_check_ok,
            self_check_notes=ctx.self_check_notes,
        )
        store_trace(trace)
        trace_logger.info(trace.model_dump_json())
        return insight

    # ---- helpers ----

    def _select_event(self, ctx: AgentContext) -> dict | None:
        if ctx.requested_event_id:
            for e in ctx.ranked_events:
                if e["event_id"] == ctx.requested_event_id:
                    return e
        return ctx.ranked_events[0] if ctx.ranked_events else None

    def _build_insight(self, ctx: AgentContext) -> Insight:
        p = ctx.insight_payload
        return Insight(
            insight_id=p["insight_id"],
            client_id=p["client_id"],
            event_id=p["event_id"],
            title=p["title"],
            what_happened=p["what_happened"],
            why_it_matters=p["why_it_matters"],
            consequences=p["consequences"],
            actions=p["actions"],
            bank_view=p["bank_view"],
            based_on=p["based_on"],
            client_features_used=p["client_features_used"],
            relevance_score=p["relevance_score"],
            created_at=p["created_at"],
            trace_id=ctx.trace_id,
        )

    async def _run_step(self, ctx, action, input_, fn, summary=None, sources=None):
        """Безопасно выполняет шаг и всегда пишет в trace, даже при исключении."""
        t0 = time.time()
        result = None
        error: Exception | None = None
        try:
            result = await fn()
            return result
        except Exception as e:
            error = e
            raise
        finally:
            dur = int((time.time() - t0) * 1000)
            if error is not None:
                summary_str = f"ERROR {type(error).__name__}: {str(error)[:120]}"
                src_list: list[str] = []
            else:
                try:
                    summary_str = summary(result) if (summary and result is not None) else ""
                except Exception:
                    summary_str = ""
                try:
                    src_list = sources(result) if (sources and result is not None) else []
                except Exception:
                    src_list = []
            ctx.steps.append(AgentStep(
                step=len(ctx.steps) + 1,
                action=action,
                input=input_,
                output_summary=summary_str,
                duration_ms=dur,
                sources_touched=src_list,
            ))

    def _log_step(self, ctx, action, input_, summary):
        ctx.steps.append(AgentStep(
            step=len(ctx.steps) + 1,
            action=action,
            input=input_,
            output_summary=summary,
            duration_ms=0,
        ))

    @staticmethod
    def _enabled(products: dict) -> list[str]:
        return [k for k, v in products.items() if v]