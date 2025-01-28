from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from ..config import API_SECRET_KEY

bearer = HTTPBearer()


async def authenticate_key(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> None:
    """
    Authenticate using basic bearer token. Used for calling
    the question-answering endpoints. In case the JWT token is
    provided instead of the API key, it will fall back to JWT
    """
    token = credentials.credentials
    if token != API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
