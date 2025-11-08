import requests, os, json

def search_jobs(query="QA Automation Engineer", location="Bangalore OR Remote"):
    """
    Uses Google Custom Search API to safely find job postings
    from Naukri and LinkedIn for given keywords.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CX_ID")

    if not api_key or not cx:
        raise ValueError("❌ GOOGLE_API_KEY or GOOGLE_CX_ID not set in environment secrets")

    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": f"{query} site:naukri.com OR site:linkedin.com/jobs location:{location}",
    }

    response = requests.get(search_url, params=params)
    results = response.json()

    jobs = []
    for item in results.get("items", []):
        job = {
            "title": item.get("title", "Untitled"),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        jobs.append(job)

    os.makedirs("data", exist_ok=True)
    with open("data/jobcatcher.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)

    return jobs
