import os
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("SMTP_USER"),
    MAIL_PASSWORD=os.getenv("SMTP_PASSWORD"),
    MAIL_FROM=os.getenv("SMTP_USER"),
    MAIL_PORT=int(os.getenv("SMTP_PORT", "587")),
    MAIL_SERVER=os.getenv("SMTP_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_otp_email(email: str, otp: str):
    html = f"""
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
                <p style="font-size: 11px; color: #bbb; text-align: center;">© 2026 Cloudfire IT Services. All rights reserved.</p>
            </div>
        </body>
    </html>
    """

    message = MessageSchema(
        subject=f"{otp} is your Cloudfire IT Services verification code",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)
