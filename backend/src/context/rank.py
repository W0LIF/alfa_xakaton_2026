from typing import Tuple, List

def score_event(event_topics: List[str], event_text: str, profile: dict) -> Tuple[float, List[str]]:
    """
    Оценивает релевантность новости для клиента.
    
    :param event_topics: Список тем новости (например, ["interest_rate", "regulation"])
    :param event_text: Текст новости (для поиска ключевых слов)
    :param profile: Словарь с профилем клиента (из build_profile.py)
    :return: (релевантность от 0 до 1, список причин)
    """
    score = 0.0
    reasons = []
    
    weights = profile.get("personalization_weights", {})

    # 1. Базовая оценка по темам новости и весам клиента
    for topic in event_topics:
        topic_weight = weights.get(topic, 0)
        if topic_weight > 0:
            score += topic_weight
            reasons.append(f"Тема '{topic}' важна для компании (вес {topic_weight})")

    # 2. Проверяем отрасль
    sector = profile.get("industry", {}).get("sector", "").lower()
    text_lower = event_text.lower()
    
    # Если в тексте новости упоминается отрасль компании
    if sector and sector in text_lower:
        score += 0.2
        reasons.append(f"Новость напрямую касается отрасли компании ('{sector}')")

    # 3. Проверяем регион
    region = profile.get("scale", {}).get("region", "").lower()
    if region and region in text_lower:
        score += 0.1
        reasons.append(f"Событие происходит в регионе присутствия компании ('{region}')")

    # 4. Проверяем контрагентов
    top_counterparty = profile.get("relations", {}).get("top_counterparty")
    if top_counterparty and top_counterparty in event_text:
        score += 0.3
        reasons.append(f"Событие связано с ключевым контрагентом ({top_counterparty})")

    # 5. Ограничиваем максимальный скор (нормализация до 1.0)
    final_score = min(score, 1.0)
    
    # Если скор нулевой, добавляем причину
    if final_score == 0.0:
        reasons.append("Событие не имеет явной связи с профилем компании")

    return round(final_score, 2), reasons

if __name__ == "__main__":
    import json
    from pathlib import Path
    from build_profile import build_profile

    # Загружаем демо-клиента A
    processed_dir = Path(__file__).resolve().parent.parent.parent / "data" / "processed"
    with open(processed_dir / "demo_clients.json", "r", encoding="utf-8") as f:
        demo = json.load(f)
        client_id = demo["A"]["client_id"]

    profile = build_profile(client_id)

    # Тест 1: Новость про ставку
    score1, reasons1 = score_event(
        event_topics=["interest_rate", "regulation"],
        event_text="ЦБ РФ сохранил ключевую ставку на уровне 14%",
        profile=profile
    )
    print("--- ТЕСТ 1: Новость про ключевую ставку ---")
    print(f"Релевантность: {score1}")
    print("Причины:")
    for r in reasons1:
        print(f" - {r}")

    # Тест 2: Новость про логистику (не важна для клиента А)
    score2, reasons2 = score_event(
        event_topics=["logistics"],
        event_text="В Московской области открыли новый логистический хаб",
        profile=profile
    )
    print("\n--- ТЕСТ 2: Новость про логистику ---")
    print(f"Релевантность: {score2}")
    print("Причины:")
    for r in reasons2:
        print(f" - {r}")