import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from starlette.exceptions import HTTPException

from ..utils import setup_logger
from .schemas import TokenData

ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 1 day in minutes
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dummy-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

logger = setup_logger()


async def create_access_token(data: dict) -> str:
    """
    Create a new access token with the given data.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return encoded_jwt


async def verify_access_token(
    token: str, credentials_exception: HTTPException
) -> TokenData:
    """
    Verify the access token.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except jwt.InvalidTokenError:
        raise credentials_exception from None
    return token_data
