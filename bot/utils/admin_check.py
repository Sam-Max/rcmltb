import logging
from bot.core.get_vars import get_val
log = logging.getLogger(__name__)


async def is_admin(user_id):
    if user_id == get_val("OWNER_ID"):
        return True
    else:
        return False
        

