from bot.utils.admin_check import is_admin
from bot.utils.speedtest import get_speed


async def speed_handler(e):
    if await is_admin(e.sender_id):
        await get_speed(e)
    else:
        await e.reply('Not Authorized user')