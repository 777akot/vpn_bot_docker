from loader import db, outline, quickpay, key_config, referer_config

class KeyController:
    def __init__(self):
        pass
    async def set_limit(self, request):
        print("Setting limit")