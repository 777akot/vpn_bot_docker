import logging
from typing import Dict

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ChatType, CallbackQuery

from loader import dp, db, outline
from tgbot.keyboards.callback_data_factory import vpn_callback, partner_join_callback
from tgbot.keyboards.inline import keyboard_admin_action, keyboard_servers_list, keyboard_cancel, keyboard_show_users
from tgbot.states.servers_add import AddServerState
from tgbot.states.partners_add import AddPartnerState

from tgbot.controllers.p2p_payments import yoopay,referal_payment

async def admin_start(message: Message):
    await message.answer('Выберите действие:', reply_markup=keyboard_admin_action())


async def admin_add_server(callback_query: CallbackQuery, state: FSMContext):
    await dp.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await dp.bot.send_message(callback_query.from_user.id, 'Введите название сервера.\n'
                                                           'Можно использовать смайлики, например флаги стран',
                              reply_markup=keyboard_cancel())
    await state.set_state(AddServerState.server_name)
    await callback_query.answer()


async def admin_server_name(message: Message, state: FSMContext):
    server_name = message.text.strip()
    await state.update_data(server_name=server_name)
    await state.set_state(AddServerState.api_link)
    await dp.bot.send_message(message.from_user.id, f'Название сервера: {server_name}\n'
                                                    f'Введите  URL для доступа к Outline Management API',
                              reply_markup=keyboard_cancel())


async def admin_api_link(message: Message, state: FSMContext):
    url = message.text.strip()
    if url.isdigit() or url.isalpha():
        await dp.bot.send_message(message.from_user.id, 'Не похоже на ссылку')
    else:
        state_data = await state.get_data()
        server_name = state_data['server_name']
        await state.update_data(api_link=url)
        await state.set_state(AddServerState.price)
        await dp.bot.send_message(message.from_user.id, f'Стоимость сервера (месяц) {server_name}\n'
                                                    f'Введите цену',
                              reply_markup=keyboard_cancel())

async def admin_price(message: Message, state: FSMContext):
    price = message.text.strip()
    if not price.isdigit():
        await dp.bot.send_message(message.from_user.id, 'Не похоже на цену')
    else:
        state_data = await state.get_data()
        server_name = state_data['server_name']
        url = state_data['api_link']
        await state.update_data(price=price)
        await db.add_server(server_name, url, int(price))
        await dp.bot.send_message(message.from_user.id, f'Сервер {server_name} добавлен')
        await state.finish()

async def admin_testpay(message: Message):
    await message.answer("Тестовая выплата")
    await yoopay()

async def admin_servers_to_delete(callback_query: CallbackQuery):
    await dp.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await dp.bot.send_message(callback_query.from_user.id, 'Выберите сервер для удаления:',
                              reply_markup=await keyboard_servers_list('to_delete'))
    await callback_query.answer()


async def admin_delete_server(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    await dp.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    server_id = int(callback_data['server'])
    await db.delete_server(int(server_id))
    await dp.bot.send_message(callback_query.from_user.id, 'Сервер удалён из БД')
    await callback_query.answer()

async def admin_delete_key(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    data = await outline.delete_key()
    print("\n admin_delete_key: \n", data)

async def admin_show_users(callback_query: CallbackQuery):
    await dp.bot.send_message(callback_query.from_user.id, 'Пользователи:',
                              reply_markup=await keyboard_show_users())
    print("\n admin_show_users: \n")

async def admin_test_referal(message: Message):
    await message.answer("Тестовая выплата")
    user_id = message.from_user.id
    label = "aoqb8wxvyk"
    await referal_payment(user_id,label)

async def admin_add_partner(message: Message, state: FSMContext):
    print("\n ADMIN ADD PARTNER: \n")
    await state.set_state(AddPartnerState.user_id)
    await dp.bot.send_message(message.from_user.id, f'Введите id Пользователя:',
                            reply_markup=keyboard_cancel())

async def admin_save_partner(message: Message, state: FSMContext):
    user_id = message.text.strip()
    if not user_id.isdigit():
        await dp.bot.send_message(message.from_user.id, 'Не похоже на номер аккаунта',reply_markup=keyboard_cancel())

    candidate = await db.get_user_by_id(int(user_id))
    if not candidate or not len(candidate):
        await dp.bot.send_message(message.from_user.id, 'Нет такого пользователя',reply_markup=keyboard_cancel())
    else:
        res = ""
        # state_data = await state.get_data()
        # server_name = state_data['account_number']
        await state.update_data(user_id=user_id)
        # # await db.add_server(server_name, url, int(price))
        await db.add_partner(int(user_id), "partner")
        await dp.bot.send_message(message.from_user.id, f'Аккаунт {user_id} добавлен')
        await state.finish()

async def partner_join_approve(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    await dp.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    partner_id = callback_data['partner_id']
    await db.add_partner(int(partner_id), "partner")
    print(f'\n partner_join_approve \n {partner_id}')
    await dp.bot.send_message(partner_id, 'Поздравляем ваша заявка одобрена! Теперь вы можете пользоваться личным кабинетом партнёра используя команду /partner')
    await dp.bot.send_message(callback_query.from_user.id, f'{partner_id} теперь Партнер')



def register_admin(dispatcher: Dispatcher):
    dispatcher.register_message_handler(admin_testpay, commands=["admin_pay"], chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_message_handler(admin_start, commands=["admin"], chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_callback_query_handler(admin_add_server, lambda c: c.data and c.data == 'add_server',
                                               chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_message_handler(admin_server_name, chat_type=ChatType.PRIVATE, is_admin=True, state=AddServerState.server_name)
    dispatcher.register_message_handler(admin_api_link, chat_type=ChatType.PRIVATE, is_admin=True, state=AddServerState.api_link)
    dispatcher.register_message_handler(admin_price, chat_type=ChatType.PRIVATE, is_admin=True, state=AddServerState.price)
    dispatcher.register_callback_query_handler(admin_servers_to_delete, lambda c: c.data and c.data == 'delete_server',
                                               chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_callback_query_handler(admin_delete_server, vpn_callback.filter(action_type='to_delete'), chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_callback_query_handler(admin_delete_key, lambda c: c.data and c.data == 'delete_key', chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_callback_query_handler(admin_show_users, lambda c: c.data and c.data == "show_users", chat_type=ChatType.PRIVATE, is_admin=True)


    dispatcher.register_message_handler(admin_test_referal, commands=["admin_referal"], chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_callback_query_handler(admin_add_partner, lambda c: c.data and c.data == "add_partner", chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_message_handler(admin_save_partner, chat_type=ChatType.PRIVATE, state=AddPartnerState.user_id)

    dispatcher.register_callback_query_handler(partner_join_approve, partner_join_callback.filter(action_type='partner_join_approve'), chat_type=ChatType.PRIVATE, is_admin=True)

    

