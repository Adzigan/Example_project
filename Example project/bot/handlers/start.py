from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main import main_menu
from bot.services.finance import get_or_create_user

router = Router()

WELCOME = (
    "Привет! Я бот для учёта личных финансов.\n\n"
    "Что умею:\n"
    "• записывать расходы и доходы\n"
    "• показывать баланс и статистику за месяц\n"
    "• хранить историю операций\n\n"
    "Используй кнопки меню или команды:\n"
    "/expense — добавить расход\n"
    "/income — добавить доход\n"
    "/balance — баланс\n"
    "/stats — статистика\n"
    "/history — последние операции"
)


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
    )
    await message.answer(WELCOME, reply_markup=main_menu())


@router.message(Command("help"))
@router.message(lambda m: m.text == "❓ Помощь")
async def cmd_help(message: Message) -> None:
    await message.answer(WELCOME, reply_markup=main_menu())
