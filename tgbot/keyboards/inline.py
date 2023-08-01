import logging

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, User

import math

from loader import db, dp
from .callback_data_factory import vpn_callback, vpn_p2p_callback, vpn_p2p_claim_callback, vpn_keys_callback,trial_callback, partner_join_callback, admin_send_notification_callback, vpn_prolong_callback, vpn_p2p_period_callback

from tgbot.controllers import key_controller

logger = logging.getLogger(__name__)


def keyboard_start():
    keyboard = InlineKeyboardMarkup()
    inline_btn_1 = InlineKeyboardButton(f'Доступ к VPN',
                                        callback_data=vpn_callback.new(action_type='vpn_settings', server='no'))
    inline_btn_2 = InlineKeyboardButton(f'Что за VPN?', callback_data='why')
    return keyboard.row(inline_btn_1, inline_btn_2)

def keyboard_p2p_start():
    keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
    inline_btn_1 = InlineKeyboardButton(f'Доступ к VPN',
                                        callback_data=vpn_p2p_callback.new(action_type='vpn_settings', server='no'))
    inline_btn_2 = InlineKeyboardButton(f'Скачать клиент', callback_data='why')
    inline_btn_3 = InlineKeyboardButton(f'Партнерская программа', callback_data='referals')
    inline_btn_4 = InlineKeyboardButton(text="Чат поддержки", url="https://t.me/vpnhubsupportchat")

    return keyboard.add(inline_btn_1, inline_btn_2, inline_btn_3, inline_btn_4)

def permanent_keyboard(is_admin=False):
    perm_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    # button1 = KeyboardButton(text=f'Доступ к VPN',
    #                                     callback_data=vpn_p2p_callback.new(action_type='vpn_settings', server='no'))
    # button2 = KeyboardButton(text=f'Скачать клиент', callback_data='why')
    # button3 = KeyboardButton(text=f"Чат поддержки", url="https://t.me/vpnhubsupportchat")
    button1 = KeyboardButton("🕹 Главное меню")
    button2 = KeyboardButton("🗝 Мои ключи")
    button3 = KeyboardButton("🛠 Админка")
    perm_keyboard.add(button1, button2)
    if is_admin: perm_keyboard.add(button3)
    return perm_keyboard

async def keyboard_prolong_payment(quickpay_url: str, label: str, server: str, payment_id: int):
    try:
        keyboard = InlineKeyboardMarkup()
        inline_btn_1 = InlineKeyboardButton(f'Перейти к оплате!', url=quickpay_url)
        inline_btn_2 = InlineKeyboardButton(f'Я оплатил!', callback_data=vpn_prolong_callback.new(action_type='prolong_key', server=server, label=label, payment_id=payment_id))
        keyboard.add(inline_btn_1, inline_btn_2)
        return keyboard
    except Exception as e:
        print(f"ERROR: KEYBOARD : {e}")

async def keyboard_p2p_payment(quickpay_url: str, label: str, user_id: str, server: str):
    keyboard = InlineKeyboardMarkup()
    
    inline_btn_1 = InlineKeyboardButton(f'Перейти к оплате!', url=quickpay_url)
    inline_btn_2 = InlineKeyboardButton(f'Получить ключ!', callback_data=vpn_p2p_claim_callback.new(action_type='p2p_claim', server=server, label=label))

    keyboard.add(inline_btn_1)
    keyboard.add(inline_btn_2)
    return keyboard

def keyboard_help():
    keyboard = InlineKeyboardMarkup()
    btn_vpn_client = InlineKeyboardButton(f'Скачать клиент Outline VPN',
                                          url=f'https://getoutline.org/ru/get-started/')
    keyboard.row(btn_vpn_client)
    return keyboard

def keyboard_client():
    keyboard = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton(f'Android',
                                          url=f'https://play.google.com/store/apps/details?id=org.outline.android.client')
    btn2 = InlineKeyboardButton(f'Windows',
                                          url=f'https://s3.amazonaws.com/outline-releases/client/windows/stable/Outline-Client.exe')
    btn3 = InlineKeyboardButton(f'Chrome',
                                          url=f'https://play.google.com/store/apps/details?id=org.outline.android.client')
    btn4 = InlineKeyboardButton(f'iOS',
                                          url=f'https://itunes.apple.com/us/app/outline-app/id1356177741')
    btn5 = InlineKeyboardButton(f'MacOS',
                                          url=f'https://itunes.apple.com/us/app/outline-app/id1356178125')
    btn6 = InlineKeyboardButton(f'Linux',
                                          url=f'https://s3.amazonaws.com/outline-releases/client/linux/stable/Outline-Client.AppImage')
    keyboard.row(btn1, btn2, btn3) 
    keyboard.row(btn4, btn5, btn6)
    return keyboard


async def keyboard_servers_list(action_type: str):
    keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
    for x in await db.get_servers():
        keyboard.insert(InlineKeyboardButton(f'{x[0][1]}', callback_data=vpn_callback.new(action_type=action_type,
                                                                                          server=f'{x[0][0]}')))
    if action_type == 'to_delete':
        keyboard.row(InlineKeyboardButton(f'❌Выйти из меню', callback_data=f"cancel"))
    keyboard.row(InlineKeyboardButton(f'❌Отмена', callback_data=f"cancel"))
    return keyboard

async def keyboard_keys_list(action_type: str, user_id: int):
    keyboard = InlineKeyboardMarkup(row_width=1,resize_keyboard=True)
    keys = await key_controller.get_all_keys(user_id)
    

    for x in keys:
        print(f"\n key {x} \n")
        days_left = f". ⏱ {x[5]} дней" if x[1] != "🔴" else ""
        keyboard.insert(InlineKeyboardButton(f'{x[0]} : {x[1]}{days_left}', callback_data=vpn_keys_callback.new(action_type=action_type,
                                                                                          key=f'{x[3]}')))
    return keyboard

