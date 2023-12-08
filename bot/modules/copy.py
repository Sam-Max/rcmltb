from bot import bot, config_dict
from pyrogram.filters import regex, command
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from bot.helper.ext_utils.bot_utils import run_sync
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.menu_utils import (
    Menus,
    rcloneListButtonMaker,
    rcloneListNextPage,
)
from bot.helper.telegram_helper.message_utils import (
    deleteMessage,
    editMessage,
    sendMessage,
)
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.rclone_utils import (
    create_next_buttons,
    is_rclone_config,
    is_valid_path,
    list_folder,
    list_remotes,
)
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data, update_rclone_data
from bot.helper.mirror_leech_utils.download_utils.rclone_copy import RcloneCopy
from bot.modules.tasks_listener import TaskListener


listener_dict = {}


async def handle_copy(client, message):
    user_id = message.from_user.id
    message_id = message.id
    tag = f"@{message.from_user.username}"
    if await is_rclone_config(user_id, message):
        listener = TaskListener(message, tag, user_id)
        listener_dict[message_id] = [listener]
        if config_dict["MULTI_RCLONE_CONFIG"] or CustomFilters._owner_query(user_id):
            await list_remotes(
                message, remote_type="remote_origin", menu_type=Menus.COPY
            )
        else:
            await sendMessage("Not allowed to use", message)


async def copy_menu_callback(client, callback_query):
    query = callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id = query.from_user.id
    msg_id = message.reply_to_message.id
    listener = listener_dict[msg_id][0]

    origin_remote = get_rclone_data("COPY_ORIGIN_REMOTE", user_id)
    origin_dir = get_rclone_data("COPY_ORIGIN_DIR", user_id)
    destination_remote = get_rclone_data("COPY_DESTINATION_REMOTE", user_id)
    destination_dir = get_rclone_data("COPY_DESTINATION_DIR", user_id)

    if int(cmd[-1]) != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
        return

    # First Menu
    if cmd[1] == "remote_origin":
        update_rclone_data("COPY_ORIGIN_DIR", "", user_id)  # Reset Dir
        update_rclone_data("COPY_ORIGIN_REMOTE", cmd[2], user_id)
        await list_folder(message, cmd[2], "", menu_type=Menus.COPY, edit=True)
    elif cmd[1] == "origin_dir":
        path = get_rclone_data(cmd[2], user_id)
        origin_dir_ = origin_dir + path + "/"
        if await is_valid_path(origin_remote, origin_dir_, message):
            update_rclone_data("COPY_ORIGIN_DIR", origin_dir_, user_id)
            await list_folder(
                message, origin_remote, origin_dir_, menu_type=Menus.COPY, edit=True
            )

    # Second Menu
    elif cmd[1] == "second_menu":
        if cmd[3] == "True":
            path = get_rclone_data(cmd[2], user_id)
            origin_dir_ = origin_dir + path
            update_rclone_data("COPY_ORIGIN_DIR", origin_dir_, user_id)
        await list_remotes(
            message,
            menu_type=Menus.COPY,
            remote_type="remote_dest",
            is_second_menu=True,
            edit=True,
        )
    elif cmd[1] == "remote_dest":
        update_rclone_data("COPY_DESTINATION_DIR", "", user_id)  # Reset Dir
        update_rclone_data("COPY_DESTINATION_REMOTE", cmd[2], user_id)
        await list_folder(
            message, cmd[2], "", menu_type=Menus.COPY, edit=True, is_second_menu=True
        )
    elif cmd[1] == "dest_dir":
        path = get_rclone_data(cmd[2], user_id)
        _destination_dir = destination_dir + path + "/"
        if await is_valid_path(destination_remote, _destination_dir, message):
            update_rclone_data("COPY_DESTINATION_DIR", _destination_dir, user_id)
            await list_folder(
                message,
                destination_remote,
                _destination_dir,
                menu_type=Menus.COPY,
                edit=True,
                is_second_menu=True,
            )

    if cmd[1] == "copy":
        await query.answer()
        await deleteMessage(message)
        rclone_copy = RcloneCopy(user_id, listener)
        await rclone_copy.copy(
            origin_remote, origin_dir, destination_remote, destination_dir
        )
    elif cmd[1] == "pages":
        await query.answer()
    elif cmd[1] == "close":
        await message.delete()

    # Origin Menu Back Button
    if cmd[1] == "back_origin":
        if len(origin_dir) == 0:
            await list_remotes(
                message, menu_type=Menus.COPY, remote_type="remote_origin", edit=True
            )
            return
        origin_dir_list = origin_dir.split("/")[:-2]
        origin_dir_string = ""
        for dir in origin_dir_list:
            origin_dir_string += dir + "/"
        origin_dir = origin_dir_string
        update_rclone_data("COPY_ORIGIN_DIR", origin_dir, user_id)
        await list_folder(
            message, origin_remote, origin_dir, menu_type=Menus.COPY, edit=True
        )

    # Destination Menu Back Button
    if cmd[1] == "back_dest":
        if len(destination_dir) == 0:
            await list_remotes(
                message,
                menu_type=Menus.COPY,
                remote_type="remote_dest",
                is_second_menu=True,
                edit=True,
            )
            return
        destination_dir_list = destination_dir.split("/")[:-2]
        destination_dir_string = ""
        for dir in destination_dir_list:
            destination_dir_string += dir + "/"
        destination_dir = destination_dir_string
        update_rclone_data("COPY_DESTINATION_DIR", destination_dir, user_id)
        await list_folder(
            message,
            destination_remote,
            destination_dir,
            menu_type=Menus.COPY,
            edit=True,
            is_second_menu=True,
        )


