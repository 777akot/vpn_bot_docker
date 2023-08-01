from typing import Dict

import aiohttp.client_exceptions
from aiogram import Dispatcher, types
from aiogram.types import Message, CallbackQuery, ChatType
from aiohttp import ClientConnectorError

import re
import uuid
import string
import random
import math
from urllib.parse import quote

from datetime import datetime, timedelta
import pytz
from dateutil.relativedelta import relativedelta

from loader import dp, db, bot, outline, quickpay, key_config, referer_config, admin_ids
from tgbot.keyboards.callback_data_factory import (
    vpn_callback, 
    vpn_p2p_callback, 
    vpn_p2p_claim_callback, 
    trial_callback, 
    vpn_keys_callback, 
    vpn_prolong_callback,
    vpn_p2p_period_callback
    )
from tgbot.keyboards.inline import (
    keyboard_servers_list, 
    keyboard_p2p_payment, 
    keyboard_keys_actions, 
    keyboard_cancel, 
    keyboard_prolong_payment, 
    keyboard_show_periods
    )

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
                           reply_markup=await keyboard_servers_list('select_period')) #new_p2p_key

async def generate_outline_link_with_servername(link, server_id):
    server_data = await db.get_server_by_id(server_id)
    print(f"\n GENERATE OUTLINE LINK:{server_data}\n")
    server_name_url = f"#{quote(server_data[0][0][1])}"
    return f"{link}{server_name_url}"


async def generate_label():
    labels = await db.get_all_labels()
    while True:
        label = ''.join(random.sample(string.ascii_lowercase + string.digits, 10))
        label_exists = any(x['label'] == label for x in labels)
        if not label_exists:
            return label
            

async def generate_expiration(period):
    try:
        if period is None:
            raise Exception('Invalid period')
        
        quantity = int(period[:-1])
        unit = period[-1]

        if unit == 'w':
            return datetime.now() + timedelta(weeks=quantity)
        elif unit == 'm':
            return datetime.now() + relativedelta(months=quantity)
        else:
            raise Exception('Invalid unit in period')
    except Exception as e:
        print(f"ERROR: generate_expiration: {e}")
        return None

