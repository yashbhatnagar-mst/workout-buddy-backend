import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.settings import settings  # or import directly from os.getenv()

def send_reset_email(to_email: str, reset_link: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset Your Password"
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = to_email

    html_content = f"""
    <html>
    <head>
        <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .button {{
            display: inline-block;
            padding: 12px 20px;
            margin-top: 20px;
            font-size: 16px;
            color: #ffffff;
            background-color: #007BFF;
            text-decoration: none;
            border-radius: 5px;
        }}
        .footer {{
            margin-top: 30px;
            font-size: 12px;
            color: #888888;
        }}
        </style>
    </head>
    <body>
        <div class="container">
        <h2>Password Reset Request</h2>
        <p>Hello,</p>
        <p>You have requested to reset your password. Click the button below to proceed:</p>
        <a href="{reset_link}" class="button">Reset Password</a>
        <p>If you did not request this, please ignore this email or contact support.</p>
        <div class="footer">
            <p>&copy; 2025 WorkOut Buddy. All rights reserved.</p>
        </div>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP(settings.MAILTRAP_HOST, settings.MAILTRAP_PORT) as server:
        server.starttls()
        server.login(settings.MAILTRAP_USERNAME, settings.MAILTRAP_PASSWORD)
        server.sendmail(settings.FROM_EMAIL, to_email, msg.as_string())
