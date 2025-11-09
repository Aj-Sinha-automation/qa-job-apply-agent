"""
Telegram Bot Utilities – with retry & markdown-safe output
"""

import os
import time
import requests

def send_message(text: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("⚠️ Telegram credentials not set.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for attempt in range(3):
        try:
            r = requests.post(url, data={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }, timeout=15)
            if r.status_code == 200:
                print("✅ Telegram message sent.")
                return
            else:
                print(f"⚠️ Telegram error {r.status_code}: {r.text}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Telegram send failed (attempt {attempt+1}/3):", e)
            time.sleep(3)
    print("❌ Telegram send failed after 3 attempts.")
