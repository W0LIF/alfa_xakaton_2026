from langchain_text_splitters import RecursiveCharacterTextSplitter
import hashlib


def chunk_documents(docs: list[dict], chunk_size: int = 500, chunk_overlap: int = 75) -> list[dict]:
    """Нарезает тексты, удаляя точные дубликаты."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_chunks = []
    seen_hashes = set()  # Хэши для дедупликации

    for doc in docs:
        texts = splitter.split_text(doc.get("body", ""))

        for i, text in enumerate(texts):
            # Хэшируем текст чанка
            text_hash = hashlib.md5(text.strip().encode("utf-8")).hexdigest()

            if text_hash in seen_hashes:
                continue  # Пропускаем дубликат
            seen_hashes.add(text_hash)

            chunk = doc.copy()
            chunk["chunk_id"] = f"{doc.get('doc_id', 'unknown')}_c{i}"
            chunk["text"] = text

            if "body" in chunk:
                del chunk["body"]

            all_chunks.append(chunk)

    return all_chunks