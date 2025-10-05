import requests
import feedparser

def fetch_remoteok(keyword):
    """Fetch job listings from RemoteOK API filtered by keyword."""
    url = "https://remoteok.io/api"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        print("⚠️ RemoteOK fetch failed.")
        return []

    jobs = response.json()[1:]  # skip metadata
    filtered = []
    for job in jobs:
        if keyword.lower() in job.get("position", "").lower() or keyword.lower() in str(job.get("tags", [])):
            filtered.append({
                "Source": "RemoteOK",
                "Title": job.get("position"),
                "Company": job.get("company"),
                "Location": job.get("location"),
                "URL": job.get("url")
            })
    return filtered


def fetch_weworkremotely(keyword):
    """Fetch job listings from WeWorkRemotely RSS feed filtered by keyword."""
    feed_url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
    feed = feedparser.parse(feed_url)

    filtered = []
    for entry in feed.entries:
        if keyword.lower() in entry.title.lower():
            filtered.append({
                "Source": "WeWorkRemotely",
                "Title": entry.title,
                "Company": entry.author if hasattr(entry, 'author') else "Unknown",
                "Location": "Remote",
                "URL": entry.link
            })
    return filtered


def fetch_jobs(keyword):
    """Combine results from multiple sources."""
    print(f"🔍 Searching for jobs matching '{keyword}'...")
    jobs = fetch_remoteok(keyword) + fetch_weworkremotely(keyword)
    return jobs
