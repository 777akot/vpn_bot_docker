from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types
from aiogram.utils.exceptions import BadRequest
from aiogram.dispatcher.handler import CancelHandler

class SubscriptionMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        user = message.from_user
        channel_id = '@hubvpnchannel'  # Замените на имя вашего канала
        user_id = user.id

        try:
            chat_member = await message.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if chat_member.status != 'member' and chat_member.status != 'administrator' and chat_member.status != 'creator':
                raise BadRequest("User is not subscribed to the channel.")
        except BadRequest:
            await message.answer(f"Пожалуйста, подпишитесь на канал {channel_id}, чтобы взаимодействовать с ботом")
            raise CancelHandler()
        