from jose import jwt
from datetime import datetime, timedelta, timezone

from pydantic import EmailStr
from app.config import get_auth_data
from app.users.dao import UsersDAO
from app.users.security import verify_password


def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=30)) -> str:
    """
    expire = datetime.now(timezone.utc) + expires_delta

    Args:
        data (dict): The data to encode in the token.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    auth_data = get_auth_data()
    encoded_jwt = jwt.encode(to_encode, auth_data['secret_key'],
                             algorithm=auth_data['algorithm'])
    return encoded_jwt


async def authenticate_user(email: EmailStr, password: str):
    """
    Authenticate a user by their email and password.

    Args:
        email (EmailStr): The email of the user.
        password (str): The password of the user.

    Returns:
        The authenticated user object if authentication is successful, otherwise None.
    """
    user = await UsersDAO.find_one_or_none(email=email)
    if not user or verify_password(plain_password=password, hashed_password=user.password) is False:
        return None
    return user