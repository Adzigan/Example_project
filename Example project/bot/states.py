from aiogram.fsm.state import State, StatesGroup


class AddTransaction(StatesGroup):
    amount = State()
    category = State()
    note = State()
