from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery, ChatType

from typing import Dict

from loader import bot, db
from tgbot.keyboards.callback_data_factory import vpn_keys_callback
from tgbot.keyboards.inline import keyboard_start, keyboard_help, keyboard_p2p_start, keyboard_keys_list, keyboard_client

from tgbot.controllers.referal import get_referal_users

def extract_referer_id(text):
    # Extracts referer id from the sent /start command.
    return text.split()[1] if len(text.split()) > 1 else None


async def user_start(message: Message):
    await message.answer('Привет, я помогу тебе с VPN\n\n',
                         reply_markup=keyboard_start(), disable_web_page_preview=True)
    
async def p2p_start(message: Message):
    
    referer_id = extract_referer_id(message.text) or None
    ref = referer_id
    if referer_id:
        # await message.answer('referer_id: ' + referer_id)
        print(f'referer_id: {referer_id}')
        ref = int(referer_id)
    try:
        await db.add_user(message.chat.id, message.chat.first_name, ref)
    except Exception as e:
        print(f'error: {e}')
        pass
    finally:
        await message.answer(f'Привет, {message.chat.first_name}! \n\n'
                             f'Чтобы начать пользоваться VPN, вам необходимо скачать клиент Outline для вашего устройства. \n'
                             f'Дальше необходимо нажать кнопку “Доступ к впн “ и выбрать страну.\n\n'
                             f'Получить информацию об аккаунте: /info \n'
                             f'\n\n'
                             ,
                        reply_markup=keyboard_p2p_start(), disable_web_page_preview=True)


async def help_handler(message: Message):
    await message.answer(f'Outline – это ПО с открытым исходным кодом, '
                         f'которое прошло проверку организаций '
                         f'<a href="https://s3.amazonaws.com/outline-vpn/static_downloads/ros-report.pdf">Radically Open Security</a> и '
                         f'<a href="https://s3.amazonaws.com/outline-vpn/static_downloads/cure53-report.pdf">Cure53</a>.\n\n'
                         f'Outline использует технологии <a href="https://shadowsocks.org/">Shadowsocks</a>',
                         reply_markup=keyboard_help(), disable_web_page_preview=True)


async def help_callback_handler(callback_query: CallbackQuery):
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id,
                           f'Outline – это ПО с открытым исходным кодом, '
                           f'которое прошло проверку организаций '
                           f'<a href="https://s3.amazonaws.com/outline-vpn/static_downloads/ros-report.pdf">Radically Open Security</a> и '
                           f'<a href="https://s3.amazonaws.com/outline-vpn/static_downloads/cure53-report.pdf">Cure53</a>.\n\n'
                           f'Outline использует технологии <a href="https://shadowsocks.org/">Shadowsocks</a>\n\n'
                           f'Скачать клиент Outline с официального сайта:\n'
                           ,
                           reply_markup=keyboard_client(), disable_web_page_preview=True)

async def show_my_keys(message: Message):
    await message.answer(f'Список ваших ключей. \n'
                         f'Выберите ключ чтобы получить ссылку для доступа \n\n'
                         ,
                         reply_markup=await keyboard_keys_list('showkeys',message.chat.id), disable_web_page_preview=True)
    

async def show_info(message: Message):
    user_name = message.chat.first_name
    user_id = message.chat.id
    bot_info = await bot.get_me()
    ref_link = f'https://t.me/{bot_info.username}?start={user_id}'
    ref_link_view = f't.me/{bot_info.username}?start={user_id}'
    referal_users = await get_referal_users(user_id)
    paid_referal_users = 0
    if len(referal_users) > 0:
        for x in referal_users:
            if x[0] == True:
                paid_referal_users += 1
    
    await message.answer(f'Пользователь {user_name}: \n\n'
                         f'Список ваших ключей: /mykeys \n\n'
                         f'Ваша реферальная ссылка: \n'
                         f'{ref_link} \n'
                         f'Количество привлеченных пользователей: \n'
                         f'{len(referal_users)} из них оплатили: {paid_referal_users}'
                         )

async def select_key(callback_query: CallbackQuery, callback_data: Dict [str,str]):
    access_url = await db.get_key_by_label(callback_data['key'])
    await callback_query.answer()
    text = "Ключ не оплачен"
    if access_url != None:
        text = f"Вставьте вашу ссылку доступа в приложение Outline: \n\n {access_url}"
    await bot.send_message(callback_query.from_user.id,text              
                            )

def register_user(dp: Dispatcher):
    # dp.register_message_handler(user_start, commands=["start"], chat_type=ChatType.PRIVATE)
    dp.register_message_handler(p2p_start, commands=["start"], chat_type=ChatType.PRIVATE)
    dp.register_message_handler(help_handler, commands=["help"], chat_type=ChatType.PRIVATE)
    dp.register_message_handler(show_my_keys, commands=["mykeys"], chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(help_callback_handler, lambda c: c.data == 'why', chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(select_key, vpn_keys_callback.filter(action_type="showkeys"), chat_type=ChatType.PRIVATE)
    dp.register_message_handler(show_info, commands=["info"], chat_type=ChatType.PRIVATE)
    
