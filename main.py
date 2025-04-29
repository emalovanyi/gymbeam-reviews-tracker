from google_play_scraper import reviews
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import requests

# 🔹 Налаштування підключення до Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
sheet = client.open("Recenzii").sheet1  # <-- Назва твоєї Google Таблиці

# 🔹 Отримати список вже існуючих коментарів (4-та колонка - Коментар)
existing_comments = sheet.col_values(4)

# === 1. Завантаження відгуків з Google Play ===
result, _ = reviews(
    'com.gymbeam.app',  # <-- ID додатку в Google Play
    lang='en',
    country='us',
    count=100,
    sort=0  # newest first
)

for review in result:
    if review['content'] not in existing_comments:
        review_date = review['at'].strftime("%Y-%m-%d")
        sheet.append_row([
            review_date,
            review['userName'],
            review['score'],
            review['content'],
            review.get('reviewCreatedVersion', 'N/A'),
            review.get('countryName', 'Unknown') + ' (Google Play)'
        ])

# === 2. Завантаження відгуків з App Store ===
app_store_url = "https://itunes.apple.com/rss/customerreviews/id=6738916844/json"  # <-- ID додатку в App Store
response = requests.get(app_store_url)

if response.status_code == 200:
    data = response.json()
    entries = data.get('feed', {}).get('entry', [])[1:]  # перший запис це мета-дані

    for entry in entries:
        comment_text = entry.get('content', {}).get('label', '')
        if comment_text not in existing_comments:
            review_date = entry.get('updated', '')[:10] if 'updated' in entry else 'N/A'
            author = entry.get('author', {}).get('name', {}).get('label', 'Unknown')
            rating = entry.get('im:rating', {}).get('label', 'N/A')
            version = entry.get('im:version', {}).get('label', 'N/A')

            sheet.append_row([
                review_date,
                author,
                rating,
                comment_text,
                version,
                'App Store'
            ])
else:
    print("Помилка завантаження відгуків з App Store RSS")
