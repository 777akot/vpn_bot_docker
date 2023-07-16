import logging
from typing import Dict

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ChatType, CallbackQuery

from loader import dp, db, outline
from tgbot.keyboards.callback_data_factory import vpn_callback, partner_join_callback, admin_send_notification_callback
from tgbot.keyboards.inline import keyboard_admin_action, keyboard_servers_list, keyboard_cancel, keyboard_show_users
from tgbot.states.servers_add import AddServerState
from tgbot.states.partners_add import AddPartnerState
from tgbot.states.notification_add import AddNotificationState

from tgbot.controllers.p2p_payments import yoopay,referal_payment, check_payment, check_yoomoney

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
    # await check_payment(347207594,"v82henxufl")
    payments = await db.get_all_payments()
    for x in payments:
        print(f"\n X: {x[0][0]}")
        label = x[0][0]
        user_id = x[0][1]
        print(f"{label}\n")
        status = await check_yoomoney(label)
        key_exist = await db.get_key_all_data_by_label(label)
        
        if len(key_exist) == 0:
            print(f'KEY NOT EXIST: {key_exist}')
            await db.delete_payment_by_label(user_id, label)
            await dp.bot.send_message(message.from_user.id, f'KEY NOT EXIST. AND PAYMENT DELETED: {label}')

        else:
            key_item = key_exist[0]
            server_id = key_item['server_id']
            api_key = await db.get_server_key(int(server_id))
            key_id = key_item['outline_key_id']
            await outline.set_name_label(api_key, key_id, label)
            await dp.bot.send_message(message.from_user.id, f'KEY EXIST')

        if status:
            await dp.bot.send_message(message.from_user.id, f'L: {label}. S: {status}')
        else:
            payment_status = await db.get_payment_by_id(label, int(user_id))
            for p in payment_status:
                label = p['label']
                payment_sum = p['sum']
                payment_sum_paid = p['sum_paid']
                if payment_sum > 0 and status is None:
                    # await db.update_payment_trial(user_id, label)
                    print(f"\n Payment status: {p['sum']}")
                    await dp.bot.send_message(message.from_user.id, f'P: {p["sum"]} Paid: {payment_sum_paid==True} L: {label}')
                
            # 
    # await yoopay()

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

async def admin_send_notification(callback_query: CallbackQuery, state: FSMContext):
    print(f"\n SEND NOTIFICATION \n")
    await state.set_state(AddNotificationState.message_text)
    await dp.bot.send_message(callback_query.from_user.id, f'Введите текст сообщения:')

async def admin_send_notification_send(message: Message, state: FSMContext):
    message_text = message.text
    print(f"\n MESSAGE: {message_text} \n")
    await state.update_data(message_text=message_text)
    await state.finish()
    users = await db.show_users()
    
    for x in users:
        print(f"USER: {x}")
        user_id = x['user_id']
        # await dp.bot.send_message(x['user_id'],'Привет')
        await dp.bot.send_message(user_id, text=message_text, entities=message.entities)
    
    
async def admin_renew_trial(message: Message):
    await db.set_trial_used(message.from_user.id, False)
    await dp.bot.send_message(message.from_user.id, f'Триал обновлён')

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

    dispatcher.register_callback_query_handler(admin_renew_trial, lambda c: c.data and c.data == "renew_trial", chat_type=ChatType.PRIVATE, is_admin=True)


    dispatcher.register_message_handler(admin_test_referal, commands=["admin_referal"], chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_callback_query_handler(admin_add_partner, lambda c: c.data and c.data == "add_partner", chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_message_handler(admin_save_partner, chat_type=ChatType.PRIVATE, state=AddPartnerState.user_id)
    dispatcher.register_callback_query_handler(partner_join_approve, partner_join_callback.filter(action_type='partner_join_approve'), chat_type=ChatType.PRIVATE, is_admin=True)

    dispatcher.register_callback_query_handler(admin_send_notification, admin_send_notification_callback.filter(action_type='send_notification'), chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_message_handler(admin_send_notification_send, chat_type=ChatType.PRIVATE, state=AddNotificationState.message_text)

