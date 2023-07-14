from aiogram.dispatcher.filters.state import StatesGroup, State


class AddNotificationState(StatesGroup):
    message_text = State()
