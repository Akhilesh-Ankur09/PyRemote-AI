import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
import streamlit as st


def load_credentials():
    """
    Load Gmail credentials.
    Priority:
      1️⃣ Streamlit Cloud secrets (if available)
      2️⃣ Local config.json (for local testing)
    """
    try:
        # --- Cloud: Streamlit Secrets ---
        if hasattr(st, "secrets") and len(st.secrets) > 0:
            if "sender_email" in st.secrets and "app_password" in st.secrets:
                st.write("🔐 Using Streamlit Cloud secrets.")
                return {
                    "sender_email": st.secrets["sender_email"],
                    "app_password": st.secrets["app_password"]
                }
            # In case secrets are nested (some Streamlit setups)
            elif "general" in st.secrets:
                general = st.secrets["general"]
                if "sender_email" in general and "app_password" in general:
                    st.write("🔐 Using nested Streamlit secrets.")
                    return {
                        "sender_email": general["sender_email"],
                        "app_password": general["app_password"]
                    }

        # --- Local fallback: config.json ---
        config_path = "config.json"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                creds = json.load(f)
                st.write("💻 Using local config.json credentials.")
                return creds
        else:
            raise FileNotFoundError("config.json not found locally or no Streamlit secrets detected.")
    except Exception as e:
        st.error(f"❌ Failed to load credentials: {e}")
        return {}


def send_email(jobs, recipient=None):
    """
    Sends job summary email.
    Reads credentials via load_credentials().
    """
    creds = load_credentials()
    sender = creds.get("sender_email")
    password = creds.get("app_password")

    if not sender or not password:
        raise ValueError("Email or password missing. Check your Streamlit secrets or config.json.")

    # Format email body
    body = "Here are your latest job results from PyRemote-AI 🚀\n\n"
    for job in jobs:
        body += f"🔹 {job.get('Title', 'N/A')} at {job.get('Company', 'N/A')} ({job.get('Location', 'Remote')})\n"
        body += f"🔗 {job.get('URL', '')}\n\n"

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient or sender
    msg["Subject"] = "Your PyRemote-AI Job Results"
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
            st.write("✅ Email sent successfully.")
    except smtplib.SMTPAuthenticationError:
        raise Exception("Authentication failed. Double-check your Gmail App Password.")
    except Exception as e:
        raise Exception(f"SMTP error: {e}")
