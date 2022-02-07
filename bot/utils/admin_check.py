# -*- coding: utf-8 -*-

from ..core.getVars import get_val


async def is_admin(user_id):
    if user_id == get_val("OWNER_ID"):
        return True
    else:
        return False
