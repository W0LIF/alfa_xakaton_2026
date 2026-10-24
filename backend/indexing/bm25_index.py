import json
import pickle
from pathlib import Path
from typing import Optional

from rank_bm25 import BM25Okapi

from retrieval.text_normalizer import tokenize


INDEX_PATH = Path("data/bm25_index.pkl")
CHUNKS_PATH = Path("data/processed/chunks.jsonl")


class BM25Index:
    """
    Лёгкий лексический индекс.
    - Строится из chunks.jsonl.
    - Сохраняется в pickle (быстро грузится).
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.bm25: Optional[BM25Okapi] = None
        self.chunks: list[dict] = []
        self.k1 = k1
        self.b = b

    # ---------- построение ----------

    def build(self, chunks: list[dict]) -> None:
        """Строит индекс из списка чанков."""
        if not chunks:
            raise ValueError("Список чанков пуст")

        print(f"[BM25] Токенизация {len(chunks)} чанков...")
        tokenized = []
        for i, c in enumerate(chunks):
            # Для поиска склеиваем title + text: заголовок даёт сильный сигнал
            combined = f"{c.get('title', '')} {c.get('text', '')}"
            tokenized.append(tokenize(combined))
            if (i + 1) % 100 == 0:
                print(f"  → {i + 1}/{len(chunks)}")

        print("[BM25] Построение индекса...")
        self.bm25 = BM25Okapi(tokenized, k1=self.k1, b=self.b)
        self.chunks = chunks
        print(f"[BM25] Готово. Чанков: {len(chunks)}")

    # ---------- сохранение / загрузка ----------

    def save(self, path: Path = INDEX_PATH) -> None:
        if self.bm25 is None:
            raise RuntimeError("Сначала вызовите build()")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "bm25": self.bm25,
                    "chunks": self.chunks,
                    "k1": self.k1,
                    "b": self.b,
                },
                f,
            )
        print(f"[BM25] Сохранено: {path} ({path.stat().st_size / 1e6:.1f} МБ)")

    @classmethod
    def load(cls, path: Path = INDEX_PATH) -> "BM25Index":
        if not path.exists():
            raise FileNotFoundError(
                f"Индекс не найден: {path}. Запустите build_bm25_index.py"
            )
        with open(path, "rb") as f:
            data = pickle.load(f)
        idx = cls(k1=data["k1"], b=data["b"])
        idx.bm25 = data["bm25"]
        idx.chunks = data["chunks"]
        print(f"[BM25] Загружено: {len(idx.chunks)} чанков из {path}")
        return idx

    # ---------- поиск ----------

    def search(
        self,
        query: str,
        k: int = 5,
        source_type: str | None = None,
        min_score: float = 0.0,
    ) -> list[dict]:
        """
        BM25-поиск.
        :param query: поисковый запрос
        :param k: топ-k
        :param source_type: 'news' | 'alfa_analytics' | None
        :param min_score: отсечка (BM25-скор не нормирован, 0 — без отсечки)
        :return: список чанков, отсортированных по релевантности
        """
        if self.bm25 is None:
            raise RuntimeError("Индекс не загружен")

        tokens = tokenize(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)  # numpy array

        # Фильтр по типу источника + отсечка
        indexed = []
        for i, score in enumerate(scores):
            if score < min_score or score <= 0:
                continue
            if source_type and self.chunks[i].get("source_type") != source_type:
                continue
            indexed.append((i, float(score)))

        # Сортируем и берём top-k
        indexed.sort(key=lambda x: x[1], reverse=True)
        top = indexed[:k]

        if not top:
            return []

        # Нормируем скоры в [0,1] по максимуму — удобно для UI и порогов
        max_score = top[0][1] or 1.0
        results = []
        for i, score in top:
            chunk = self.chunks[i]
            results.append({
                "chunk_id": chunk.get("chunk_id", f"idx_{i}"),
                "text": chunk.get("text", ""),
                "score": round(score / max_score, 4),        # нормированный
                "raw_score": round(score, 4),                # BM25 «как есть»
                "doc_id": chunk.get("doc_id", ""),
                "source_type": chunk.get("source_type", ""),
                "source_url": chunk.get("source_url", ""),
                "publisher": chunk.get("publisher", ""),
                "title": chunk.get("title", ""),
                "matched_tokens": _matched_tokens(tokens, chunk),
            })
        return results


def _matched_tokens(query_tokens: list[str], chunk: dict) -> list[str]:
    """Какие токены запроса реально встретились в чанке (для дебага/подсветки)."""
    chunk_tokens = set(tokenize(f"{chunk.get('title', '')} {chunk.get('text', '')}"))
    return [t for t in query_tokens if t in chunk_tokens]