from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import TransactionType
from bot.keyboards.main import main_menu
from bot.services.finance import (
    get_balance,
    get_month_stats,
    get_or_create_user,
    get_period_expense,
    get_recent_transactions,
)

router = Router()


def _fmt(amount: float) -> str:
    return f"{amount:,.2f}".replace(",", " ").replace(".", ",")


@router.message(Command("balance"))
@router.message(F.text == "💰 Баланс")
async def show_balance(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
    )
    income, expense, balance = await get_balance(session, user.id)
    week = await get_period_expense(session, user.id, 7)
    text = (
        f"💰 Баланс: {_fmt(balance)} ₽\n\n"
        f"Доходы: {_fmt(income)} ₽\n"
        f"Расходы: {_fmt(expense)} ₽\n"
        f"Расходы за 7 дней: {_fmt(week)} ₽"
    )
    await message.answer(text, reply_markup=main_menu())


@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
    )
    income, expense, by_category = await get_month_stats(session, user.id)
    lines = [
        "📊 Статистика за текущий месяц",
        "",
        f"Доходы: {_fmt(income)} ₽",
        f"Расходы: {_fmt(expense)} ₽",
        f"Итого: {_fmt(income - expense)} ₽",
    ]
    if by_category:
        lines.append("")
        lines.append("Расходы по категориям:")
        for cat, amount in sorted(by_category.items(), key=lambda x: -x[1]):
            lines.append(f"  • {cat}: {_fmt(amount)} ₽")
    await message.answer("\n".join(lines), reply_markup=main_menu())


@router.message(Command("history"))
@router.message(F.text == "📋 История")
async def show_history(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
    )
    txs = await get_recent_transactions(session, user.id, limit=15)
    if not txs:
        await message.answer("Пока нет операций.", reply_markup=main_menu())
        return

    lines = ["📋 Последние операции:", ""]
    for tx in txs:
        sign = "+" if tx.type == TransactionType.INCOME.value else "−"
        dt = tx.created_at.strftime("%d.%m %H:%M")
        line = f"{dt} {sign}{_fmt(float(tx.amount))} ₽ · {tx.category}"
        if tx.note:
            line += f" ({tx.note})"
        lines.append(line)
    await message.answer("\n".join(lines), reply_markup=main_menu())
