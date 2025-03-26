import os

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_async_session
from ..users.models import UsersDB
from ..utils import setup_logger

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dummy-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

logger = setup_logger()

api_key_scheme = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)


async def authenticate_user(
    token: str = Security(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> UsersDB | None:
    """
    Authenticate the user using an access token.
    """

    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("user_id")
            if user_id:
                result = await session.execute(
                    select(UsersDB).where(UsersDB.user_id == user_id)
                )
                user = result.scalars().first()
                if user:
                    return user

        except jwt.PyJWTError as e:
            logger.warning(f"Token decoding failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
