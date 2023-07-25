from loader import db, outline
from datetime import datetime, timedelta
import pytz

from tgbot.controllers import notifications_controller

def new_key():
    print("\n NEW_KEY \n")
    return "key"

async def trial_prolong_for_all():
    try:
        current_date = datetime.now(pytz.utc)
        keys = await db.get_all_keys_data()

        for x in keys:
            key_label = x['label']
            user_id = x["owner_id"]
            key_outline_key_id = x["outline_key_id"]

            if key_outline_key_id:
                payments = await db.get_payment_by_id(key_label, user_id)
                if len(payments) > 0:
                    last_payment = payments[0] 
                    if last_payment['sum'] == 0:
                        print(f"last_payment: {last_payment['sum']}")
                        print(f"key_id: {key_outline_key_id}")
                        expiration_date = current_date + timedelta(days=7)
                        await db.update_key_expiration(key_outline_key_id, key_label, expiration_date)
                        print(f"expiration_date: {expiration_date}")
            else:
                print(f"No outline_key_id")

    except Exception as e:
        print(f"ERROR: {e}")

async def disable_expired_keys():
    try:
        current_date = datetime.now(pytz.utc)
        keys = await db.get_all_keys_data()
        
        async def get_name_data(x):
            server_data = await db.get_server_by_id(int(x["server_id"]))
            server_name = server_data[0][0][1]
            return server_name

        for x in keys:
            print(f'\n{x}')
            print(f'\n X: {x["expiration_at"]} \n NOW: {current_date} \n')
            days_left = (x["expiration_at"] - current_date).days
            key_active = x['active']
            key_bought = x['bought']
            key_id = x['id']
            label = x["label"]
            user_id = x["owner_id"]

            

            print(f'\n{days_left}\n')

            if days_left <= 0:
                if key_active == True or key_bought == True:
                    print(f'\nKEY EXPIRED\n')
                    print(f'ACTIVE: {key_active}\n')
                    label = x["label"]
                    user_id = x["owner_id"]
                    outline_key_id = x["outline_key_id"]
                    api_link = await db.get_server_key(int(x["server_id"]))
                    print(f'KEY_ID: {outline_key_id}\n')
                    print(f'API_LINK: {api_link}\n')
                    if not outline_key_id:
                        raise Exception("Invalid Key ID")
                    if not api_link:
                        raise Exception("Invalid Api Link")
                    
                    await outline.set_data_limit(api_link, outline_key_id)
                    await db.update_payment_status(user_id, label, False)
                    # await db.set_key_active(key_id, label, False)
            
            if days_left == 6:
                if key_active == True or key_bought == True:
                    server_name = await get_name_data(x)
                    await notifications_controller.send_expiration_notification(user_id, server_name, key_id, days_left)
                
            if days_left == 1:
                if key_active == True or key_bought == True:
                    server_name = await get_name_data(x)
                    await notifications_controller.send_expiration_notification(user_id, server_name, key_id, days_left)
        return
    except Exception as e:
        print(f'\n ERROR: {e}\n')

async def delete_unused_keys():
    try:
        current_date = datetime.now(pytz.utc)
        keys = await db.get_all_keys_data()

        for x in keys:

            days_live = (current_date - x["created_at"]).days
            key_active = x['active']
            key_bought = x['bought']
            key_outline = x['outline_key_id']
            key_label = x['label']
            key_owner_id = x['owner_id']
            key_server_id = x['server_id']
            
            if days_live > 0:
                if not key_active and not key_outline and not key_bought:
                    await db.delete_payment_by_label(key_owner_id, key_label)
                    await db.delete_key(key_label, key_server_id)
                    print(f'\nKEY UNUSED\n {x} \n')
        return
    except Exception as e:
        print(f"ERROR: {e}")

async def get_all_keys(user_id):
    
    async def get_server_name(server):
        print(f"\n SERVER_ID: {server}")
        result = await db.get_server_by_id(server)
        print (f"RESULT: {result}")
        return f"{result[0][0][1]}"

    def get_active(active):
        print(f"\n ACTIVE: {active}")
        result = "🔴"
        if active == True:
            result = "🟢"
        return f"{result}"
    
    def get_paid(bought):
        result = "Неоплачен"
        if bought == True:
            result = "Оплачен"
        return f"{result}"

    def days_left(date):
        current_date = datetime.now(pytz.utc)
        result = (date - current_date).days
        return result
    
    keys = await db.get_all_keys(user_id)

    predefined_keys = [x[0] for x in keys]

    # for x in keys:
    #     print(f'\n X IN KEYS: {x[0]}')
    
    
    
    result = [(await get_server_name(server), get_active(active), get_paid(bought), label, outline_key_id, days_left(expiration_at)) for server, active, bought, label, outline_key_id, expiration_at in predefined_keys]
    
    
    return result
