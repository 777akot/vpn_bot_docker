from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery

from loader import dp


async def do_nothing_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await message.answer()


async def do_nothing_callback(callback_query: CallbackQuery, state: FSMContext):

    await state.finish()
    await callback_query.answer()
    current_state = await state.get_state()
    if current_state is None:
        return


def register_do_nothing(dispatcher: Dispatcher):
    dispatcher.register_callback_query_handler(do_nothing_callback, lambda c: c.data and c.data == 'do_nothing', state='*')
    dispatcher.register_message_handler(do_nothing_handler, commands=["do_nothing"], state="*")
