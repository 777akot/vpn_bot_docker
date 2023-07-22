import logging
from typing import Dict

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ChatType, CallbackQuery

from loader import dp, db, outline
from tgbot.keyboards.callback_data_factory import vpn_callback, partner_join_callback, admin_send_notification_callback
from tgbot.keyboards.inline import keyboard_admin_action, keyboard_servers_list, keyboard_cancel, keyboard_show_users
from tgbot.states.servers_add import AddServerState
from tgbot.states.partners_add import AddPartnerState
from tgbot.states.notification_add import AddNotificationState

from tgbot.controllers.p2p_payments import yoopay,referal_payment, check_payment, check_yoomoney

async def admin_start(message: Message):
    await message.answer('Выберите действие:', reply_markup=keyboard_admin_action())


async def admin_add_server(callback_query: CallbackQuery, state: FSMContext):
    await dp.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await dp.bot.send_message(callback_query.from_user.id, 'Введите название сервера.\n'
                                                           'Можно использовать смайлики, например флаги стран',
                              reply_markup=keyboard_cancel())
    await state.set_state(AddServerState.server_name)
    await callback_query.answer()


async def admin_server_name(message: Message, state: FSMContext):
    server_name = message.text.strip()
    await state.update_data(server_name=server_name)
    await state.set_state(AddServerState.api_link)
    await dp.bot.send_message(message.from_user.id, f'Название сервера: {server_name}\n'
                                                    f'Введите  URL для доступа к Outline Management API',
                              reply_markup=keyboard_cancel())


async def admin_api_link(message: Message, state: FSMContext):
    url = message.text.strip()
    if url.isdigit() or url.isalpha():
        await dp.bot.send_message(message.from_user.id, 'Не похоже на ссылку')
    else:
        state_data = await state.get_data()
        server_name = state_data['server_name']
        await state.update_data(api_link=url)
        await state.set_state(AddServerState.price)
        await dp.bot.send_message(message.from_user.id, f'Стоимость сервера (месяц) {server_name}\n'
                                                    f'Введите цену',
                              reply_markup=keyboard_cancel())

async def admin_price(message: Message, state: FSMContext):
    price = message.text.strip()
    if not price.isdigit():
        await dp.bot.send_message(message.from_user.id, 'Не похоже на цену')
    else:
        state_data = await state.get_data()
        server_name = state_data['server_name']
        url = state_data['api_link']
        await state.update_data(price=price)
        await db.add_server(server_name, url, int(price))
        await dp.bot.send_message(message.from_user.id, f'Сервер {server_name} добавлен')
        await state.finish()

