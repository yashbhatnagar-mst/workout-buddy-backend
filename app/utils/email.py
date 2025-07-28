import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.settings import settings

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

def send_verification_email(to_email: str, otp: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify Your WorkOut Buddy Account"
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
        .otp-box {{
            font-size: 24px;
            font-weight: bold;
            color: #007BFF;
            background-color: #f0f8ff;
            padding: 12px;
            text-align: center;
            border-radius: 5px;
            margin: 20px 0;
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
            <h2>Email Verification Required</h2>
            <p>Hello,</p>
            <p>Thank you for registering with WorkOut Buddy! Please verify your email using the OTP below:</p>
            <div class="otp-box">{otp}</div>
            <p>This OTP will expire in 10 minutes. If you didn’t request this, please ignore this email.</p>
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
