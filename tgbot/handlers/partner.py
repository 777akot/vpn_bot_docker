import logging
from typing import Dict
import math

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ChatType, CallbackQuery

from loader import dp, db, outline, admin_ids
from tgbot.keyboards.callback_data_factory import vpn_callback
from tgbot.keyboards.inline import keyboard_servers_list, keyboard_cancel, keyboard_show_users, keyboard_partner_action, keyboard_partner_join, keyboard_admin_partner_submit
from tgbot.states.partners_add_account import AddPartnerState

from tgbot.controllers.p2p_payments import yoopay,referal_payment

async def check_partner(user_id):
    try:
        partner = await db.check_referal(user_id, "partner")
        if not partner:
            return False
        else: 
            return True
    except Exception as e:
        print(f"ERROR: {e}")

async def get_user_data(user_id):
    try:
        user = await db.get_user_by_id(user_id)
        referals = await db.get_referal_users(user_id)
        payments = await db.get_payment_by_referer_id(user_id)
        payments_sum = 0
        if payments and len(payments) > 0:
            for x in payments:
                # print(f"\n FOR X : {x[0][0]} \n")
                payments_sum += max(2, math.floor(x[0][0] * x[0][1] / 100))

        if user and len(user) > 0:
            res = {'user':user[0], 'referals': referals, 'payments_sum': payments_sum}
            return res
        else:
            return None
    except Exception as e:
        print(f'ERROR: {e}')

async def partner_start(message: Message):
    ispartner = await check_partner(message.from_user.id)
    user = await get_user_data(message.from_user.id)
    print(f"\n USER: {user}")
    referal_users = user["referals"]
    payments_sum = user["payments_sum"]
    paid_referal_users = 0
    if len(referal_users) > 0:
        for x in referal_users:
            if x[0] == True:
                paid_referal_users += 1
    bot_info = await dp.bot.get_me()
    ref_link = f'https://t.me/{bot_info.username}?start={message.from_user.id}'

    if not ispartner:
        await dp.bot.send_message(message.from_user.id, f'Вы вошли в закрытую зону только для участников партнёрской программы\n'
                                                        f'Для того чтобы стать партнёром подайте заявку',
                                  reply_markup=keyboard_partner_join())

    else:
        await message.answer(f'Личный кабинет Партнёра\n\n'
                             f'Ваша реферальная ссылка:\n'
                             f'<code>{ref_link}</code> \n'
                             f'Привлеченные пользователи:\n'
                             f'{len(referal_users)} из них оплатили {paid_referal_users}\n'
                             f'Получено выплат: {payments_sum} руб\n\n'
                             , 
                             reply_markup=keyboard_partner_action())

async def partner_add_account(message: Message, state: FSMContext):
    ispartner = await check_partner(message.from_user.id)
    if not ispartner:
        await dp.bot.send_message(message.from_user.id, f'По поводу партнерства обратитесь к администратору')
    else:
        await state.set_state(AddPartnerState.account)
        await dp.bot.send_message(message.from_user.id, f'Введите 16-ти значный номер аккаунта Yoo:',
                                reply_markup=keyboard_cancel())

async def save_partner(message: Message, state: FSMContext):
    ispartner = await check_partner(message.from_user.id)
    if not ispartner:
        await dp.bot.send_message(message.from_user.id, f'По поводу партнерства обратитесь к администратору')
    else:
        account = message.text.strip()
        if not account.isdigit():
            await dp.bot.send_message(message.from_user.id, 'Не похоже на номер аккаунта')
        if not len(str(account)) == 16:
            await dp.bot.send_message(message.from_user.id, 'Введите 16-ти значный номер аккаунта Yoo')
        else:
            res = ""
            # state_data = await state.get_data()
            # server_name = state_data['account_number']
            await state.update_data(account=account)
            await db.add_account(message.from_user.id, account)
            await dp.bot.send_message(message.from_user.id, f'Вы успешно добавили кошелек {account} !')
            await state.finish()

async def partner_submit(message: Message):
    
    for x in admin_ids:
        await dp.bot.send_message(x, f'Тут одному приспичило {message.from_user}',
                                  reply_markup=keyboard_admin_partner_submit(message.from_user.id))
    await dp.bot.send_message(message.from_user.id, f'Ваша заявка принята на рассмотрение. Дожитесь уведомления о результате')

def register_partner(dispatcher: Dispatcher):
    dispatcher.register_message_handler(partner_start, commands=["partner"], chat_type=ChatType.PRIVATE)
    dispatcher.register_callback_query_handler(partner_add_account, lambda c: c.data and c.data == 'add_account',
                                               chat_type=ChatType.PRIVATE)
    dispatcher.register_message_handler(save_partner, chat_type=ChatType.PRIVATE, state=AddPartnerState.account)
    dispatcher.register_callback_query_handler(partner_submit, lambda c: c.data and c.data == 'partner_join',
                                               chat_type=ChatType.PRIVATE)
