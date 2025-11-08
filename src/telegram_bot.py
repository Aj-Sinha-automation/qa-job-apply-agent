import os
import requests
from main import main

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message(text):
    """Send a message to your Telegram chat"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def run_agent_from_telegram():
    """Run the main job agent and notify status"""
    try:
        send_message("🤖 QA Job Agent started running...")
        main()
        send_message("✅ Job Agent run completed successfully!")
    except Exception as e:
        send_message(f"⚠️ Error occurred during run: {str(e)}")

if __name__ == "__main__":
    run_agent_from_telegram()
