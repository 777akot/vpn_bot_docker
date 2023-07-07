from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import load_config
from db_api import Database
from outline.base import OutlineManager
from yoomoney import Quickpay

def qp(**args):
    return args

config = load_config()
db = Database(
    username=config.db.user,
    password=config.db.password,
    host=config.db.host,
    database=config.db.database,
    port=config.db.port)
bot = Bot(token=config.tg_bot.token, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
outline = OutlineManager()

admin_ids = config.tg_bot.admin_ids

quickpay = qp(
    receiver=config.yoomoney.receiver,
    quickpay_form='shop',
    targets='Test',
    paymentType='SB',
    sum=config.yoomoney.price,
    label=''
)

yooclient = {
    "token": config.yoomoney.token, 
    "receiver": config.yoomoney.receiver,
    "host": config.yoomoney.host
}

key_config = {
    "ttl": config.key.ttl,
    "expiration": config.key.expiration
}

referer_config = {
    "payout_percent": config.referer.payout_percent
}