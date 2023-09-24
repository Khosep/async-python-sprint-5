import pathlib

from pydantic import BaseModel, PostgresDsn, DirectoryPath, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent  # abs path to \src
ENV_PATH = pathlib.Path(BASE_DIR.parent, '.env')


class PaginationParams(BaseModel):
    limit: int = 10
    offset: int = 0


class AppPostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_PATH, env_file_encoding='utf-8', extra='ignore')

    scheme: str = 'postgresql+asyncpg'
    postgres_user: str = ...
    postgres_password: str = ...
    postgres_host: str = ...
    postgres_port: int = ...
    postgres_db: str = ...

    @property
    def dsn(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme=self.scheme,
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            path=self.postgres_db
        )


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_PATH, env_file_encoding='utf-8', extra='ignore')

    app_title: str = "File Storage"
    database_dsn: str = str(AppPostgresSettings().dsn)

    project_host: str = ...
    project_port: int = ...

    prefix: str = '/api/v1'
    docs_url: str = '/api/openapi'
    openapi_url: str = '/api/openapi.json'

    # TODO Создать каталог 'storage' в докере (не скопировать, а создать)
    storage_path: DirectoryPath = pathlib.Path(BASE_DIR.parent, 'storage')

    token_expire_minutes: int = 60
    token_secret_key: str = Field(..., alias='SECRET_KEY')
    token_jwt_algorithm: str = 'HS256'


app_settings = AppSettings()