async def next_page_copy(client, callback_query):
    query = callback_query
    data = query.data
    message = query.message
    await query.answer()
    user_id = message.reply_to_message.from_user.id
    _, next_offset, is_second_menu, data_back_cb = data.split()
    is_second_menu = is_second_menu.lower() == "true"

    info = get_rclone_data("info", user_id)
    total = len(info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10
    buttons = ButtonMaker()
    next_info, _next_offset = await run_sync(rcloneListNextPage, info, next_offset)

    if is_second_menu:
        dir_callback = "dest_dir"
        file_callback = "copy"
        buttons.cb_buildbutton("✅ Select this folder", f"copymenu^copy^{user_id}")
    else:
        dir_callback = "origin_dir"
        file_callback = "second_menu"
        buttons.cb_buildbutton(
            "✅ Select this folder", f"copymenu^second_menu^_^False^{user_id}"
        )

    await run_sync(
        rcloneListButtonMaker,
        info=next_info,
        button=buttons,
        menu_type=Menus.COPY,
        dir_callback=dir_callback,
        file_callback=file_callback,
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
        filter="next_copy",
        menu_type=Menus.COPY,
        is_second_menu=is_second_menu,
    )

    if is_second_menu:
        destination_remote = get_rclone_data("COPY_DESTINATION_REMOTE", user_id)
        destination_dir = get_rclone_data("COPY_DESTINATION_DIR", user_id)
        msg = f"Select folder where you want to copy\n\nPath:<code>{destination_remote}:{destination_dir}</code>"
        await editMessage(msg, message, reply_markup=buttons.build_menu(1))
    else:
        origin_remote = get_rclone_data("COPY_ORIGIN_REMOTE", user_id)
        origin_dir = get_rclone_data("COPY_ORIGIN_DIR", user_id)
        msg = f"Select file or folder which you want to copy\n\nPath:<code>{origin_remote}:{origin_dir}</code>"
        await editMessage(msg, message, reply_markup=buttons.build_menu(1))


copy_handler = MessageHandler(
    handle_copy,
    filters=command(BotCommands.CopyCommand)
    & (CustomFilters.user_filter | CustomFilters.chat_filter),
)
next_page_cb = CallbackQueryHandler(next_page_copy, filters=regex("next_copy"))
copy_menu_cb = CallbackQueryHandler(copy_menu_callback, filters=regex("copymenu"))

bot.add_handler(copy_handler)
bot.add_handler(next_page_cb)
bot.add_handler(copy_menu_cb)
