import asyncio
from aiogram import types

from tgbot.views.graph_view import generate_dynamic_plot

async def handle_plot_command(bot: types.Bot, chat_id: int):
    sent_message = await bot.send_photo(chat_id, photo=None)
    asyncio.create_task(_update_dynamic_plot(bot, chat_id, sent_message.message_id))

async def _update_dynamic_plot(bot: types.Bot, chat_id: int, message_id: int):
    while True:
        image_data = await generate_dynamic_plot()
        await bot.edit_media(chat_id=chat_id, message_id=message_id, media=types.InputMediaPhoto(media=image_data))
        await asyncio.sleep(10) 