from loader import db

async def get_referal_users(referal_id):
    referal_users = await db.get_referal_users(referal_id)
    print('\n Referal users: \n', referal_users)
    return referal_users