from storage.insight_store import (
    init_db, save_insight, get_insight, save_trace, get_traces, list_insights,
)

init_db()

insight = {
    "client_id": "U_000001",
    "event_title": "ЦБ сохранил ставку на 14%",
    "interpretation": "Для компании с кредитами это сигнал о сохранении высокой долговой нагрузки.",
    "risks": ["Рост процентных расходов", "Замедление инвестиций"],
    "opportunities": [],
    "actions": ["Пересмотреть график кредитования"],
    "alfa_view": "Альфа-Банк ожидает сохранения ставки до конца года.",
    "confidence": 0.85,
}

insight_id = save_insight(insight)
save_trace(insight_id, "retrieve", {"query": "ключевая ставка", "hits": 3})
save_trace(insight_id, "extract", {"facts": 5, "risks": 2})

loaded = get_insight(insight_id)
print(f"\n✅ Загружено из БД: {loaded['event_title']}")
print(f"   Риски: {loaded['risks']}")
print(f"   Трассы: {len(get_traces(insight_id))} шагов")
for t in get_traces(insight_id):
    print(f"     - {t['step']}: {t['payload']}")

all_insights = list_insights("U_000001")
print(f"✅ Всего инсайтов у клиента U_000001: {len(all_insights)}")
print(f"\n🎉 Данные успешно сохранены в data/insights.db")