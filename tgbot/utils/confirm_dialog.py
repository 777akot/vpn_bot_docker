from aiogram import types
from aiogram import Dispatcher

from loader import dp, db, bot, outline, quickpay, key_config, referer_config, admin_ids

async def confirm_dialog(event, action_function):
    
    # Создание InlineKeyboardButton для подтверждения действия
    confirm_button = types.InlineKeyboardButton("Подтвердить", callback_data='confirm_action')
    cancel_button = types.InlineKeyboardButton("Отменить", callback_data='cancel_action')

    # Создание InlineKeyboardMarkup с кнопками
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(confirm_button, cancel_button)

    if isinstance(event, types.Message):
        msg = await event.reply("Вы уверены, что хотите выполнить это действие?", reply_markup=keyboard)
    elif isinstance(event,types.CallbackQuery):
        await bot.send_message(event.message.chat.id, "Вы уверены, что хотите выполнить это действие?", reply_markup=keyboard)
    # Отправка сообщения с запросом подтверждения
    

    # try:
    #     callback_query = await dp.current_context().wait_for_callback_query(timeout=60)
    # except Exception as e:
    #     print(f"\n ERROR: {e} \n")
    #     callback_query = None

    # if callback_query and callback_query.data == 'confirm_action':
    #     # Вызов функции при подтверждении
    #     await action_function()

    #     # Отправка ответа пользователю
    #     await callback_query.message.answer("Действие подтверждено!")
    # elif callback_query and callback_query.data == 'cancel_action':
    #     # Отправка ответа пользователю
    #     await callback_query.message.answer("Действие отменено.")

    # def register_confirm_dialog(dispatcher: Dispatcher):
    #     dispatcher.register_callback_query_handler(confirm_callback, lambda c: c.data and c.data == 'confirm_action', state='*')
        