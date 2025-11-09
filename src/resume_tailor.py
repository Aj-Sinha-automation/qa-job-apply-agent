"""
Resume Tailoring Agent (Updated – Free Hugging Face Fallback)
-------------------------------------------------------------
Takes base_resume.docx → tailors to a job description using OpenAI (if available)
or Hugging Face Gemma 2B (free) → outputs DOCX + PDF.
"""

import os
import json
import re
import subprocess
import requests
from datetime import datetime
from docx import Document
from openai import OpenAI

# --- Environment setup ---
from dotenv import load_dotenv
load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
HF_KEY = os.getenv("HUGGINGFACE_API_KEY")

BASE_DOCX = "data/base_resume.docx"
OUT_DIR_RESUMES = "output/resumes"
OUT_DIR_DESC = "output/descriptions"

# --- Initialize OpenAI client if available ---
client = None
if OPENAI_KEY:
    try:
        client = OpenAI(api_key=OPENAI_KEY)
    except Exception:
        client = None

# --- Utility ---
def sanitize_name(name: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", name.strip())
    s = re.sub(r"__+", "_", s)
    return s.strip("_")[:120]


def extract_docx_text(path=BASE_DOCX) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Base resume not found: {path}")
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


PROMPT_TEMPLATE = """
You are an expert resume writer and ATS optimizer for QA Automation roles.

Given:
1) Base resume text.
2) A job title and a short job description (snippet).

Task:
- Return JSON with: "summary", "skills" (array), "experience_updates" (array of bullets).
- Use truthful info, tailor language for ATS, avoid fake employers.
- Keep concise and relevant (max 6 bullets/skills).

INPUT:
Base Resume:
\"\"\"{base_text}\"\"\"

Job Title: {job_title}
Job Description:
\"\"\"{job_desc}\"\"\"
"""

# --- Hugging Face Fallback ---
def hf_tailor_request(base_text, job_title, job_desc):
    if not HF_KEY:
        raise RuntimeError("Hugging Face API key not set in .env")

    url = "https://router.huggingface.co/hf-inference/models/google/gemma-2b-it"
    headers = {"Authorization": f"Bearer {HF_KEY}"}

    prompt = PROMPT_TEMPLATE.format(base_text=base_text, job_title=job_title, job_desc=job_desc)
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 512, "temperature": 0.4}
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Hugging Face request failed: {e}")

    data = r.json()
    if isinstance(data, list) and len(data) and "generated_text" in data[0]:
        content = data[0]["generated_text"]
    elif isinstance(data, dict) and "generated_text" in data:
        content = data["generated_text"]
    else:
        content = str(data)

    try:
        return json.loads(re.search(r"(\{.*\})", content, flags=re.S).group(1))
    except Exception:
        return {
            "summary": "Tailored summary (HF Gemma fallback).",
            "skills": ["QA", "Automation", "Selenium", "Java"],
            "experience_updates": ["Adapted resume using free Hugging Face API."]
        }

# --- OpenAI or fallback ---
def request_tailored_sections(base_text: str, job_title: str, job_desc: str) -> dict:
    if client:
        try:
            prompt = PROMPT_TEMPLATE.format(base_text=base_text, job_title=job_title, job_desc=job_desc)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=700,
            )
            content = resp.choices[0].message.content
            return json.loads(re.search(r"(\{.*\})", content, flags=re.S).group(1))
        except Exception as e:
            print("⚠️ OpenAI error, falling back to Hugging Face:", e)

    # fallback route
    return hf_tailor_request(base_text, job_title, job_desc)


# --- Apply tailored updates ---
def apply_updates_to_docx(out_docx_path: str, updates: dict):
    doc = Document(BASE_DOCX)

    def replace_section(heading_keywords, new_lines):
        lower = [p.text.lower().strip() for p in doc.paragraphs]
        for idx, text in enumerate(lower):
            if any(h in text for h in heading_keywords):
                for i, line in enumerate(new_lines):
                    pos = idx + 1 + i
                    if pos < len(doc.paragraphs):
                        doc.paragraphs[pos].text = line
                    else:
                        doc.add_paragraph(line)
                return

    if updates.get("summary"):
        lines = [l.strip() for l in updates["summary"].split("\n") if l.strip()]
        replace_section(["profile summary", "summary"], lines)

    if updates.get("skills"):
        replace_section(["core competencies", "skills"], [", ".join(updates["skills"])])

    if updates.get("experience_updates"):
        for bullet in updates["experience_updates"]:
            doc.add_paragraph("- " + bullet)

    os.makedirs(os.path.dirname(out_docx_path), exist_ok=True)
    doc.save(out_docx_path)
    print(f"✅ Saved tailored DOCX: {out_docx_path}")


def convert_docx_to_pdf(docx_path):
    if not os.path.exists(docx_path):
        raise FileNotFoundError(docx_path)
    pdf_path = docx_path.rsplit(".", 1)[0] + ".pdf"
    cmd = ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", os.path.dirname(docx_path), docx_path]
    try:
        subprocess.check_call(cmd)
        print(f"✅ Saved PDF: {pdf_path}")
    except Exception as e:
        print("⚠️ PDF conversion failed:", e)
        pdf_path = None
    return pdf_path


def tailor_and_save(job_title: str, company_name: str, job_desc: str):
    base_text = extract_docx_text(BASE_DOCX)
    updates = request_tailored_sections(base_text, job_title, job_desc)

    clean_name = sanitize_name(company_name or job_title)
    fname = f"Anuraj_{clean_name}"

    out_docx = os.path.join(OUT_DIR_RESUMES, fname + ".docx")
    out_desc = os.path.join(OUT_DIR_DESC, f"{clean_name}_description.txt")

    os.makedirs(OUT_DIR_RESUMES, exist_ok=True)
    os.makedirs(OUT_DIR_DESC, exist_ok=True)

    with open(out_desc, "w", encoding="utf-8") as f:
        f.write(job_desc)

    apply_updates_to_docx(out_docx, updates)
    out_pdf = convert_docx_to_pdf(out_docx)
    return out_docx, out_pdf


if __name__ == "__main__":
    job_title = "QA Automation Engineer"
    company_name = "TechNova Systems"
    job_desc = "Looking for QA Automation Engineer skilled in Java, Selenium, and API testing."
    print("Tailoring resume...")
    tailor_and_save(job_title, company_name, job_desc)
    print("Done.")
