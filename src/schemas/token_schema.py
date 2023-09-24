from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from src.core.config import app_settings


class Token(BaseModel):
    access_token: str
    token_type: str

#TODO Delete
class TokenData(BaseModel):
    username: str | None = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=app_settings.prefix + "/auth")
