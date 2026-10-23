from typing import Optional
from app.schemas.client import ClientProfile
from app.schemas.insight import Insight
from app.schemas.news import NewsEvent, AnalyticsFragment
from app.schemas.trace import Trace


class _Store:
    def __init__(self):
        self.clients: dict[str, ClientProfile] = {}
        self.events: dict[str, NewsEvent] = {}
        self.analytics: dict[str, AnalyticsFragment] = {}
        self.insights: dict[str, Insight] = {}
        self.traces: dict[str, Trace] = {}
        self.feed_cache: dict[str, list[str]] = {}   # client_id -> [event_id]


store = _Store()


def store_insight(insight: Insight) -> None:
    store.insights[insight.insight_id] = insight


def store_trace(trace: Trace) -> None:
    store.traces[trace.trace_id] = trace


def get_insight(insight_id: str) -> Optional[Insight]:
    return store.insights.get(insight_id)


def get_trace(trace_id: str) -> Optional[Trace]:
    return store.traces.get(trace_id)