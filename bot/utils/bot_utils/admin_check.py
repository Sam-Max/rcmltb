from bot import OWNER_ID


async def is_admin(user_id):
    if user_id == OWNER_ID:
        return True
    else:
        return False
        

