import asyncio
from html import escape
from os import remove as osremove, path as ospath, mkdir
from PIL import Image
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters
from bot import (
    DATABASE_URL,
    IS_PREMIUM_USER,
    TG_MAX_FILE_SIZE,
    bot,
    config_dict,
    user_data,
)
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import run_sync, update_user_ldata
from bot.helper.ext_utils.db_handler import DbManager
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (
    editMessage,
    sendFile,
    sendMarkup,
    sendMessage,
)
from bot.helper.telegram_helper.button_build import ButtonMaker


def get_user_settings(from_user):
    user_id = from_user.id
    name = from_user.first_name
    buttons = ButtonMaker()
    thumbpath = f"Thumbnails/{user_id}.jpg"
    user_dict = user_data.get(user_id, {})
    if (
        user_dict.get("as_doc", False)
        or "as_doc" not in user_dict
        and config_dict["AS_DOCUMENT"]
    ):
        ltype = "DOCUMENT"
        buttons.cb_buildbutton("Send As Media", f"userset {user_id} doc")
    else:
        ltype = "MEDIA"
        buttons.cb_buildbutton("Send As Document", f"userset {user_id} doc")

    buttons.cb_buildbutton("Leech Splits", f"userset {user_id} lss")
    if user_dict.get("split_size", False):
        split_size = user_dict["split_size"]
    else:
        split_size = config_dict["LEECH_SPLIT_SIZE"]

    if (
        user_dict.get("equal_splits", False)
        or "equal_splits" not in user_dict
        and config_dict["EQUAL_SPLITS"]
    ):
        equal_splits = "Enabled"
    else:
        equal_splits = "Disabled"

    buttons.cb_buildbutton("YT-DLP Options", f"userset {user_id} yto")
    if user_dict.get("yt_opt", False):
        ytopt = user_dict["yt_opt"]
    elif "yt_opt" not in user_dict and (YTO := config_dict["YT_DLP_OPTIONS"]):
        ytopt = YTO
    else:
        ytopt = "None"

    buttons.cb_buildbutton("Thumbnail", f"userset {user_id} sthumb")
    if ospath.exists(thumbpath):
        thumbmsg = "Exists"
    else:
        thumbmsg = "Not Exists"

    buttons.cb_buildbutton("✘ Close Menu", f"userset {user_id} close")

    text = f"""<b>Settings for {name}</b>
Leech Type: <b>{ltype}</b>
Custom Thumbnail: <b>{thumbmsg}</b>
Leech Split Size: <b>{split_size}</b>
Equal Splits: <b>{equal_splits}</b>
Yy-dlp options: <b><code>{escape(ytopt)}</code></b>"""

    return text, buttons.build_menu(1)


async def update_user_settings(query):
    msg, button = get_user_settings(query.from_user)
    await editMessage(msg, query.message, button)


async def user_settings(_, message):
    msg, button = get_user_settings(message.from_user)
    await sendMarkup(msg, message, button)


async def set_yt_options(_, message, query):
    user_id = message.from_user.id
    value = message.text
    update_user_ldata(user_id, "yt_opt", value)
    await message.delete()
    await update_user_settings(query)
    if DATABASE_URL:
        await DbManager().update_user_data(user_id)


async def leech_split_size(_, message, query):
    user_id = message.from_user.id
    value = min(int(message.text), TG_MAX_FILE_SIZE)
    update_user_ldata(user_id, "split_size", value)
    await message.delete()
    await update_user_settings(query)
    if DATABASE_URL:
        await DbManager().update_user_data(user_id)


