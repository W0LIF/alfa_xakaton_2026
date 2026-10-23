from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.llm_client import budget
from app.api import clients, feed, insights, sources
from app.core.config import settings

app = FastAPI(title="Alfa News Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

app.include_router(clients.router, prefix="/clients", tags=["clients"])
app.include_router(feed.router, prefix="/clients", tags=["feed"])
app.include_router(insights.router, prefix="/insights", tags=["insights"])
app.include_router(sources.router, prefix="/sources", tags=["sources"])


@app.get("/health")
def health():
    return {"ok": True, "llm_mode": settings.llm_mode}


@app.get("/system/budget")
def system_budget():
    """Текущий расход токенов (in-memory). Полезно для контроля 500₽/день."""
    return budget.stats