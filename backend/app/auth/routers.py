from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..auth.schemas import UserLoginDetails
from ..database import get_async_session
from ..users.models import UsersDB
from ..utils import verify_password_salted_hash
from .utils import create_access_token

router = APIRouter(tags=["Authentication"])

TAG_METADATA = {
    "name": "Authentication",
    "description": "Auth endpoints.",
}


@router.post("/login", response_model=UserLoginDetails)
async def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
) -> UserLoginDetails:
    """
    Login to the application
    """
    result = await session.execute(
        select(UsersDB).where(UsersDB.email == user_credentials.username)
    )
    user = result.scalars().first()

    # Check if user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not recognized.",
        )

    # Verify password
    if not verify_password_salted_hash(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password"
        )
    access_token = await create_access_token(data={"user_id": user.user_id})

    return UserLoginDetails(
        email=user.email,
        user_id=user.user_id,
        created_at=user.created_at,
        action_taken="Logged in",
        access_token=access_token,
    )
