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
  <table width="100%" cellpadding="0" cellspacing="0" bgcolor="#001f3f" style="background-color:#001f3f; padding:20px;">
  <tr>
    <td align="center">
      <!-- Content container -->
      <table width="600" cellpadding="0" cellspacing="0">
        <tr>
          <td style="font-family:Arial, sans-serif; font-size:16px; color:#ffffff; padding-bottom:16px;">
            Hi there,
          </td>
        </tr>
        <tr>
          <td style="font-family:Arial, sans-serif; font-size:16px; color:#ffffff; padding-bottom:16px;">
            Your new temporary password is:
          </td>
        </tr>
        <tr>
          <td align="center" style="padding:20px 0;">
            <span style="display:inline-block; background-color:#f4f4f4; color:#d29e01; font-size:20px; font-weight:bold; padding:10px 20px; border-radius:4px;">
              {new_password}
            </span>
          </td>
        </tr>
        <tr>
          <td style="font-family:Arial, sans-serif; font-size:16px; color:#ffffff; padding-bottom:32px;">
            You can use this password to sign in, then reset your password.
          </td>
        </tr>
        <tr>
  <td style="font-family:Arial, sans-serif; font-size:12px; color:#999999; border-top:1px solid #444; padding-top:16px; text-align:center;">
    &copy; 2025 IDinsight. All rights reserved.<br>
    If you have any issues or suggestions for surveys to add to Survey Accelerator, please email 
    <a href="mailto:surveyaccelerator@idinsight.org" style="color:#d29e01; text-decoration:none;">surveyaccelerator@idinsight.org</a>
  </td>
</tr>
      </table>
    </td>
  </tr>
</table>

</html>


"""

    message.add_alternative(html_content, subtype="html")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(message)
