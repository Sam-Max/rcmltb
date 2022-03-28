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
                await e.edit("Data Cleared")
                await clear_stuff("./Downloads")
            else:
                await e.answer("Aborting.")
                await e.delete()
        else:
            buttons = [[KeyboardButtonCallback("Yes", data= "cleardata yes"),
                        KeyboardButtonCallback("No", data= "cleardata no")]]
            await e.reply("¿Are you sure you want to delete?\n"
                          "This will affect currents transfers!!\n",
                          buttons= buttons)
    else:
        await e.reply('Not Authorized user')
