import streamlit as st
import pandas as pd
import json
import os
from core.job_sources import fetch_jobs
from core.notifier import send_email

st.set_page_config(page_title="PyRemote-AI", page_icon="🤖", layout="wide")
st.title("🤖 PyRemote-AI Dashboard")
st.markdown("Discover and receive AI-curated remote jobs directly in your inbox! 🚀")

# Sidebar — user preferences
st.sidebar.header("⚙️ Preferences")

CONFIG_PATH = "data/user_config.json"
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        user_conf = json.load(f)
else:
    user_conf = {}

email = st.sidebar.text_input("📧 Your Email", user_conf.get("email", ""))
keywords = st.sidebar.text_area("🔍 Keywords (comma separated)", ",".join(user_conf.get("keywords", ["Python", "AI"])))
sources = st.sidebar.multiselect("🌐 Job Sources", ["RemoteOK", "WeWorkRemotely"], default=user_conf.get("sources", ["RemoteOK"]))
save_pref = st.sidebar.button("💾 Save Preferences")

if save_pref:
    os.makedirs("data", exist_ok=True)
    user_conf = {"email": email, "keywords": [k.strip() for k in keywords.split(",")], "sources": sources}
    with open(CONFIG_PATH, "w") as f:
        json.dump(user_conf, f, indent=4)
    st.sidebar.success("✅ Preferences Saved")

st.sidebar.markdown("---")
st.sidebar.markdown("**Built by [Akhilesh Ankur](https://github.com/Akhilesh-Ankur09)** 🇯🇵")

# Main app — search and results
if st.button("🚀 Run Job Search"):
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    with st.spinner("Fetching jobs..."):
        jobs = fetch_jobs(kw_list, sources)
    if not jobs:
        st.warning("No jobs found. Try different keywords.")
    else:
        df = pd.DataFrame(jobs)
        st.success(f"Found {len(df)} jobs!")
        st.dataframe(df)

        # Save CSV
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/job_results.csv", index=False)

        if st.checkbox("📬 Send results to my email"):
            send_email(jobs, recipient=email)
            st.info("Email sent successfully! 📩")

# Optional download
if os.path.exists("data/job_results.csv"):
    st.download_button("⬇️ Download Latest CSV", data=open("data/job_results.csv", "rb"), file_name="job_results.csv")
