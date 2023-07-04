import asyncio
from aiohttp import web
from server_controllers.key_controller import KeyController

class Handler:
    def __init__(self):
        pass

    async def handle_execute(self, request):
        print("handle_execute")
        print(request)
        result = 'Script executed successfully'
        return web.Response(text=result)
    
    async def handle_root(self, request):
        print("handle_root")
        result = 'Script executed successfully'
        return web.Response(text=result)
    
handler = Handler()


# async def handle(request):
#     print("HANDLE EXECUTED")
#     if request.path == '/execute-script':
        
#         # Ваш код для выполнения скрипта здесь
#         result = 'Script executed successfully'
#         return web.Response(text=result)

#     return web.Response(text='Not Found', status=404)

app = web.Application()
app.add_routes([web.get('/execute-script', handler.handle_execute),
                web.get('/', handler.handle_root)
                ])
# app.router.add_get('/execute-script', handle)


if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=6000)