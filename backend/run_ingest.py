import json
import os
from ingestion.parsers.rss_parser import parse_rss
from ingestion.cleaner import clean_document

def main():
    rss_url = "https://www.interfax.ru/rss.asp"
    source = "Interfax"

    print(f"Загрузка новостей из {source}...")
    raw_docs = parse_rss(rss_url, source)

    print(f"Загружено {len(raw_docs)} новостей. Очистка...")
    cleaned_docs = [clean_document(doc) for doc in raw_docs]

    output_path = "data/raw/news_sample.json"
    os.makedirs(os.path.dirname(output_path), exist_ok = True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_docs, f, ensure_ascii=False, indent=2)

    print(f"Успешно сохранено в {output_path}")

if __name__ == "__main__":
    main()
       

