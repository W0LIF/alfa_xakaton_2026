
import os
import pymupdf as fitz

TESSERACT_DIR = r"C:\Program Files\Tesseract-OCR"
TESSDATA_DIR = os.path.join(TESSERACT_DIR, "tessdata")

os.environ["PATH"] = (
    TESSERACT_DIR + os.pathsep + os.environ.get("PATH", "")
)


def parse_pdf(
    pdf_path: str,
    source_name: str = "Alfa_bank Analytics"
) -> list[dict]:
    docs = []

    if not os.path.exists(pdf_path):
        print(f"Файл не найден: {pdf_path}")
        return docs

    try:
        with fitz.open(pdf_path) as pdf_document:
            file_name = os.path.basename(pdf_path)
            doc_base_id = os.path.splitext(file_name)[0]

            print(
                f"  -> В файле {file_name} "
                f"найдено страниц: {pdf_document.page_count}"
            )

            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]

                # Сначала пробуем извлечь встроенный текст
                text = page.get_text("text", sort=True)

                # Если текст отсутствует, распознаём изображение
                if not text.strip():
                    print(
                        f"    Страница {page_num + 1}: OCR..."
                    )

                    try:
                        textpage = page.get_textpage_ocr(
                            language="eng+rus",
                            dpi=200,
                            full=True,
                            tessdata=TESSDATA_DIR
                        )

                        text = page.get_text(
                            "text",
                            textpage=textpage
                        )

                    except Exception as e:
                        print(f"    Ошибка OCR: {e}")
                        continue

                if not text.strip():
                    print(
                        f"    Страница {page_num + 1}: "
                        "текст не распознан"
                    )
                    continue

                print(
                    f"    Страница {page_num + 1}: "
                    f"получено символов — {len(text)}"
                )

                docs.append({
                    "doc_id": f"{doc_base_id}_p{page_num + 1}",
                    "source_type": "alfa_analytics",
                    "publisher": source_name,
                    "source_url": (
                        f"alfa_analytics/{file_name}"
                        f"#page={page_num + 1}"
                    ),
                    "published_at": "2026",
                    "title": (
                        f"{doc_base_id} - Страница {page_num + 1}"
                    ),
                    "body": text
                })

    except Exception as e:
        print(f"Ошибка обработки {pdf_path}: {e}")

    return docs
