import math

from datetime import datetime, timedelta
import pytz

import urllib
from loader import bot, db, yooclient, quickpay, admin_ids

async def send_expiration_notification(user_id, server_name, key_id, days_left):
    try:
        print("Sending expiration notification")
        text = (
                    f"Срок действия вашего ключа <b>{server_name}</b>\n"
                    f"Истекает через (дней) <b>{days_left}</b>\n"
                    f"Перейдите в '🗝 Мои ключи' чтобы продлить /mykeys\n"
                )
        await bot.send_message(user_id, text)


    except Exception as e:
        print(f"ERROR: {e}")