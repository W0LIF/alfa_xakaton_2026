"""
LLM-клиент для разрешённых моделей через OpenAI-compatible API.
- Реальные URL и модели — из инструкции организаторов.
- Fallback на запасной base_url.
- Обработка RateLimitError / budget exceeded.
- Mock-режим для тестов без трат токенов.
- Дневной лимит токенов (in-memory, для хакатона достаточно).
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import date

from openai import OpenAI, RateLimitError, APIError, APIConnectionError

from app.core.config import settings
from app.core.logging import llm_logger


class BudgetExceededError(RuntimeError):
    """Организаторы вернули Budget has been exceeded."""


# ---------------------------------------------------------------- budget
class _TokenBudget:
    def __init__(self):
        self._day = date.today()
        self._prompt = 0
        self._completion = 0
        self._calls = 0
        self._lock = asyncio.Lock()

    def _rollover(self):
        today = date.today()
        if today != self._day:
            self._day = today
            self._prompt = 0
            self._completion = 0
            self._calls = 0

    async def charge(self, prompt_tokens: int, completion_tokens: int):
        async with self._lock:
            self._rollover()
            self._prompt += prompt_tokens
            self._completion += completion_tokens
            self._calls += 1
            total = self._prompt + self._completion
            if total > settings.llm_daily_token_limit:
                raise BudgetExceededError(
                    f"Дневной лимит токенов превышен: {total} > "
                    f"{settings.llm_daily_token_limit}. Сброс в 3:00 МСК."
                )

    @property
    def stats(self) -> dict:
        return {
            "day": self._day.isoformat(),
            "calls": self._calls,
            "prompt_tokens": self._prompt,
            "completion_tokens": self._completion,
            "total_tokens": self._prompt + self._completion,
            "limit": settings.llm_daily_token_limit,
            "remaining": max(settings.llm_daily_token_limit - self._prompt - self._completion, 0),
        }


budget = _TokenBudget()


# ---------------------------------------------------------------- clients
_clients: dict[str, OpenAI] = {}


def _get_client(base_url: str) -> OpenAI:
    if base_url not in _clients:
        _clients[base_url] = OpenAI(
            api_key=settings.llm_api_key,
            base_url=base_url,
            timeout=60.0,
        )
    return _clients[base_url]


def _pick_model(tier: str) -> str:
    return {
        "cheap": settings.llm_model_cheap,
        "universal": settings.llm_model_universal,
        "reasoning": settings.llm_model_reasoning,
        "research": settings.llm_model_research,
    }[tier]


def _base_urls() -> list[str]:
    urls = [settings.llm_base_url]
    if settings.llm_base_url_fallback and settings.llm_base_url_fallback != settings.llm_base_url:
        urls.append(settings.llm_base_url_fallback)
    return urls


# ---------------------------------------------------------------- public API
async def chat_completion(
    system: str,
    user: str,
    tier: str = "universal",
    json_mode: bool = True,
    max_tokens: int = 2000,
    temperature: float = 0.2,
) -> str:
    if settings.llm_mode == "mock":
        return _mock_response(system, user)

    model = _pick_model(tier)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    kwargs: dict = dict(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    last_err: Exception | None = None
    for attempt in range(settings.llm_max_retries):
        for base_url in _base_urls():
            client = _get_client(base_url)
            try:
                t0 = time.time()
                resp = await asyncio.to_thread(client.chat.completions.create, **kwargs)
                content = resp.choices[0].message.content or ""
                usage = resp.usage
                pt = usage.prompt_tokens if usage else 0
                ct = usage.completion_tokens if usage else 0
                await budget.charge(pt, ct)
                llm_logger.info(
                    f"llm_ok model={model} url={base_url} "
                    f"prompt={pt} completion={ct} "
                    f"dur_ms={int((time.time()-t0)*1000)}"
                )
                return content
            except RateLimitError as e:
                last_err = e
                msg = str(e)
                llm_logger.warning(f"rate_limit url={base_url}: {msg[:300]}")
                if "budget" in msg.lower():
                    raise BudgetExceededError(
                        "Общий бюджет команды исчерпан. Сброс в 3:00 МСК."
                    )
                await asyncio.sleep(2)
            except APIConnectionError as e:
                last_err = e
                llm_logger.warning(f"connection url={base_url}: {str(e)[:200]}")
                continue
            except APIError as e:
                last_err = e
                llm_logger.warning(f"api_error url={base_url}: {str(e)[:300]}")
                continue

    raise RuntimeError(f"LLM call failed after retries: {last_err}")


def parse_json_safe(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise
        return json.loads(m.group(0))


async def json_call(
    system: str,
    user: str,
    schema_hint: str,
    tier: str = "universal",
) -> dict:
    full_system = system.rstrip() + (
        "\n\nВерни ТОЛЬКО валидный JSON по схеме:\n" + schema_hint
    )
    raw = await chat_completion(full_system, user, tier=tier, json_mode=True)
    return parse_json_safe(raw)


# ---------------------------------------------------------------- mock
def _mock_response(system: str, user: str) -> str:
    if "контролёр качества" in system.lower():
        return json.dumps({"ok": True, "notes": []}, ensure_ascii=False)
    if "уточняющий вопрос" in system.lower():
        return json.dumps({
            "answer": "Событие касается изменения ключевой ставки. Для компании "
                      "с кредитным портфелем это означает сохранение стоимости "
                      "обслуживания долга без выгоды от ожидаемого снижения ставок.",
            "source_ids": ["AN-KEY-RATE-2026"],
        }, ensure_ascii=False)
    return json.dumps({
        "title": "Сохранение ключевой ставки на 14%: давление на заёмщиков сохраняется",
        "what_happened": [
            {"text": "Банк России сохранил ключевую ставку на уровне 14% годовых.",
             "origin": "fact", "source_ids": ["NEWS-1"]}
        ],
        "why_it_matters": [
            {"text": "Компания активно использует кредитные продукты, сохранение ставки "
                     "означает, что стоимость обслуживания долга не снизится.",
             "origin": "client_feature", "source_ids": ["NEWS-1", "CL-001"]}
        ],
        "consequences": [
            {"kind": "risk", "severity": "high",
             "text": "Проценты по кредитной линии останутся высокими.",
             "origin": "ai_inference", "source_ids": ["NEWS-1"]},
            {"kind": "opportunity", "severity": "medium",
             "text": "Можно зафиксировать ставку по текущим условиям.",
             "origin": "ai_inference", "source_ids": ["AN-KEY-RATE-2026"]},
        ],
        "actions": [
            {"text": "Пересмотреть график платежей по кредитам.",
             "origin": "ai_inference", "source_ids": []}
        ],
        "bank_view": [
            {"text": "Аналитики Альфа-Банка отмечают ужесточение риторики ЦБ.",
             "origin": "bank_analytics", "source_ids": ["AN-KEY-RATE-2026"]}
        ],
        "client_features_used": [
            {"name": "CL_PRODUCT_LOA_MARK", "value": "true",
             "why_matters": "Наличие кредитов делает компанию чувствительной к ставке."}
        ],
    }, ensure_ascii=False)