from datetime import timedelta, datetime
from typing import Type

from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import app_settings
from src.models.user_model import User as UserModel
from src.schemas.user_schema import UserIn, UserInDB, Username
from src.services.base_service import SQLAlchemyRepository, Repository
from src.services.utils import create_hashed_password, check_password


class UserRepository(SQLAlchemyRepository):
    model = UserModel


class UserService:
    def __init__(self, repo: Type[Repository]):
        self.repo = repo()

    async def create_user_in_db(self, db: AsyncSession, user: UserIn) -> UserModel:
        hashed_password = await create_hashed_password(user.password)
        user_in_db = UserInDB(**user.model_dump(), hashed_password=hashed_password)
        new_user = await self.repo.create(db=db, obj_in=user_in_db)
        return new_user

    async def authenticate_user(self, db: AsyncSession, form_data: OAuth2PasswordRequestForm) -> UserModel | None:
        username_obj = Username(username=form_data.username)
        user = await self.repo.get(db=db, db_obj=username_obj)
        if not user or not await check_password(form_data.password, user.hashed_password):
            return None
        return user

    async def get_token(self, username: str) -> dict:
        access_token_expires = timedelta(minutes=app_settings.token_expire_minutes)
        access_token = await self._create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires,
        )
        return {"access_token": access_token, "token_type": "bearer"}

    async def _create_access_token(self, data: dict, expires_delta: timedelta) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, app_settings.token_secret_key, algorithm=app_settings.token_jwt_algorithm)
        return encoded_jwt

    async def get_user(self, db: AsyncSession, username: Username) -> UserModel:
        user = await self.repo.get(db=db, db_obj=username)
        return user


user_service = UserService(UserRepository)
