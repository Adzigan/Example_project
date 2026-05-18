import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.database.session import init_db
from bot.network import ensure_telegram_reachable
from bot.handlers import start, stats, transactions
from bot.middlewares.db import DbSessionMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    await init_db()
    await ensure_telegram_reachable(settings.bot_proxy)

    session = AiohttpSession(proxy=settings.bot_proxy) if settings.bot_proxy else None
    bot = Bot(
        token=settings.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    if settings.bot_proxy:
        logger.info("Using proxy for Telegram API")
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DbSessionMiddleware())

    dp.include_router(start.router)
    dp.include_router(transactions.router)
    dp.include_router(stats.router)

    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
