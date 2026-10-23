from app.schemas.news import AnalyticsFragment
from app.storage import store


_MOCK_ANALYTICS = [
    AnalyticsFragment(
        fragment_id="AN-KEY-RATE-2026",
        doc_title="Ключевая ставка ЦБ РФ: ставка без изменения на 14,0%, риторика стала жестче",
        excerpt="Совет директоров ЦБ РФ принял решение сохранить ключевую ставку на уровне "
                "14,0% годовых. Риторика регулятора ужесточилась: инфляционные риски "
                "остаются значительными. Пауза в цикле смягчения ДКП может продлиться "
                "дольше, чем ожидалось.",
        topics=["rates", "macro"],
    ),
    AnalyticsFragment(
        fragment_id="AN-INFLATION-AUG-2026",
        doc_title="Инфляция 25–31 августа: основные выводы",
        excerpt="Годовая инфляция в августе составила 8,4%. Продовольственная инфляция "
                "ускорилась до 9,1% — это окажет давление на маржу ритейлеров и потребует "
                "корректировки цен.",
        topics=["inflation", "consumer"],
    ),
    AnalyticsFragment(
        fragment_id="AN-GOLD-AUG-2026",
        doc_title="Обзор рынка золота, август 2026",
        excerpt="Золото продолжает укрепляться на фоне глобальной неопределённости. "
                "Российские золотодобытчики выигрывают от роста цен — маржинальность "
                "сектора достигла исторических максимумов.",
        topics=["commodities", "gold"],
    ),
    AnalyticsFragment(
        fragment_id="AN-MACRO-2026",
        doc_title="Макростатистика 7М26: данные по рынку труда не подтверждают охлаждения",
        excerpt="Рынок труда остаётся напряжённым, заработные платы растут быстрее "
                "инфляции. Это поддерживает потребительский спрос, но ограничивает "
                "возможности ЦБ по снижению ставки.",
        topics=["macro", "rates"],
    ),
]


async def search(query: str, profile: dict, k: int = 4) -> list[dict]:
    """Простейший поиск по topics. Person 3 заменит на RAG с эмбеддингами."""
    for a in _MOCK_ANALYTICS:
        store.analytics[a.fragment_id] = a

    q = query.lower()
    scored = []
    for a in _MOCK_ANALYTICS:
        score = 0
        for t in a.topics:
            if t in q:
                score += 2
        if any(w in a.doc_title.lower() for w in q.split() if len(w) > 3):
            score += 1
        if score > 0:
            scored.append((score, a))

    if not scored:
        # fallback — вернём макро-аналитику
        return [a.model_dump() for a in _MOCK_ANALYTICS[:2]]

    scored.sort(key=lambda x: x[0], reverse=True)
    return [a.model_dump() for _, a in scored[:k]]