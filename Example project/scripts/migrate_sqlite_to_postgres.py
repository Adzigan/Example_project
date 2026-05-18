"""Перенос данных из SQLite (data/finance.db) в PostgreSQL (DATABASE_URL из .env)."""

from __future__ import annotations

import argparse
import asyncio
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import Base, Transaction, User
from bot.database.session import engine

DEFAULT_SQLITE_PATH = Path("data/finance.db")


def _parse_dt(value: object) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif value is None:
        dt = datetime.now(UTC)
    else:
        s = str(value).replace("Z", "+00:00")
        if " " in s and "T" not in s:
            s = s.replace(" ", "T", 1)
        dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _load_sqlite(path: Path) -> tuple[list[sqlite3.Row], list[sqlite3.Row]]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "users" not in tables:
            raise SystemExit(f"В {path} нет таблицы users — нечего переносить.")
        users = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
        transactions = (
            conn.execute("SELECT * FROM transactions ORDER BY id").fetchall()
            if "transactions" in tables
            else []
        )
    finally:
        conn.close()
    return users, transactions


async def _ensure_pg_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _existing_users_by_telegram(session: AsyncSession) -> dict[int, int]:
    result = await session.execute(select(User.id, User.telegram_id))
    return {telegram_id: user_id for user_id, telegram_id in result.all()}


async def _reset_sequence(session: AsyncSession, table: str, column: str = "id") -> None:
    await session.execute(
        text(
            f"""
            SELECT setval(
                pg_get_serial_sequence(:table, :column),
                GREATEST(COALESCE((SELECT MAX({column}) FROM {table}), 0), 1),
                (SELECT COUNT(*) > 0 FROM {table})
            )
            """
        ),
        {"table": table, "column": column},
    )


async def migrate(
    sqlite_path: Path,
    *,
    dry_run: bool = False,
    skip_existing: bool = True,
) -> None:
    if not sqlite_path.is_file():
        raise SystemExit(f"Файл SQLite не найден: {sqlite_path.resolve()}")

    users, transactions = _load_sqlite(sqlite_path)
    print(f"SQLite: {len(users)} пользователей, {len(transactions)} транзакций")

    if dry_run:
        print("Режим --dry-run: запись в PostgreSQL не выполняется.")
        return

    await _ensure_pg_schema()

    async with AsyncSession(engine, expire_on_commit=False) as session:
        async with session.begin():
            by_telegram = await _existing_users_by_telegram(session)
            user_id_map: dict[int, int] = {}
            users_added = 0
            users_skipped = 0

            for row in users:
                old_id = row["id"]
                telegram_id = row["telegram_id"]

                if telegram_id in by_telegram:
                    user_id_map[old_id] = by_telegram[telegram_id]
                    users_skipped += 1
                    continue

                id_taken = await session.scalar(
                    select(User.id).where(User.id == old_id)
                )
                if id_taken is not None:
                    user = User(
                        telegram_id=telegram_id,
                        username=row["username"],
                        created_at=_parse_dt(row["created_at"]),
                    )
                    session.add(user)
                    await session.flush()
                    user_id_map[old_id] = user.id
                    by_telegram[telegram_id] = user.id
                    users_added += 1
                    continue

                user = User(
                    id=old_id,
                    telegram_id=telegram_id,
                    username=row["username"],
                    created_at=_parse_dt(row["created_at"]),
                )
                session.add(user)
                by_telegram[telegram_id] = old_id
                user_id_map[old_id] = old_id
                users_added += 1

            await session.flush()

            tx_added = 0
            tx_skipped = 0

            for row in transactions:
                old_user_id = row["user_id"]
                pg_user_id = user_id_map.get(old_user_id)
                if pg_user_id is None:
                    tx_skipped += 1
                    continue

                if skip_existing:
                    exists = await session.scalar(
                        select(Transaction.id).where(Transaction.id == row["id"])
                    )
                    if exists is not None:
                        tx_skipped += 1
                        continue

                session.add(
                    Transaction(
                        id=row["id"],
                        user_id=pg_user_id,
                        type=row["type"],
                        amount=row["amount"],
                        category=row["category"],
                        note=row["note"],
                        created_at=_parse_dt(row["created_at"]),
                    )
                )
                tx_added += 1

            await _reset_sequence(session, "users")
            await _reset_sequence(session, "transactions")

    print(
        f"Готово. Пользователей: +{users_added}, пропущено (уже в PG): {users_skipped}. "
        f"Транзакций: +{tx_added}, пропущено: {tx_skipped}."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Перенос data/finance.db (SQLite) в PostgreSQL из DATABASE_URL."
    )
    parser.add_argument(
        "--sqlite-path",
        type=Path,
        default=DEFAULT_SQLITE_PATH,
        help=f"Путь к SQLite-файлу (по умолчанию: {DEFAULT_SQLITE_PATH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только показать, сколько записей будет перенесено",
    )
    args = parser.parse_args()

    print(f"PostgreSQL: {settings.database_url.split('@')[-1]}")
    asyncio.run(
        migrate(args.sqlite_path, dry_run=args.dry_run, skip_existing=True)
    )


if __name__ == "__main__":
    main()