async def edit_user_settings(client, query):
    message = query.message
    user_id = query.from_user.id
    from_user = query.from_user
    data = query.data.split()
    user_dict = user_data.get(user_id, {})
    thumb_path = f"Thumbnails/{user_id}.jpg"

    if user_id != int(data[1]):
        await query.answer(text="Not Yours!", show_alert=True)
    elif data[2] == "doc":
        update_user_ldata(user_id, "as_doc", not user_dict.get("as_doc", False))
        await query.answer()
        await update_user_settings(query)
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == "vthumb":
        await query.answer()
        await sendFile(message, thumb_path, from_user.mention)
        await update_user_settings(query)
    elif data[2] == "dthumb":
        if ospath.lexists(thumb_path):
            await query.answer()
            osremove(thumb_path)
            update_user_ldata(user_id, "thumb", "")
            await update_user_settings(query)
            if DATABASE_URL:
                await DbManager().update_thumb(user_id)
        else:
            await query.answer(text="Old Settings", show_alert=True)
            await update_user_settings(query)
    elif data[2] == "sthumb":
        await query.answer()
        buttons = ButtonMaker()
        if ospath.exists(thumb_path):
            buttons.cb_buildbutton("View Thumbnail", f"userset {user_id} vthumb")
            buttons.cb_buildbutton("Delete Thumbnail", f"userset {user_id} dthumb")
        buttons.cb_buildbutton("Back", f"userset {user_id} back")
        buttons.cb_buildbutton("Close", f"userset {user_id} close")
        question = await editMessage(
            "Send a photo to save as custom thumbnail", message, buttons.build_menu(1)
        )
        try:
            if response := await client.listen.Message(
                filters.photo, id=filters.user(user_id), timeout=60
            ):
                try:
                    path = "Thumbnails/"
                    if not ospath.isdir(path):
                        mkdir(path)
                    photo_dir = await client.download_media(response)
                    des_dir = ospath.join(path, f"{user_id}.jpg")
                    await run_sync(
                        Image.open(photo_dir).convert("RGB").save, des_dir, "JPEG"
                    )
                    osremove(photo_dir)
                    update_user_ldata(user_id, "thumb", des_dir)
                    await update_user_settings(query)
                    if DATABASE_URL:
                        await DbManager().update_thumb(user_id, des_dir)
                except Exception as ex:
                    await editMessage(str(ex), question)
        except asyncio.TimeoutError:
            await sendMessage("Too late 60s gone, try again!", message)
    elif data[2] == "yto":
        await query.answer()
        buttons = ButtonMaker()
        buttons.cb_buildbutton("Back", f"userset {user_id} back")
        if user_dict.get("yt_opt", False) or config_dict["YT_DLP_OPTIONS"]:
            buttons.cb_buildbutton(
                "Remove YT-DLP Options", f"userset {user_id} ryto", "header"
            )
        buttons.cb_buildbutton("Close", f"userset {user_id} close")
        rmsg = """
Send YT-DLP Options.
Format: key:value|key:value|key:value.
Example: format:bv*+mergeall[vcodec=none]|nocheckcertificate:True
Check all yt-dlp api options from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L184'>FILE</a> or use this <a href='https://t.me/mltb_official/177'>script</a> to convert cli arguments to api options.
        """
        await editMessage(rmsg, message, buttons.build_menu(1))
        try:
            if response := await client.listen.Message(
                filters.text, id=filters.user(user_id), timeout=60
            ):
                await set_yt_options(client, response, query)
        except asyncio.TimeoutError:
            await sendMessage("Too late 60s gone, try again!", message)
    elif data[2] == "ryto":
        await query.answer()
        update_user_ldata(user_id, "yt_opt", "")
        await update_user_settings(query)
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == "lss":
        await query.answer()
        buttons = ButtonMaker()
        if user_dict.get("split_size", False):
            buttons.cb_buildbutton("Reset Split Size", f"userset {user_id} rlss")
        if (
            user_dict.get("equal_splits", False)
            or "equal_splits" not in user_dict
            and config_dict["EQUAL_SPLITS"]
        ):
            buttons.cb_buildbutton("Disable Equal Splits", f"userset {user_id} esplits")
        else:
            buttons.cb_buildbutton("Enable Equal Splits", f"userset {user_id} esplits")
        buttons.cb_buildbutton("Back", f"userset {user_id} back")
        buttons.cb_buildbutton("Close", f"userset {user_id} close")
        await editMessage(
            f"Send Leech split size in bytes. IS_PREMIUM_USER: {IS_PREMIUM_USER}. Timeout: 60 sec",
            message,
            buttons.build_menu(1),
        )
        try:
            if response := await client.listen.Message(
                filters.text, id=filters.user(user_id), timeout=60
            ):
                await leech_split_size(client, response, query)
        except asyncio.TimeoutError:
            await sendMessage("Too late 60s gone, try again!", message)
    elif data[2] == "rlss":
        await query.answer()
        update_user_ldata(user_id, "split_size", "")
        await update_user_settings(query)
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == "esplits":
        await query.answer()
        update_user_ldata(
            user_id, "equal_splits", not user_dict.get("equal_splits", False)
        )
        await update_user_settings(query)
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == "back":
        await client.listen.Cancel(filters.user(user_id))
        await query.answer()
        await update_user_settings(query)
    elif data[2] == "close":
        await client.listen.Cancel(filters.user(user_id))
        await query.answer()
        await message.delete()
    else:
        await query.answer()
        await query.message.delete()
        await query.message.reply_to_message.delete()


user_set_handler = MessageHandler(
    user_settings,
    filters=filters.command(BotCommands.UserSetCommand)
    & (CustomFilters.user_filter | CustomFilters.chat_filter),
)
but_set_handler = CallbackQueryHandler(
    edit_user_settings, filters=filters.regex("userset")
)

bot.add_handler(user_set_handler)
bot.add_handler(but_set_handler)
