from bot.utils.admin_check import is_admin


async def start_handler(e):
    if await is_admin(e.sender_id):
        msg = '''**Hello, ¡Welcome to Rclone-Tg-Bot!\n\nI can help you transfer files from one cloud to another.\nI can also mirror files from telegram to cloud and leech files and folders from cloud to telegram (you can use me inside chats too)**\n\nMade by: https://github.com/Sam-Max
        '''
        await e.reply(msg)
    else:
        await e.delete()