from bot.utils.admin_check import is_admin


async def start_handler(e):
    if await is_admin(e.sender_id):
        msg = ''' **Hola, ¡Bienvenido a Rclone bot!**\n
Puedo ayudarte a transferir archivos de una nube a otra nube. También puedo subir archivos de telegram a su almacenamiento en la nube.\n
**Se admiten más de 40 tipos de almacenamiento en la nube.**\n
'''
        await e.reply(msg)
    else:
        await e.delete()