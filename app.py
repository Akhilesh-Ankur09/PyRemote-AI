# app.py
import streamlit as st
import pandas as pd
import json
import os
from PIL import Image
from core.job_sources import fetch_jobs
from core.notifier import send_email


# ---------- STREAMLIT SETUP ----------
st.set_page_config(
    page_title="PyRemote-AI",
    page_icon="assets/logo.png",
    layout="wide"
)


# ---------- HEADER ----------
col1, col2 = st.columns([1, 9])
with col1:
    try:
        logo = Image.open("assets/logo.png")
        st.image(logo, width=90)
    except Exception:
        st.write("🤖")
with col2:
    st.title("PyRemote-AI Dashboard")
    st.markdown("**AI-powered Remote Job Discovery Assistant.** 🌍")


# ---------- CONFIG LOADING ----------
CONFIG_PATH = "data/user_config.json"
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            user_conf = json.load(f)
    except (UnicodeDecodeError, json.JSONDecodeError):
        user_conf = {}
else:
    user_conf = {}


# ---------- SIDEBAR UI ----------
with st.sidebar:
    # --- Branding ---
    st.image("assets/logo.png", width=120)
    st.markdown("<h2 style='text-align:center;'>PyRemote-AI</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray;'>AI-powered Remote Job Finder 🌍</p>", unsafe_allow_html=True)
    st.markdown("---")

    # --- User Profile ---
    with st.expander("👤 User Profile", expanded=True):
        email = st.text_input("📧 Email Address", user_conf.get("email", ""))

        exp_levels = ["Fresher", "0–2 years", "3–5 years", "5+ years"]
        # Normalize to handle both hyphens and en-dashes
        user_exp = user_conf.get("experience", "Fresher").replace("–", "-")
        exp_levels_normalized = [e.replace("–", "-") for e in exp_levels]

        if user_exp not in exp_levels_normalized:
            exp_index = 0
        else:
            exp_index = exp_levels_normalized.index(user_exp)

        experience = st.selectbox("💼 Experience Level", exp_levels, index=exp_index)

    # --- Search Preferences ---
    with st.expander("🔍 Job Search Settings", expanded=True):
        keywords = st.text_area(
            "🧩 Keywords (comma separated)",
            ",".join(user_conf.get("keywords", ["Python", "AI"]))
        )
        sources = st.multiselect(
            "🌐 Job Sources",
            ["RemoteOK", "WeWorkRemotely"],
            default=user_conf.get("sources", ["RemoteOK"])
        )

    # --- Save Preferences ---
    save_pref = st.button("💾 Save Preferences")
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
        st.success("✅ Preferences Saved Successfully!")

    st.markdown("---")

    # --- About Section ---
    st.markdown("### ℹ️ About PyRemote-AI")
    st.info(
        "PyRemote-AI helps you discover, analyze, and receive curated remote jobs "
        "using AI-driven matching. Run your search, download results, or get them "
        "instantly delivered to your inbox. 📬"
    )

    # --- Footer ---
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align:center; font-size:14px;">
            <b>Created by</b><br>
            <a href="https://github.com/Akhilesh-Ankur09" target="_blank">Akhilesh Ankur</a><br>
            <a href="https://www.linkedin.com/in/akhilesh-ankur-3354712aa" target="_blank">LinkedIn</a> |
            <a href="https://github.com/Akhilesh-Ankur09" target="_blank">GitHub</a><br><br>
            🇯🇵 <i>Journey to Japan · 2025</i>
        </div>
        """,
        unsafe_allow_html=True
    )


# ---------- HELPER FUNCTION ----------
def jobs_to_df(jobs):
    if not jobs:
        return pd.DataFrame()
    df = pd.DataFrame(jobs)
    cols = ["Source", "Title", "Company", "Location", "URL"]
    present = [c for c in cols if c in df.columns]
    extras = [c for c in df.columns if c not in present]
    return df[present + extras]


# ---------- MAIN APP ----------
st.header("Run Job Search")

if "jobs" not in st.session_state:
    st.session_state.jobs = []

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

jobs = st.session_state.jobs
if not jobs:
    st.info("No job results yet. Click **Run Search Now**.")
else:
    df = jobs_to_df(jobs)
    st.success(f"Found {len(df)} job(s)! Displaying below:")
    st.dataframe(df, width="stretch")

    # --- Save CSV ---
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

    # --- Email Sending ---
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

# ---------- EXPORT / ANALYTICS ----------
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
