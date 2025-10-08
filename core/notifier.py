import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
import streamlit as st


def send_email(jobs, recipient=None):
    """
    Send email with job results using credentials from Streamlit secrets (preferred)
    or fallback to local config.json if running locally.
    """
    sender = None
    password = None

    # --- Step 1: Try Streamlit Cloud secrets ---
    try:
        if hasattr(st, "secrets") and "email_sender" in st.secrets:
            creds = st.secrets["email_sender"]
            sender = creds.get("sender_email")
            password = creds.get("app_password")
            print("🔐 Loaded credentials from Streamlit secrets.")
    except Exception as e:
        print(f"⚠️ Error reading secrets: {e}")

    # --- Step 2: Fallback to local config.json for local testing ---
    if not sender or not password:
        config_path = "config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    creds = json.load(f)
                    sender = creds.get("sender_email")
                    password = creds.get("app_password")
                    print("🧩 Loaded credentials from local config.json.")
            except Exception as e:
                raise Exception(f"Failed to load credentials from config.json: {e}")

    # --- Step 3: Error if credentials still not found ---
    if not sender or not password:
        raise ValueError("Email or password missing. Check your Streamlit secrets or config.json.")

    # --- Step 4: Format email body ---
    if not jobs:
        body = "No jobs found for your current search."
    else:
        body = "Here are your latest job results:\n\n"
        for job in jobs:
            body += f"🔹 {job.get('Title', 'N/A')} at {job.get('Company', 'N/A')} ({job.get('Location', 'Remote')})\n"
            body += f"{job.get('URL', '')}\n\n"

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient or sender
    msg["Subject"] = "Your PyRemote-AI Job Results"
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # --- Step 5: Send email via Gmail ---
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        print("✅ Email sent successfully.")
    except smtplib.SMTPAuthenticationError:
        raise Exception("SMTP authentication failed. Check your Gmail app password.")
    except Exception as e:
        raise Exception(f"SMTP error: {e}")
