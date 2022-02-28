
from bot.core.set_vars import set_val


async def handle_cancel(callback_query):
        set_val("UPLOAD_CANCEL", True)