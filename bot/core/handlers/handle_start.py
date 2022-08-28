from bot import ALLOWED_CHATS, ALLOWED_USERS, OWNER_ID


async def start_handler(message):
    user_id= message.sender_id
    chat_id= message.chat_id
    if user_id in ALLOWED_USERS or chat_id in ALLOWED_CHATS or user_id == OWNER_ID:
        msg = '''**Hello, ¡Welcome to Rclone-Tg-Bot!\n
I can help you copy files from one cloud to another.
Also can mirror files from Telegram to cloud and leech from cloud to Telegram**\n\n
Repository: https://github.com/Sam-Max/Rclone-Tg-Bot
'''
        await message.reply(msg)
    else:
        await message.reply('Not Authorized user, deploy your own version\n\nhttps://github.com/Sam-Max/Rclone-Tg-Bot')