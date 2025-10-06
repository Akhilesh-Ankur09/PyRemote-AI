import requests
import feedparser
import time

def fetch_remoteok_jobs():
    """Fetch jobs from RemoteOK API."""
    url = "https://remoteok.io/api"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("Error fetching RemoteOK:", e)
        return []

    jobs = []
    for item in data[1:]:  # skip metadata
        jobs.append({
            "Source": "RemoteOK",
            "Title": item.get("position", ""),
            "Company": item.get("company", ""),
            "Location": item.get("location", "Remote"),
            "URL": item.get("url", ""),
            "Description": item.get("description", "")
        })
    return jobs


def fetch_weworkremotely_jobs():
    """Fetch jobs from WeWorkRemotely RSS."""
    feed_url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
    try:
        feed = feedparser.parse(feed_url)
    except Exception as e:
        print("Error parsing WWR feed:", e)
        return []

    jobs = []
    for entry in feed.entries:
        jobs.append({
            "Source": "WeWorkRemotely",
            "Title": entry.title,
            "Company": getattr(entry, "author", "Unknown"),
            "Location": "Remote",
            "URL": entry.link,
            "Description": getattr(entry, "summary", "")
        })
    return jobs


def fetch_jobs(keywords, sources=None):
    """Fetch and filter jobs from selected sources."""
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]
    keywords = [k.lower() for k in keywords]

    if sources is None:
        sources = ["RemoteOK", "WeWorkRemotely"]

    all_jobs = []

    if "RemoteOK" in sources:
        all_jobs.extend(fetch_remoteok_jobs())

    if "WeWorkRemotely" in sources:
        all_jobs.extend(fetch_weworkremotely_jobs())

    # filter by keywords
    filtered = []
    for job in all_jobs:
        combined_text = (job["Title"] + " " + job["Description"]).lower()
        if any(k in combined_text for k in keywords):
            filtered.append(job)

    # remove duplicates by URL
    unique = {job["URL"]: job for job in filtered}
    return list(unique.values())
