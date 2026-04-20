import easyocr
import os

# Инициализируем ридер (только русский и английский)
print("⏳ Загружаем модели EasyOCR...")
reader = easyocr.Reader(['ru', 'en'], gpu=False)

# Укажи здесь имя файла, который ты кидал боту (он должен быть в папке проекта)
# Если бот его удалил, просто положи копию рядом под именем test.jpg
IMAGE_NAME = "test.jpg"

if not os.path.exists(IMAGE_NAME):
    print(f"❌ Файл {IMAGE_NAME} не найден в папке проекта!")
else:
    print(f"🧐 Читаем файл {IMAGE_NAME}...")
    results = reader.readtext(IMAGE_NAME, detail=0, paragraph=True)

    print("\n--- РЕЗУЛЬТАТ РАСПОЗНАВАНИЯ ---")
    if not results:
        print("🤷‍♂️ Пусто. Сканер ничего не увидел.")
    for text in results:
        print(f"👉 {text}")
    print("------------------------------")