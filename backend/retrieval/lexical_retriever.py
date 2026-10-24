from typing import Optional

from indexing.bm25_index import BM25Index

_index: Optional[BM25Index] = None


def get_index() -> BM25Index:
    """Ленивая загрузка индекса (кэш в памяти процесса)."""
    global _index
    if _index is None:
        _index = BM25Index.load()
    return _index


def retrieve_evidence_lexical(
    query: str,
    k: int = 5,
    source_type: str | None = None,
    min_score: float = 0.0,
) -> list[dict]:
    """
    Лексический (BM25) поиск. Возвращает список чанков.

    Каждый чанк:
      {
        "chunk_id", "text", "score" (0..1), "raw_score" (BM25),
        "source_url", "source_type", "title", "matched_tokens"
      }
    """
    return get_index().search(
        query=query, k=k, source_type=source_type, min_score=min_score
    )


def refresh_index() -> None:
    """Перезагрузить индекс с диска (после scheduler.py)."""
    global _index
    _index = BM25Index.load()