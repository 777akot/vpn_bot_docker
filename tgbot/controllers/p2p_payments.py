# from aiogram import Dispatcher
# from aiogram.types import Message, CallbackQuery, ChatType

# import requests

import math

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

async def yoopay(toaccount, amount, label):
    print("\nYOOPAY:\n")
    url = f"{yooclient.get('host')}/api/request-payment"
    process_url = f"{yooclient.get('host')}/api/process-payment"
    
    data =urllib.parse.urlencode({
        "pattern_id": "p2p",
        "to": f"{toaccount}",
        "amount": amount,
        "comment": "test_payout",
        "message": "test_payout",
        "label": label
    })

    headers = {
        "Authorization":f"Bearer {yooclient['token']}",
        "Content-Type":"application/x-www-form-urlencoded"
    }
    
    try:
        response = await make_post_request(url, data, headers)
        # Process the response here
        print(f"\n RESPONSE: {response} \n")
        # return response
    
    except aiohttp.ClientError as e:
        # Handle any exceptions that occurred during the request
        print(f"An error occurred: {str(e)}")

    request_id = response['request_id']
    process_data = urllib.parse.urlencode({
        "request_id": request_id
    })

    try:
        res = await make_post_request(process_url, process_data, headers)
        print(f"\n RESPONSE: {res} \n")
        return res
    except aiohttp.ClientError as e:
        # Handle any exceptions that occurred during the request
        print(f"An error occurred: {str(e)}")

async def referal_payment(user_id,label):
    #ВЫПЛАТА ПО РЕФЕРАЛКЕ
    try:
        print(f"\nREFERAL PAYMENT\n")
        payment = await db.get_payment_by_id(label,int(user_id))
        referer_id = payment[0]['referer_id']
        referer_payout_percent = payment[0]['referer_payout']
        referer_payout_paid = bool(payment[0]['referer_payout_paid'])
        payment_sum = payment[0]['sum']
        sum_paid = bool(payment[0]['sum_paid'])
        

        print(f"\n Payment: {payment}\n"
            f"\n Referer ID: {referer_id}"
            f"\n Referer Payout Percent: {referer_payout_percent}"
            f"\n Referer Payout Paid: {referer_payout_paid}"
            f"\n Sum: {payment_sum}"
            f"\n Sum Paid: {sum_paid}"
            )

        if not sum_paid:
            error_message = "Sum is not paid"
            raise Exception(error_message)

        if referer_payout_paid:
            error_message = "Referer payout is already paid"
            raise Exception(error_message)

        if referer_id:
            referer_data = await db.get_user_by_id(referer_id)
            referer_account = referer_data[0]['user_account']
            print(f"\n Referer: \n"
            f"\n User: {referer_id}"
            f"\n Account: {referer_account}"
            )

        referer_payout_sum = payment_sum - max(2, math.floor(payment_sum * referer_payout_percent / 100))
        print(f"\n Payout Sum: {referer_payout_sum}\n")
        
        if not referer_account:
            error_message = "No Referer Account"
            raise Exception(error_message)
        
        await yoopay(referer_account, referer_payout_sum, label)

        await db.update_payment_referer_status_by_id(user_id, label, bool(True))

    except Exception as e:
        print(f"ERROR: {e}")
    return

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

async def check_yoomoney(label):
    client = Client(yooclient['token'])
    history = client.operation_history(label=label)
    operation = history.operations[-1]
    print(f"\n OPERATION: {operation}")

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
                #УКАЗЫВАЕМ ЧТО КЛЮЧ ОПЛАЧЕН
                await db.update_payment_status(user_id, label, bool(True))
                #УКАЗЫВАЕМ ЧТО ПЛАТЕЖКА ОПЛАЧЕНА
                await db.update_payment_status_by_id(user_id, label, bool(True))
                #УКАЗЫВАЕМ У ПОЛЬЗОВАТЕЛЯ ЧТО ОН СОВЕРШИЛ ОПЛАТУ ХОТЬ РАЗ
                await db.update_user_payment_status(user_id, bool(True))
                #ВЫЗОВ ВЫПЛАТЫ ПО РЕФЕРАЛКЕ
                await referal_payment(user_id,label)
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
