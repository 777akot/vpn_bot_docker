from aiohttp import web
from tgbot.controllers import key_controller, p2p_payments

async def handle_http_request(request):
    try:
        print('\n Handle_http_request \n')
        
        await key_controller.delete_unused_keys()
        await p2p_payments.delete_unused_payments()
        await key_controller.disable_expired_keys()
        
        # # Получаем данные из запроса
        # data = await request.json()

        # # Отправляем сообщение боту
        # chat_id = data.get('chat_id')
        # text = data.get('text')
        # await bot.send_message(chat_id, text)
        return web.Response(status=204)
    except Exception as e:
        print(f'ERROR: {e}')
        return web.Response(status=500)
    

async def handle_http_payments(request):
    print(f'\n HANDLE PAYMENTS: ')
    label = request.query.get('label', 'default_label')
    status = request.query.get('status', 'default_status')
    print(f"\n Label: {label}, Status: {status}")
    raise web.HTTPFound(location="https://t.me/Hubvpnbot")

    return web.Response(text=f"Label: {label}, Status: {status}")
    
    return web.Response(text='Оплата прошла! Вернитесь в бот...')

async def handle_http_prolong_trial(request):
    try:
        return
        await key_controller.trial_prolong_for_all()
        
    except Exception as e:
        print(f'ERROR: {e}')
        return web.Response(status=500)

async def handle_http_getchat(request):
    print(f"HANDLE HTTP GETchat")
