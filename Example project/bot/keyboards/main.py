from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.services.finance import DEFAULT_EXPENSE_CATEGORIES, DEFAULT_INCOME_CATEGORIES


def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="➕ Расход")
    builder.button(text="➕ Доход")
    builder.button(text="💰 Баланс")
    builder.button(text="📊 Статистика")
    builder.button(text="📋 История")
    builder.button(text="❓ Помощь")
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Отмена")
    return builder.as_markup(resize_keyboard=True)


def categories_keyboard(categories: tuple[str, ...]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name in categories:
        builder.button(text=name, callback_data=f"cat:{name}")
    builder.adjust(2)
    return builder.as_markup()


def expense_categories() -> InlineKeyboardMarkup:
    return categories_keyboard(DEFAULT_EXPENSE_CATEGORIES)


def income_categories() -> InlineKeyboardMarkup:
    return categories_keyboard(DEFAULT_INCOME_CATEGORIES)
