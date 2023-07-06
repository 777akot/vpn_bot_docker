from aiogram.dispatcher.filters.state import StatesGroup, State


class AddPartnerState(StatesGroup):
    account = State()
