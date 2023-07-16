from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery, ChatType

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from typing import Dict

from loader import bot, db, admin_ids
from tgbot.keyboards.callback_data_factory import vpn_keys_callback
from tgbot.keyboards.inline import keyboard_start, keyboard_help, keyboard_p2p_start, keyboard_keys_list, keyboard_client, permanent_keyboard

from tgbot.controllers.referal import get_referal_users
from tgbot.handlers.partner import check_partner, partner_start


def extract_referer_id(text):
    # Extracts referer id from the sent /start command.
    if len(text.split()) > 1:
        return text.split()[1]
    else: 
        return None
    


# async def user_start(message: Message):
#     await message.answer('Привет, я помогу тебе с VPN\n\n',
#                          reply_markup=keyboard_start(), disable_web_page_preview=True)

async def clear_screen(message):
    i = 0
    while i <= 1 :
        await bot.delete_message(message.chat.id, message.message_id - i)
        i += 1

async def p2p_start(message: Message):

    # await clear_screen(message)
    print("START")
    referer_id = extract_referer_id(message.text)
    ref = referer_id
    if referer_id is not None:
        # await message.answer('referer_id: ' + referer_id)
        print(f'referer_id: {referer_id}')
        ref = int(referer_id)
    try:
        await db.add_user(message.chat.id, message.chat.first_name, ref)
    except Exception as e:
        print(f'error: {e}')
        pass
    finally:
        await bot.send_message(chat_id=message.chat.id,text=f"Привет, {message.chat.first_name}! \n\n",reply_markup=permanent_keyboard())
        await message.answer(f'🕹 Главное меню \n\n'
                             f'Чтобы начать пользоваться VPN, вам необходимо скачать клиент Outline для вашего устройства. \n\n'
                             f'Дальше необходимо нажать кнопку “Доступ к VPN“ и выбрать страну.\n\n'
                             f'Обязательно добавляйтесь в чат поддержки\n\n'
                             f'\n\n'

                             ,
                        reply_markup=keyboard_p2p_start(), disable_web_page_preview=False)


async def help_handler(message: Message):
    # await clear_screen(message)
    await message.answer(f'Outline – это ПО с открытым исходным кодом, '
                         f'которое прошло проверку организаций '
                         f'<a href="https://s3.amazonaws.com/outline-vpn/static_downloads/ros-report.pdf">Radically Open Security</a> и '
                         f'<a href="https://s3.amazonaws.com/outline-vpn/static_downloads/cure53-report.pdf">Cure53</a>.\n\n'
                         f'Outline использует технологии <a href="https://shadowsocks.org/">Shadowsocks</a>',
                         reply_markup=keyboard_help(), disable_web_page_preview=True)


async def help_callback_handler(callback_query: CallbackQuery):
    # await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
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
    # await clear_screen(message)
    keys = await db.get_all_keys(message.chat.id)
    if len(keys) > 0:
        await message.answer(f'Список ваших ключей. \n'
                         f'Выберите ключ чтобы получить ссылку для доступа \n\n'
                         ,
                         reply_markup=await keyboard_keys_list('showkeys',message.chat.id), disable_web_page_preview=True)
    else:
        await message.answer(f'У вас пока что нет ключей доступа. Перейдите в главное меню чтобы создать новый ключ.')
    

async def show_info(message: Message):
    # await clear_screen(message)
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
                         f'<b>Зовите друзей и получайте бесплатный месяц за каждого приглашенного</b>*\n\n'
                         f'Ваша реферальная ссылка: \n'
                         f'<code>{ref_link}</code> \n\n'
                         f'Количество привлеченных пользователей: \n'
                         f'{len(referal_users)} из них оплатили: {paid_referal_users}'
                         f'\n\n'
                         f'* - Учитываются только пользователи оплатившие подписку'
                         ,parse_mode="HTML")

async def text_process(message: Message):
    if message.text == '🕹 Главное меню':
        await bot.delete_message(message.chat.id, message.message_id)
        msg = message
        msg.text = "/start"
        await p2p_start(msg)
    if message.text == '🗝 Мои ключи':
        await bot.delete_message(message.chat.id, message.message_id)
        msg = message
        msg.text = "/mykeys"
        await show_my_keys(msg)

async def referals_handler(callback_query: CallbackQuery):
    print(f"\n Referals_handler \n")
    ispartner = await check_partner(callback_query.from_user.id)
    if ispartner:
        print(f"\n You are partner \n")
        msg = callback_query.message
        msg.from_user.id = callback_query.from_user.id
        msg.text = "/partner"
        await partner_start(msg)
        return
    else:
        print(f"\n You are NOT a partner \n")
        msg = callback_query.message
        msg.from_user.id = callback_query.from_user.id
        msg.text = "/info"
        await show_info(msg)
        return

def register_user(dp: Dispatcher):
    # dp.register_message_handler(user_start, commands=["start"], chat_type=ChatType.PRIVATE)
    dp.register_message_handler(p2p_start, commands=["start"], chat_type=ChatType.PRIVATE)
    dp.register_message_handler(help_handler, commands=["help"], chat_type=ChatType.PRIVATE)
    dp.register_message_handler(show_my_keys, commands=["mykeys"], chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(help_callback_handler, lambda c: c.data == 'why', chat_type=ChatType.PRIVATE)
    dp.register_message_handler(show_info, commands=["info"], chat_type=ChatType.PRIVATE)
    dp.register_message_handler(text_process, content_types=["text"], chat_type=ChatType.PRIVATE)
    dp.register_callback_query_handler(referals_handler, lambda c: c.data == 'referals', chat_type=ChatType.PRIVATE)
    
