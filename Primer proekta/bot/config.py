from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )

    bot_token: str
    database_url: str = "sqlite+aiosqlite:///./data/finance.db"
    # http://127.0.0.1:7890  или  socks5://127.0.0.1:1080  (нужен VPN/прокси, если Telegram заблокирован)
    bot_proxy: str | None = None

    @property
    def data_dir(self) -> Path:
        if self.database_url.startswith("sqlite"):
            # sqlite+aiosqlite:///./data/finance.db
            raw = self.database_url.split("///", 1)[-1]
            return Path(raw).parent
        return Path("data")


settings = Settings()
