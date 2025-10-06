import smtplib
import ssl
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)

def send_email(jobs, recipient=None):
    """Send an HTML email of job listings."""
    cfg = load_config()
    sender = cfg.get("email")
    password = cfg.get("app_password")

    if recipient is None:
        recipient = sender

    message = MIMEMultipart("alternative")
    message["Subject"] = "PyRemote-AI: Your Job Matches"
    message["From"] = sender
    message["To"] = recipient

    html = "<h3>Job Matches:</h3><ul>"
    for job in jobs:
        html += f"<li><b>{job['Title']}</b> at {job['Company']} (<a href='{job['URL']}'>Apply</a>)</li>"
    html += "</ul>"

    message.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, message.as_string())

    print("Email sent successfully!")
