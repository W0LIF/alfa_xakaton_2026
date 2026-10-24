import json
import os
from indexing.bm25_index import BM25Index


def main():
    chunks_path = "data/processed/chunks.jsonl"
    if not os.path.exists(chunks_path):
        print(f"❌ Не найден {chunks_path}. Сначала запустите run_chunking.py")
        return

    chunks = []
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    print(f"Загружено {len(chunks)} чанков")

    idx = BM25Index()
    idx.build(chunks)
    idx.save()


if __name__ == "__main__":
    main()