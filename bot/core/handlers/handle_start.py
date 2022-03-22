from bot.core.get_vars import get_val


async def start_handler(message):
    user_id= message.sender_id
    chat_id= message.chat_id
    if user_id in get_val("ALLOWED_USERS") or chat_id in get_val("ALLOWED_CHATS") or user_id == get_val("OWNER_ID"):
        msg = '''**Hello, ¡Welcome to Rclone-Tg-Bot!\n\n
I can help you transfer files from one cloud to another.\n
Can also mirror files from telegram to cloud and leech from cloud to telegram**\n\n
Made by: https://github.com/Sam-Max
'''
        await message.reply(msg)
    else:
        await message.reply('Not Authorized user, deploy your own version\n\nhttps://github.com/Sam-Max/Rclone-Tg-Bot')