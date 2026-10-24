from retrieval.lexical_retriever import retrieve_evidence_lexical

QUERIES = [
    "ключевая ставка ЦБ 14%",
    "ОФЗ 26254 доходность",
    "Полюс рейтинг ruAAA",
    "инфляция инфляционные ожидания",
    "РусГидро EBITDA",
]

for q in QUERIES:
    print(f"\n🔎 {q}")
    results = retrieve_evidence_lexical(q, k=3)
    if not results:
        print("  (ничего не найдено)")
        continue
    for hit in results:
        print(f"  [{hit['score']}] {hit['source_url']}")
        print(f"     совпало: {hit['matched_tokens']}")
        print(f"     {hit['text'][:140]}...")