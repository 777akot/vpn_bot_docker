import logging
from typing import Dict
import traceback

from aiogram import Dispatcher, exceptions
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ChatType, CallbackQuery

from loader import dp, db, outline, admin_ids
from tgbot.keyboards.callback_data_factory import vpn_callback, partner_join_callback, admin_send_notification_callback
from tgbot.keyboards.inline import keyboard_admin_action, keyboard_servers_list, keyboard_cancel, keyboard_show_users
from tgbot.states.servers_add import AddServerState
from tgbot.states.partners_add import AddPartnerState
from tgbot.states.notification_add import AddNotificationState

from tgbot.controllers.p2p_payments import yoopay,referal_payment, check_yoomoney, admin_check_yoomoney
from tgbot.controllers import key_controller, p2p_payments, notifications_controller
# from tgbot.controllers.graph_controller import handle_plot_command


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

    # await handle_plot_command(dp.bot, message.chat.id)
    return
    # await check_payment(347207594,"v82henxufl")
    users = await db.show_users()
    errors = []
    live = []
    dead = []
    for x in users:
        try:
            chat = await dp.bot.get_chat(x['user_id'])
            print(chat)
            if chat and chat['ok']:
                print("OK")
                live.append(x['user_id'])
            else:
                print(f"NOT OK: {chat}")
                dead.append(x['user_id'])
        except Exception as e:
            errors.append(x['user_id'])
            dead.append(x['user_id'])
            print(f"Error: {e}")
            traceback.print_exc()

    if len(errors) > 0:
        for e in errors:
            print(f"\n {e}")

    print(f"\n LIVE ({len(live)}): \n{','.join(map(str, live))}")
    print(f"\n DEAD ({len(dead)}): \n{','.join(map(str, dead))}")
    print(f"\n ERRORS ({len(errors)}): \n{','.join(map(str, errors))}")
    return

    
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
    print("\n admin_show_users: \n")
    try:
        users = await db.show_users()
        chunk_size = 50
        # for i in range(0, len(users), chunk_size):
        # for i in range(0, chunk_size):
        users_chunk = users[:chunk_size]
        await dp.bot.send_message(callback_query.from_user.id, f'Пользователи: {len(users)}',
                            reply_markup=await keyboard_show_users(users_chunk))
    except Exception as e:
        print(f"ERROR: {e}")
    

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
    errors = []
    sliced_users = users
    for x in sliced_users:
        try:
            print(f"USER: {x}")
            user_id = x['user_id']
            trial_used = x['trial_used']
            if trial_used == False:
                await dp.bot.send_message(user_id, text=message_text, entities=message.entities)
            # await dp.bot.send_message(x['user_id'],'Привет')
        except Exception as e:
            if isinstance(e, exceptions.BotBlocked):
                await db.set_user_dead(user_id)
            errors.append(x)
            print(f"ERROR: {e}")
    
    if len(errors) > 0:
        print(f"\n Errors: {errors}")
    
async def admin_renew_trial(message: Message):
    await db.set_trial_used(message.from_user.id, False)
    await dp.bot.send_message(message.from_user.id, f'Триал обновлён')


async def text_process(message: Message):
    if message.text == '🛠 Админка':
        await dp.bot.delete_message(message.chat.id, message.message_id)
        if message.chat.id in admin_ids:
            msg = message
            msg.text = "/admin"
            await admin_start(msg)

async def admin_trial_all(message: Message):
    try:
        print(f"\n ADMIN_TRIAL_PROLONG_ALL:")
        await key_controller.trial_prolong_for_all()

    except Exception as e:
        print(f"ERROR: ADMIN_TRIAL_PROLONG_ALL '{e}'")

async def admin_set_trial_sum(message: Message):
    try:
        print(f"admin_set_trial_sum:")
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
                print(f'KEY NOT EXIST. AND PAYMENT DELETED: {label}')
                # await dp.bot.send_message(message.from_user.id, f'KEY NOT EXIST. AND PAYMENT DELETED: {label}')

            else:
                key_item = key_exist[0]
                server_id = key_item['server_id']
                api_key = await db.get_server_key(int(server_id))
                key_id = key_item['outline_key_id']
                await outline.set_name_label(api_key, key_id, label)
                print(f'KEY EXIST')
                # await dp.bot.send_message(message.from_user.id, f'KEY EXIST')

            if status:
                await dp.bot.send_message(message.from_user.id, f'L: {label}. S: {status}')
            else:
                payment_status = await db.get_payment_by_id(label, int(user_id))
                for p in payment_status:
                    label = p['label']
                    payment_sum = p['sum']
                    payment_sum_paid = p['sum_paid']
                    if payment_sum > 0 and status is None:
                        await db.update_payment_trial(user_id, label)
                        print(f"\n Payment status: {p['sum']}")
                        print(f'P: {p["sum"]} Paid: {payment_sum_paid==True} L: {label}')
                        # await dp.bot.send_message(message.from_user.id, f'P: {p["sum"]} Paid: {payment_sum_paid==True} L: {label}')
                    
    except Exception as e:
        print(f"ERROR: admin_set_trial_sum '{e}'")

async def admin_disable_expired(message):
    try:
        print(f"admin_disable_expired")
        await key_controller.delete_unused_keys()
        await p2p_payments.delete_unused_payments()
        await key_controller.disable_expired_keys()
    except Exception as e:
        print(f"ERROR: admin_disable_expired '{e}'")

async def admin_notification_expired(message):
    try:
        for x in admin_ids:
            print(f"admin_notification_expired")
            await notifications_controller.send_expiration_notification(x)
        
    except Exception as e:
        print(f"ERROR: admin_notification_expired {e}")

async def admin_checkyoo(message: Message):
    await message.answer("admin_checkyoo")
    label = 'jaq87wxfzm'
    await admin_check_yoomoney(label)

async def admin_delete_messages(message: Message):
    await message.answer("admin_delete_messages")
    chat_id = message.chat.id
    message_id = message.message_id

    chat = await dp.bot.get_chat(chat_id)
    # messages = await dp.bot.get_chat_history(chat_id=chat_id)

    print(f"CHAT: {chat}")
    # for m in messages:
    #     dp.bot.delete_message(chat_id, m.message_id)
    # await dp.bot.delete_message(chat_id, message_id)

def register_admin(dispatcher: Dispatcher):
    dispatcher.register_message_handler(admin_notification_expired, commands=["admin_notification_expired"], chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_message_handler(admin_disable_expired, commands=["admin_disable_expired"], chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_message_handler(admin_set_trial_sum, commands=["admin_set_trial_sum"], chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_message_handler(admin_trial_all, commands=["admin_trial_all"], chat_type=ChatType.PRIVATE, is_admin=True)
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

    dispatcher.register_message_handler(admin_checkyoo, commands=["admin_checkyoo"], chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_message_handler(admin_delete_messages, commands=["admin_delete_messages"], chat_type=ChatType.PRIVATE, is_admin=True)
    