async def admin_testpay(message: Message):
    await message.answer("Тестовая выплата")
    # await check_payment(347207594,"v82henxufl")
    users = await db.show_users()
    # errors = [<Record id=639 user_id=330771875 user_name='Ilyaushenin' created_at=datetime.datetime(2023, 7, 22, 13, 29, 49, 609012, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=635 user_id=6081507817 user_name='Sayan' created_at=datetime.datetime(2023, 7, 22, 13, 19, 6, 107403, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=629 user_id=329398378 user_name='Сергей' created_at=datetime.datetime(2023, 7, 22, 12, 44, 48, 933164, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=627 user_id=6159333148 user_name='Максим' created_at=datetime.datetime(2023, 7, 22, 12, 9, 25, 145535, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=619 user_id=5837525421 user_name='\\VVV/' created_at=datetime.datetime(2023, 7, 22, 11, 19, 51, 148016, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=611 user_id=5287493009 user_name='Артëм' created_at=datetime.datetime(2023, 7, 22, 10, 20, 28, 472458, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=610 user_id=5931664052 user_name='.' created_at=datetime.datetime(2023, 7, 22, 10, 4, 44, 72452, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=604 user_id=5244709478 user_name='ℍ.ℳᎶa∂ʝî' created_at=datetime.datetime(2023, 7, 22, 9, 44, 52, 669499, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=598 user_id=1193086631 user_name='EXPx93' created_at=datetime.datetime(2023, 7, 22, 9, 15, 26, 931600, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=596 user_id=5649694270 user_name='Fanat Mr beast' created_at=datetime.datetime(2023, 7, 22, 9, 3, 19, 154474, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=592 user_id=5903755028 user_name='Rogalik Bulka Hlebowna' created_at=datetime.datetime(2023, 7, 22, 8, 59, 57, 296047, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=591 user_id=6221905880 user_name='Azam' created_at=datetime.datetime(2023, 7, 22, 8, 53, 8, 220914, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=589 user_id=6019281812 user_name='Богдан♠♥♠' created_at=datetime.datetime(2023, 7, 22, 8, 42, 29, 558527, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=583 user_id=819133440 user_name='.....000....' created_at=datetime.datetime(2023, 7, 22, 6, 2, 22, 502831, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=576 user_id=1004879310 user_name='᠌ ᠌ ᠌᠌ ᠌ ᠌ ᠌ ᠌' created_at=datetime.datetime(2023, 7, 22, 5, 16, 58, 16389, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=574 user_id=5429702670 user_name='Azizbek' created_at=datetime.datetime(2023, 7, 22, 4, 53, 50, 669978, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=560 user_id=933616641 user_name='Вячеслав' created_at=datetime.datetime(2023, 7, 21, 20, 8, 16, 282572, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=558 user_id=5519471272 user_name='ᅠ ᅠ' created_at=datetime.datetime(2023, 7, 21, 19, 33, 29, 796894, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=542 user_id=1184287585 user_name='𝕭𝖔𝖇𝖔𝖐𝖍𝖔𝖓𝖔𝖛' created_at=datetime.datetime(2023, 7, 21, 15, 28, 59, 20434          4, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=536 user_id=1772894475 user_name='-' created_at=datetime.datetime(2023, 7, 21, 15, 26, 38, 46759, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=529 user_id=819763052 user_name='Alexy' created_at=datetime.datetime(2023, 7, 21, 15, 4, 10, 431134, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=525 user_id=5855881239 user_name='Игорь' created_at=datetime.datetime(2023, 7, 21, 14, 58, 39, 533122, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=522 user_id=6028835734 user_name='Alan' created_at=datetime.datetime(2023, 7, 21, 14, 51, 58, 114368, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=520 user_id=5889733343 user_name='Мехрон' created_at=datetime.datetime(2023, 7, 21, 14, 33, 16, 190748, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=512 user_id=6126387964 user_name='Анзор' created_at=datetime.datetime(2023, 7, 21, 14, 1, 28, 223135, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=508 user_id=5186234359 user_name='Валентин Щанович' created_at=datetime.datetime(2023, 7, 21, 13, 49, 2, 526484, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=499 user_id=824556452 user_name='🧚\u200d♂️🧚\u200d♀️🧚' created_at=datetime.datetime(2023, 7, 21, 12, 3, 33, 672042, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=496 user_id=1416246208 user_name='АнтоШик2' created_at=datetime.datetime(2023, 7, 21, 12, 1, 16, 250071, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=494 user_id=5979738902 user_name='Андрей' created_at=datetime.datetime(2023, 7, 21, 11, 49, 47, 450849, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=490 user_id=6315531836 user_name='САПАРОВ С665' created_at=datetime.datetime(2023, 7, 21, 11, 8, 42, 781737, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=488 user_id=5139577608 user_name='Alex' created_at=datetime.datetime(2023, 7, 21, 10, 41, 1, 150265, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=477 user_id=888557425 user_name='İsmet' created_at=datetime.datetime(2023, 7, 21, 8, 5, 36, 12380, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=476 user_id=1329284933 user_name='максим' created_at=datetime.datetime(2023, 7, 21, 7, 57, 12, 979986, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=None referal_role='inviter' user_account=None free_months=0>, <Record id=446 user_id=5919958473 user_name='92410' created_at=datetime.datetime(2023, 7, 20, 16, 35, 8, 94949, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=433 user_id=5951521312 user_name='Миша' created_at=datetime.datetime(2023, 7, 20, 14, 25, 22, 322833, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=429 user_id=691649404 user_name='Begijon' created_at=datetime.datetime(2023, 7, 20, 13, 16, 48, 617943, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=427 user_id=1620191036 user_name='Олеся' created_at=datetime.datetime(2023, 7, 20, 12, 54, 20, 995215, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=421 user_id=969603942 user_name='Филиппова Вера' created_at=datetime.datetime(2023, 7, 20, 12, 15, 36, 708620, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=418 user_id=749450787 user_name='Александр' created_at=datetime.datetime(2023, 7, 20, 11, 52, 42, 808628, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=64579923 referal_role='inviter' user_account=None free_months=0>, <Record id=407 user_id=1306684475 user_name='Юлия' created_at=datetime.datetime(2023, 7, 19, 19, 41, 48, 714899, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=None referal_role='inviter' user_account=None free_months=0>, <Record id=385 user_id=1424397733 user_name='W.A.Y.N.E.' created_at=datetime.datetime(2023, 7, 19, 9, 52, 11, 576616, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=351 user_id=1818604637 user_name='\xa0᠌ ᠌ ᠌᠌ ᠌ ᠌ ᠌ ᠌ ᠌\xa0' created_at=datetime.datetime(2023, 7, 18, 8, 41, 35, 516577, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=349 user_id=731503879 user_name='Zashle' created_at=datetime.datetime(2023, 7, 18, 7, 35, 28, 469978, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=346 user_id=6299634684 user_name='Nekki' created_at=datetime.datetime(2023, 7, 18, 4, 59, 51, 275991, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=340 user_id=5207586227 user_name='Kokush' created_at=datetime.datetime(2023, 7, 18, 2, 50, 8, 2513, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=339 user_id=2056878565 user_name='No' created_at=datetime.datetime(2023, 7, 18, 1, 39, 51, 452529, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=336 user_id=6075700693 user_name='🃏Danya�'' created_at=datetime.datetime(2023, 7, 18, 1, 22, 18, 915547, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=331 user_id=1394982084 user_name='Yasin' created_at=datetime.datetime(2023, 7, 17, 23, 10, 52, 343703, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=325 user_id=5315917105 user_name='S_29men_Х' created_at=datetime.datetime(2023, 7, 17, 21, 59, 3, 30900, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=306 user_id=953177964 user_name='ǟʍǟռƭɛֆ ֆʊռƭ ǟʍɛռƭɛֆ' created_at=datetime.datetime(2023, 7, 17, 20, 20, 20, 650486, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=302 user_id=2086134702 user_name='Юлия' created_at=datetime.datetime(2023, 7, 17, 19, 57, 21, 849205, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=293 user_id=2062473560 user_name=':)' created_at=datetime.datetime(2023, 7, 17, 19, 10, 28, 346788, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=291 user_id=813586272 user_name='Kerrlll🕷' created_at=datetime.datetime(2023, 7, 17, 17, 54, 53, 786277 , tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=290 user_id=1275187724 user_name='ульяна' created_at=datetime.datetime(2023, 7, 17, 16, 51, 10, 148456, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=286 user_id=959305451 user_name='Анастасия' created_at=datetime.datetime(2023, 7, 17, 12, 24, 41, 781312, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=None referal_role='inviter' user_account=None free_months=0>, <Record id=279 user_id=1588729695 user_name='ᅠ' created_at=datetime.datetime(2023, 7, 17, 11, 10, 30, 586906, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=None referal_role='inviter' user_account=None free_months=0>, <Record id=277 user_id=1760042131 user_name='�🖤  𝔄𝔫𝔦𝔅𝔢𝔰𝔶𝔞 🖤🕷' created_at=datetime.datetime(2023, 7, 17, 8, 19, 18, 556766, tzinfo=datet         ime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=275 user_id=1821717383 user_name='Batareyka' created_at=datetime.datetime(2023, 7, 17, 5, 33, 51, 730202, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=274 user_id=1649165366 user_name='Yerry' created_at=datetime.datetime(2023, 7, 17, 4, 22, 39, 977583, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=217133707 referal_role='inviter' user_account=None free_months=0>, <Record id=227 user_id=447957412 user_name='Денис' created_at=datetime.datetime(2023, 7, 13, 20, 52, 3, 226701, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=None referal_role='inviter' user_account=None free_months=0>, <Record id=223 user_id=462277276 user_name='мискаМ' created_at=datetime.datetime(2023, 7, 12, 18, 16, 2, 570250, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=2023325452 referal_role='inviter' user_account=None free_months=0>, <Record id=171 user_id=483823081 user_name='Abu' created_at=datetime.datetime(2023, 7, 8, 21, 20, 26, 970274, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=None referal_role='inviter' user_account=None free_months=0>, <Record id=132 user_id=1910858249 user_name='Анатолий' created_at=datetime.datetime(2023, 7, 6, 10, 36, 52, 838000, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=None referal_role='inviter' user_account=None free_months=0>, <Record id=126 user_id=976326764 user_name='Mishanya' created_at=datetime.datetime(2023, 7, 6, 6, 31, 43, 951596, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=2023325452 referal_role='inviter' user_account=None free_months=0>, <Record id=119 user_id=964850099 user_name='Руся' created_at=datetime.datetime(2023, 7, 5, 18, 32, 25, 331334, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=2023325452 referal_role='inviter' user_account=None free_months=0>, <Record id=115 user_id=440835704 user_name='Алексей' created_at=datetime.datetime(2023, 7, 5, 18, 14, 32, 235654, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=2023325452 referal_role='inviter' user_account=None free_months=0>, <Record id=96 user_id=967262260 user_name='Менеджер' created_at=datetime.datetime(2023, 7, 5, 15, 22, 30, 495411, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=None referal_role='inviter' user_account=None free_months=0>, <Record id=58 user_id=1806577091 user_name='Riajul' created_at=datetime.datetime(2023, 6, 21, 19, 44, 46, 49752, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=None referal_role='inviter' user_account=None free_months=0>, <Record id=55 user_id=577406035 user_name='Mo' created_at=datetime.datetime(2023, 6, 14, 10, 25, 24, 375243, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=None referal_role='inviter' user_account=None free_months=0>, <Record id=38 user_id=754307017 user_name='Эмиль' created_at=datetime.datetime(2023, 6, 3, 11, 56, 43, 553516, tzinfo=datetime.timezone.utc) role='user' trial_used=False bought=False referer_id=None referal_role='inviter' user_account=None free_months=0>, <Record id=9 user_id=333617575 user_name='HSG' created_at=datetime.datetime(2023, 5, 19, 17, 12, 3, 507172, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=None referal_role='inviter' user_account=None free_months=0>, <Record id=8 user_id=357500936 user_name='Ivano' created_at=datetime.datetime(2023, 5, 19, 17, 0, 52, 512250, tzinfo=datetime.timezone.utc) role='user' trial_used=True bought=False referer_id=None referal_role='inviter' user_account=None free_months=0>]
    errors = []
    for x in users:
        try:
            chat = await dp.bot.get_chat(x['user_id'])
            if chat and chat.ok:
                print("OK")
            else:
                print(f"NOT OK: {chat}")
        except Exception as e:
            errors.append(x)
            print(f"Error: {e}")

    if len(errors) > 0:
        for e in errors:
            print(f"\n {e}")

    return

    payments = await db.get_all_payments()
    for x in payments:
        print(f"\n X: {x[0][0]}")
        label = x[0][0]
        user_id = x[0][1]
        print(f"{label}\n")
        status = await check_yoomoney(label)
        key_exist = await db.get_key_all_data_by_label(label)
        
        if len(key_exist) == 0:
            print(f'KEY NOT EXIST: {key_exist}')
            await db.delete_payment_by_label(user_id, label)
            await dp.bot.send_message(message.from_user.id, f'KEY NOT EXIST. AND PAYMENT DELETED: {label}')

        else:
            key_item = key_exist[0]
            server_id = key_item['server_id']
            api_key = await db.get_server_key(int(server_id))
            key_id = key_item['outline_key_id']
            await outline.set_name_label(api_key, key_id, label)
            await dp.bot.send_message(message.from_user.id, f'KEY EXIST')

        if status:
            await dp.bot.send_message(message.from_user.id, f'L: {label}. S: {status}')
        else:
            payment_status = await db.get_payment_by_id(label, int(user_id))
            for p in payment_status:
                label = p['label']
                payment_sum = p['sum']
                payment_sum_paid = p['sum_paid']
                if payment_sum > 0 and status is None:
                    # await db.update_payment_trial(user_id, label)
                    print(f"\n Payment status: {p['sum']}")
                    await dp.bot.send_message(message.from_user.id, f'P: {p["sum"]} Paid: {payment_sum_paid==True} L: {label}')
                
            # 
    # await yoopay()

