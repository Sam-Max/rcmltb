import asyncio
from os import remove as osremove, path as ospath, mkdir
from PIL import Image
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters
from bot import AS_DOC_USERS, AS_MEDIA_USERS, DB_URI, bot, config_dict
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import auto_delete_message, editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker

def getleechinfo(from_user):
    user_id = from_user.id
    name = from_user.first_name
    buttons = ButtonMaker()
    thumbpath = f"Thumbnails/{user_id}.jpg"
    if (user_id in AS_DOC_USERS or user_id not in AS_MEDIA_USERS and config_dict['AS_DOCUMENT']):
        ltype = "DOCUMENT"
        buttons.cb_buildbutton("Send As Media", f"leechset {user_id} med")
    else:
        ltype = "MEDIA"
        buttons.cb_buildbutton("Send As Document", f"leechset {user_id} doc")

    if ospath.exists(thumbpath):
        thumbmsg = "Exists"
        buttons.cb_buildbutton("Delete Thumbnail", f"leechset {user_id} thumb")
    else:
        thumbmsg = "Not Exists"  
        buttons.cb_buildbutton("Set Thumbnail", f"leechset {user_id} thumb")

    buttons.cb_buildbutton("✘ Close Menu", f"leechset {user_id} close")
    button = buttons.build_menu(1)

    text = f"<u>Settings for <a href='tg://user?id={user_id}'>{name}</a></u>\n\n"\
           f"Leech Type <b>{ltype}</b>\n"\
           f"Custom Thumbnail <b>{thumbmsg}</b>"
    return text, button

async def editLeechType(message, query):
    msg, button = getleechinfo(query.from_user)
    await editMessage(msg, message, button)

async def handle_leech_set(client, message):
    msg, button = getleechinfo(message.from_user)
    msg= await sendMarkup(msg, message, button)
    await auto_delete_message(message, msg)

async def handle_leech_set_type(client, callback_query):
    query = callback_query
    message = query.message
    user_id = query.from_user.id
    data = query.data
    data = data.split()
    if user_id != int(data[1]):
        await query.answer(text="This menu is not for you!", show_alert=True)
    elif data[2] == "doc":
        if user_id in AS_MEDIA_USERS:
            AS_MEDIA_USERS.remove(user_id)
        AS_DOC_USERS.add(user_id)
        if DB_URI is not None:
            DbManger().user_doc(user_id)
        await editLeechType(message, query)
    elif data[2] == "med":
        if user_id in AS_DOC_USERS:
            AS_DOC_USERS.remove(user_id)
        AS_MEDIA_USERS.add(user_id)
        if DB_URI is not None:
            DbManger().user_media(user_id)
        await editLeechType(message, query)
    elif data[2] == "thumb":
        path = f"Thumbnails/{user_id}.jpg"
        if ospath.lexists(path):
            osremove(path)
            if DB_URI is not None:
                DbManger().user_rm_thumb(user_id)
            await query.answer(text="Thumbnail Removed!", show_alert=True)
            await editLeechType(message, query)
        else:
            question= await editMessage("Send a photo to save thumbnail, /ignore to cancel", message)
            try:
                response = await client.listen.Message(filters.photo | filters.text, id=filters.user(user_id), timeout = 30)
            except asyncio.TimeoutError:
                await sendMessage("Too late 30s gone, try again!", message)
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
                            Image.open(photo_dir).convert("RGB").save(des_dir, "JPEG")
                            osremove(photo_dir)
                            if DB_URI is not None:
                                DbManger().user_save_thumb(user_id, des_dir)
                            await query.answer(text="Thumbnail Added!!", show_alert=True)
                    except Exception as ex:
                        await editMessage(str(ex), question)
            finally: 
                await editLeechType(message, query)
    elif data[2] == "close":
        await query.answer()
        await message.delete()
    else:
        await query.answer()
        try:
            await query.message.delete()
        except:
            pass

leech_set_handler = MessageHandler(handle_leech_set, filters= filters.command(BotCommands.UserSetCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
but_set_handler = CallbackQueryHandler(handle_leech_set_type, filters= filters.regex("leechset"))

bot.add_handler(leech_set_handler)
bot.add_handler(but_set_handler)
        