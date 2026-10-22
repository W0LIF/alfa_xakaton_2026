import re

def clean_text(text: str) -> str:
    if not text:
        return ""

    # Убираем html-теги
    text = re.sub(r'<[^>]+>', '', text)
    
    # Разрешаем цифры, проценты, валюты и базовую математику
    text = re.sub(r'[^\w\s\u0400-\u04FF.,!?;:()\-–—"«»%$+=/]', '', text)
    
    # Схлопываем пробелы
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def clean_document(raw_doc: dict) -> dict:
    cleaned = raw_doc.copy()
    cleaned["title"] = clean_text(cleaned.get("title", ""))
    cleaned["body"] = clean_text(cleaned.get("body", ""))
    
    # Если после очистки текст пустой, мы все равно возвращаем документ, 
    # чтобы не ломать пайплайн, просто body будет пустым.
    return cleaned