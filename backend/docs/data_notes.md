# Данные и персонализация

## 1. Синтетические данные
Сгенерированы скриптом `generate_synthetic.py` (seed=42).
- `df_Uid_data_hack.csv` — компании (400 шт.)
- `df_Fid_Uid_link_hack.csv` — связи с физлицами (842 шт.)
- `df_Uid_payment_hack.csv` — платежи (2672 шт.)
- `demo_clients.json` — ID демо-клиентов A, B, C.

Перегенерация:
```bash
python backend/data/generate_synthetic.py --seed 42
```

## 2. Профиль клиента (build_profile.py)
Собирает JSON-профиль по ID компании (SYNTHETIC_U).
Возвращает: отрасль, масштаб, банковские продукты, связи, контрагентов.
Считает personalization_weights (веса тем новостей, сумма = 1) на основе продуктов и отрасли.

Пример:
``` bash
python
from src.context.build_profile import build_profile
profile = build_profile("U_000001")
```

## 3. Ранжирование событий (rank.py)
Оценивает важность новости для клиента (от 0 до 1) и возвращает причины.

Суммирует веса тем новости из профиля клиента.

Добавляет баллы за совпадение отрасли, региона и контрагентов.

Пример:
``` bash
python
from src.context.rank import score_event
score, reasons = score_event(
    event_topics=["interest_rate"], 
    event_text="ЦБ сохранил ключевую ставку", 
    profile=profile
)
```
Ожидаемый результат: для клиента А новость про ставку — score ≈ 0.75, про логистику — score ≈ 0.08.