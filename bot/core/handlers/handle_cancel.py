
from bot.core import set_vars


async def handle_cancel(callback_query):
        set_vars("UP_CANCEL", True)