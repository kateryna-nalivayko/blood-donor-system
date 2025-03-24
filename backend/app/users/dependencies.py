from fastapi import Request, HTTPException, status, Depends
from jose import jwt, JWTError
from datetime import datetime, timezone
from app.config import get_auth_data
from app.users.exceptions import TokenExpiredException, NoJwtException, NoUserIdException, ForbiddenException
from app.users.dao import UsersDAO


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