async def get_new_p2p_key(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    try:
        from .vpn_settings import get_trial
        # await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        await callback_query.answer()
        
        period = callback_data.get('period')
        if period is None:
            raise Exception('No period')
        period_quantity = int(period[:-1])
        expiration_at = await generate_expiration(period)
        
        if expiration_at is None:
            raise Exception('Invalid expiration')
          
        selected_price = int(callback_data.get('price')) if callback_data.get('price') is not None else None
        if selected_price is None:
            raise Exception('No price')
        
        server_id = callback_data.get('server')
        server = await db.get_server_by_id(int(server_id))
        server_name = server[0][0][1]
        server_price = server[0][0][2]
     
        label = await generate_label()

        print(f"\n Expiration_at: {expiration_at}\n Price: {selected_price}")
        
        user_id = callback_query.from_user.id
        user_data = await db.get_user_by_id(user_id)
        print(f'\n USER DATA: {user_data}')
        print(f'\n USER NAME: {user_data[0]["user_name"]}')

        referer_id = int(user_data[0]["referer_id"]) if user_data[0].get("referer_id") else None
        referer_payout = None
        
        if referer_id is not None:
            print(f'\n REFERER EXIST: {referer_id}')
            referer_payout = int(referer_config.get('payout_percent')) if referer_config.get('payout_percent') else None
            
        print(f'\n REFERER : {referer_id}, {referer_payout} \n')

        # return
        
        #ГЕНЕРИТЬСЯ ПЛАТЕЖКА ДЛЯ ПЕРЕДАЧИ ССЫЛКИ НА ОПЛАТУ
        new_payment = await db.add_payment(label, user_id, referer_id, selected_price, referer_payout)
        # print(f"\n NEW PAYMENT: {new_payment}")

        #СОЗДАЕТСЯ КЛЮЧ
        await db.add_key(user_id,label,expiration_at,int(server_id))

        if selected_price == 0:
            # ЕСЛИ БЕСПЛАТНО НЕ ГЕНЕРИМ YOOMONEY И ПЕРЕХОДИМ СРАЗУ В GET_TRIAL
            # Имитируем обработку callback_query события
            data = {'action_type':'trial', 'server':server_id, 'label':label}
            await get_trial(callback_query, data)
            return
        else:
        
            #ГЕНЕРИТЬСЯ ПЛАТЕЖКА ДЛЯ ПЕРЕДАЧИ ССЫЛКИ НА ОПЛАТУ
            quickpay = await p2p_payments.create_payment(label,selected_price)

            print(
                f"\n KEY DATA: \n",
                f"owner_id: {user_id} \n",
                f"label: {label} \n",
                f"expiration_at: {expiration_at} \n"
                )

            text = (
                f'Вы выбрали сервер <b>{server_name}</b> \n'
                ) + (
                f'Сроком (месяцев): <b>{period_quantity}</b> \n'
                f'Стоимость: <b>{selected_price} RUB</b>\n' if period_quantity > 1 else ''
                ) + (
                f'Стоимость ежемесячной подписки <b>{selected_price} RUB</b>\n \n' if period_quantity == 1 else ''
                ) + (
                f'После проведения оплаты необходимо нажать кнопку <b>"Получить ключ!"</b> \n'
            )

            await bot.send_message(callback_query.from_user.id, text,
                                        reply_markup=await keyboard_p2p_payment(
                                                                                quickpay.redirected_url,
                                                                                label,
                                                                                user_id,
                                                                                server_id                                                                        
                                                                                ))
    except Exception as e:
        print(f"ERROR: {e}")
        await bot.send_message(callback_query.from_user.id, "Что-то пошло не так... Попробуйте ещё раз или обратитесь в чат поддержки")

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
                                f'<code>{await generate_outline_link_with_servername(accessUrl, int(server_id))}</code>')
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
    user_id = callback_query.from_user.id

    print(f"\n GET TRIAL CALLBACK U:{user_id} \n C:{callback_data}\n\n")
    # return
    paymentstatus = await p2p_payments.check_trial_payment(callback_query.from_user.id, label)
    check_outline_key = await db.get_outline_key(callback_query.from_user.id, label)

    if paymentstatus == True:
        try:
            accessUrl = check_outline_key[1]
            if check_outline_key[0] == None:
                current_date = datetime.now(pytz.utc)
                new_expiration_at = current_date + timedelta(days=7)
                api_key = await db.get_server_key(int(server_id))
                data = await outline.create_key(api_key)
                key_id = int(data.get('id'))
                key_accessUrl = data.get('accessUrl')
                await outline.set_name_label(api_key, key_id, label)
                updatekey = await db.update_outline_key_id(callback_query.from_user.id, 
                                                           label, 
                                                           key_id, 
                                                           key_accessUrl)
                await db.update_key_expiration(key_id, label, new_expiration_at)
                print(f"\n Data: \n: {data} , {updatekey}")
                accessUrl = key_accessUrl

            # limited = await outline.set_data_limit(await db.get_server_key(int(server_id)),data.get('id'))
            result = await db.set_trial_used(callback_query.from_user.id, True)

            await bot.send_message(callback_query.from_user.id,
                                f'Вставьте вашу ссылку доступа в приложение Outline:')
            await bot.send_message(callback_query.from_user.id,
                                f'<code>{await generate_outline_link_with_servername(accessUrl, int(server_id))}</code>')
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
    await callback_query.answer()
    # async def test_func():
    #     print(f"\n ДЕЙСТВИЕ ВЫПОЛНЕНО!!!!! \n")
    #     await bot.send_message(callback_query.from_user.user_id, "Выполнено")
        
    # await confirm_dialog(callback_query, test_func)
    # await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id

    label = callback_data['key']
    user_id = callback_query.from_user.id
    is_admin = user_id in admin_ids
    user_data = await db.get_user_by_id(user_id)
    free_months = (user_data[0]['free_months'] if user_data[0]['free_months'] > 0 else 0) if len(user_data) > 0 else 0

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
    
    paymentstatus = await p2p_payments.check_payment(callback_query.from_user.id, label)
    payment = await db.get_payment_by_id(label, int(user_id))
    # ЕСЛИ В ПЛАТЕЖКЕ ЦЕНА БОЛЬШЕ НУЛЯ ТО СТАВИТСЯ ТЕКУЩАЯ ЦЕНА ИЗ ЦЕНЫ СЕРВЕРА (server_price)
    price = (server_price if payment[0]['sum'] > 0 else f"Free ({server_price})") if len(payment) > 0 else server_price
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
    
    text = (
        f"Ключ не оплачен \n\n"
        f"Сервер: {server_name}\n"
        f"Цена\Месяц: {price}\n"
    )
    if accessUrl != None:
        text = (
            f"Вставьте вашу ссылку доступа в приложение Outline: \n"
            f"<code>{await generate_outline_link_with_servername(accessUrl, int(server_id))}</code>\n\n"
            f"Сервер: <b>{server_name}</b>\n"
            f"Цена\Месяц: <b>{price}</b>\n"
            f"Активен до: <b>{key_expriration.date()}</b> Осталось: <b>{days_left}</b> дней\n\n"
            )
    await bot.send_message(callback_query.from_user.id,
                           text,
                            reply_markup=keyboard_keys_actions(callback_data['key'],free_months,is_admin),parse_mode="HTML", disable_web_page_preview=True
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

async def get_free_month(callback_query: CallbackQuery, callback_data: Dict [str,str]):
    try:
        label = callback_data['key']
        key_data = await db.get_key_all_data_by_label(label)
        server_id = key_data[0]['server_id']
        print(f'\n GET FREE MONTH: {key_data[0]} \n')
        

        user_id = callback_query.from_user.id
        user_data = await db.get_user_by_id(user_id)
        free_months = user_data[0]['free_months']
        referer_id = user_data[0]['referer_id']
        
        outline_key_id = key_data[0]['outline_key_id']
        outline_access_url = key_data[0]['outline_access_url']

   

        async def prepare_data(label, user_id, referer_id, outline_key_id, new_expiration_at):
            await db.add_payment(label, user_id, referer_id, 0, 0)
            await db.update_payment_status_by_id(user_id, label, True)
            await db.update_payment_referer_status_by_id(user_id, label, True)
            await db.update_key_expiration(outline_key_id, label, new_expiration_at)
            await db.update_free_months(user_id,-1)
            await outline.remove_data_limit(await db.get_server_key(int(server_id)), outline_key_id)

        if free_months > 0:
            new_expiration_at = datetime.now() + relativedelta(months=1)
            if outline_key_id and outline_access_url:                
                print(f'\n GET FREE MONTH: OUTLINE KEY EXIST: {outline_key_id} \n')
                await prepare_data(label, user_id, referer_id, outline_key_id, new_expiration_at)
            else:                
                print(f'\n GET FREE MONTH: OUTLINE KEY NOT EXIST: {outline_key_id} \n')
                api_key = await db.get_server_key(int(server_id))
                data = await outline.create_key(api_key)
                outline_key_id = int(data.get('id'))
                outline_access_url = data.get('accessUrl')
                await outline.set_name_label(api_key, outline_key_id, label)
                updatekey = await db.update_outline_key_id(user_id, 
                                                        label, 
                                                        outline_key_id, 
                                                        outline_access_url)
                print(f"\n Data: \n: {data} , {updatekey}")
                await prepare_data(label, user_id, referer_id, outline_key_id, new_expiration_at)
        else:
            raise Exception("NO FREE MONTHS")

        if outline_access_url:
            await bot.send_message(user_id, (
                f"Вы успешно применили бесплатный месяц!\n"
                f"Ключ теперь Активен\n"
                f"Вставьте вашу ссылку доступа в приложение Outline: \n"
                f"<code>{await generate_outline_link_with_servername(outline_access_url, int(server_id))}</code>\n\n"
                                            ))
    
    except Exception as e:
        print(f'ERROR: {e}')
        await bot.send_message(callback_query.from_user.id, "Что-то пошло не так... Попробуйте ещё раз или обратитесь в чат поддержки")

async def wait_for_payment(user_id, label, payment_id):
    await p2p_payments.check_payment(user_id, label, payment_id)
    return

async def prolong_key(callback_query: CallbackQuery, callback_data: Dict [str,str]):
    try:
        print(f"\n PROLONG KEY: {callback_data}")
        user_id = callback_query.from_user.id
        user_data = await db.get_user_by_id(user_id)
        referer_id = int(user_data[0]["referer_id"]) if user_data[0].get("referer_id") else None
        referer_payout = (int(referer_config.get('payout_percent')) if referer_config.get('payout_percent') else None) if referer_id else None

        if referer_id != None:
            print(f'\n REFERER EXIST: {referer_id}')
            referer_payout = int(referer_config.get('payout_percent')) if referer_config.get('payout_percent') else None

        label = callback_data['key']
        key_data = await db.get_key_all_data_by_label(label)
        key_active = key_data[0]['active']
        if key_active==True:
            raise Exception('KEY_IS_ACTIVE')
        
        server_id = key_data[0]['server_id']
        server = await db.get_server_by_id(int(server_id))
        server_name = server[0][0][1]
        server_price = server[0][0][2]

        success_url = f"http://80.90.179.110/:6060/process?label={label}&status=some_status"

        if key_data[0]['outline_key_id']:
            print(f"\n PROLONG KEYDATA: {key_data[0]['outline_key_id']}")

        new_payment = await db.add_payment(label, user_id, referer_id, server_price, referer_payout)
        print(f"\n NEW PAYMENT: {new_payment['id']}")
        quickpay = await p2p_payments.create_payment(label, server_price)
        print(f"\n Quickpay: {quickpay}")
        await bot.send_message(user_id,
                                    f'Вы выбрали сервер <b>{server_name}</b> \n'
                                    f'Стоимость ежемесячной подписки <b>{server_price} RUB</b> \n \n'
                                    ,
                                    reply_markup=await keyboard_prolong_payment(
                                                                            quickpay.redirected_url,
                                                                            label,
                                                                            server_id,
                                                                            new_payment['id']                                                                  
                                                                            ))
                               
        # payment_status = await wait_for_payment(user_id, label, )

        return
    except Exception as e:
        print(f"ERROR: PROLONG KEY: {e}")
        if e:
            print('KEY_IS_ACTIVE' in str(e))
            if "KEY_IS_ACTIVE" in str(e):
                await bot.send_message(user_id,f"Ключ уже активен и не нуждается в продлении")
                return
            await bot.send_message(user_id,f"Что-то пошло не так, попробуйте ещё раз или обратитесь в чат-поддержки...")

async def get_prolong_key(callback_query: CallbackQuery, callback_data: Dict [str,str]):
    try:
        print(f"get_prolong_key: {callback_data}")
        label = callback_data['label']
        payment_id = callback_data['payment_id']
        server_id = callback_data['server']
        check_outline_key = await db.get_outline_key(callback_query.from_user.id, label)
        api_key = await db.get_server_key(int(server_id))


        paymentstatus = await p2p_payments.check_payment(callback_query.from_user.id, label, payment_id)
        if paymentstatus == True:
            check_outline_key = await db.get_outline_key(callback_query.from_user.id, label)
            accessUrl = check_outline_key[1]
            outline_key_id = check_outline_key[0]
            
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
                outline_key_id = key_id
                await bot.send_message(callback_query.from_user.id,
                                f'Вставьте вашу ссылку доступа в приложение Outline:')
                await bot.send_message(callback_query.from_user.id,
                                    f'<code>{await generate_outline_link_with_servername(accessUrl, int(server_id))}</code>')
                await callback_query.answer()
            
            # ОБНОВИТЬ EXPIRATION_AT у ключа
            expiration_at = datetime.now() + relativedelta(months=int(key_config.get('expiration')))
            await db.update_key_expiration(outline_key_id, label, expiration_at)
            await outline.remove_data_limit(api_key, outline_key_id)

            await bot.send_message(callback_query.from_user.id,
                                f'Ключ успешно оплачен!')
        elif paymentstatus == False:
            await bot.send_message(callback_query.from_user.id,
                                f'Оплата ещё не прошла. Попробуйте позже...')

    except Exception as e:
        print(f"ERROR: {e}")

async def select_period(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    try:
        await callback_query.answer()
        data = callback_data
        server_id = data['server']
        server = await db.get_server_by_id(int(server_id))
        server_name = server[0][0][1]
        price = server[0][0][2]

        special = await p2p_payments.check_special_price()

        if special is not None:
            special_price = special.get('special_price')
            special_days_to_go = special.get('special_days_to_go')
        else:
            special_price, special_days_to_go = None, None

        price_year = special_price if special else price*10

        user_id = callback_query.from_user.id
        trial_used = await db.check_trial(user_id)

        print(f"\n trial_used: {trial_used}")

        prices = [price, price * 3, price_year]
        print(f"\n DATA: {data} \n")
        text = (
            f"Вы выбрали сервер: <b>{server_name}</b>\n\n"
            f"Цена/месяц: <b>{price} RUB (со скидкой 50%*)</b>\n"
            f"* Скидка действует до 1 сентября. С 1 сентября стоимость станет 200р \n"
            ) + (
            f"\n<b>Внимание Акция! Оставшиеся дни: {special_days_to_go}. \n{special_price} за годовую подписку! ({math.ceil((special_price/12)*10)/10} в месяц!)</b> \n"
            if special else ""
            ) + (
            f"\nИли воспользуйтесь бесплатным тестовым периодом (1 неделя), нажав соответствующую кнопку.\n"
            if trial_used == False else ""
            ) + (
            f"\n<b>Выберите период:</b>\n"
            )
        
        await bot.send_message(callback_query.from_user.id,text, reply_markup=await keyboard_show_periods(server_id, prices, trial_used))
    except Exception as e:
        print(f"ERROR: {e}")

def register_vpn_handlers(dp: Dispatcher):
    dp.register_message_handler(vpn_handler, commands=["vpn"], chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(vpn_callback_handler, vpn_callback.filter(action_type='vpn_settings'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(vpn_p2p_callback_handler, vpn_p2p_callback.filter(action_type='vpn_settings'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(select_period, vpn_callback.filter(action_type='select_period'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(get_new_p2p_key, vpn_p2p_period_callback.filter(action_type='new_p2p_key'), chat_type=ChatType.PRIVATE)

    dp.register_callback_query_handler(get_new_p2p_key, vpn_callback.filter(action_type='new_p2p_key'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(get_claimed_key, vpn_p2p_claim_callback.filter(action_type='p2p_claim'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(get_trial, trial_callback.filter(action_type='trial'), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(select_key, vpn_keys_callback.filter(action_type="showkeys"), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(delete_key, vpn_keys_callback.filter(action_type="delete_key"), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(get_free_month, vpn_keys_callback.filter(action_type="free_month"), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(prolong_key, vpn_keys_callback.filter(action_type="prolong_key"), chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(get_prolong_key, vpn_prolong_callback.filter(action_type='prolong_key'), chat_type=ChatType.PRIVATE)
