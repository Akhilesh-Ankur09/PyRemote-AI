import requests
import feedparser
import time
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer, util
# torch required by sentence-transformers backend
import torch  # noqa: F401


# ---------------------------------------------------------------------------
# ⚙️ Load the semantic model once (cached for speed)
# ---------------------------------------------------------------------------
print("🧠 Loading SentenceTransformer model... This may take a few seconds.")
model = SentenceTransformer("all-MiniLM-L6-v2")


# ---------------------------------------------------------------------------
# 🔍 SMART MATCHING LOGIC (Hybrid + Domain Isolation)
# ---------------------------------------------------------------------------

def is_relevant_position(position, title, desc=None, fuzzy_threshold=82, semantic_threshold=0.68):
    """
    Determine if a job title/description is relevant to the searched position.
    Combines fuzzy matching, semantic similarity, and domain context filtering.
    """

    position_lower = position.lower()
    title_lower = title.lower()
    desc_lower = desc.lower() if desc else ""

    # --- Step 1: Fuzzy lexical match ---
    fuzzy_score = fuzz.partial_ratio(position_lower, title_lower)

    # --- Step 2: Semantic similarity between position & title ---
    emb1 = model.encode(position_lower, convert_to_tensor=True)
    emb2 = model.encode(title_lower, convert_to_tensor=True)
    semantic_score = float(util.cos_sim(emb1, emb2))

    # --- Step 3: Domain keyword groups ---
    design_terms = ["ui", "ux", "design", "designer", "product design", "visual", "interface", "user experience", "interaction"]
    dev_terms = ["frontend", "developer", "software", "engineer", "react", "backend", "web", "full stack"]
    ml_terms = ["machine learning", "ai", "data", "deep learning", "neural", "nlp"]
    edu_terms = ["teacher", "tutor", "trainer", "professor", "instructor", "lecturer", "education", "school"]
    excluded_terms = [
        "marketing", "sales", "manager", "seo", "copywriter", "business", "analyst",
        "recruiter", "finance", "account", "executive", "legal", "consultant",
        "customer", "growth", "brand", "advertising", "success"
    ]

    # --- Step 4: Determine domain context ---
    domain = None
    if any(t in position_lower for t in design_terms):
        domain = "design"
    elif any(t in position_lower for t in ml_terms):
        domain = "ml"
    elif any(t in position_lower for t in dev_terms):
        domain = "dev"
    elif any(t in position_lower for t in edu_terms):
        domain = "edu"

    # --- Step 5: Apply domain-specific logic ---
    # Design
    if domain == "design":
        if not any(t in title_lower for t in design_terms):
            return False
        if any(t in title_lower for t in excluded_terms):
            return False

    # ML/AI
    elif domain == "ml":
        if not any(t in title_lower for t in ml_terms + dev_terms):
            return False
        if any(t in title_lower for t in excluded_terms):
            return False

    # Developer
    elif domain == "dev":
        if not any(t in title_lower for t in dev_terms):
            return False
        if any(t in title_lower for t in excluded_terms):
            return False

    # Education (NEW)
    elif domain == "edu":
        if not any(t in title_lower for t in edu_terms):
            return False
        # exclude tech or design jobs that use “trainer”, “coach”, etc.
        if any(t in title_lower for t in design_terms + ml_terms + dev_terms):
            return False
        if any(t in title_lower for t in excluded_terms):
            return False

    # --- Step 6: Hybrid match decision ---
    # Dynamically adjust thresholds for general domains like "teacher"
    if domain in ["edu"]:
        fuzzy_threshold = 85
        semantic_threshold = 0.7

    if fuzzy_score >= fuzzy_threshold or semantic_score >= semantic_threshold:
        return True

    # --- Step 7: Fallback (keyword in description) ---
    if position_lower in desc_lower:
        return True

    return False


# ---------------------------------------------------------------------------
# 🌐 JOB SOURCE FUNCTIONS
# ---------------------------------------------------------------------------

def fetch_remoteok_jobs(position=None):
    """Fetch jobs from RemoteOK API (optionally filter client-side)."""
    url = "https://remoteok.io/api"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("⚠️ Error fetching RemoteOK:", e)
        return []

    jobs = []
    for item in data[1:]:  # skip metadata
        title = item.get("position", "") or ""
        desc = item.get("description", "") or ""
        company = item.get("company", "") or ""
        location = item.get("location", "Remote") or ""
        url = item.get("url", "") or ""

        if not position or is_relevant_position(position, title, desc):
            jobs.append({
                "Source": "RemoteOK",
                "Title": title.strip(),
                "Company": company.strip(),
                "Location": location.strip(),
                "URL": url.strip(),
                "Description": desc.strip(),
                "Matched Keyword": position if position else "N/A"
            })
    return jobs


def fetch_weworkremotely_jobs(position=None):
    """Fetch jobs from WeWorkRemotely RSS feed (optionally filter client-side)."""
    feed_url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
    try:
        feed = feedparser.parse(feed_url)
    except Exception as e:
        print("⚠️ Error parsing WWR feed:", e)
        return []

    jobs = []
    for entry in feed.entries:
        title = getattr(entry, "title", "")
        desc = getattr(entry, "summary", "")
        company = getattr(entry, "author", "Unknown")
        link = getattr(entry, "link", "")

        if not position or is_relevant_position(position, title, desc):
            jobs.append({
                "Source": "WeWorkRemotely",
                "Title": title.strip(),
                "Company": company.strip(),
                "Location": "Remote",
                "URL": link.strip(),
                "Description": desc.strip(),
                "Matched Keyword": position if position else "N/A"
            })
    return jobs


# ---------------------------------------------------------------------------
# 🧩 MAIN FETCHER (multi-keyword + multi-source)
# ---------------------------------------------------------------------------

def fetch_jobs(keywords, sources=None):
    """
    Fetch and filter jobs from multiple sources.
    Each result is tagged with its matched position/keyword and timestamp.
    Uses hybrid matching with contextual and domain-aware filtering.
    """

    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]
    keywords = [k for k in keywords if k]

    if not keywords:
        print("⚠️ No keywords provided.")
        return []

    if sources is None:
        sources = ["RemoteOK", "WeWorkRemotely"]

    all_jobs = []

    print(f"🔍 Fetching jobs for positions: {keywords} from sources: {sources}")

    for kw in keywords:
        for source in sources:
            try:
                if source == "RemoteOK":
                    jobs = fetch_remoteok_jobs(kw)
                elif source == "WeWorkRemotely":
                    jobs = fetch_weworkremotely_jobs(kw)
                else:
                    print(f"⚠️ Unsupported source: {source}")
                    continue

                for job in jobs:
                    job["Fetched At"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    all_jobs.append(job)

                print(f"✅ {len(jobs)} relevant jobs found for position '{kw}' from {source}")

            except Exception as e:
                print(f"⚠️ Error fetching from {source} for '{kw}': {e}")
                continue

    # --- Deduplicate by URL ---
    unique_jobs = {}
    for job in all_jobs:
        url = job.get("URL", "")
        if url not in unique_jobs:
            unique_jobs[url] = job

    results = list(unique_jobs.values())
    print(f"📦 Total unique relevant jobs collected: {len(results)}")

    return results