async def admin_servers_to_delete(callback_query: CallbackQuery):
    await dp.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await dp.bot.send_message(callback_query.from_user.id, 'Выберите сервер для удаления:',
                              reply_markup=await keyboard_servers_list('to_delete'))
    await callback_query.answer()


async def admin_delete_server(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    await dp.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    server_id = int(callback_data['server'])
    await db.delete_server(int(server_id))
    await dp.bot.send_message(callback_query.from_user.id, 'Сервер удалён из БД')
    await callback_query.answer()

async def admin_delete_key(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    data = await outline.delete_key()
    print("\n admin_delete_key: \n", data)

async def admin_show_users(callback_query: CallbackQuery):
    print("\n admin_show_users: \n")
    try:
        users = await db.show_users()
        chunk_size = 50
        for i in range(0, len(users), chunk_size):
            users_chunk = users[i:i + chunk_size]
            await dp.bot.send_message(callback_query.from_user.id, f'Пользователи: {len(users)}',
                                reply_markup=await keyboard_show_users(users_chunk))
    except Exception as e:
        print(f"ERROR: {e}")
    

async def admin_test_referal(message: Message):
    await message.answer("Тестовая выплата")
    user_id = message.from_user.id
    label = "aoqb8wxvyk"
    await referal_payment(user_id,label)

async def admin_add_partner(message: Message, state: FSMContext):
    print("\n ADMIN ADD PARTNER: \n")
    await state.set_state(AddPartnerState.user_id)
    await dp.bot.send_message(message.from_user.id, f'Введите id Пользователя:',
                            reply_markup=keyboard_cancel())

async def admin_save_partner(message: Message, state: FSMContext):
    user_id = message.text.strip()
    if not user_id.isdigit():
        await dp.bot.send_message(message.from_user.id, 'Не похоже на номер аккаунта',reply_markup=keyboard_cancel())

    candidate = await db.get_user_by_id(int(user_id))
    if not candidate or not len(candidate):
        await dp.bot.send_message(message.from_user.id, 'Нет такого пользователя',reply_markup=keyboard_cancel())
    else:
        res = ""
        # state_data = await state.get_data()
        # server_name = state_data['account_number']
        await state.update_data(user_id=user_id)
        # # await db.add_server(server_name, url, int(price))
        await db.add_partner(int(user_id), "partner")
        await dp.bot.send_message(message.from_user.id, f'Аккаунт {user_id} добавлен')
        await state.finish()

async def partner_join_approve(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    await dp.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    partner_id = callback_data['partner_id']
    await db.add_partner(int(partner_id), "partner")
    print(f'\n partner_join_approve \n {partner_id}')
    await dp.bot.send_message(partner_id, 'Поздравляем ваша заявка одобрена! Теперь вы можете пользоваться личным кабинетом партнёра используя команду /partner')
    await dp.bot.send_message(callback_query.from_user.id, f'{partner_id} теперь Партнер')

async def admin_send_notification(callback_query: CallbackQuery, state: FSMContext):
    print(f"\n SEND NOTIFICATION \n")
    await state.set_state(AddNotificationState.message_text)
    await dp.bot.send_message(callback_query.from_user.id, f'Введите текст сообщения:')

async def admin_send_notification_send(message: Message, state: FSMContext):
    message_text = message.text
    print(f"\n MESSAGE: {message_text} \n")
    await state.update_data(message_text=message_text)
    await state.finish()
    users = await db.show_users()
    errors = []
    sliced_users = users[5:]
    for x in sliced_users:
        try:
            print(f"USER: {x}")
            user_id = x['user_id']
            # await dp.bot.send_message(x['user_id'],'Привет')
            await dp.bot.send_message(user_id, text=message_text, entities=message.entities)
        except Exception as e:
            errors.append(x)
            print(f"ERROR: {e}")
    
    if len(errors) > 0:
        print(f"\n Errors: {errors}")
    
async def admin_renew_trial(message: Message):
    await db.set_trial_used(message.from_user.id, False)
    await dp.bot.send_message(message.from_user.id, f'Триал обновлён')

def register_admin(dispatcher: Dispatcher):
    dispatcher.register_message_handler(admin_testpay, commands=["admin_pay"], chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_message_handler(admin_start, commands=["admin"], chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_callback_query_handler(admin_add_server, lambda c: c.data and c.data == 'add_server',
                                               chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_message_handler(admin_server_name, chat_type=ChatType.PRIVATE, is_admin=True, state=AddServerState.server_name)
    dispatcher.register_message_handler(admin_api_link, chat_type=ChatType.PRIVATE, is_admin=True, state=AddServerState.api_link)
    dispatcher.register_message_handler(admin_price, chat_type=ChatType.PRIVATE, is_admin=True, state=AddServerState.price)
    dispatcher.register_callback_query_handler(admin_servers_to_delete, lambda c: c.data and c.data == 'delete_server',
                                               chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_callback_query_handler(admin_delete_server, vpn_callback.filter(action_type='to_delete'), chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_callback_query_handler(admin_delete_key, lambda c: c.data and c.data == 'delete_key', chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_callback_query_handler(admin_show_users, lambda c: c.data and c.data == "show_users", chat_type=ChatType.PRIVATE, is_admin=True)

    dispatcher.register_callback_query_handler(admin_renew_trial, lambda c: c.data and c.data == "renew_trial", chat_type=ChatType.PRIVATE, is_admin=True)


    dispatcher.register_message_handler(admin_test_referal, commands=["admin_referal"], chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_callback_query_handler(admin_add_partner, lambda c: c.data and c.data == "add_partner", chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_message_handler(admin_save_partner, chat_type=ChatType.PRIVATE, state=AddPartnerState.user_id)
    dispatcher.register_callback_query_handler(partner_join_approve, partner_join_callback.filter(action_type='partner_join_approve'), chat_type=ChatType.PRIVATE, is_admin=True)

    dispatcher.register_callback_query_handler(admin_send_notification, admin_send_notification_callback.filter(action_type='send_notification'), chat_type=ChatType.PRIVATE, is_admin=True)
    dispatcher.register_message_handler(admin_send_notification_send, chat_type=ChatType.PRIVATE, state=AddNotificationState.message_text)

