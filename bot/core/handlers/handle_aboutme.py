import time

from telethon import __version__ as telethonver
from pyrogram import __version__ as pyrogramver
from bot.utils import human_format
from ... import uptime

async def about_me(message):
    diff = time.time() - uptime
    diff = human_format.human_readable_timedelta(diff)

    msg = (
        f"<b>Telethon Version</b>: {telethonver}\n"
        f"<b>Pyrogram Version</b>: {pyrogramver}\n"
        "<b>Upload Engine:-</b> <code>Rclone</code> \n"
        "\n"
    )

    await message.reply(msg, parse_mode="html")