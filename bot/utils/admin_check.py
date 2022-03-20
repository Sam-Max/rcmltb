import logging
from bot.core.get_vars import get_val
log = logging.getLogger(__name__)


async def is_admin(user_id, force_owner=False):
    if force_owner:
        if user_id == get_val("OWNER_ID"):
            return True
        else:
            return False
        
    if user_id in get_val("ALD_USR"):
       return True
    else:
       return False

