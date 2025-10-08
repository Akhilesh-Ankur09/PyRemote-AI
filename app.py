# app.py
import streamlit as st
import pandas as pd
import json
import os
import io
from PIL import Image
from core.job_sources import fetch_jobs
from core.notifier import send_email

# ✅ DEBUG: Confirm if Streamlit Cloud secrets are loaded
try:
    if hasattr(st, "secrets") and len(st.secrets) > 0:
        if "email_sender" in st.secrets:
            sender_info = st.secrets["email_sender"]
            has_email = "sender_email" in sender_info
            has_pass = "app_password" in sender_info
            if has_email and has_pass:
                st.sidebar.success("✅ Streamlit Secrets: Email credentials detected")
            else:
                st.sidebar.warning("⚠️ Streamlit Secrets found, but missing sender_email or app_password")
        else:
            st.sidebar.warning("⚠️ Streamlit Secrets exist, but no [email_sender] section found")
    else:
        st.sidebar.error("❌ Streamlit Secrets not detected — using local config.json fallback")
except Exception as e:
    st.sidebar.error(f"⚠️ Error checking secrets: {e}")


# ---------- DEBUG: Check Streamlit Secrets ----------
try:
    if hasattr(st, "secrets") and len(st.secrets) > 0:
        st.sidebar.info("✅ Streamlit secrets loaded successfully.")
        st.sidebar.write("Secrets keys detected:", list(st.secrets.keys()))
    else:
        st.sidebar.error("⚠️ No secrets detected. Using local config fallback.")
except Exception as e:
    st.sidebar.error(f"❌ Secrets access error: {e}")

# ---------- Page Setup ----------
st.set_page_config(
    page_title="PyRemote-AI",
    page_icon="assets/logo.png",
    layout="wide"
)

# Header with logo
col1, col2 = st.columns([1, 9])
with col1:
    try:
        logo = Image.open("assets/logo.png")
        st.image(logo, width=90)
    except Exception:
        st.write("🤖")
with col2:
    st.title("PyRemote-AI Dashboard")
    st.markdown("**AI-powered remote job discovery assistant.** 🌍")

# ---------- Sidebar: Preferences ----------
st.sidebar.header("⚙️ Preferences")

CONFIG_PATH = "data/user_config.json"

# Load saved preferences safely
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            user_conf = json.load(f)
    except (UnicodeDecodeError, json.JSONDecodeError):
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

# ---------- Helper Function ----------
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

# Keep jobs persistent in session
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

# --- Display results ---
jobs = st.session_state.jobs
if not jobs:
    st.info("No job results yet. Click **Run Search Now**.")
else:
    df = jobs_to_df(jobs)
    st.success(f"Found {len(df)} job(s)! Displaying below:")
    st.dataframe(df, use_container_width=True)

    # ---------- CSV Handling ----------
    os.makedirs("data", exist_ok=True)
    csv_path = "data/job_results.csv"
    try:
        df.to_csv(csv_path, index=False, encoding="utf-8")
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_data = f.read()
        st.session_state["csv_data"] = csv_data
        st.caption("✅ Results ready for download.")
    except Exception as e:
        st.warning(f"⚠️ Could not save CSV: {e}")

    # ---------- Email Sending ----------
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

if "csv_data" in st.session_state and st.session_state["csv_data"]:
    st.download_button(
        label="⬇️ Download Latest CSV",
        data=st.session_state["csv_data"],
        file_name="job_results.csv",
        mime="text/csv"
    )
else:
    st.info("Run a search to enable CSV export.")

st.markdown("---")
st.header("Quick Analytics (by Source)")

if jobs:
    try:
        df_local = pd.DataFrame(jobs)
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
