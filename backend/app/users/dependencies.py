from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from jose import jwt, JWTError
from datetime import datetime, timezone
from app.config import get_auth_data
from app.users.exceptions import TokenExpiredException, NoJwtException, NoUserIdException, ForbiddenException
from app.users.dao import UsersDAO
from app.users.models import User


def get_token(request: Request):
    token = request.cookies.get("user_access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not found')
    return token


async def get_current_user(token: str = Depends(get_token)):
    try:
        auth_data = get_auth_data()
        payload = jwt.decode(token, auth_data['secret_key'], algorithms=[auth_data['algorithm']])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Токен не валідний!')

    expire = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Токен вже не дійсний')

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Не знайдено ID користувача')

    user = await UsersDAO.find_one_or_none_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Користувач не знайдент')

    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.is_admin:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                        detail='Недостатньо прав користувача!')



async def get_current_hospital_staff(current_user: User = Depends(get_current_user)):
    if current_user.is_hospital_staff:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, 
        detail='Недостатньо прав користувача! Доступ дозволено лише медичному персоналу.'
    )

def get_admin_or_hospital_staff(current_user: User = Depends(get_current_user)):
    """Allow access to either admins or hospital staff"""
    if current_user.is_admin or current_user.is_hospital_staff:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail='Необхідні права адміністратора або медичного персоналу'
    )


async def get_current_user_optional(request: Request) -> Optional[User]:
    """
    Get the current user if authenticated, or None if not authenticated.
    Unlike get_current_user, this doesn't raise an exception for anonymous users.
    """
    token = request.cookies.get("user_access_token")
    if not token:
        return None
        
    try:
        auth_data = get_auth_data()
        payload = jwt.decode(token, auth_data['secret_key'], algorithms=[auth_data['algorithm']])
        
        expire = payload.get('exp')
        if expire:
            expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
            if expire_time < datetime.now(timezone.utc):
                return None
                
        user_id = payload.get('sub')
        if not user_id:
            return None
            
        user = await UsersDAO.find_one_or_none_by_id(int(user_id))
        return user
    except JWTError:
        return None