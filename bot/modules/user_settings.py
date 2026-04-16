import asyncio
from html import escape
from os import remove as osremove, path as ospath, mkdir
from PIL import Image
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters
from bot import (
    DATABASE_URL,
    IS_PREMIUM_USER,
    TG_MAX_SPLIT_SIZE,
    bot,
    config_dict,
    user_data,
)
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import run_sync_to_async, update_user_ldata
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
    rclone_conf = f"rclone/{user_id}/rclone.conf"
    token_pickle = f"tokens/{user_id}.pickle"
    user_dict = user_data.get(user_id, {})

    if (
        user_dict.get("as_doc", False)
        or "as_doc" not in user_dict
        and config_dict["AS_DOCUMENT"]
    ):
        ltype = "DOCUMENT"
        buttons.cb_buildbutton("📷 Send As Media", f"userset {user_id} doc")
    else:
        ltype = "MEDIA"
        buttons.cb_buildbutton("📄 Send As Document", f"userset {user_id} doc")

    buttons.cb_buildbutton("🔪 Leech Splits", f"userset {user_id} lss")
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

    rccmsg = "Exists" if ospath.exists(rclone_conf) else "Not Exists"

    tokenmsg = "Exists" if ospath.exists(token_pickle) else "Not Exists"

    index = user_dict["index_url"] if user_dict.get("index_url", False) else "None"

    if user_dict.get("gdrive_id", False):
        gdrive_id = user_dict["gdrive_id"]
    elif GI := config_dict["GDRIVE_FOLDER_ID"]:
        gdrive_id = GI
    else:
        gdrive_id = "None"

    buttons.cb_buildbutton("🎥 YT-DLP Options", f"userset {user_id} yto")
    if user_dict.get("yt_opt", False):
        ytopt = user_dict["yt_opt"]
    elif "yt_opt" not in user_dict and (YTO := config_dict["YT_DLP_OPTIONS"]):
        ytopt = YTO
    else:
        ytopt = "None"

    buttons.cb_buildbutton("📝 Name Substitute", f"userset {user_id} ns")
    if user_dict.get("name_sub", False):
        name_sub = user_dict["name_sub"]
    elif "name_sub" not in user_dict and (NS := config_dict["NAME_SUBSTITUTE"]):
        name_sub = NS
    else:
        name_sub = "None"

    buttons.cb_buildbutton("🖼️ Thumbnail", f"userset {user_id} sthumb")
    if ospath.exists(thumbpath):
        thumbmsg = "Exists"
    else:
        thumbmsg = "Not Exists"

    buttons.cb_buildbutton("📸 Screenshots", f"userset {user_id} sscreenshots")
    screenshots_count = user_dict.get("screenshots_count", 0)
    if screenshots_count == 0:
        screenshots_msg = "Disabled"
    else:
        screenshots_msg = f"{screenshots_count} shots"

    buttons.cb_buildbutton("📂 Category", f"userset {user_id} category")
    category = user_dict.get("category", "")
    category_msg = category if category else "None"

    buttons.cb_buildbutton("📁 Upload Template", f"userset {user_id} utemplate")
    upload_template = user_dict.get("upload_template", "")
    if upload_template:
        template_msg = "Custom"
    elif config_dict.get("UPLOAD_PATH_TEMPLATE"):
        template_msg = "Global"
    else:
        template_msg = "None"

    buttons.cb_buildbutton("✘ Close Menu", f"userset {user_id} close")

    text = f"""
⚙️ <b>Settings for {name}</b>

Leech Type: <b>{ltype}</b>
Custom Thumbnail: <b>{thumbmsg}</b>
Screenshots: <b>{screenshots_msg}</b>
Category: <b>{category_msg}</b>
Upload Template: <b>{template_msg}</b>
Leech Split Size: <b>{split_size}</b>
Equal Splits: <b>{equal_splits}</b>
YT-DLP Options: <b><code>{escape(ytopt)}</code></b>
Name Substitute: <b><code>{escape(name_sub)}</code></b>
Rclone Config <b>{rccmsg}</b>
Gdrive Token <b>{tokenmsg}</b>
Gdrive ID is <code>{gdrive_id}</code>
Index Link is <code>{index}</code>
"""

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