def keyboard_keys_actions(key_id: int, free_months: int, is_admin=False):
    print(f"\n key_id {key_id} \n")

    keyboard = InlineKeyboardMarkup(row_width=1,resize_keyboard=True)
    btn_trial = (InlineKeyboardButton(f' 🎟 Бесплатный доступ', callback_data=vpn_keys_callback.new(action_type="free_month",
                                                                                          key=key_id)))
    btn_pay = (InlineKeyboardButton(f'💲 Оплатить', callback_data=vpn_keys_callback.new(action_type="prolong_key",
                                                                                          key=key_id)))
    btn_delete = (InlineKeyboardButton(f'❌ Удалить Ключ', callback_data=vpn_keys_callback.new(action_type="delete_key",key=key_id)))
    if free_months > 0: 
        keyboard.add(btn_trial)

    keyboard.add(btn_pay)

    if is_admin:
        keyboard.add(btn_delete)
    return keyboard

async def get_nickname(user_id):
    user = await dp.bot.get_chat(user_id)
    # print(f"\n get_nickname: {user} \n")
    if "username" in user:
        # print(f"\n IS INSTANCE \n")
        nickname = user.username
        if nickname:
            return nickname
    return None

async def keyboard_show_periods(server_id, prices, trial_used):
    try:
        keyboard = InlineKeyboardMarkup(row_width=1,resize_keyboard=True)
        
        print(f"\n TRIAL: {trial_used}")
        btn0 = InlineKeyboardButton(f'1 неделя - Бесплатный тестовый период', 
                                            callback_data=vpn_p2p_period_callback.new(
                                                                action_type="new_p2p_key",
                                                                server=server_id, period="1w", 
                                                                price=0))
        
        btn1 = InlineKeyboardButton(f'1 Месяц - {prices[0]} RUB', 
                                            callback_data=vpn_p2p_period_callback.new(
                                                                action_type="new_p2p_key",
                                                                server=server_id,
                                                                period="1m",
                                                                price=prices[0]))
        # btn2 = (InlineKeyboardButton(f'3 Месяца - {prices[1]}', callback_data=vpn_p2p_period_callback.new(action_type="",server=server_id, period=3)))
        btn3 = InlineKeyboardButton(f'1 Год - {prices[2]} ({math.ceil((prices[2]/12)*10)/10} RUB в месяц)',
                                            callback_data=vpn_p2p_period_callback.new(
                                                                action_type="new_p2p_key",
                                                                server=server_id,
                                                                period="12m",
                                                                price=prices[2]))
        
        if trial_used != True:
            keyboard.add(btn0)
        keyboard.add(btn1, btn3)
        return keyboard
    except Exception as e:
        print(f"ERROR: keyboard_show_periods: {e}")

async def keyboard_show_users(users_chunk):
    try: 
        keyboard = InlineKeyboardMarkup(row_width=1,resize_keyboard=True)
        def show_emoji(value):
            if value == True:
                return "✔️"
            else:
                if value == False:
                    return "❌"

        for x in users_chunk:
            # print(f"\n user {x} \n")
            username = await get_nickname(x[1])
            keyboard.insert(InlineKeyboardButton(f'{x[1]}: {username} {x[2]} Триал:{show_emoji(x[5])} Оплата:{show_emoji(x[6])} R:{x[7]}', callback_data=f'cancel'))
        return keyboard
    except Exception as e:
        print(f"ERROR: {e}")

def keyboard_admin_action():
    keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
    btn_add_server = InlineKeyboardButton(f'Добавить сервер', callback_data='add_server')
    btn_delete_server = InlineKeyboardButton(f'Удалить сервер', callback_data='delete_server')
    btn_show_users = InlineKeyboardButton(f'Отобразить пользователей', callback_data='show_users')
    btn_add_partner = InlineKeyboardButton(f'Добавить партнера', callback_data='add_partner')
    btn_send_invite = InlineKeyboardButton(f'Отправить сообщение', callback_data=admin_send_notification_callback.new(action_type='send_notification'))
    btn_renew_trial = InlineKeyboardButton(f'Вернуть триал', callback_data='renew_trial')
    btn_cancel = InlineKeyboardButton(f'❌Выйти из меню', callback_data=f"cancel")
    keyboard.add(btn_add_server, btn_delete_server, btn_show_users, btn_add_partner, btn_send_invite, btn_renew_trial, btn_cancel)
    return keyboard

def keyboard_partner_action():
    keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
    btn_add_account = InlineKeyboardButton(f'Привязать Yoomoney', callback_data='add_account')
    btn_users = InlineKeyboardButton(f'Отобразить пользователей', callback_data='show_partner_referals')
    keyboard.add(btn_add_account, btn_users)
    return keyboard

def keyboard_partner_join():
    keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
    btn_submit = InlineKeyboardButton(f'Подать заявку', callback_data='partner_join')
    btn_cancel = InlineKeyboardButton(f'❌Выйти из меню', callback_data=f"cancel")
    keyboard.add(btn_submit, btn_cancel)
    return keyboard

def keyboard_admin_partner_submit(partner_id: str):
    keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
    btn_submit = InlineKeyboardButton(f'Подтвердить', callback_data=partner_join_callback.new(action_type='partner_join_approve',partner_id=partner_id))
    btn_cancel = InlineKeyboardButton(f'❌Выйти из меню', callback_data=f"cancel")
    keyboard.add(btn_submit, btn_cancel)
    return keyboard

def keyboard_cancel():
    return InlineKeyboardMarkup().add(InlineKeyboardButton(f'❌Выйти из меню', callback_data=f"cancel"))
