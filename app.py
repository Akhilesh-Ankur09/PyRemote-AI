# app.py
import streamlit as st
import pandas as pd
import json
import os
from core.job_sources import fetch_jobs
from core.notifier import send_email

# ---------- Page setup ----------
from PIL import Image

st.set_page_config(
    page_title="PyRemote-AI",
    page_icon="assets/logo.png",
    layout="wide"
)

# header with logo
col1, col2 = st.columns([1, 9])
with col1:
    logo = Image.open("assets/logo.png")
    st.image(logo, width=90)
with col2:
    st.title("PyRemote-AI Dashboard")
    st.markdown("**AI-powered remote job discovery assistant.** 🌍")


# ---------- Sidebar: user preferences ----------
st.sidebar.header("⚙️ Preferences")

CONFIG_PATH = "data/user_config.json"

# Load user preferences safely
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            user_conf = json.load(f)
    except UnicodeDecodeError:
        try:
            with open(CONFIG_PATH, "r", encoding="cp1252") as f:
                user_conf = json.load(f)
        except Exception:
            user_conf = {}
    except json.JSONDecodeError:
        user_conf = {}
else:
    user_conf = {}

email = st.sidebar.text_input("📧 Your Email", user_conf.get("email", ""))
keywords = st.sidebar.text_area(
    "🔍 Keywords (comma separated)",
    ",".join(user_conf.get("keywords", ["Python", "AI"]))
)
sources = st.sidebar.multiselect(
    "🌐 Job Sources",
    ["RemoteOK", "WeWorkRemotely"],
    default=user_conf.get("sources", ["RemoteOK"])
)
experience = st.sidebar.selectbox(
    "💼 Experience Level (for future filtering)",
    ["Fresher", "0-2 years", "3-5 years", "5+ years"],
    index=0
)
save_pref = st.sidebar.button("💾 Save Preferences")

if save_pref:
    os.makedirs("data", exist_ok=True)
    user_conf = {
        "email": email,
        "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
        "sources": sources,
        "experience": experience
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(user_conf, f, indent=4, ensure_ascii=False)
    st.sidebar.success("✅ Preferences Saved")

st.sidebar.markdown("---")
st.sidebar.markdown("**Built by [Akhilesh Ankur](https://github.com/Akhilesh-Ankur09)** 🇯🇵")
st.sidebar.markdown("🔒 Note: keep `config.json` private (contains Gmail app password).")

# ---------- Helper ----------
def jobs_to_df(jobs):
    if not jobs:
        return pd.DataFrame()
    df = pd.DataFrame(jobs)
    cols = ["Source", "Title", "Company", "Location", "URL"]
    present = [c for c in cols if c in df.columns]
    extras = [c for c in df.columns if c not in present]
    return df[present + extras]

# ---------- Main ----------
st.header("Run Job Search")

# Keep jobs in session_state so they persist across reruns
if "jobs" not in st.session_state:
    st.session_state.jobs = []

# --- Run Search button ---
if st.button("🚀 Run Search Now"):
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    if not kw_list:
        st.warning("Please enter at least one keyword in the sidebar.")
    else:
        with st.spinner("Fetching jobs from selected sources..."):
            try:
                st.session_state.jobs = fetch_jobs(kw_list, sources)
            except Exception as e:
                st.error(f"Failed to fetch jobs: {e}")
                st.session_state.jobs = []

# --- Display current results (if any) ---
jobs = st.session_state.jobs
if not jobs:
    st.info("No job results yet. Click **Run Search Now**.")
else:
    df = pd.DataFrame(jobs)
    st.success(f"Found {len(df)} job(s)! Displaying below:")
    st.dataframe(df, use_container_width=True)

    # Save CSV
    os.makedirs("data", exist_ok=True)
    csv_path = "data/job_results.csv"
    try:
        df.to_csv(csv_path, index=False, encoding="utf-8")
        st.caption(f"Saved results to `{csv_path}`")
    except Exception as e:
        st.warning(f"Could not save CSV: {e}")

    # ---------- Email sending (state-safe) ----------
    st.markdown("### 📬 Email Options")
    st.caption("Send the current job results to your inbox.")

    if "email_sent" not in st.session_state:
        st.session_state.email_sent = False

    if st.button("📧 Send Results Now") and not st.session_state.email_sent:
        if not email:
            st.warning("Please enter your email address in the sidebar before sending.")
        else:
            with st.spinner("📡 Sending email..."):
                try:
                    send_email(jobs, recipient=email)
                    st.session_state.email_sent = True
                    st.success(f"📩 Email sent successfully to {email}!")
                except FileNotFoundError:
                    st.error("⚠️ config.json not found. Add your Gmail credentials.")
                except Exception as e:
                    st.error(f"❌ Failed to send email: {e}")

    elif st.session_state.email_sent:
        st.info("✅ Email already sent in this session.")


# ---------- Export / Analytics ----------
st.markdown("---")
st.header("Export / Utilities")

if os.path.exists("data/job_results.csv"):
    try:
        with open("data/job_results.csv", "rb") as fh:
            st.download_button(
                label="⬇️ Download Latest CSV",
                data=fh,
                file_name="job_results.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.warning(f"Could not provide download: {e}")
else:
    st.info("Run a search to enable export.")

st.markdown("---")
st.header("Quick Analytics (by Source)")

if os.path.exists("data/job_results.csv"):
    try:
        df_local = pd.read_csv("data/job_results.csv")
        if "Source" in df_local.columns:
            counts = df_local["Source"].value_counts().reset_index()
            counts.columns = ["Source", "Count"]
            st.bar_chart(counts.set_index("Source"))
        else:
            st.info("No 'Source' column found yet.")
    except Exception as e:
        st.warning(f"Analytics failed: {e}")
else:
    st.info("No data yet for analytics. Run a search first.")
