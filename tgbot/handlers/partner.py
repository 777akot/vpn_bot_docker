import logging
from typing import Dict

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ChatType, CallbackQuery

from loader import dp, db, outline
from tgbot.keyboards.callback_data_factory import vpn_callback
from tgbot.keyboards.inline import keyboard_admin_action, keyboard_servers_list, keyboard_cancel, keyboard_show_users, keyboard_partner_action
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

async def partner_start(message: Message):
    ispartner = await check_partner(message.from_user.id)
    if not ispartner:
        await dp.bot.send_message(message.from_user.id, f'По поводу партнерства обратитесь к администратору')
    else:
        await message.answer('Выберите действие:', reply_markup=keyboard_partner_action())

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
            await dp.bot.send_message(message.from_user.id, f'Аккаунт {account} добавлен')
            await state.finish()

def register_partner(dispatcher: Dispatcher):
    dispatcher.register_message_handler(partner_start, commands=["partner"], chat_type=ChatType.PRIVATE)
    dispatcher.register_callback_query_handler(partner_add_account, lambda c: c.data and c.data == 'add_account',
                                               chat_type=ChatType.PRIVATE)
    dispatcher.register_message_handler(save_partner, chat_type=ChatType.PRIVATE, state=AddPartnerState.account)