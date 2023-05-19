from aiogram.dispatcher.filters.state import StatesGroup, State


class AddServerState(StatesGroup):
    server_name = State()
    api_link = State()
    price = State()
