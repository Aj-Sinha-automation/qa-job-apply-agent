# src/telegram_bot.py
import os
import time
import json
import requests

from job_search import search_jobs
from resume_tailor import tailor_and_save

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
UPDATES_URL = API_BASE + "/getUpdates"
SEND_URL = API_BASE + "/sendMessage"
OFFSET_FILE = "data/telegram_offset.txt"
JOBCACHE_FILE = "data/jobcatcher.json"

def send_message(text, parse_mode="Markdown"):
    requests.post(SEND_URL, json={"chat_id": CHAT_ID, "text": text, "parse_mode": parse_mode}, timeout=15)

def get_updates(offset=None, timeout=5):
    params = {"timeout": timeout}
    if offset:
        params["offset"] = offset
    r = requests.get(UPDATES_URL, params=params, timeout=timeout+5)
    r.raise_for_status()
    return r.json().get("result", [])

def save_offset(offset):
    os.makedirs("data", exist_ok=True)
    with open(OFFSET_FILE, "w") as f:
        f.write(str(offset))

def load_offset():
    try:
        with open(OFFSET_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return None

def save_jobcache(jobs):
    os.makedirs("data", exist_ok=True)
    with open(JOBCACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

def load_jobcache():
    try:
        with open(JOBCACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# Command handlers
def handle_search_command():
    send_message("🔍 Searching for QA jobs (Bangalore / Remote) ...")
    jobs = search_jobs(query="QA Automation Engineer", location_keywords=["Bangalore","Bengaluru","Remote"], max_results=10)
    if not jobs:
        send_message("No jobs found.")
        return
    save_jobcache(jobs)
    # Build message with numbered list
    lines = ["*Found jobs (reply with /tailor <n> to tailor resume for job n):*"]
    for i, j in enumerate(jobs, start=1):
        lines.append(f"{i}. {j.get('title')}\n{j.get('url')}\n")
    send_message("\n".join(lines))

def handle_tailor_command(arg):
    jobs = load_jobcache()
    if not jobs:
        send_message("No cached jobs. Run /search first.")
        return
    try:
        idx = int(arg) - 1
        if idx < 0 or idx >= len(jobs):
            send_message("Invalid job number.")
            return
    except:
        send_message("Usage: /tailor <job-number>")
        return

    job = jobs[idx]
    title = job.get("title", "Job")
    url = job.get("url", "")
    snippet = job.get("snippet", "") or ""
    send_message(f"✂️ Tailoring resume for *{title}* ...")
    docx_path, pdf_path = tailor_and_save(title, title.split(" - ")[0], snippet)
    msg = f"✅ Tailored resume created for *{title}*.\nDOCX: `{docx_path}`"
    if pdf_path:
        msg += f"\nPDF: `{pdf_path}`"
    msg += f"\nLink: {url}"
    send_message(msg)

def handle_status():
    jobs = load_jobcache()
    send_message(f"Status: {len(jobs)} cached jobs. Last run: check output/resumes/ for tailored files.")

# Main loop: poll updates and handle commands (one run-through)
def main_once():
    offset = load_offset()
    updates = get_updates(offset=offset, timeout=10)
    if not updates:
        return
    max_offset = offset or 0
    for u in updates:
        max_offset = max(max_offset, u["update_id"] + 1)
        msg = u.get("message") or u.get("edited_message") or {}
        text = msg.get("text", "")
        chat = msg.get("chat", {})
        # only respond to messages from authorized chat id
        try:
            if str(chat.get("id")) != str(CHAT_ID):
                # ignore messages that are not from your chat
                continue
        except:
            continue

        if text.startswith("/search"):
            handle_search_command()
        elif text.startswith("/tailor"):
            parts = text.split()
            if len(parts) >= 2:
                handle_tailor_command(parts[1])
            else:
                send_message("Usage: /tailor <job-number>")
        elif text.startswith("/status"):
            handle_status()
        else:
            send_message("Unknown command. Use /search, /tailor <n>, /status.")

    save_offset(max_offset)

if __name__ == "__main__":
    # Run only one polling pass (good for GitHub Actions runs).
    try:
        main_once()
    except Exception as e:
        send_message(f"Bot error: {e}")
        raise
