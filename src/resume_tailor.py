"""
Tailor a base_resume.docx (converted from your PDF) to a job description using OpenAI.

Output:
  - output/resumes/Anuraj_<CompanyName>.docx
  - output/resumes/Anuraj_<CompanyName>.pdf  (via libreoffice conversion)
  - output/descriptions/<CompanyName>_description.txt
"""

import os
import json
import re
import subprocess
from datetime import datetime
from docx import Document
from openai import OpenAI  # ✅ new OpenAI client import

# --- Load OpenAI key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DOCX = "data/base_resume.docx"
OUT_DIR_RESUMES = "output/resumes"
OUT_DIR_DESC = "output/descriptions"

# Utility: sanitize company name for filename
def sanitize_name(name: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", name.strip())
    s = re.sub(r"__+", "_", s)
    return s.strip("_")[:120]

# Step A: read base docx text for context
def extract_docx_text(path=BASE_DOCX) -> str:
    doc = Document(path)
    texts = []
    for p in doc.paragraphs:
        if p.text and not p.text.isspace():
            texts.append(p.text)
    return "\n".join(texts)

# Step B: Ask OpenAI for tailored sections in JSON
PROMPT_TEMPLATE = """
You are an expert resume writer and ATS optimizer for QA Automation roles.

Given:
1) The base resume text (extracted from a DOCX).
2) A job title and a short job description (snippet).

Task:
- Produce JSON with three keys: "summary", "skills" (array), "experience_updates" (array of bullets to replace or add).
- Keep content truthful to the candidate profile. Use exact job phrases when relevant (e.g., "Selenium WebDriver", "Page Object Model", "BDD", "Cucumber", "Java", "REST Assured", "CI/CD", "Jenkins").
- Output concise sentences or bullets. Do NOT invent new employers, dates, or roles.
- Provide at most 6 skill entries and at most 6 bullets for experience_updates.

Return strictly valid JSON.

INPUT:
Base Resume Text:
\"\"\"{base_text}\"\"\"

Job Title: {job_title}

Job Description Snippet:
\"\"\"{job_desc}\"\"\"
"""

def request_tailored_sections(base_text: str, job_title: str, job_desc: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(base_text=base_text, job_title=job_title, job_desc=job_desc)
    # ✅ Updated to new API interface
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=700
    )
    content = resp.choices[0].message.content

    # Try parsing JSON safely
    try:
        return json.loads(content)
    except Exception:
        m = re.search(r"(\{.*\})", content, flags=re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except:
                raise RuntimeError(f"❌ JSON parse failed. Response:\n{content}")
        raise RuntimeError(f"❌ Non-JSON response:\n{content}")

# Step C: Replace targeted sections in DOCX
def apply_updates_to_docx(out_docx_path: str, updates: dict):
    doc = Document(BASE_DOCX)
    headings = {
        "summary": ["profile summary", "profile", "summary"],
        "skills": ["core competencies", "it skills", "skills", "core skills"],
        "experience": ["work experience", "experience", "projects"]
    }

    para_texts = [p.text.strip() if p.text else "" for p in doc.paragraphs]
    lower_texts = [t.lower() for t in para_texts]

    def replace_section_by_heading(heading_list, new_lines):
        for h in heading_list:
            if h in "".join(lower_texts):
                for idx, t in enumerate(lower_texts):
                    if h in t:
                        start = idx + 1
                        for i, line in enumerate(new_lines):
                            if start + i < len(doc.paragraphs):
                                doc.paragraphs[start + i].text = line
                            else:
                                doc.add_paragraph(line)
                        return True
        return False

    # Apply summary
    summary = updates.get("summary")
    if summary:
        lines = [l.strip() for l in summary.split("\n") if l.strip()]
        replaced = replace_section_by_heading(headings["summary"], lines)
        if not replaced and len(doc.paragraphs) > 0:
            doc.paragraphs[0].text = " ".join(lines)

    # Apply skills
    skills = updates.get("skills", [])
    if skills:
        replace_section_by_heading(headings["skills"], [", ".join(skills)])

    # Apply experience updates
    exp_updates = updates.get("experience_updates", [])
    if exp_updates:
        appended = False
        for h in headings["experience"]:
            for idx, t in enumerate(lower_texts):
                if h in t:
                    insert_at = idx + 1
                    for b in exp_updates:
                        if insert_at < len(doc.paragraphs):
                            doc.paragraphs[insert_at].text = f"- {b}"
                        else:
                            doc.add_paragraph(f"- {b}")
                        insert_at += 1
                    appended = True
                    break
            if appended:
                break
        if not appended:
            doc.add_paragraph("Experience updates:")
            for b in exp_updates:
                doc.add_paragraph(f"- {b}")

    os.makedirs(os.path.dirname(out_docx_path), exist_ok=True)
    doc.save(out_docx_path)
    print(f"✅ Saved tailored DOCX: {out_docx_path}")

# Step D: Convert DOCX → PDF via LibreOffice
def convert_docx_to_pdf(docx_path):
    if not os.path.exists(docx_path):
        raise FileNotFoundError(docx_path)
    pdf_path = docx_path.rsplit(".", 1)[0] + ".pdf"
    cmd = ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", os.path.dirname(docx_path), docx_path]
    subprocess.check_call(cmd)
    if os.path.exists(pdf_path):
        print(f"✅ Saved PDF: {pdf_path}")
    return pdf_path

# High-level orchestrator
def tailor_and_save(job_title: str, company_name: str, job_desc: str):
    base_text = extract_docx_text(BASE_DOCX)
    updates = request_tailored_sections(base_text, job_title, job_desc)
    company_clean = sanitize_name(company_name or job_title.split()[0] or "Company")
    fname = f"Anuraj_{company_clean}"
    out_docx = os.path.join(OUT_DIR_RESUMES, fname + ".docx")
    out_desc = os.path.join(OUT_DIR_DESC, f"{company_clean}_description.txt")

    os.makedirs(OUT_DIR_RESUMES, exist_ok=True)
    os.makedirs(OUT_DIR_DESC, exist_ok=True)

    with open(out_desc, "w", encoding="utf-8") as f:
        f.write(job_desc)

    apply_updates_to_docx(out_docx, updates)

    try:
        out_pdf = convert_docx_to_pdf(out_docx)
    except Exception as e:
        print("⚠️ PDF conversion failed:", e)
        out_pdf = None

    return out_docx, out_pdf

# Local test mode
if __name__ == "__main__":
    job_title = "QA Automation Engineer"
    company_name = "TechNova Systems"
    job_desc = "Looking for a QA Automation Engineer with 3+ years experience in Selenium WebDriver and Java. CI/CD and API testing required."
    print("🚀 Tailoring resume...")
    docx_path, pdf_path = tailor_and_save(job_title, company_name, job_desc)
    print("✅ Done:", docx_path, pdf_path)
