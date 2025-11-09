"""
src/main.py
Main orchestrator for the QA Job Apply Agent.
"""
import os
import traceback
from scripts.convert_pdf_to_docx import convert as convert_pdf_to_docx
from src.job_search import search_jobs
from src.resume_tailor import tailor_and_save
from src.telegram_bot import send_message
from dotenv import load_dotenv
load_dotenv()


def main():
    try:
        send_message("🚀 Starting QA Job Apply Agent...")
        # Step 1: Ensure resume converted
        if not os.path.exists("data/base_resume.docx") and os.path.exists("data/Resume-ANURAJ.pdf"):
            send_message("📄 Converting PDF → DOCX resume...")
            convert_pdf_to_docx()
        else:
            send_message("✅ Base resume ready.")

        # Step 2: Job Search
        send_message("🔍 Searching jobs (Bangalore / Remote)...")
        jobs = search_jobs(query="QA Automation Engineer", location_keywords=["Bangalore", "Bengaluru", "Remote"], max_results=10)
        if not jobs:
            send_message("❌ No jobs found this run.")
            return
        send_message(f"✅ Found {len(jobs)} jobs. Tailoring top 3...")

        # Step 3: Tailor resumes for top jobs
        for i, job in enumerate(jobs[:3]):
            title = job.get("title", "QA Engineer")
            snippet = job.get("snippet", "")
            company_name = title.split(" ")[0] if title else "Company"
            send_message(f"✂️ Tailoring resume for *{title}*...")
            docx_path, pdf_path = tailor_and_save(title, company_name, snippet)
            send_message(f"📄 Tailored resume ready:\n{docx_path}\n{pdf_path or 'PDF conversion failed.'}\n🔗 {job.get('url')}")

        send_message("✅ All done! Check output/resumes for files.")

    except Exception as e:
        tb = traceback.format_exc()
        msg = f"❌ Agent crashed with error:\n{e}\n\nTraceback:\n{tb[:3000]}"
        print(msg)
        try:
            send_message(msg)
        except:
            pass

if __name__ == "__main__":
    main()
