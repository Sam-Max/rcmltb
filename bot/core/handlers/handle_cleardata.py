from datetime import datetime
from telethon.tl.types import KeyboardButtonCallback
from telethon import events
from bot.utils.admin_check import is_admin
from bot.utils.misc_utils import clear_stuff

async def cleardata_handler(e):
    if await is_admin(e.sender_id):
        if isinstance(e, events.CallbackQuery.Event):
            data = e.data.decode("UTF-8").split(" ")
            if data[1] == "yes":
                await e.answer("Clearing data.")
                await e.edit("Datos Limpiados {}".format(datetime.now().strftime("%d-%B-%Y, %H:%M:%S")))
                await clear_stuff("./Downloads")
            else:
                await e.answer("Aborting.")
                await e.delete()
        else:
            buttons = [[KeyboardButtonCallback("Yes", data= "cleardata yes"),
                        KeyboardButtonCallback("No", data= "cleardata no")]]
            await e.reply("¿Estás seguro de que quieres borrar los datos?\n"
                          "Esto eliminará todos sus datos, incluidos los archivos descargados, y afectará las transferencias en curso..\n",
                          buttons= buttons)
    else:
        await e.answer("⚠️ WARN ⚠️ Dont Touch Admin Settings.", alert=True)
