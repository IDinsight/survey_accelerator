from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """
    Base class for user schemas.
    """

    email: EmailStr = Field(..., description="The email address of the user.")


class UserCreate(UserBase):
    """
    Schema for creating a new user.
    """

    password: str = Field(..., description="The password of the new user.")
    organization: str = Field(..., description="The organization of the user.")
    role: str = Field(..., description="The role of the user.")


class UserOut(UserBase):
    """
    Schema for outputting user information. Never shows password.
    """

    user_id: int
    created_at: datetime
    action_taken: Optional[str] = None

    class Config:
        """
        Configuration for the schema.
        """

        from_attributes = True


class UserLogin(BaseModel):
    """
    Schema for user login.
    """

    email: EmailStr
    password: str


class UpdatePassword(BaseModel):
    """
    Schema for user for update password.
    """

    new_password: str


class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
