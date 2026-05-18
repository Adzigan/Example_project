from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )

    bot_token: str
    database_url: str = "postgresql+asyncpg://finance:finance@localhost:5432/finance"
    # http://127.0.0.1:7890  или  socks5://127.0.0.1:1080  (нужен VPN/прокси, если Telegram заблокирован)
    bot_proxy: str | None = None


settings = Settings()
