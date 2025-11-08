import os, json, requests
from job_finder import search_jobs

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_message(text):
    """Send a message to the Telegram chat."""
    requests.post(API_URL, data={"chat_id": CHAT_ID, "text": text})

def main():
    try:
        send_message("🔍 Searching for QA jobs (Bangalore / Remote)...")

        jobs = search_jobs()

        if not jobs:
            send_message("❌ No new jobs found.")
            return

        message = "✨ *Found QA Engineer Jobs (Bangalore / Remote):*\n\n"
        for job in jobs[:5]:
            message += f"🏢 {job['title']}\n🔗 {job['url']}\n\n"

        send_message(message)
    except Exception as e:
        send_message(f"⚠️ Error occurred: {e}")

if __name__ == "__main__":
    main()
