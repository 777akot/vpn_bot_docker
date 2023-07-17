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
import pytz
from dateutil.relativedelta import relativedelta

from loader import db, bot, outline, quickpay, key_config, referer_config, admin_ids
from tgbot.keyboards.callback_data_factory import vpn_callback, vpn_p2p_callback, vpn_p2p_claim_callback, trial_callback, vpn_keys_callback
from tgbot.keyboards.inline import keyboard_servers_list, keyboard_p2p_payment, keyboard_keys_actions, keyboard_cancel

from tgbot.controllers import key_controller
from tgbot.controllers import p2p_payments

from tgbot.utils.confirm_dialog import confirm_dialog


async def vpn_handler(message: Message):
    # await bot.delete_message(message.chat.id, message.message_id)
    await bot.send_message(message.from_user.id, f'Выберите страну сервера', reply_markup=await keyboard_servers_list('new_key'))


async def vpn_callback_handler(callback_query: CallbackQuery):
    # await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, f'Выберите страну сервера',
                           reply_markup=await keyboard_servers_list('new_key'))

async def vpn_p2p_callback_handler(callback_query: CallbackQuery):
    # await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, f'Выберите страну сервера',
                           reply_markup=await keyboard_servers_list('new_p2p_key'))


async def get_new_key(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    # await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
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

async def generate_label():

    labels = await db.get_all_labels()
    while True:

        label = ''.join(random.sample(string.ascii_lowercase + string.digits, 10))
        label_exists = any(x['label'] == label for x in labels)
        if not label_exists:
            return label
                

async def get_new_p2p_key(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    # await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await callback_query.answer()

    key_controller.new_key()
    server_id = callback_data['server']
    server = await db.get_server_by_id(int(server_id))
    server_name = server[0][0][1]
    price = server[0][0][2]

    owner_id = callback_query.from_user.id
    
    label = await generate_label()
    expiration_at = datetime.now() + relativedelta(months=int(key_config.get('expiration')))

    user_data = await db.get_user_by_id(owner_id)

    print(f'\n USER DATA: {user_data}')
    # print(f'\n USER DATA . : {user_data[0].user_name}')
    print(f'\n USER DATA [] : {user_data[0]["user_name"]}')

    trial_used = user_data[0]['trial_used']
    referer_id = int(user_data[0]["referer_id"]) if user_data[0].get("referer_id") else None
    referer_payout = None
    
    if referer_id != None:
        print(f'\n REFERER EXIST: {referer_id}')
        referer_payout = int(referer_config.get('payout_percent')) if referer_config.get('payout_percent') else None
        

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
                                f'Вы выбрали сервер <b>{server_name}</b> \n'
                                f'Стоимость ежемесячной подписки <b>{price} RUB</b> \n \n' 
                                f'После проведения оплаты необходимо нажать кнопку <b>Получить ключ</b> \n'
                                f'{"Или воспользуйтесь бесплатным тестовым периодом (1 неделя), нажав соответствующую кнопку." if trial_used != True else ""}'
                                f'\n\n'
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
                api_key = await db.get_server_key(int(server_id))
                data = await outline.create_key(api_key)
                key_id = int(data.get('id'))
                key_accessUrl = data.get('accessUrl')
                await outline.set_name_label(api_key, key_id, label)
                updatekey = await db.update_outline_key_id(callback_query.from_user.id, 
                                                           label,
                                                           key_id, 
                                                           key_accessUrl)
                print(f"\n Data: \n: {data} , {updatekey}")
                accessUrl = key_accessUrl

            # limited = await outline.set_data_limit(await db.get_server_key(int(server_id)),data.get('id'))
            
            await bot.send_message(callback_query.from_user.id,
                                f'Вставьте вашу ссылку доступа в приложение Outline:')
            await bot.send_message(callback_query.from_user.id,
                                f'<code>{accessUrl}</code>')
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
                api_key = await db.get_server_key(int(server_id))
                data = await outline.create_key(api_key)
                key_id = int(data.get('id'))
                key_accessUrl = data.get('accessUrl')
                await outline.set_name_label(api_key, key_id, label)
                updatekey = await db.update_outline_key_id(callback_query.from_user.id, 
                                                           label, 
                                                           key_id, 
                                                           key_accessUrl)
                print(f"\n Data: \n: {data} , {updatekey}")
                accessUrl = key_accessUrl

            # limited = await outline.set_data_limit(await db.get_server_key(int(server_id)),data.get('id'))
            result = await db.set_trial_used(callback_query.from_user.id, True)

            await bot.send_message(callback_query.from_user.id,
                                f'Вставьте вашу ссылку доступа в приложение Outline:')
            await bot.send_message(callback_query.from_user.id,
                                f'<code>{accessUrl}</code>')
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

async def select_key(callback_query: CallbackQuery, callback_data: Dict [str,str]):
    
    # async def test_func():
    #     print(f"\n ДЕЙСТВИЕ ВЫПОЛНЕНО!!!!! \n")
    #     await bot.send_message(callback_query.from_user.user_id, "Выполнено")
        
    # await confirm_dialog(callback_query, test_func)
    # await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    label = callback_data['key']
    user_id = callback_query.from_user.id
    key_data = await db.get_key_all_data_by_label(label)
    key_expriration = key_data[0]['expiration_at']
    current_date = datetime.now(pytz.utc)
    days_left = (key_expriration - current_date).days
    print(f"\n SELECT KEY > KEY_DATA: {key_data} \n")
    server_id = key_data[0]['server_id'] if len(key_data) > 0 else None
    server = await db.get_server_by_id(int(server_id))
    print(f"\n SELECT KEY > SERVER: {server}\n")
    server_name = server[0][0][1]
    server_price = server[0][0][2]
    print(f"\n SELECT KEY > SERVER NAME: {server_name}\n")
    paymentstatus = await p2p_payments.check_payment(callback_query.from_user.id, label)
    payment = await db.get_payment_by_id(label, int(user_id))
    price = (payment[0]['sum'] if payment[0]['sum'] > 0 else "Free") if len(payment) > 0 else server_price
    check_outline_key = await db.get_outline_key(callback_query.from_user.id, label)
    if paymentstatus == True and server_id is not None:
        try:
            accessUrl = check_outline_key[1]
            if check_outline_key[0] == None:
                print(f"\n CREATE OUTLINE KEY \n")
                api_key = await db.get_server_key(int(server_id))
                data = await outline.create_key(api_key)
                key_id = int(data.get('id'))
                key_accessUrl = data.get('accessUrl')
                await outline.set_name_label(api_key, key_id, label)
                updatekey = await db.update_outline_key_id(callback_query.from_user.id, 
                                                           label, 
                                                           key_id, 
                                                           key_accessUrl)
                print(f"\n Data: \n: {data} , {updatekey}")
                accessUrl = key_accessUrl
        except Exception as e:
            print(f"ERROR: {e}")
    else:
        accessUrl = None
    await callback_query.answer()
    text = (
        f"Ключ не оплачен \n\n"
        f"Сервер: {server_name}\n"
        f"Цена\Месяц: {price}\n"
    )
    if accessUrl != None:
        text = (
            f"Вставьте вашу ссылку доступа в приложение Outline: \n"
            f"<code>{accessUrl}</code>\n\n"
            f"Сервер: <b>{server_name}</b>\n"
            f"Цена\Месяц: <b>{price}</b>\n"
            f"Активен до: <b>{key_expriration.date()}</b> Осталось: <b>{days_left}</b> дней\n\n"
            )
    await bot.send_message(callback_query.from_user.id,
                           text,
                            reply_markup=keyboard_keys_actions(callback_data['key']),parse_mode="HTML", disable_web_page_preview=True
                            )

async def delete_key(callback_query: CallbackQuery, callback_data: Dict [str,str]):
    key_data = await db.get_key_data_by_label(callback_data['key'])
    label = callback_data['key']
    user_id = callback_query.from_user.id
    server_id = key_data[0]
    outline_key_id = key_data[1]
    api_link = await db.get_server_key(int(server_id))

    if outline_key_id is None:
        print(f"\n is None: {outline_key_id} \n")
        await db.delete_key(label,server_id)
        await db.delete_payment_by_label(user_id, label)
    else:
        print(f"\n is Not None: {outline_key_id} \n")
        await outline.delete_key(api_link, outline_key_id)
        await db.delete_key(label,server_id)
        await db.delete_payment_by_label(user_id, label)
        

    print(f"\n KEY DATA: {key_data[0]} : {key_data[1]}\n")
    await bot.send_message(callback_query.from_user.id, f'Ключ удалён')

async def prolong_key():
    return


def register_vpn_handlers(dp: Dispatcher):
    dp.register_message_handler(vpn_handler, commands=["vpn"], chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(vpn_callback_handler, vpn_callback.filter(action_type='vpn_settings'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(vpn_p2p_callback_handler, vpn_p2p_callback.filter(action_type='vpn_settings'), chat_type=ChatType.PRIVATE)
    # dp.register_callback_query_handler(get_new_key, vpn_callback.filter(action_type='new_key'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(get_new_p2p_key, vpn_callback.filter(action_type='new_p2p_key'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(get_claimed_key, vpn_p2p_claim_callback.filter(action_type='p2p_claim'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(get_trial, trial_callback.filter(action_type='trial'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(select_key, vpn_keys_callback.filter(action_type="showkeys"), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(delete_key, vpn_keys_callback.filter(action_type="delete_key"), chat_type=ChatType.PRIVATE)
