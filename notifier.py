import smtplib
import ssl
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(jobs):
    # Load credentials
    with open("config.json", "r") as f:
        creds = json.load(f)
    sender = creds["email"]
    password = creds["app_password"]
    receiver = creds["email"]  # send to yourself

    # Build message
    message = MIMEMultipart("alternative")
    message["Subject"] = "💼 JobTracker: New Jobs Found!"
    message["From"] = sender
    message["To"] = receiver

    if not jobs:
        html = "<p>No matching jobs found today.</p>"
    else:
        html = "<h3>Matching Jobs</h3><ul>"
        for job in jobs:
            html += f"<li><b>{job['Title']}</b> at {job['Company']} ({job['Location']})<br>"
            html += f"<a href='{job['URL']}'>Apply Here</a></li><br>"
        html += "</ul>"

    message.attach(MIMEText(html, "html"))

    # Send email securely
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, message.as_string())

    print("✅ Email sent successfully!")
