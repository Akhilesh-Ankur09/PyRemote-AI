import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os


def send_email(jobs, recipient=None):
    """
    Send job results using Gmail SMTP and credentials from config.json.
    The config.json file must be located in the project root (same folder as app.py).
    """

    # --- Locate config.json dynamically (works locally & on Streamlit Cloud) ---
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    config_path = os.path.abspath(config_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"❌ config.json not found at: {config_path}\n"
                                "Make sure it exists next to app.py (not inside /core/).")

    # --- Load credentials safely ---
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            creds = json.load(f)
    except json.JSONDecodeError:
        raise ValueError("⚠️ config.json is invalid. Please fix formatting (check commas, quotes, etc).")
    except Exception as e:
        raise Exception(f"⚠️ Failed to read config.json: {e}")

    sender = creds.get("sender_email")
    password = creds.get("app_password")

    if not sender or not password:
        raise ValueError("❌ Email or app password missing in config.json. "
                         "Ensure keys are 'sender_email' and 'app_password'.")

    # --- Build email content ---
    body_lines = []
    for job in jobs:
        title = job.get("Title", "N/A")
        company = job.get("Company", "N/A")
        location = job.get("Location", "Remote")
        url = job.get("URL", "")
        body_lines.append(f"{title} at {company} ({location})\n{url}\n")

    body = "\n".join(body_lines) if body_lines else "No job results found."

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient or sender
    msg["Subject"] = "Your PyRemote-AI Job Results"
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # --- Send via Gmail SMTP ---
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
            print(f"✅ Email sent successfully from {sender} to {recipient or sender}")
    except smtplib.SMTPAuthenticationError:
        raise Exception("❌ Gmail authentication failed. Check your App Password and 2-Step Verification settings.")
    except Exception as e:
        raise Exception(f"⚠️ SMTP error: {e}")
