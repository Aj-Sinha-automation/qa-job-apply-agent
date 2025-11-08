import yaml, os, schedule, time
from job_finder import fetch_jobs
from resume_optimizer import tailor_resume
from email_sender import send_email

def main():
    with open("config/settings.yaml") as f:
        config = yaml.safe_load(f)

    jobs = fetch_jobs(config)
    print(f"Fetched {len(jobs)} jobs")

    for job in jobs[:5]:
        desc = job.get("description") or job.get("title", "")
        output_path = f"data/tailored_resume_{job.get('id', 'temp')}.docx"
        tailor_resume(config['resume']['template_path'], desc, output_path)

        if "email" in job:
            send_email(job["email"], "Application for QA Engineer Role", "Please find my tailored resume attached.", output_path)

def run_schedule():
    schedule.every(6).hours.do(main)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run_schedule()
