from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    surreal_url: str = "ws://surrealdb:8000/rpc"
    surreal_ns: str = "tnved"
    surreal_db: str = "main"
    surreal_user: str = "root"
    surreal_pass: str = "root"

    admin_user: str
    admin_password: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    telegram_bot_token: str

    static_dir: str = "/app/static"


settings = Settings()
