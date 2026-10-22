import json
import os
from ingestion.chunker import chunk_documents

def main():
    news_path = "data/raw/news_sample.json"
    pdf_path = "data/raw/alfa_analytics.json"
    
    all_docs = []
    
    if os.path.exists(news_path):
        with open(news_path, "r", encoding="utf-8") as f:
            news_docs = json.load(f)
            all_docs.extend(news_docs)
            print(f"Загружено {len(news_docs)} новостей.")
            
    if os.path.exists(pdf_path):
        with open(pdf_path, "r", encoding="utf-8") as f:
            pdf_docs = json.load(f)
            all_docs.extend(pdf_docs)
            print(f"Загружено {len(pdf_docs)} страниц аналитики.")

    if not all_docs:
        print("Нет данных для обработки. Сначала запустите run_ingest.py и run_pdf_ingest.py")
        return

    print("Нарезаем документы на чанки...")
    chunks = chunk_documents(all_docs, chunk_size=500, chunk_overlap=75)
    
    print(f"Получилось {len(chunks)} чанков. Сохраняем...")
    
    output_path = "data/processed/chunks.jsonl"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            
    print(f"Готово! Чанки сохранены в {output_path}")

if __name__ == "__main__":
    main()