from pyrogram.filters import regex
from pyrogram import filters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from bot import bot, config_dict
from bot.helper.ext_utils.bot_utils import run_sync
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.menu_utils import (
    Menus,
    rcloneListButtonMaker,
    rcloneListNextPage,
)
from bot.helper.telegram_helper.message_utils import editMessage, sendMessage
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.rclone_utils import (
    create_next_buttons,
    is_rclone_config,
    is_valid_path,
    list_folder,
    list_remotes,
)
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data, update_rclone_data
from bot.modules.myfilesset import (
    calculate_size,
    delete_empty_dir,
    delete_selected,
    delete_selection,
    myfiles_settings,
    rclone_dedupe,
    rclone_mkdir,
    rclone_rename,
    search_action,
)


async def handle_myfiles(client, message):
    user_id = message.from_user.id
    if await is_rclone_config(user_id, message):
        if config_dict["MULTI_RCLONE_CONFIG"] or CustomFilters._owner_query(user_id):
            await list_remotes(message, menu_type=Menus.MYFILES)
        else:
            await sendMessage("Not allowed to use", message)


async def myfiles_callback(client, callback_query):
    query = callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    tag = f"@{message.reply_to_message.from_user.username}"
    user_id = query.from_user.id
    base_dir = get_rclone_data("MYFILES_BASE_DIR", user_id)
    rclone_remote = get_rclone_data("MYFILES_REMOTE", user_id)
    is_folder = False

    if int(cmd[-1]) != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
        return
    if cmd[1] == "remote":
        update_rclone_data("MYFILES_BASE_DIR", "", user_id)  # Reset Dir
        update_rclone_data("MYFILES_REMOTE", cmd[2], user_id)
        await list_folder(message, cmd[2], "", menu_type=Menus.MYFILES, edit=True)
    elif cmd[1] == "remote_dir":
        path = get_rclone_data(cmd[2], user_id)
        base_dir += path + "/"
        if await is_valid_path(rclone_remote, base_dir, message):
            update_rclone_data("MYFILES_BASE_DIR", base_dir, user_id)
            await list_folder(
                message, rclone_remote, base_dir, menu_type=Menus.MYFILES, edit=True
            )
    # Handle back button
    elif cmd[1] == "back":
        if len(base_dir) == 0:
            await list_remotes(message, menu_type=Menus.MYFILES, edit=True)
            return
        base_dir_split = base_dir.split("/")[:-2]
        base_dir_string = ""
        for dir in base_dir_split:
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        update_rclone_data("MYFILES_BASE_DIR", base_dir, user_id)
        await list_folder(
            message, rclone_remote, base_dir, menu_type=Menus.MYFILES, edit=True
        )
    elif cmd[1] == "back_remotes_menu":
        await list_remotes(message, menu_type=Menus.MYFILES, edit=True)
    # Handle actions
    elif cmd[1] == "file_action":
        path = get_rclone_data(cmd[2], user_id)
        base_dir += path
        update_rclone_data("MYFILES_BASE_DIR", base_dir, user_id)
        await myfiles_settings(
            message, rclone_remote, base_dir, edit=True, is_folder=False
        )
        await query.answer()
    elif cmd[1] == "folder_action":
        await myfiles_settings(
            message, rclone_remote, base_dir, edit=True, is_folder=True
        )
        await query.answer()
    elif cmd[1] == "search":
        await search_action(client, message, query, rclone_remote, user_id)
    elif cmd[1] == "delete":
        if cmd[2] == "folder":
            is_folder = True
        await delete_selection(message, user_id, is_folder=is_folder)
        await query.answer()
    elif cmd[1] == "size":
        await calculate_size(message, base_dir, rclone_remote, user_id)
        await query.answer()
    elif cmd[1] == "mkdir":
        await query.answer()
        await rclone_mkdir(client, message, rclone_remote, base_dir, tag)
    elif cmd[1] == "rmdir":
        await query.answer()
        await delete_empty_dir(message, user_id, rclone_remote, base_dir)
    elif cmd[1] == "dedupe":
        await query.answer()
        await rclone_dedupe(message, rclone_remote, base_dir, user_id, tag)
    elif cmd[1] == "rename":
        await query.answer()
        await rclone_rename(client, message, rclone_remote, base_dir, tag)
    elif cmd[1] == "yes":
        if cmd[2] == "folder":
            is_folder = True
        await delete_selected(
            message, user_id, base_dir, rclone_remote, is_folder=is_folder
        )
        await query.answer()
    elif cmd[1] == "no":
        await query.answer()
        await message.delete()
    elif cmd[1] == "pages":
        await query.answer()
    else:
        await query.answer()
        await message.delete()


async def next_page_myfiles(client, callback_query):
    query = callback_query
    data = query.data
    message = query.message
    await query.answer()
    user_id = message.reply_to_message.from_user.id
    _, next_offset, _, data_back_cb = data.split()

    info = get_rclone_data("info", user_id)
    total = len(info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10

    buttons = ButtonMaker()
    buttons.cb_buildbutton(f"⚙️ Folder Options", f"myfilesmenu^folder_action^{user_id}")
    buttons.cb_buildbutton("🔍 Search", f"myfilesmenu^search^{user_id}")

    next_info, _next_offset = await run_sync(rcloneListNextPage, info, next_offset)

    await run_sync(
        rcloneListButtonMaker,
        info=next_info,
        button=buttons,
        menu_type=Menus.MYFILES,
        dir_callback="remote_dir",
        file_callback="file_action",
        user_id=user_id,
    )

    await create_next_buttons(
        next_offset,
        prev_offset,
        _next_offset,
        data_back_cb,
        total,
        user_id,
        buttons,
        filter="next_myfiles",
        menu_type=Menus.MYFILES,
    )

    remote = get_rclone_data("MYFILES_REMOTE", user_id)
    base_dir = get_rclone_data("MYFILES_BASE_DIR", user_id)
    msg = f"Your cloud files are listed below\n\n<b>Path:</b><code>{remote}:{base_dir}</code>"
    await editMessage(msg, message, reply_markup=buttons.build_menu(1))


myfiles_handler = MessageHandler(
    handle_myfiles,
    filters=filters.command(BotCommands.MyFilesCommand)
    & (CustomFilters.user_filter | CustomFilters.chat_filter),
)
next_page_myfiles_cb = CallbackQueryHandler(
    next_page_myfiles, filters=regex("next_myfiles")
)
myfiles_cb = CallbackQueryHandler(myfiles_callback, filters=regex("myfilesmenu"))


bot.add_handler(myfiles_cb)
bot.add_handler(next_page_myfiles_cb)
bot.add_handler(myfiles_handler)
