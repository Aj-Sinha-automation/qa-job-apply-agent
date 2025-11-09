# src/job_search.py
import requests, os, json, urllib.parse
from dotenv import load_dotenv
load_dotenv()


def search_jobs(query="QA Automation Engineer", location_keywords=None, max_results=10):
    """
    Use Google Custom Search API to find job postings.
    location_keywords: list e.g. ["Bangalore", "Bengaluru", "Remote"]
    Returns a list of {title, url, snippet}
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CXID") or os.getenv("GOOGLE_CX_ID") or os.getenv("GOOGLE_CX")

    if not api_key or not cx:
        raise ValueError("GOOGLE_API_KEY or GOOGLE_CXID not set in environment")

    if not location_keywords:
        location_keywords = ["Bangalore", "Bengaluru", "Remote"]

    # build location part like: (Bangalore OR Bengaluru OR Remote)
    loc_part = "(" + " OR ".join(location_keywords) + ")"
    # search sites: naukri and linkedin jobs
    site_part = "(site:naukri.com OR site:linkedin.com/jobs)"
    q = f'{query} {site_part} {loc_part}'

    params = {
        "key": api_key,
        "cx": cx,
        "q": q,
        "num": min(max_results, 10)  # Google CSE limits to 10 per request
    }

    url = "https://www.googleapis.com/customsearch/v1"
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("items", [])
    jobs = []
    for it in items:
        jobs.append({
            "title": it.get("title"),
            "url": it.get("link"),
            "snippet": it.get("snippet")
        })

    # persist to file for later steps
    os.makedirs("data", exist_ok=True)
    with open("data/jobcatcher.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    return jobs
