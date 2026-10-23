from pydantic import BaseModel, Field


class NewsEvent(BaseModel):
    event_id: str
    title: str
    summary: str
    body: str = ""
    source_name: str
    source_url: str | None = None
    published_at: str
    industries: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)   # "rates", "regulation", "commodities"
    relevance_score: float = 0.0                       # заполняет Person 2


class AnalyticsFragment(BaseModel):
    fragment_id: str
    doc_title: str
    excerpt: str
    url: str | None = None
    topics: list[str] = Field(default_factory=list)