import re

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import TransactionType
from bot.keyboards.main import (
    cancel_keyboard,
    expense_categories,
    income_categories,
    main_menu,
)
from bot.services.finance import add_transaction, get_or_create_user
from bot.states import AddTransaction

router = Router()

AMOUNT_RE = re.compile(r"^[\d]+([.,]\d{1,2})?$")


def _parse_amount(text: str) -> float | None:
    cleaned = text.strip().replace(",", ".")
    if not AMOUNT_RE.match(cleaned):
        return None
    value = float(cleaned)
    return value if value > 0 else None


async def _start_flow(
    message: Message, state: FSMContext, tx_type: TransactionType
) -> None:
    await state.set_state(AddTransaction.amount)
    await state.update_data(tx_type=tx_type.value)
    label = "расхода" if tx_type == TransactionType.EXPENSE else "дохода"
    await message.answer(
        f"Введите сумму {label} (например: 350 или 1200.50):",
        reply_markup=cancel_keyboard(),
    )


@router.message(Command("expense"))
@router.message(F.text == "➕ Расход")
async def start_expense(message: Message, state: FSMContext) -> None:
    await _start_flow(message, state, TransactionType.EXPENSE)


@router.message(Command("income"))
@router.message(F.text == "➕ Доход")
async def start_income(message: Message, state: FSMContext) -> None:
    await _start_flow(message, state, TransactionType.INCOME)


@router.message(F.text == "❌ Отмена", StateFilter("*"))
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu())


@router.message(AddTransaction.amount)
async def process_amount(message: Message, state: FSMContext) -> None:
    amount = _parse_amount(message.text or "")
    if amount is None:
        await message.answer("Некорректная сумма. Пример: 500 или 99.90")
        return

    await state.update_data(amount=amount)
    await state.set_state(AddTransaction.category)
    data = await state.get_data()
    kb = (
        expense_categories()
        if data["tx_type"] == TransactionType.EXPENSE.value
        else income_categories()
    )
    await message.answer("Выберите категорию:", reply_markup=kb)


@router.callback_query(AddTransaction.category, F.data.startswith("cat:"))
async def process_category(
    callback: CallbackQuery, state: FSMContext
) -> None:
    category = callback.data.removeprefix("cat:")
    await state.update_data(category=category)
    await state.set_state(AddTransaction.note)
    await callback.message.edit_text(f"Категория: {category}")
    await callback.message.answer(
        "Добавьте комментарий или отправьте «-» чтобы пропустить:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(AddTransaction.note)
async def process_note(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    note = None if (message.text or "").strip() == "-" else (message.text or "").strip()

    user = await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
    )
    tx = await add_transaction(
        session,
        user,
        TransactionType(data["tx_type"]),
        data["amount"],
        data["category"],
        note,
    )

    await state.clear()
    sign = "➕" if tx.type == TransactionType.INCOME.value else "➖"
    lines = [
        f"{sign} Записано: {float(tx.amount):.2f} ₽",
        f"Категория: {tx.category}",
    ]
    if tx.note:
        lines.append(f"Комментарий: {tx.note}")
    await message.answer("\n".join(lines), reply_markup=main_menu())
