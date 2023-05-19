# from aiogram import Dispatcher
# from aiogram.types import Message, CallbackQuery, ChatType

# import requests

import urllib
from loader import bot, db, yooclient, quickpay
from yoomoney import Client, Quickpay

import aiohttp

async def make_post_request(url, data, headers):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as response:
            response_data = response
            try:
                response_data = await response.json()
            except Exception as e:
                print("Exception: ", e)
            return response_data

async def yoopay():
    print("\nYOOPAY:\n")
    url = f"{yooclient.get('host')}/api/request-payment"
    phone = "79013530124"
    account = "4100118191300567"
    myaccount = "4100118191287950"
    data =urllib.parse.urlencode({
        "pattern_id": "p2p",
        "to": f"{phone}",
        "amount": 2,
        "comment": "test_payout",
        "message": "test_payout",
        "label": "test"
    })
    headers = {
        "Authorization":f"Bearer {yooclient['token']}",
        "Content-Type":"application/x-www-form-urlencoded"
    }
    try:
        response = await make_post_request(url, data, headers)
        # Process the response here
        print(f"\n RESPONSE: {response} \n")
        return response
    except aiohttp.ClientError as e:
        # Handle any exceptions that occurred during the request
        print(f"An error occurred: {str(e)}")


async def create_payment(label, price: int):
    qp = Quickpay(
        receiver=quickpay['receiver'],
        quickpay_form=quickpay['quickpay_form'],
        targets=quickpay['targets'],
        paymentType=quickpay['paymentType'],
        sum=price,
        label=label
    )
    return qp

async def check_payment(user_id, label):
    print("\n CHECK PAYMENT: \n")
    #СМОТРИМ В БАЗЕ БЫЛ ЛИ УЖЕ ОПЛАЧЕН КЛЮЧ И ЕСТЬ ОТМЕТКА В БАЗЕ
    key_data = await db.get_payment_status(user_id, label)
    label = key_data[0]
    bought = key_data[1]
    print("\n KEY_DATA: \n", key_data)

    #ЗДЕСЬ ОБРАЩЕНИЕ К PAYMENT API (YOOMONEY) ДЛЯ ПРОВЕРКИ ОПЛАТЫ
    if bought == False:
        client = Client(yooclient['token'])
        history = client.operation_history(label=label)
        try:
            operation = history.operations[-1]
            #ЕСЛИ ОПЛАТА ПРОШЛА - МЕНЯЕТ PAYMENT STATUS (BOUGHT)
            if operation.status == 'success':
                print ("operation.status: SUCCESS")
                await db.update_payment_status(user_id, label, bool(True))
                await db.update_payment_status_by_id(user_id, label, bool(True))
                return True
                # await bot.send_message(call.message.chat.id,
                #                        MESSAGES['successful_payment'])
        except Exception as e:
            return False
            # await bot.send_message(call.message.chat.id,
            #                        MESSAGES['wait_message'])

    else:
        print("\n BOUGHT =", bought)
        return True
        # return True
        # await bot.send_message(call.message.chat.id,
        #                        MESSAGES['successful_payment'])

    return True

async def check_trial_payment(user_id, label):
    key_data = await db.get_payment_status(user_id, label)
    label = key_data[0]
    bought = key_data[1]
    print("\n KEY_DATA: \n", key_data)

    if bought == False:
        try:
            await db.update_payment_status(user_id, label, bool(True))
            await db.update_payment_status_by_id(user_id, label, bool(True))
        except Exception as e:
            return False
    else:
        return True
    
    return True
