# Handoff: что делает Person 1 и что нужно от остальных

## Что уже готово (Person 1)

- FastAPI-сервис: `backend/app/main.py`
- Агент: `backend/app/agent/orchestrator.py` (шаги plan → … → self_check → finalize)
- LLM-клиент с реальным API: `backend/app/agent/llm_client.py`
- Промпты: `backend/app/agent/prompts.py`
- Контракты: `backend/app/schemas/*.py`
- Заглушки для P2/P3: `backend/app/services/*.py`
- API-эндпоинты: `/clients`, `/clients/{id}/feed`, `/insights/generate`, `/insights/{id}`,
  `/insights/{id}/trace`, `/insights/{id}/ask`, `/sources/{id}`, `/system/budget`
- Docker: `Dockerfile`, `docker-compose.yml`
- Тест e2e: `backend/tests/test_e2e.py`

## Что нужно от каждого

### Person 2 — Data / Ranking
Заменить в `backend/app/services/`:
- `client_context.py`
  - `get_profile(client_id) -> ClientProfile | None`
  - `list_profiles() -> list[ClientProfile]`
  - Прочитать `df_Uid_data_hack.csv`, `df_Fid_Uid_link_hack.csv`, `df_Uid_payment_hack.csv`
  - Заполнять поля `ClientProfile` из `schemas/client.py`
  - Ключевые поля: `products` (rko/credit/leasing/deposit/garantii/salary_project/factoring),
    `industry`, `revenue_billion_rub`, `region`, `counterparties`, `ftn_countries`
- `ranking.py`
  - `rank(profile: dict, events: list[dict]) -> list[dict]`
  - Проставлять `relevance_score` (0..1) каждому событию
  - Возвращать отсортированный список

**Не менять** сигнатуры. Агент вызывает их через `agent/tools.py`.

### Person 3 — NLP / RAG
Заменить в `backend/app/services/`:
- `news_pipeline.py`
  - `get_recent_events() -> list[NewsEvent]`
  - `get_event(event_id) -> NewsEvent | None`
  - Парсер новостей из выбранных источников
  - Обогащать поля `industries`, `regions`, `topics`
- `rag.py`
  - `search(query: str, profile: dict, k: int = 4) -> list[dict]`
  - Индекс по аналитике Альфа-Банка (Приложение 2)
  - Возвращать `[{"fragment_id", "doc_title", "excerpt", "url", "topics"}]`

**Не менять** сигнатуры. Агент вызывает их через `agent/tools.py`.

### Person 4 — Frontend
Звать API на `http://localhost:8000`:
- `GET  /clients` — список клиентов
- `GET  /clients/{id}/feed` — лента событий
- `POST /insights/generate?client_id=CL-001[&event_id=NEWS-1]` — генерация
- `GET  /insights/{id}` — карточка инсайта
- `GET  /insights/{id}/trace` — трассировка
- `POST /insights/{id}/ask` — уточняющий вопрос, body: `{"question": "..."}`
- `GET  /sources/{source_id}` — первоисточник
- `GET  /system/budget` — расход токенов

Поля `Insight`: `what_happened`, `why_it_matters`, `consequences` (risk/opportunity),
`actions`, `bank_view`, `based_on`, `client_features_used`, `relevance_score`, `trace_id`.
В каждом `Claim` есть `origin` (`fact` / `bank_analytics` / `ai_inference` / `client_feature`)
и `source_ids`. **Визуально разделить эти origin — критерий приёмки.**

### Person 5 — DevOps / QA
- Запустить: `make up` или `make dev`, `make test`, `make smoke`
- Развернуть на внешнем сервере (Railway/Fly/Render — по бесплатному тарифу)
- Собрать `THIRD_PARTY_NOTICES` (openai, fastapi, uvicorn, pydantic, python-json-logger)
- Проверить `.env` не попал в git (`git check-ignore .env`)
- Зафиксировать commit hash для сдачи

## Переменные окружения

`.env` (не коммитить!), шаблон в `.env.example`.
Значения `LLM_API_KEY` — у Team Lead (Person 1). Ключ **не публиковать в открытых репозиториях**.

## Как локально проверить

```bash
cp .env.example .env       # заполнить LLM_API_KEY
make install
make smoke                # проверит ключ и потратит ~30 токенов
make dev                  # http://localhost:8000/docs
make test                 # e2e на mock