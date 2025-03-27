import os
import secrets
import smtplib
from email.message import EmailMessage
from typing import Optional

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_async_session
from ..users.models import UsersDB
from ..utils import get_password_salted_hash

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[UsersDB]:
    result = await session.execute(select(UsersDB).where(UsersDB.email == email))
    return result.scalars().first()


async def update_user_password(
    user: UsersDB, new_password: str, session: AsyncSession
) -> None:
    user.hashed_password = get_password_salted_hash(new_password)
    await session.commit()


async def send_password_reset_email(
    email: str, session: AsyncSession = Depends(get_async_session)
) -> None:
    user = await get_user_by_email(session, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_password = secrets.token_urlsafe(12)
    await update_user_password(user, new_password, session)

    message = EmailMessage()
    message["Subject"] = "Your Password Reset"
    message["From"] = "Survey Accelerator Support"
    message["To"] = email

    # Set the plain text content as a fallback
    message.set_content(
        f"Hi,\n\nYour password has been reset. Your new temporary password is:\n\n{new_password}\n\nPlease log in and change it immediately."
    )

    # Add an HTML alternative with a styled header
    html_content = f"""
<html>
  <body style="margin: 0; padding: 20px; background-color: #f9f9f9; font-family: Arial, sans-serif; color: #333;">
    <div style="max-width: 600px; margin: auto;">
      <p style="font-size: 16px;">Hi there,</p>
      <p style="font-size: 16px;">Your new temporary password is:</p>
      <div style="margin: 20px 0; text-align: center;">
        <span style="display: inline-block; padding: 10px 20px; font-size: 20px; font-weight: bold; color: #d29e01; background-color: #f4f4f4; border-radius: 4px;">
          {new_password}
        </span>
      </div>
      <p style="font-size: 16px;">You can use this password to sign in and reset your password.</p>
      <footer style="margin-top: 40px; text-align: center; font-size: 12px; color: #999;">
        <p style="margin: 0;">&copy; 2025 IDinsight. All rights reserved.</p>
        <p style="margin: 0;">If you have any issues or suggestions for surveys to add to Survey Accelerator, please don't hesitate to email <a href="mailto:surveyaccelerator@idinsight.org" style="color: #d29e01; text-decoration: none;">surveyaccelerator@idinsight.org</a></p>
      </footer>
    </div>
  </body>
</html>
"""

    message.add_alternative(html_content, subtype="html")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(message)
