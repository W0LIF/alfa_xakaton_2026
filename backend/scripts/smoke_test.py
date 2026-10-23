"""
Smoke test для реального API организаторов.
Запуск:  make smoke   или   PYTHONPATH=backend python backend/scripts/smoke_test.py
"""
import asyncio
import sys

from app.agent.llm_client import budget, chat_completion
from app.core.config import settings


async def main() -> int:
    print(f"base_url      : {settings.llm_base_url}")
    print(f"fallback_url  : {settings.llm_base_url_fallback}")
    print(f"model (universal): {settings.llm_model_universal}")
    print(f"api_key       : {settings.llm_api_key[:6]}...{settings.llm_api_key[-4:]}"
          if settings.llm_api_key.startswith("sk-") else "!! ключ не sk-…")
    print(f"llm_mode      : {settings.llm_mode}")

    if not settings.llm_api_key.startswith("sk-"):
        print("\n[FAIL] LLM_API_KEY должен начинаться с 'sk-'. Заполните .env")
        return 2

    if settings.llm_mode != "real":
        print("\n[WARN] LLM_MODE != real — вызов не пойдёт в сеть.")

    try:
        content = await chat_completion(
            system="Ты — короткий помощник. Отвечай одной строкой.",
            user="Скажи 'pong' и укажи текущий год.",
            tier="cheap",
            json_mode=False,
            max_tokens=30,
        )
        print(f"\n[OK] Ответ модели: {content[:200]}")
        print(f"[USAGE] {budget.stats}")
        return 0
    except Exception as e:
        print(f"\n[FAIL] {type(e).__name__}: {e}")
        print(f"[USAGE] {budget.stats}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))