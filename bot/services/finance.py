from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Transaction, TransactionType, User

DEFAULT_EXPENSE_CATEGORIES = (
    "Еда",
    "Транспорт",
    "Жильё",
    "Развлечения",
    "Здоровье",
    "Покупки",
    "Другое",
)
DEFAULT_INCOME_CATEGORIES = ("Зарплата", "Подработка", "Подарок", "Другое")


async def get_or_create_user(
    session: AsyncSession, telegram_id: int, username: str | None
) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    elif username and user.username != username:
        user.username = username
        await session.commit()
    return user


async def add_transaction(
    session: AsyncSession,
    user: User,
    tx_type: TransactionType,
    amount: float,
    category: str,
    note: str | None = None,
) -> Transaction:
    tx = Transaction(
        user_id=user.id,
        type=tx_type.value,
        amount=amount,
        category=category,
        note=note,
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    return tx


async def get_balance(session: AsyncSession, user_id: int) -> tuple[float, float, float]:
    income_q = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.INCOME.value,
    )
    expense_q = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE.value,
    )
    income = float((await session.execute(income_q)).scalar_one())
    expense = float((await session.execute(expense_q)).scalar_one())
    return income, expense, income - expense


async def get_recent_transactions(
    session: AsyncSession, user_id: int, limit: int = 10
) -> list[Transaction]:
    result = await session.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_month_stats(
    session: AsyncSession, user_id: int
) -> tuple[float, float, dict[str, float]]:
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    base = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.created_at >= month_start,
    )

    income = 0.0
    expense = 0.0
    by_category: dict[str, float] = {}

    result = await session.execute(base)
    for tx in result.scalars().all():
        amount = float(tx.amount)
        if tx.type == TransactionType.INCOME.value:
            income += amount
        else:
            expense += amount
            by_category[tx.category] = by_category.get(tx.category, 0) + amount

    return income, expense, by_category


async def get_period_expense(
    session: AsyncSession, user_id: int, days: int
) -> float:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    q = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE.value,
        Transaction.created_at >= since,
    )
    return float((await session.execute(q)).scalar_one())
