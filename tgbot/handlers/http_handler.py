from aiohttp import web

async def handle_http_request(request):
    print('\n Handle_http_request \n')
    # keys = await key_controller.disable_expired_keys()
    
    # # Получаем данные из запроса
    # data = await request.json()

    # # Отправляем сообщение боту
    # chat_id = data.get('chat_id')
    # text = data.get('text')
    # await bot.send_message(chat_id, text)

    return web.Response(text='Сообщение отправлено')

async def handle_http_payments(request):
    print(f'\n HANDLE PAYMENTS: ')
    label = request.query.get('label', 'default_label')
    status = request.query.get('status', 'default_status')
    print(f"\n Label: {label}, Status: {status}")
    raise web.HTTPFound(location="https://t.me/Hubvpnbot")

    return web.Response(text=f"Label: {label}, Status: {status}")
    
    return web.Response(text='Оплата прошла! Вернитесь в бот...')