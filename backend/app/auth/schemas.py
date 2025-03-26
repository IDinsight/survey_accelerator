from pydantic import BaseModel

from ..users.schemas import UserOut


class UserLoginDetails(UserOut):
    """
    Class representing the user details model with access token.
    """

    access_token: str


class TokenData(BaseModel):
    """
    Class representing the token data model.
    """

    user_id: str
