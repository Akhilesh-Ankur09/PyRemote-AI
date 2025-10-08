# core/notifier.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import os
import streamlit as st


def load_credentials():
    """Load sender credentials from Streamlit secrets or local config.json."""
    creds = {}

    # Priority 1: Streamlit secrets
    try:
        if "email_sender" in st.secrets:
            sender_block = st.secrets["email_sender"]
            creds["sender_email"] = sender_block.get("sender_email")
            creds["app_password"] = sender_block.get("app_password")
            if creds["sender_email"] and creds["app_password"]:
                return creds
    except Exception as e:
        print(f"⚠️ Streamlit secrets not found: {e}")

    # Priority 2: config.json fallback
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            local_conf = json.load(f)
        creds["sender_email"] = local_conf.get("sender_email")
        creds["app_password"] = local_conf.get("app_password")

    return creds


def build_html_email(jobs, recipient):
    """Generate a beautiful HTML-formatted email with clickable job links."""
    logo_url = "https://raw.githubusercontent.com/Akhilesh-Ankur09/PyRemote-AI/main/assets/logo.png"

    # Header section
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background-color: #f8f9fc;
                color: #333;
                margin: 0;
                padding: 0;
            }}
            .container {{
                width: 90%;
                max-width: 650px;
                margin: 30px auto;
                background: #ffffff;
                border-radius: 10px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.05);
                overflow: hidden;
            }}
            .header {{
                background-color: #007bff;
                color: white;
                padding: 15px 20px;
                text-align: center;
            }}
            .header img {{
                height: 60px;
                margin-bottom: 10px;
            }}
            .job {{
                border-bottom: 1px solid #eee;
                padding: 12px 18px;
            }}
            .job:last-child {{
                border-bottom: none;
            }}
            .job a {{
                color: #007bff;
                font-weight: 600;
                text-decoration: none;
            }}
            .footer {{
                text-align: center;
                font-size: 13px;
                color: #999;
                padding: 15px;
                border-top: 1px solid #eee;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="{logo_url}" alt="PyRemote-AI Logo">
                <h2>PyRemote-AI Job Digest</h2>
                <p>Your personalized AI-curated remote jobs ✉️</p>
            </div>
            <div class="content">
    """

    if not jobs:
        html += "<p style='padding:20px;'>No new job results found this time. Try updating your keywords!</p>"
    else:
        for job in jobs:
            title = job.get("Title", "N/A")
            company = job.get("Company", "N/A")
            loc = job.get("Location", "Remote")
            url = job.get("URL", "")
            src = job.get("Source", "")
            html += f"""
                <div class="job">
                    <a href="{url}" target="_blank">{title}</a><br>
                    <span style="color:#555;">{company} — {loc}</span><br>
                    <small style="color:#888;">Source: {src}</small>
                </div>
            """

    html += f"""
            </div>
            <div class="footer">
                <p>Delivered with ❤️ by <b>PyRemote-AI</b><br>
                Created by <a href="https://github.com/Akhilesh-Ankur09" style="color:#007bff;text-decoration:none;">Akhilesh Ankur</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def send_email(jobs, recipient=None):
    """Send branded HTML email using Gmail credentials."""
    creds = load_credentials()
    sender = creds.get("sender_email")
    password = creds.get("app_password")

    if not sender or not password:
        raise ValueError("Email or password missing. Check Streamlit secrets or config.json.")
    if not recipient:
        raise ValueError("Recipient email is required.")

    # Create email
    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = "Your PyRemote-AI Job Results — Curated Just for You 🌍"

    html_body = build_html_email(jobs, recipient)
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        print(f"✅ Email successfully sent to {recipient}")
    except Exception as e:
        raise Exception(f"SMTP error: {e}")
