from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    app_name: str = "Digital commerce platform"
    debug: bool = False
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    @property
    def database_url(self) -> URL:
        database_url = URL.create(
        "postgresql+psycopg",
        username=self.postgres_user,
        password=self.postgres_password,
        host=self.postgres_host,
        database=self.postgres_db,
        port=self.postgres_port,
        )
        return database_url
    

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()