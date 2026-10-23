async def rank(profile: dict, events: list[dict]) -> list[dict]:
    """Простой rule-based ранкер как baseline. Person 2 заменит на свой."""
    industry = profile.get("industry", "").lower()
    products = profile.get("products", {})
    topics_weight = {
        "rates": 3 if products.get("credit") else 1,
        "inflation": 3 if products.get("deposit") else 2,
        "commodities": 3 if "добыча" in industry else 0,
        "regulation": 1,
        "construction": 4 if "строительство" in industry else 0,
        "consumer": 3 if "ритейл" in industry or "торговля" in industry else 0,
        "credit": 2 if products.get("credit") else 0,
    }

    ranked = []
    for e in events:
        score = 0.0
        for t in e.get("topics", []):
            score += topics_weight.get(t, 0)
        for ind in e.get("industries", []):
            if ind.lower() in industry:
                score += 2
        e = {**e, "relevance_score": round(min(score / 10.0, 1.0), 2)}
        ranked.append(e)

    return sorted(ranked, key=lambda x: x["relevance_score"], reverse=True)