from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    test_db_user: str = ...
    test_db_password: str = ...
    test_db_host: str = ...
    test_db_port: int = ...
    test_db_name: str = ...

    @property
    def dsn(self) -> str:
        return str(PostgresDsn.build(
            scheme='postgresql+asyncpg',
            username=self.test_db_user,
            password=self.test_db_password,
            host=self.test_db_host,
            port=self.test_db_port,
            path=self.test_db_name
        )
        )


test_settings = TestSettings()
