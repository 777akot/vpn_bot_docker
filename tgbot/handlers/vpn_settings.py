from typing import Dict

import aiohttp.client_exceptions
from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery, ChatType
from aiohttp import ClientConnectorError

import uuid
import string
import random
import math

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from loader import db, bot, outline, quickpay, key_config, referer_config
from tgbot.keyboards.callback_data_factory import vpn_callback, vpn_p2p_callback, vpn_p2p_claim_callback, trial_callback
from tgbot.keyboards.inline import keyboard_servers_list, keyboard_p2p_payment

from tgbot.controllers import key_controller
from tgbot.controllers import p2p_payments


async def vpn_handler(message: Message):
    await bot.send_message(message.from_user.id, f'Выберите страну сервера', reply_markup=await keyboard_servers_list('new_key'))


async def vpn_callback_handler(callback_query: CallbackQuery):
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, f'Выберите страну сервера',
                           reply_markup=await keyboard_servers_list('new_key'))

async def vpn_p2p_callback_handler(callback_query: CallbackQuery):
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, f'Выберите страну сервера',
                           reply_markup=await keyboard_servers_list('new_p2p_key'))


async def get_new_key(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    try:
        data = await outline.create_key(await db.get_server_key(int(callback_data['server'])))
        await bot.send_message(callback_query.from_user.id,
                               f'Вставьте вашу ссылку доступа в приложение Outline:')
        await bot.send_message(callback_query.from_user.id,
                               f'{data["accessUrl"]}')
        await callback_query.answer()
    except ClientConnectorError:
        await bot.send_message(callback_query.from_user.id,
                               f'Не удалось связаться с сервером для получения ключа, попробуйте через какое-то время')
    except aiohttp.client_exceptions:
        await bot.send_message(callback_query.from_user.id,
                               f'Не удалось связаться с сервером для получения ключа, попробуйте через какое-то время')


async def get_new_p2p_key(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    await callback_query.answer()

    key_controller.new_key()
    server_id = callback_data['server']
    server = await db.get_server_by_id(int(server_id))
    server_name = server[0][0][1]
    price = server[0][0][2]

    owner_id = callback_query.from_user.id
    label = ''.join(random.sample(string.ascii_lowercase + string.digits, 10))
    expiration_at = datetime.now() + relativedelta(months=int(key_config.get('expiration')))

    user_data = await db.get_user_by_id(owner_id)

    print(f'\n USER DATA: {user_data}')
    # print(f'\n USER DATA . : {user_data[0].user_name}')
    print(f'\n USER DATA [] : {user_data[0]["user_name"]}')

    referer_id = user_data[0]["referer_id"]
    referer_payout = None
    
    if referer_id != None:
        print(f'\n REFERER EXIST: {referer_id}')
        referer_payout = referer_config.get('payout_percent')
        

    print(f'\n REFERER : {referer_id}, {referer_payout} \n')

    await db.add_payment(label, owner_id, referer_id, price, referer_payout)

    # return
    #ГЕНЕРИТЬСЯ ПЛАТЕЖКА ДЛЯ ПЕРЕДАЧИ ССЫЛКИ НА ОПЛАТУ
    quickpay = await p2p_payments.create_payment(label,price)

    print(
        f"\n KEY DATA: \n",
        f"owner_id: {owner_id} \n",
        f"label: {label} \n",
        f"expiration_at: {expiration_at} \n"
        )
    # ttl = key_config.get('ttl')

    await db.add_key(owner_id,label,expiration_at,int(server_id))

    await bot.send_message(callback_query.from_user.id,
                               f'Вы выбрали сервер: {server_name} \n'
                               f'Оплатите {price} рексов \n'
                               f'{owner_id}'
                               f'{label}'
                               ,
                               reply_markup=await keyboard_p2p_payment(
                                                                        quickpay.redirected_url,
                                                                        label,
                                                                        owner_id,
                                                                        server_id                                                                        
                                                                        ))

async def get_claimed_key(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    await callback_query.answer()
    label = callback_data['label']
    server_id = callback_data['server']
    print("\n SERVER \n: ", callback_data['server'])

    # paymentstatus = await db.get_payment_status(callback_query.from_user.id, label)
    paymentstatus = await p2p_payments.check_payment(callback_query.from_user.id, label)
    print("\n Paymentstatus: \n", paymentstatus)
    
    check_outline_key = await db.get_outline_key(callback_query.from_user.id, label)
    print("\n Checkoutline: ", check_outline_key[0])

    if paymentstatus == True:
        try:
            accessUrl = check_outline_key[1]
            if check_outline_key[0] == None:
                data = await outline.create_key(await db.get_server_key(int(server_id)))
                updatekey = await db.update_outline_key_id(callback_query.from_user.id, 
                                                           label, 
                                                           int(data.get('id')), 
                                                           data.get('accessUrl'))
                print(f"\n Data: \n: {data} , {updatekey}")
                accessUrl = data["accessUrl"]

            # limited = await outline.set_data_limit(await db.get_server_key(int(server_id)),data.get('id'))
            
            await bot.send_message(callback_query.from_user.id,
                                f'Вставьте вашу ссылку доступа в приложение Outline:')
            await bot.send_message(callback_query.from_user.id,
                                f'{accessUrl}')
            await callback_query.answer()
        except ClientConnectorError:
            await bot.send_message(callback_query.from_user.id,
                                f'Не удалось связаться с сервером для получения ключа, попробуйте через какое-то время')
        except aiohttp.client_exceptions.ClientError:
            await bot.send_message(callback_query.from_user.id,
                                f'Не удалось связаться с сервером для получения ключа, попробуйте через какое-то время')
    else:
        await bot.send_message(callback_query.from_user.id,
                                f'Оплата ещё не прошла. Попробуйте позже...')

async def get_trial(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    label = callback_data['label']
    server_id = callback_data['server']

    paymentstatus = await p2p_payments.check_trial_payment(callback_query.from_user.id, label)
    check_outline_key = await db.get_outline_key(callback_query.from_user.id, label)

    if paymentstatus == True:
        try:
            accessUrl = check_outline_key[1]
            if check_outline_key[0] == None:
                data = await outline.create_key(await db.get_server_key(int(server_id)))
                updatekey = await db.update_outline_key_id(callback_query.from_user.id, 
                                                           label, 
                                                           int(data.get('id')), 
                                                           data.get('accessUrl'))
                print(f"\n Data: \n: {data} , {updatekey}")
                accessUrl = data["accessUrl"]

            # limited = await outline.set_data_limit(await db.get_server_key(int(server_id)),data.get('id'))
            result = await db.set_trial_used(callback_query.from_user.id, True)
            
            await bot.send_message(callback_query.from_user.id,
                                f'Вставьте вашу ссылку доступа в приложение Outline:')
            await bot.send_message(callback_query.from_user.id,
                                f'{accessUrl}')
            await callback_query.answer()
        except ClientConnectorError:
            await bot.send_message(callback_query.from_user.id,
                                f'Не удалось связаться с сервером для получения ключа, попробуйте через какое-то время')
        except aiohttp.client_exceptions.ClientError:
            await bot.send_message(callback_query.from_user.id,
                                f'Не удалось связаться с сервером для получения ключа, попробуйте через какое-то время')
    else:
        await bot.send_message(callback_query.from_user.id,
                                f'Оплата ещё не прошла. Попробуйте позже...')
    
    
    # print(f"\n GET TRIAL RESULT: {result}\n")


def register_vpn_handlers(dp: Dispatcher):
    dp.register_message_handler(vpn_handler, commands=["vpn"], chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(vpn_callback_handler, vpn_callback.filter(action_type='vpn_settings'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(vpn_p2p_callback_handler, vpn_p2p_callback.filter(action_type='vpn_settings'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(get_new_key, vpn_callback.filter(action_type='new_key'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(get_new_p2p_key, vpn_callback.filter(action_type='new_p2p_key'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(get_claimed_key, vpn_p2p_claim_callback.filter(action_type='p2p_claim'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(get_trial, trial_callback.filter(action_type='trial'), chat_type=ChatType.PRIVATE)
