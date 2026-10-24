import json
from ingestion.chunker import chunk_documents
from ingestion.cleaner import clean_document
from indexing.bm25_index import BM25Index


unseen_news = {
    "doc_id": "unseen_test_001",
    "source_type": "news",
    "publisher": "Test Source",
    "source_url": "https://example.com/unseen",
    "published_at": "2026-10-24",
    "title": "Крупный металлургический завод объявил о дефолте",
    "body": (
        "Крупный металлургический завод в Челябинске объявил о техническом "
        "дефолте по облигациям серии БО-01. Компания ссылается на резкое "
        "падение цен на никель и логистические проблемы."
    ),
}


cleaned = clean_document(unseen_news)
new_chunks = chunk_documents([cleaned])
print(f"Создано {len(new_chunks)} чанков из новой новости")

print("\nЗагрузка базового индекса...")
idx = BM25Index.load()
old_chunks = idx.chunks.copy()

idx.chunks = old_chunks + new_chunks
idx.build(idx.chunks)

print("\n🔎 Ищем: 'дефолт металлургического завода'")
results = idx.search("дефолт металлургического завода", k=3)

if not results:
    print("❌ Поиск не нашел новую новость!")
else:
    found_new = False
    for r in results:
        print(f"  [{r['score']}] {r['source_url']}")
        print(f"     {r['text'][:120]}...")
        if r["doc_id"] == "unseen_test_001":
            found_new = True

    if found_new:
        print("\n✅ УСПЕХ: Новая новость найдена поиском!")
    else:
        print("\n⚠️ Новая новость не попала в топ-3, но поиск работает.")


idx.chunks = old_chunks
idx.build(old_chunks)
idx.save()
print("\n✅ Оригинальный индекс восстановлен на диске.")