from app.schemas.news import NewsEvent
from app.storage import store


_MOCK_EVENTS = [
    NewsEvent(
        event_id="NEWS-1",
        title="ЦБ РФ сохранил ключевую ставку на уровне 14% годовых",
        summary="Совет директоров Банка России принял решение сохранить ключевую ставку "
                "на уровне 14,00% годовых. Риторика регулятора стала жёстче.",
        source_name="Банк России",
        source_url="https://cbr.ru/",
        published_at="2026-09-11T13:30:00+03:00",
        industries=["Строительство", "Ритейл"],
        regions=["Россия"],
        topics=["rates", "macro", "regulation"],
    ),
    NewsEvent(
        event_id="NEWS-2",
        title="Мировые цены на золото выросли на 4% за неделю",
        summary="Котировки золота обновили максимум на фоне роста геополитической "
                "напряжённости и спроса на защитные активы.",
        source_name="Bloomberg",
        source_url="https://bloomberg.com/",
        published_at="2026-09-12T10:00:00+03:00",
        industries=["Добыча золота"],
        regions=["Россия"],
        topics=["commodities", "gold"],
    ),
    NewsEvent(
        event_id="NEWS-3",
        title="Инфляция в РФ в августе составила 8,4% год к году",
        summary="Росстат опубликовал данные по инфляции. Продовольственная инфляция "
                "ускорилась до 9,1%.",
        source_name="Росстат",
        source_url="https://rosstat.gov.ru/",
        published_at="2026-09-10T16:00:00+03:00",
        industries=["Ритейл"],
        regions=["Россия"],
        topics=["inflation", "macro", "consumer"],
    ),
    NewsEvent(
        event_id="NEWS-4",
        title="Правительство повысило пошлины на импорт строительных материалов",
        summary="Пошлины на ряд строительных материалов повышены на 5–8% с 1 октября.",
        source_name="Правительство РФ",
        source_url="https://government.ru/",
        published_at="2026-09-13T09:00:00+03:00",
        industries=["Строительство"],
        regions=["Россия"],
        topics=["regulation", "construction", "imports"],
    ),
    NewsEvent(
        event_id="NEWS-5",
        title="Запущен новый механизм льготного кредитования МСП",
        summary="Программа распространяется на компании с выручкой до 2 млрд рублей.",
        source_name="Минэкономразвития",
        source_url="https://economy.gov.ru/",
        published_at="2026-09-14T11:00:00+03:00",
        industries=["Ритейл", "Строительство"],
        regions=["Россия"],
        topics=["regulation", "credit", "sme"],
    ),
]


async def get_recent_events() -> list[NewsEvent]:
    for e in _MOCK_EVENTS:
        store.events[e.event_id] = e
    return list(_MOCK_EVENTS)


async def get_event(event_id: str) -> NewsEvent | None:
    return store.events.get(event_id)