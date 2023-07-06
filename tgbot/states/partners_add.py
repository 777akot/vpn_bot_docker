from aiogram.dispatcher.filters.state import StatesGroup, State


class AddPartnerState(StatesGroup):
    user_id = State()
