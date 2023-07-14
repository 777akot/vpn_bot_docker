from loader import db, outline
from datetime import datetime, timedelta
import pytz

def new_key():
    print("\n NEW_KEY \n")
    return "key"

async def disable_expired_keys():
    try:
        current_date = datetime.now(pytz.utc)
        keys = await db.get_all_keys_data()
        
        for x in keys:
            print(f'\n{x}')
            print(f'\n X: {x["expiration_at"]} \n NOW: {current_date} \n')
            days_left = (x["expiration_at"] - current_date).days
            key_active = x['active']
            print(f'\n{days_left}\n')
            if days_left <= 0 and key_active == True:
                
                print(f'\nKEY EXPIRED\n')
                print(f'ACTIVE: {key_active}\n')
                label = x["label"]
                key_id = x["outline_key_id"]
                api_link = await db.get_server_key(int(x["server_id"]))
                print(f'KEY_ID: {key_id}\n')
                print(f'API_LINK: {api_link}\n')
                if not key_id:
                    raise "Invalid Key ID"
                if not api_link:
                    raise "Invalid Api Link"
                
                await outline.set_data_limit(api_link, key_id)
                await db.set_key_active(key_id, label, False)

        return
    except Exception as e:
        print(f'\n ERROR: {e}\n')

async def get_all_keys(user_id):
    
    async def get_server_name(server):
        print(f"\n SERVER_ID: {server}")
        result = await db.get_server_by_id(server)
        print (f"RESULT: {result}")
        return f"{result[0][0][1]}"

    def get_active(active):
        print(f"\n ACTIVE: {active}")
        result = "Неактивен"
        if active == True:
            result = "Активен"
        return f"{result}"
    
    def get_paid(bought):
        result = "Неоплачен"
        if bought == True:
            result = "Оплачен"
        return f"{result}"

    keys = await db.get_all_keys(user_id)

    predefined_keys = [x[0] for x in keys]

    for x in keys:
        print(f'\n X IN KEYS: {x[0]}')
    
    
    
    result = [(await get_server_name(server), get_active(active), get_paid(bought), label, outline_key_id) for server, active, bought, label, outline_key_id in predefined_keys]
    
    
    return result
