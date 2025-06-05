import smtplib
from email.mime.text import MIMEText
import os

SMTP_SERVER = os.getenv("MAILHOG_HOST", "mailhog")     
SMTP_PORT = int(os.getenv("MAILHOG_PORT", "1025"))
FROM_EMAIL = "noreply@factually.com"

def send_email(recipient: str, subject: str, body: str):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = recipient

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        # ONLY IF AUTHENTICATION IS REQUIRED, NOT THE CASE WITH MAILHOG
        # server.starttls()
        # server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, [recipient], msg.as_string())