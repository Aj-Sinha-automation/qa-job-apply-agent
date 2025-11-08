import smtplib, os
from email.message import EmailMessage

def send_email(to_email, subject, body, attachment_path=None):
    msg = EmailMessage()
    msg["From"] = os.getenv("SENDER_EMAIL")
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment_path:
        with open(attachment_path, "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="octet-stream", filename=os.path.basename(attachment_path))
    
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(os.getenv("SENDER_EMAIL"), os.getenv("EMAIL_PASSWORD"))
        smtp.send_message(msg)
