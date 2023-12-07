from bot import OWNER_ID, bot, config_dict, remotes_multi
from bot.helper.ext_utils.bot_utils import run_sync
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram.filters import regex
from pyrogram import filters
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


async def handle_mirrorselect(_, message):
    user_id = message.from_user.id
    if await is_rclone_config(user_id, message):
        if DEFAULT_OWNER_REMOTE := config_dict["DEFAULT_OWNER_REMOTE"]:
            if user_id == OWNER_ID:
                update_rclone_data(
                    "MIRROR_SELECT_REMOTE", DEFAULT_OWNER_REMOTE, user_id
                )
        if config_dict["MULTI_RCLONE_CONFIG"] or CustomFilters._owner_query(user_id):
            await list_remotes(message, menu_type=Menus.MIRROR_SELECT)
        else:
            await sendMessage("Not allowed to use", message)


async def mirrorselect_callback(_, query):
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id = query.from_user.id
    base_dir = get_rclone_data("MIRROR_SELECT_BASE_DIR", user_id)
    rclone_remote = get_rclone_data("MIRROR_SELECT_REMOTE", user_id)

    if int(cmd[-1]) != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
        return
    if cmd[1] == "remote":
        is_crypt = False if cmd[-2] == "False" else True
        if CustomFilters._owner_query(user_id):
            if config_dict["MULTI_REMOTE_UP"]:
                remotes_multi.append(cmd[2])
                await list_remotes(message, menu_type=Menus.MIRROR_SELECT, edit=True)
                return
            config_dict.update({"DEFAULT_OWNER_REMOTE": cmd[2]})
        update_rclone_data("MIRROR_SELECT_BASE_DIR", "", user_id)
        update_rclone_data("MIRROR_SELECT_REMOTE", cmd[2], user_id)
        await list_folder(
            message,
            cmd[2],
            "",
            menu_type=Menus.MIRROR_SELECT,
            is_crypt=is_crypt,
            edit=True,
        )
    elif cmd[1] == "remote_dir":
        path = get_rclone_data(cmd[2], user_id)
        base_dir += path + "/"
        if await is_valid_path(rclone_remote, base_dir, message):
            update_rclone_data("MIRROR_SELECT_BASE_DIR", base_dir, user_id)
            await list_folder(
                message,
                rclone_remote,
                base_dir,
                menu_type=Menus.MIRROR_SELECT,
                edit=True,
            )
    elif cmd[1] == "back":
        if len(base_dir) == 0:
            await list_remotes(message, menu_type=Menus.MIRROR_SELECT, edit=True)
            return
        base_dir_split = base_dir.split("/")[:-2]
        base_dir_string = ""
        for dir in base_dir_split:
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        update_rclone_data("MIRROR_SELECT_BASE_DIR", base_dir, user_id)
        await list_folder(
            message, rclone_remote, base_dir, menu_type=Menus.MIRROR_SELECT, edit=True
        )
        await query.answer()
    elif cmd[1] == "pages":
        await query.answer()
    elif cmd[1] == "reset":
        remotes_multi.clear()
        await list_remotes(message, menu_type=Menus.MIRROR_SELECT, edit=True)
    else:
        await query.answer()
        await message.delete()


async def next_page_mirrorselect(_, callback_query):
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
    buttons.cb_buildbutton(
        "✅ Select this folder", f"{Menus.MIRROR_SELECT}^close^{user_id}"
    )

    next_info, _next_offset = await run_sync(rcloneListNextPage, info, next_offset)

    await run_sync(
        rcloneListButtonMaker,
        info=next_info,
        button=buttons,
        menu_type=Menus.MIRROR_SELECT,
        dir_callback="remote_dir",
        file_callback="",
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
        filter="next_ms",
        menu_type=Menus.MIRROR_SELECT,
    )

    mirrorsel_remote = get_rclone_data("MIRROR_SELECT_REMOTE", user_id)
    base_dir = get_rclone_data("MIRROR_SELECT_BASE_DIR", user_id)
    msg = f"Select folder where you want to store files\n\n<b>Path:</b><code>{mirrorsel_remote}:{base_dir}</code>"
    await editMessage(msg, message, reply_markup=buttons.build_menu(1))


bot.add_handler(
    MessageHandler(
        handle_mirrorselect,
        filters=filters.command(BotCommands.MirrorSelectCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
bot.add_handler(CallbackQueryHandler(next_page_mirrorselect, filters=regex("next_ms")))
bot.add_handler(
    CallbackQueryHandler(mirrorselect_callback, filters=regex("mirrorselectmenu"))
)
