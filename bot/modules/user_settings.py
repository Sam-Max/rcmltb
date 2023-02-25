import asyncio
from os import remove as osremove, path as ospath, mkdir
from PIL import Image
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters
from bot import DATABASE_URL, bot, config_dict, user_data
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import run_sync, update_user_ldata
from bot.helper.ext_utils.db_handler import DbManager
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.button_build import ButtonMaker



def get_user_settings(from_user):
    user_id = from_user.id
    name = from_user.first_name
    buttons = ButtonMaker()
    thumbpath = f"Thumbnails/{user_id}.jpg"
    user_dict = user_data.get(user_id, False)
    if not user_dict and config_dict['AS_DOCUMENT'] or user_dict and user_dict.get('as_doc'):
        ltype = "DOCUMENT"
        buttons.cb_buildbutton("Send As Media", f"userset {user_id} med")
    else:
        ltype = "MEDIA"
        buttons.cb_buildbutton("Send As Document", f"userset {user_id} doc")

    if ospath.exists(thumbpath):
        thumbmsg = "Exists"
        buttons.cb_buildbutton("Change Thumbnail", f"userset {user_id} sthumb")
        buttons.cb_buildbutton("Delete Thumbnail", f"userset {user_id} dthumb")
    else:
        thumbmsg = "Not Exists"  
        buttons.cb_buildbutton("Set Thumbnail", f"userset {user_id} sthumb")

    buttons.cb_buildbutton("✘ Close Menu", f"userset {user_id} close")

    text = f"<u>Settings for <a href='tg://user?id={user_id}'>{name}</a></u>\n\n"\
           f"Leech Type <b>{ltype}</b>\n"\
           f"Custom Thumbnail <b>{thumbmsg}</b>"
    return text, buttons.build_menu(1)

async def update_user_settings(message, from_user):
    msg, button = get_user_settings(from_user)
    await editMessage(msg, message, button)

async def user_settings(client, message):
    msg, button = get_user_settings(message.from_user)
    await sendMarkup(msg, message, button)

async def edit_user_settings(client, callback_query):
    query = callback_query
    message = query.message
    user_id = query.from_user.id
    data = query.data
    data = data.split()
    if user_id != int(data[1]):
        await query.answer(text="Not Yours!", show_alert=True)
    elif data[2] == "doc":
        update_user_ldata(user_id, 'as_doc', True)
        await query.answer(text="Your File Will Deliver As Document!", show_alert=True)
        await update_user_settings(message, query.from_user)
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == "med":
        update_user_ldata(user_id, 'as_doc', False)
        await query.answer(text="Your File Will Deliver As Media!", show_alert=True)
        await update_user_settings(message, query.from_user)
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == "dthumb":
        path = f"Thumbnails/{user_id}.jpg"
        if ospath.lexists(path):
            await query.answer(text="Thumbnail Removed!", show_alert=True)
            osremove(path)
            update_user_ldata(user_id, 'thumb', '')
            await update_user_settings(message, query.from_user)
            if DATABASE_URL:
                await DbManager().update_thumb(user_id)
        else:
            await query.answer(text="Old Settings", show_alert=True)
            await update_user_settings(message, query.from_user)
    elif data[2] == "sthumb":
        await query.answer()
        question= await editMessage("Send a photo to save as custom thumbnail, /ignore to cancel", message)
        try:
            response = await client.listen.Message(filters.photo | filters.text, id=filters.user(user_id), timeout = 60)
        except asyncio.TimeoutError:
            await sendMessage("Too late 60s gone, try again!", message)
        else:
            if response:
                try: 
                    if response.text:
                        if "/ignore" in response.text:
                            await client.listen.Cancel(filters.user(user_id))
                    else:  
                        path = "Thumbnails/"
                        if not ospath.isdir(path):
                            mkdir(path)
                        photo_dir = await client.download_media(response)
                        des_dir = ospath.join(path, f'{user_id}.jpg')
                        await run_sync(Image.open(photo_dir).convert("RGB").save, des_dir, "JPEG")
                        osremove(photo_dir)
                        await query.answer(text="Thumbnail Added!!", show_alert=True)
                        if DATABASE_URL:
                            await DbManager().update_thumb(user_id, des_dir)
                except Exception as ex:
                    await editMessage(str(ex), question)
        finally: 
            await update_user_settings(message, message.from_user)
    elif data[2] == 'back':
        await query.answer()
        await update_user_settings(message, query.from_user)
    elif data[2] == "close":
        await query.answer()
        await message.delete()
    else:
        await query.answer()
        await query.message.delete()
        await query.message.reply_to_message.delete()



user_set_handler = MessageHandler(user_settings, filters= filters.command(BotCommands.UserSetCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
but_set_handler = CallbackQueryHandler(edit_user_settings, filters= filters.regex("userset"))

bot.add_handler(user_set_handler)
bot.add_handler(but_set_handler)

        