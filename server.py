import asyncio
from aiohttp import web

async def handle(request):
    print("HANDLE EXECUTED")
    if request.path == '/execute-script':
        
        # Ваш код для выполнения скрипта здесь
        result = 'Script executed successfully'
        return web.Response(text=result)

    return web.Response(text='Not Found', status=404)

app = web.Application()
app.router.add_get('/', handle)


if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=6000)