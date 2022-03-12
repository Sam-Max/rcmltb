from bot.utils.admin_check import is_admin


async def start_handler(e):
    if await is_admin(e.sender_id):
        msg = ''' 
        **Hello, ¡Welcome to Rclone Bot!**\n
        **I can help you transfer files from one cloud to another. 
        I can also mirror files from telegram to cloud and leech from cloud to telegram**\n
        '''
        await e.reply(msg)
    else:
        await e.delete()