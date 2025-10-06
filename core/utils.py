import re
from typing import List

def clean_keywords(raw_keywords: str) -> List[str]:
    """Split and clean comma-separated keywords entered by the user."""
    return [kw.strip().lower() for kw in re.split(r"[,\n]+", raw_keywords) if kw.strip()]

def format_job_entry(job: dict) -> str:
    """Return a formatted string for job notifications."""
    return f"{job.get('title')} — {job.get('company')} ({job.get('location')})\n{job.get('link')}"

def filter_jobs(jobs: List[dict], keywords: List[str]) -> List[dict]:
    """Filter job results by matching keywords in title or description."""
    filtered = []
    for job in jobs:
        text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        if any(kw in text for kw in keywords):
            filtered.append(job)
    return filtered
