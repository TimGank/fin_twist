import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DADATA_API_KEY")
SECRET_KEY = os.getenv("DADATA_SECRET_KEY")

url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Token {API_KEY}"
}

# Тестируем на ИНН Сбербанка: 7707083893
data = {"query": "7707083893"}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    results = response.json().get("suggestions", [])
    if results:
        name = results[0]["value"]
        print(f"Success! Found: {name}")
    else:
        print("No results found.")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
