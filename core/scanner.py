import easyocr
import urllib.parse
from PIL import Image
from pyzbar.pyzbar import decode

# Инициализируем ридер при старте (чтобы не загружать его каждый раз заново)
# ВНИМАНИЕ: При первом запуске он скачает языковые модели (около 20-30 МБ)
print("⏳ Инициализация зрения (EasyOCR)...")
reader = easyocr.Reader(['ru', 'en'], gpu=False) # gpu=False, чтобы работало на любом ПК
print("✅ Сканер чеков готов!")

def scan_receipt(image_path: str) -> str:
    """
    Пытается достать данные из чека.
    Сначала ищет QR-код. Если не находит — читает весь текст.
    """
    # План А: Ищем QR-код (быстро и точно)
    try:
        img = Image.open(image_path)
        decoded_objects = decode(img)
        for obj in decoded_objects:
            qr_data = obj.data.decode('utf-8')
            # В РФ QR на чеках имеет формат: t=...&s=1500.00&fn=...
            parsed = urllib.parse.parse_qs(qr_data)
            if 's' in parsed:
                amount = float(parsed['s'][0])
                return f"Чек на сумму {amount} рублей."
    except Exception as e:
        print(f"⚠️ Ошибка чтения QR: {e}")

    # План Б: Если QR нет, читаем текст с картинки через ИИ
    try:
        results = reader.readtext(image_path, detail=0, paragraph=True)
        full_text = " ".join(results)
        return full_text
    except Exception as e:
        print(f"❌ Ошибка EasyOCR: {e}")
        return ""