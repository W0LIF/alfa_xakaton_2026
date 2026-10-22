import json
import os
import glob
from ingestion.parsers.pdf_parser import parse_pdf
from ingestion.cleaner import clean_document

def main():
    pdf_dir = "data/alfa_analytics"
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"В папке {pdf_dir} не найдено PDF-файлов!")
        return

    print(f"Найдено {len(pdf_files)} PDF-файлов. Начинаем обработку...")
    
    all_docs = []
    for pdf_path in pdf_files:
        print(f"Обработка: {os.path.basename(pdf_path)}")
        docs = parse_pdf(pdf_path)
        
        cleaned_docs = [clean_document(doc) for doc in docs]
        all_docs.extend(cleaned_docs) 
        
    output_path = "data/raw/alfa_analytics.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_docs, f, ensure_ascii=False, indent=2)
        
    print(f"Успешно обработано {len(all_docs)} страниц. Сохранено в {output_path}")

if __name__ == "__main__":
    main()