from fastapi import status, HTTPException

UserAlreadyExistsException = HTTPException(status_code=status.HTTP_409_CONFLICT,
                                           detail='Користувач вже існує')

IncorrectEmailOrPasswordException = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                                  detail='Хибна пошта чи пароль')

TokenExpiredException = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                      detail='Токен вже не дійсний')

TokenNoFound = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail='Токен не знайден')

NoJwtException = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                               detail='Токен не валідний!')

NoUserIdException = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                  detail='Не знайдено ID користувача')

ForbiddenException = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Недостатньо прав!')