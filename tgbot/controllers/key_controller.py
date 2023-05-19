from loader import db


def new_key():
    print("\n NEW_KEY \n")
    return "key"


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
    
    
    
    result = [(await get_server_name(server), get_active(active), get_paid(bought),label) for server, active, bought, label in predefined_keys]
    
    
    return result
