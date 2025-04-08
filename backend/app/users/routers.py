from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_async_session
from ..users.models import UsersDB
from ..users.utils import send_password_reset_email
from ..utils import get_password_salted_hash, verify_password_salted_hash
from .schemas import PasswordChange, UserCreate, UserOut
from ..auth.dependencies import authenticate_user

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
    hashed = get_password_salted_hash(user_data.password)
    new_user = UsersDB(
        email=user_data.email,
        organization=user_data.organization,
        role=user_data.role,
        hashed_password=hashed,
    )

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


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user: UsersDB = Depends(authenticate_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """
    Changes the password for the authenticated user.
    Requires the current password and new password.
    """
    # Verify current password
    if not verify_password_salted_hash(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        )

    # Hash the new password
    new_hashed_password = get_password_salted_hash(password_data.new_password)

    # Update the user's password
    stmt = select(UsersDB).where(UsersDB.id == current_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user.hashed_password = new_hashed_password
    session.add(user)

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update password: {str(e)}",
        ) from None

    return {"message": "Password changed successfully."}
