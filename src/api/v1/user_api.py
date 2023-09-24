from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.db import get_session
from src.exceptions import UserInactiveException
from src.models.user_model import User
from src.schemas.token_schema import Token
from src.schemas.user_schema import UserIn, UserOut
from src.services.user_service import user_service
from .base import TAG_USER, TAG_AUTH

router = APIRouter()


@router.post('/register', response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=[TAG_USER])
async def register_user(
        *,
        db: AsyncSession = Depends(get_session),
        user: UserIn
) -> User:
    # create user in DB
    new_user = await user_service.create_user_in_db(db=db, user=user)
    return new_user


@router.post('/auth', response_model=Token, tags=[TAG_AUTH])
async def login_for_access_token(
        *,
        db: AsyncSession = Depends(get_session),
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> dict:
    # User receives a token (by providing his username and password)
    user = await user_service.authenticate_user(db=db, form_data=form_data)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not user.is_active:
        raise UserInactiveException
    access_token = await user_service.get_token(username=form_data.username)
    return access_token
