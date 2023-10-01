from typing import Annotated

from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import app_settings
from src.db.db import get_session
from src.schemas.token_schema import oauth2_scheme
from src.schemas.user_schema import Username, UserInDB
from src.services.user_service import user_service


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           db: Annotated[AsyncSession, Depends(get_session)]):
    authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, app_settings.token_secret_key, algorithms=app_settings.token_jwt_algorithm)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except (JWTError, ValidationError):
        raise credentials_exception
    username_obj = Username(username=username)
    user = await user_service.get_user(db=db, username=username_obj)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Annotated[UserInDB, Depends(get_current_user)]) -> UserInDB:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
