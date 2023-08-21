from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types
from aiogram.utils.exceptions import BadRequest
from aiogram.dispatcher.handler import CancelHandler

class UserActionsMiddleware(BaseMiddleware):

        async def on_pre_process_message(self, message: types.Message, data: dict):
            user_id = message.from_user.id
            action_type = 'message'
            action_data = message.text
            self.save_action(user_id, action_type, action_data)

        async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
            user_id = callback_query.from_user.id
            action_type = 'callback_query'
            action_data = callback_query.data
            self.save_action(user_id, action_type, action_data)

        def save_action(self, user_id, action_type, action_data):
            print(f"USER ACTION: user_id:{user_id} action_type:{action_type} action_data:{action_data}")