import re
import os
import requests
import cv2
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DADATA_API_KEY")

def decode_qr(image_path):
    """
    Декодирует QR-код с изображения.
    Возвращает строку или None.
    """
    try:
        img = cv2.imread(image_path)
        detector = cv2.QRCodeDetector()
        data, bbox, straight_qrcode = detector.detectAndDecode(img)
        if data:
            return data
        
        # Если не нашел обычным способом, попробуем через pyzbar как запасной вариант
        try:
            from pyzbar.pyzbar import decode
            from PIL import Image
            decoded_objects = decode(Image.open(image_path))
            if decoded_objects:
                return decoded_objects[0].data.decode('utf-8')
        except ImportError:
            pass
            
        return None
    except Exception as e:
        print(f"Error decoding QR: {e}")
        return None

def parse_qr_string(qr_string):
    """
    Парсит строку QR-кода чека.
    Пример: t=20230320T1435&s=1250.50&fn=1234567890&i=12345&fp=1234567890&n=1
    Возвращает dict с данными.
    """
    data = {}
    
    # Извлекаем сумму (s=...)
    s_match = re.search(r's=([\d.]+)', qr_string)
    if s_match:
        data['amount'] = float(s_match.group(1))
    
    # Извлекаем дату (t=...)
    t_match = re.search(r't=(\d{8}T\d{4})', qr_string)
    if t_match:
        try:
            dt_str = t_match.group(1)
            data['date'] = datetime.strptime(dt_str, '%Y%m%dT%H%M')
        except:
            data['date'] = datetime.now()
            
    # Извлекаем ИНН (inn=...)
    inn_match = re.search(r'\binn=(\d+)', qr_string)
    if inn_match:
        data['inn'] = inn_match.group(1)
        
    # Извлекаем фискальные признаки для уникальности чека (fn, fd, fp)
    fn = re.search(r'fn=(\d+)', qr_string)
    fd = re.search(r'i=(\d+)', qr_string) # В QR-коде FD часто идет под ключом i=
    fp = re.search(r'fp=(\d+)', qr_string)
    
    if fn and fd and fp:
        # Формируем уникальную подпись чека
        data['receipt_sig'] = f"{fn.group(1)}_{fd.group(1)}_{fp.group(1)}"
        
    return data

def get_shop_name(inn):
    """
    Получает название магазина по ИНН через DaData.
    """
    if not inn or not API_KEY:
        return "Магазин (по чеку)"
    
    url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {API_KEY}"
    }
    payload = {"query": inn}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            results = response.json().get("suggestions", [])
            if results:
                # Берем короткое название, если есть
                org_data = results[0].get("data", {})
                name = org_data.get("name", {}).get("short_with_opf") or results[0].get("value")
                return name
    except Exception as e:
        print(f"DaData error: {e}")
        
    return "Магазин (ИНН: " + inn + ")"

def process_receipt_image(image_path):
    """
    Полный цикл: декодирование -> парсинг -> обогащение данными.
    """
    qr_string = decode_qr(image_path)
    if not qr_string:
        return None
    
    receipt_data = parse_qr_string(qr_string)
    if 'amount' not in receipt_data:
        return None
    
    inn = receipt_data.get('inn')
    receipt_data['shop'] = get_shop_name(inn)
    
    return receipt_data
