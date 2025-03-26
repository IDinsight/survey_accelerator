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
    message["From"] = SMTP_USER
    message["To"] = email
    message.set_content(
        f"Hi,\n\nYour password has been reset. Your new temporary password is:\n\n{new_password}\n\n"
        "Please log in and change it immediately."
    )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(message)
