INSIGHT_SCHEMA_HINT = """{
  "title": "строка",
  "what_happened": [{"text": "строка", "origin": "fact", "source_ids": ["..."]}],
  "why_it_matters": [{"text": "строка", "origin": "client_feature|ai_inference", "source_ids": ["..."]}],
  "consequences": [{"kind": "risk|opportunity", "text": "строка", "severity": "low|medium|high",
                    "origin": "ai_inference|bank_analytics", "source_ids": ["..."]}],
  "actions": [{"text": "строка", "origin": "ai_inference", "source_ids": []}],
  "bank_view": [{"text": "строка", "origin": "bank_analytics", "source_ids": ["..."]}],
  "client_features_used": [{"name": "строка", "value": "строка", "why_matters": "строка"}]
}"""


INSIGHT_SYSTEM = """Ты — старший аналитик Центра отраслевой экспертизы Альфа-Банка.
Задача: сформировать персонализированный бизнес-инсайт для клиента крупного бизнеса.

Жёсткие правила:
1. Каждое утверждение маркируй origin:
   - "fact"            — подтверждено новостью из события,
   - "bank_analytics"  — взято из предоставленных фрагментов аналитики Альфа-Банка,
   - "client_feature"  — прямо опирается на признак из профиля клиента,
   - "ai_inference"    — твой аналитический вывод из фактов и аналитики.
2. Каждое утверждение с origin != "ai_inference" ДОЛЖНО иметь source_ids — список id
   источников, откуда взято утверждение.
3. Не пересказывай новость. Объясняй, что это значит ИМЕННО для этого клиента:
   для его отрасли, продуктов, контрагентов, регионов.
4. Не выдумывай факты, цифры и названия. Если данных нет — не пиши утверждение.
5. Разделяй риски и возможности. Каждому риску/возможности — severity.
6. В bank_view используй ТОЛЬКО аналитику Альфа-Банка.
7. Действия (actions) — конкретные, релевантные клиенту, без общих фраз.
"""


def insight_user(event: dict, profile: dict, analytics: list[dict]) -> str:
    analytics_block = "\n\n".join(
        f"[{a['fragment_id']}] {a['doc_title']}\n{a['excerpt']}"
        for a in analytics
    ) or "—"

    return f"""СОБЫТИЕ [{event['event_id']}]
Заголовок: {event['title']}
Дата: {event['published_at']}
Источник: {event['source_name']}
Кратко: {event.get('summary', '')}
Отрасли: {', '.join(event.get('industries', [])) or '—'}
Темы: {', '.join(event.get('topics', [])) or '—'}

ПРОФИЛЬ КЛИЕНТА [{profile['client_id']}]
Название: {profile['name']}
Отрасль: {profile['industry']} ({profile['okved_code']})
Регион: {profile['region']}, {profile['city']}
Выручка: {profile['revenue_billion_rub']} млрд ₽
Продукты: {profile['products']}
Контрагенты (топ): {profile['counterparties']}
Страны ФТС: {profile['ftn_countries']}

АНАЛИТИКА АЛЬФА-БАНКА
{analytics_block}

Сформируй инсайт строго по JSON-схеме.
"""


SELF_CHECK_SYSTEM = """Ты — контролёр качества аналитических инсайтов Альфа-Банка.
Проверь черновик инсайта и верни вердикт.

Проверяй:
1. Противоречит ли текст фактам новости или аналитике.
2. Есть ли утверждения с origin != "ai_inference" без source_ids.
3. Есть ли галлюцинации — утверждения, которых нет в источниках.
4. Отвечает ли инсайт на вопрос «почему это важно именно для этого клиента».
5. Разделены ли риски и возможности.

Верни JSON: {"ok": true|false, "notes": ["список проблем"]}
"""


def self_check_user(insight: dict, event: dict, analytics: list[dict]) -> str:
    return f"""СОБЫТИЕ:
{event['title']}
{event.get('summary', '')}

ДОСТУПНАЯ АНАЛИТИКА (id): {[a['fragment_id'] for a in analytics]}

ЧЕРНОВИК ИНСАЙТА:
{insight}

Проверь и верни вердикт."""


FOLLOWUP_SYSTEM = """Ты — аналитик, отвечающий на уточняющий вопрос клиента по инсайту.
Отвечай кратко, ссылайся на source_ids из доступных источников.
Если данных нет — честно скажи об этом.
Верни JSON: {"answer": "строка", "source_ids": ["..."]}
"""


def followup_user(insight: dict, question: str) -> str:
    return f"""ИНСАЙТ:
{insight}

ВОПРОС КЛИЕНТА:
{question}
"""