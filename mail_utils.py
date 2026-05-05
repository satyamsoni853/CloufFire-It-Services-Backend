import asyncio
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))


def _build_otp_html(otp: str) -> str:
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f9f9f9; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background-color: white; padding: 40px; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #ff7301; margin: 0;">Cloudfire IT Services</h2>
                    <p style="color: #666; font-size: 14px;">Email Verification</p>
                </div>
                <p>Hello,</p>
                <p>Thank you for choosing Cloudfire IT Services. Use the following OTP to verify your email address. This OTP is valid for 10 minutes.</p>
                <div style="text-align: center; margin: 40px 0;">
                    <span style="font-size: 40px; font-weight: 800; letter-spacing: 8px; color: #ff7301; background-color: #fff9f5; padding: 15px 30px; border-radius: 12px; border: 2px dashed #ff7301;">
                        {otp}
                    </span>
                </div>
                <p style="font-size: 13px; color: #999; text-align: center;">If you did not request this code, please ignore this email.</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 11px; color: #bbb; text-align: center;">&copy; 2026 Cloudfire IT Services. All rights reserved.</p>
            </div>
        </body>
    </html>
    """


def _send_email_sync(email: str, otp: str) -> None:
    if not SMTP_USER or not SMTP_PASSWORD or not SMTP_SERVER:
        raise RuntimeError("SMTP configuration is incomplete")

    message = MIMEMultipart("alternative")
    message["Subject"] = f"{otp} is your Cloudfire IT Services verification code"
    message["From"] = SMTP_USER
    message["To"] = email
    message.attach(MIMEText(_build_otp_html(otp), "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, [email], message.as_string())


async def send_otp_email(email: str, otp: str):
    await asyncio.to_thread(_send_email_sync, email, otp)


def _send_notification_sync(email: str, subject: str, body: str) -> None:
    if not SMTP_USER or not SMTP_PASSWORD or not SMTP_SERVER:
        return  # Or log warning

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SMTP_USER
    message["To"] = email
    
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f9f9f9; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background-color: white; padding: 40px; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #ff7301; margin: 0;">Cloudfire IT Services</h2>
                    <p style="color: #666; font-size: 14px;">Notification</p>
                </div>
                <p>Hello,</p>
                <p>{body}</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 11px; color: #bbb; text-align: center;">&copy; 2026 Cloudfire IT Services. All rights reserved.</p>
            </div>
        </body>
    </html>
    """
    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, [email], message.as_string())


async def send_notification_email(email: str, subject: str, body: str):
    await asyncio.to_thread(_send_notification_sync, email, subject, body)

async def send_sms_notification(mobile: str, message: str):
    # Mock SMS Implementation
    # In a real app, integrate with Twilio or Vonage
    print(f"DEBUG: Sending SMS to {mobile}: {message}")
    await asyncio.sleep(0.1) # Simulate network delay
    return True
