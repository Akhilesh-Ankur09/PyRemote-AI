from job_sources import fetch_jobs
from notifier import send_email
import pandas as pd


def main():
    keyword = input("Enter job keyword (e.g., Python, AI, Automation): ").strip()
    jobs = fetch_jobs(keyword)

    if jobs:
        # Save locally
        df = pd.DataFrame(jobs)
        df.to_csv("job_results.csv", index=False, encoding="utf-8")
        print(f"✅ Found {len(jobs)} jobs for '{keyword}'. Saved to job_results.csv")
    else:
        print("⚠️ No matching jobs found.")

    # Email the results
    send_email(jobs)


if __name__ == "__main__":
    main()
