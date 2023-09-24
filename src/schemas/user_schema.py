from pydantic import BaseModel, EmailStr


class BaseUser(BaseModel):
    username: str
    email: EmailStr


class UserIn(BaseUser):
    password: str


class UserOut(BaseUser):
    pass


class Username(BaseModel):
    username: str


class UserInDB(BaseModel):
    username: str
    email: EmailStr
    hashed_password: bytes
    is_active: bool | None = True
