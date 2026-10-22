
import os
import pymupdf as fitz

# Пути к установленному Tesseract
TESSERACT_DIR = r"C:\Program Files\Tesseract-OCR"
TESSDATA_DIR = os.path.join(TESSERACT_DIR, "tessdata")

# Добавляем Tesseract в PATH для текущего запуска Python
os.environ["PATH"] = (
    TESSERACT_DIR + os.pathsep + os.environ.get("PATH", "")
)

# Путь к тестовому PDF
PDF_PATH = "data/alfa_analytics/ALFA-7M26.pdf"


def main():
    print("=== Проверка Tesseract OCR ===")

    # 1. Проверяем исполняемый файл
    tesseract_exe = os.path.join(TESSERACT_DIR, "tesseract.exe")

    if not os.path.isfile(tesseract_exe):
        print(f"ОШИБКА: Tesseract не найден: {tesseract_exe}")
        return

    print(f"Tesseract найден: {tesseract_exe}")

    # 2. Проверяем языковые данные
    for lang in ("eng", "rus"):
        lang_path = os.path.join(
            TESSDATA_DIR, f"{lang}.traineddata"
        )

        if os.path.isfile(lang_path):
            print(f"Язык {lang}: установлен")
        else:
            print(f"Язык {lang}: НЕ НАЙДЕН")

    if not os.path.isdir(TESSDATA_DIR):
        print(f"ОШИБКА: каталог не найден: {TESSDATA_DIR}")
        return

    # 3. Проверяем PDF
    if not os.path.isfile(PDF_PATH):
        print(f"\nОШИБКА: PDF не найден: {PDF_PATH}")
        print("Проверь расположение файла относительно backend.")
        return

    try:
        with fitz.open(PDF_PATH) as pdf:
            if pdf.page_count == 0:
                print("ОШИБКА: PDF не содержит страниц.")
                return

            print(f"\nPDF: {PDF_PATH}")
            print(f"Всего страниц: {pdf.page_count}")

            # Для теста распознаём только первую страницу
            page = pdf[0]

            print("\nЗапускаем OCR первой страницы...")

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

            print(f"\nКоличество символов: {len(text)}")
            print("\n=== Распознанный текст ===\n")

            if text.strip():
                print(text[:3000])
                print("\n=== OCR завершён ===")
            else:
                print("Текст не распознан.")

    except Exception as e:
        print(f"\nОШИБКА при обработке: {e}")
        print(
            "Проверь наличие языковых файлов "
            "и правильность путей Tesseract."
        )


if __name__ == "__main__":
    main()
