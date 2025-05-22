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


async def send_survey_contribution_email(
    admin_email: str,
    survey_title: str,
    submitter_name: str,
    submitter_email: str,
    submitter_org: str,
    justification: str,
    file_path: str,
    user_id: int,
) -> None:
    """Send an email notification about a new survey contribution with the PDF attached."""
    message = EmailMessage()
    message["Subject"] = f"New Survey Contribution: {survey_title}"
    message["From"] = "Survey Accelerator Support"
    message["To"] = admin_email
    message["Cc"] = "mark.botterill@idinsight.org"

    # Set the plain text content as a fallback
    message.set_content(
        f"A new survey has been submitted to Survey Accelerator for review.\n\n"
        f"Details:\n"
        f"- Survey Title: {survey_title}\n"
        f"- Submitted by: {submitter_name} ({submitter_email})\n"
        f"- Organization: {submitter_org}\n\n"
        f"Justification for inclusion:\n{justification}\n\n"
        f"The survey PDF is attached to this email for your review."
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
            <h2 style="color:#d29e01; margin-bottom:20px;">New Survey Contribution</h2>
            A new survey has been submitted to Survey Accelerator for review.
          </td>
        </tr>
        <tr>
          <td style="font-family:Arial, sans-serif; font-size:16px; color:#ffffff; padding:16px; background-color:#002b59; border-radius:4px; margin-bottom:16px;">
            <p><strong>Survey Title:</strong> {survey_title}</p>
            <p><strong>Submitted by:</strong> {submitter_name} ({submitter_email})</p>
            <p><strong>Organization:</strong> {submitter_org}</p>
          </td>
        </tr>
        <tr>
          <td style="font-family:Arial, sans-serif; font-size:16px; color:#ffffff; padding-top:16px;">
            <p><strong>Justification for inclusion:</strong></p>
            <p style="padding:10px; background-color:#002b59; border-radius:4px;">{justification}</p>
          </td>
        </tr>
        <tr>
          <td style="font-family:Arial, sans-serif; font-size:16px; color:#ffffff; padding:16px 0;">
            <p>The PDF is attached to this email for your convenience.</p>
            <p>Please review this contribution and contact the submitter if necessary.</p>
          </td>
        </tr>
        <tr>
          <td style="font-family:Arial, sans-serif; font-size:12px; color:#999999; border-top:1px solid #444; padding-top:16px; text-align:center;">
            &copy; 2025 IDinsight. All rights reserved.<br>
            This is an automated notification from the Survey Accelerator platform.
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</html>
"""

    message.add_alternative(html_content, subtype="html")

    # Attach the PDF file
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            pdf_data = f.read()
            # Get just the filename without the path
            filename = os.path.basename(file_path)
            message.add_attachment(
                pdf_data, maintype="application", subtype="pdf", filename=filename
            )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(message)