async def set_name_substitute(_, message, query):
    user_id = message.from_user.id
    value = message.text
    update_user_ldata(user_id, "name_sub", value)
    await message.delete()
    await update_user_settings(query)
    if DATABASE_URL:
        await DbManager().update_user_data(user_id)


async def leech_split_size(_, message, query):
    user_id = message.from_user.id
    value = min(int(message.text), TG_MAX_SPLIT_SIZE)
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
            buttons.cb_buildbutton("👁 View Thumbnail", f"userset {user_id} vthumb")
            buttons.cb_buildbutton("🗑️ Delete Thumbnail", f"userset {user_id} dthumb")
        buttons.cb_buildbutton("Back", f"userset {user_id} back")
        buttons.cb_buildbutton("Close", f"userset {user_id} close")
        question = await editMessage(
            "🖼️ <b>Send a photo to save as custom thumbnail</b>", message, buttons.build_menu(1)
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
                    await run_sync_to_async(
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
    elif data[2] == "ns":
        await query.answer()
        buttons = ButtonMaker()
        buttons.cb_buildbutton("Back", f"userset {user_id} back")
        if user_dict.get("name_sub", False) or config_dict["NAME_SUBSTITUTE"]:
            buttons.cb_buildbutton(
                "Remove Name Substitute", f"userset {user_id} rns", "header"
            )
        buttons.cb_buildbutton("Close", f"userset {user_id} close")
        rmsg = """
Send Name Substitute pattern.
Format: old::new|old2::new2
Use \\| for literal | in filenames
Use \\:: for literal :: in filenames

Examples:
  script::code          # Replace "script" with "code"
  mltb::                # Remove "mltb"
  [test]::test          # Replace "[test]" with "test"
  space::               # Remove spaces
        """
        await editMessage(rmsg, message, buttons.build_menu(1))
        try:
            if response := await client.listen.Message(
                filters.text, id=filters.user(user_id), timeout=60
            ):
                await set_name_substitute(client, response, query)
        except asyncio.TimeoutError:
            await sendMessage("Too late 60s gone, try again!", message)
    elif data[2] == "rns":
        await query.answer()
        update_user_ldata(user_id, "name_sub", "")
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
    elif data[2] == "sscreenshots":
        await query.answer()
        buttons = ButtonMaker()
        current_count = user_dict.get("screenshots_count", 0)
        if current_count > 0:
            buttons.cb_buildbutton("Disable Screenshots", f"userset {user_id} ss_disable")
        for count in [3, 5, 8, 10]:
            btn_text = f"{count} shots"
            if current_count == count:
                btn_text = f"✓ {count} shots"
            buttons.cb_buildbutton(btn_text, f"userset {user_id} ss_count {count}")

        # Album option
        is_album = user_dict.get("screenshots_as_album", True)
        album_text = "✓ Send as Album" if is_album else "Send as Album"
        buttons.cb_buildbutton(album_text, f"userset {user_id} ss_album")

        buttons.cb_buildbutton("Back", f"userset {user_id} back")
        buttons.cb_buildbutton("Close", f"userset {user_id} close")
        await editMessage(
            "📸 <b>Screenshots Settings</b>\n\nSelect number of screenshots to generate during leech (0 to disable):",
            message,
            buttons.build_menu(2)
        )
    elif data[2] == "ss_disable":
        await query.answer()
        update_user_ldata(user_id, "screenshots_count", 0)
        await update_user_settings(query)
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == "ss_count":
        await query.answer()
        count = int(data[3])
        update_user_ldata(user_id, "screenshots_count", count)
        await update_user_settings(query)
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == "ss_album":
        await query.answer()
        current = user_dict.get("screenshots_as_album", True)
        update_user_ldata(user_id, "screenshots_as_album", not current)
        await update_user_settings(query)
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == "category":
        await query.answer()
        buttons = ButtonMaker()
        categories = ["Movies", "TV Shows", "Music", "Books", "Software", "Others"]
        current_category = user_dict.get("category", "")
        for cat in categories:
            btn_text = f"✓ {cat}" if current_category == cat else cat
            buttons.cb_buildbutton(btn_text, f"userset {user_id} set_cat {cat}")
        if current_category:
            buttons.cb_buildbutton("Clear Category", f"userset {user_id} clear_cat", "header")
        buttons.cb_buildbutton("Back", f"userset {user_id} back")
        buttons.cb_buildbutton("Close", f"userset {user_id} close")
        await editMessage(
            "📂 <b>Select Category</b>\n\nThis is used for upload path organization:",
            message,
            buttons.build_menu(2)
        )
    elif data[2] == "set_cat":
        await query.answer()
        category = data[3]
        update_user_ldata(user_id, "category", category)
        await update_user_settings(query)
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == "clear_cat":
        await query.answer()
        update_user_ldata(user_id, "category", "")
        await update_user_settings(query)
        if DATABASE_URL:
            await DbManager().update_user_data(user_id)
    elif data[2] == "utemplate":
        await query.answer()
        buttons = ButtonMaker()
        current_template = user_dict.get("upload_template", "")
        global_template = config_dict.get("UPLOAD_PATH_TEMPLATE", "")

        if current_template or global_template:
            buttons.cb_buildbutton("Remove Custom Template", f"userset {user_id} rutemplate", "header")

        buttons.cb_buildbutton("Set Custom Template", f"userset {user_id} set_utemplate")
        buttons.cb_buildbutton("Back", f"userset {user_id} back")
        buttons.cb_buildbutton("Close", f"userset {user_id} close")

        template_preview = current_template or global_template or "Not set"
        preview_path = ""
        if template_preview != "Not set":
            from bot.helper.ext_utils.template_utils import apply_upload_template
            username = from_user.username or str(user_id)
            preview_path = apply_upload_template(
                template_preview,
                user_id,
                username,
                category=user_dict.get("category", ""),
                task_type="mirror"
            )

        rmsg = f"""📁 <b>Upload Path Template</b>

<b>Current Template:</b> <code>{template_preview}</code>

<b>Preview Path:</b> <code>{preview_path or 'N/A'}</code>

<b>Available Variables:</b>
<code>{{username}}</code> - Username
<code>{{user_id}}</code> - User ID
<code>{{date}}</code> - Current date (YYYY-MM-DD)
<code>{{year}}</code> - Current year
<code>{{month}}</code> - Current month
<code>{{day}}</code> - Current day
<code>{{category}}</code> - Selected category
<code>{{task_type}}</code> - Task type (mirror/leech/clone)

<b>Example:</b> <code>remote:/{{username}}/{{category}}/{{date}}/</code>
"""
        await editMessage(rmsg, message, buttons.build_menu(1))
    elif data[2] == "set_utemplate":
        await query.answer()
        buttons = ButtonMaker()
        buttons.cb_buildbutton("Back", f"userset {user_id} utemplate")
        buttons.cb_buildbutton("Close", f"userset {user_id} close")
        rmsg = """📁 <b>Set Upload Path Template</b>

Send the template path with variables.

<b>Example:</b>
<code>remote:/{username}/{category}/{date}/</code>
<code>remote:Mirror/{user_id}/{task_type}/{year}-{month}/</code>

Send <code>/ignore</code> to cancel. Timeout: 60 sec"""
        await editMessage(rmsg, message, buttons.build_menu(1))
        try:
            if response := await client.listen.Message(
                filters.text, id=filters.user(user_id), timeout=60
            ):
                if "/ignore" in response.text:
                    await client.listen.Cancel(filters.user(user_id))
                else:
                    template = response.text.strip()
                    update_user_ldata(user_id, "upload_template", template)
                    await update_user_settings(query)
                    if DATABASE_URL:
                        await DbManager().update_user_data(user_id)
        except asyncio.TimeoutError:
            await sendMessage("Too late 60s gone, try again!", message)
    elif data[2] == "rutemplate":
        await query.answer()
        update_user_ldata(user_id, "upload_template", "")
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


bot.add_handler(
    MessageHandler(
        user_settings,
        filters=filters.command(BotCommands.UserSetCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
bot.add_handler(
    CallbackQueryHandler(edit_user_settings, filters=filters.regex("userset"))
)
