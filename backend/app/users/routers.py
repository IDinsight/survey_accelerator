from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_session
from ..users.models import UsersDB
from ..users.utils import send_password_reset_email
from ..utils import get_password_salted_hash
from .schemas import UserCreate, UserOut

TAG_METADATA = {
    "name": "User Management",
    "description": "Endpoints for adding, deleting and modifying users.",
}

router = APIRouter(
    prefix="/users",
    tags=[TAG_METADATA["name"]],
)


@router.post("/create", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session),
) -> UserOut:
    hashed = await get_password_salted_hash(user_data.password)
    new_user = UsersDB(email=user_data.email, hashed_password=hashed)

    session.add(new_user)
    try:
        await session.commit()
        await session.refresh(new_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        ) from None
    user_out = UserOut.model_validate(new_user)
    user_out.action_taken = "created"
    return user_out


@router.post("/password-reset", status_code=status.HTTP_200_OK)
async def reset_password(
    email: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """
    Sends a password reset email with a temporary password.
    """
    try:
        await send_password_reset_email(email, session)
    except HTTPException as exc:
        # propagate 404 if user not found
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            raise exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset email.",
        ) from None
    return {"message": "Password reset email sent successfully."}
