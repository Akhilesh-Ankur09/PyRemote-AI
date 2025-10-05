# LinkedIn Job Tracker (Starter Version)
# Author: Akhilesh Ankur

import requests
from bs4 import BeautifulSoup
import pandas as pd

# Step 1: Define URL (we’ll use a sample job board for now)
URL = "https://realpython.github.io/fake-jobs/"  # Demo site for scraping practice
page = requests.get(URL)

# Step 2: Parse the page content
soup = BeautifulSoup(page.content, "html.parser")

# Step 3: Find job listings
results = soup.find_all("div", class_="card-content")

# Step 4: Extract useful info
jobs_data = []
for job in results:
    title = job.find("h2", class_="title").text.strip()
    company = job.find("h3", class_="company").text.strip()
    location = job.find("p", class_="location").text.strip()
    jobs_data.append({
        "Title": title,
        "Company": company,
        "Location": location
    })

# Step 5: Save to CSV
df = pd.DataFrame(jobs_data)
df.to_csv("jobs.csv", index=False, encoding="utf-8")

print(f"✅ Successfully extracted {len(jobs_data)} job listings and saved to jobs.csv!")

