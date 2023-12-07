from asyncio import TimeoutError, create_subprocess_exec, create_subprocess_shell
from pyrogram.filters import regex, command
from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from bot import (
    DATABASE_URL,
    GLOBAL_EXTENSION_FILTER,
    LOGGER,
    TG_MAX_FILE_SIZE,
    bot,
    Interval,
    aria2,
    config_dict,
    aria2_options,
    aria2c_global,
    get_client,
    qbit_options,
    status_reply_dict_lock,
    status_dict,
    leech_log,
)
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import run_sync, setInterval
from bot.helper.ext_utils.db_handler import DbManager
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (
    editMarkup,
    sendFile,
    sendMarkup,
    sendMessage,
    update_all_messages,
)
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.rclone_data_holder import update_rclone_data
from bot.modules.rss import addJob
from bot.modules.search import initiate_search_tools


START = 0
STATE = "view"
default_values = {
    "AUTO_DELETE_MESSAGE_DURATION": 30,
    "DOWNLOAD_DIR": "/usr/src/app/downloads/",
    "UPSTREAM_BRANCH": "master",
    "STATUS_UPDATE_INTERVAL": 10,
    "LEECH_SPLIT_SIZE": TG_MAX_FILE_SIZE,
    "SEARCH_LIMIT": 0,
    "RSS_DELAY": 900,
}


async def handle_ownerset(client, message):
    text, buttons = get_env_menu()
    await sendMarkup(text, message, reply_markup=buttons.build_menu(2))


async def edit_menus(message, edit_type="env"):
    if edit_type == "env":
        text, buttons = get_env_menu()
        await editMarkup(text, message, reply_markup=buttons.build_menu(2))
    elif edit_type == "aria":
        text, buttons = get_aria_menu()
        await editMarkup(text, message, reply_markup=buttons.build_menu(2))
    elif edit_type == "qbit":
        text, buttons = get_qbit_menu()
        await editMarkup(text, message, reply_markup=buttons.build_menu(2))


def get_env_menu():
    msg = f"❇️<b>Config Variables Settings</b>"
    msg += f"\n\n<b>State: {STATE.upper()} </b>"
    buttons = ButtonMaker()
    for k in list(config_dict.keys())[START : 10 + START]:
        buttons.cb_buildbutton(k, f"ownersetmenu^env^editenv^{k}")
    if STATE == "view":
        buttons.cb_buildbutton("📝Edit", "ownersetmenu^edit^env")
    else:
        buttons.cb_buildbutton("🔍View", "ownersetmenu^view^env")
    buttons.cb_buildbutton("Aria2 Settings", "ownersetmenu^aria^aria_menu")
    buttons.cb_buildbutton("Qbit Setttings", "ownersetmenu^qbit^qbit_menu")
    pages = 0
    for x in range(0, len(config_dict) - 1, 10):
        pages = int(x / 10)
    buttons.cb_buildbutton(f"🗓 {int(START/10)}/{pages}", "ownersetmenu^page")
    buttons.cb_buildbutton("⏪ BACK", "ownersetmenu^back^env", "footer")
    buttons.cb_buildbutton("NEXT ⏩", f"ownersetmenu^next^env", "footer")
    buttons.cb_buildbutton("✘ Close Menu", "ownersetmenu^close", "footer_second")
    return msg, buttons


def get_qbit_menu():
    msg = "❇️<b>Qbit Settings</b>"
    msg += f"\n\n<b>State: {STATE.upper()} </b>"
    buttons = ButtonMaker()
    for k in list(qbit_options.keys())[START : 10 + START]:
        buttons.cb_buildbutton(k, f"ownersetmenu^qbit^editqbit^{k}")
    if STATE == "view":
        buttons.cb_buildbutton("📝Edit", "ownersetmenu^edit^qbit")
    else:
        buttons.cb_buildbutton("🔍View", "ownersetmenu^view^qbit")
    pages = 0
    for x in range(0, len(qbit_options) - 1, 10):
        pages = int(x / 10)
    buttons.cb_buildbutton(f"🗓 {int(START/10)}/{pages}", "ownersetmenu^page")
    buttons.cb_buildbutton("⏪ BACK", "ownersetmenu^back^qbit", "footer")
    buttons.cb_buildbutton("NEXT ⏩", f"ownersetmenu^next^qbit", "footer")
    buttons.cb_buildbutton("⬅️ Back", "ownersetmenu^back_menu", "footer_second")
    buttons.cb_buildbutton("✘ Close Menu", "ownersetmenu^close", "footer_third")
    return msg, buttons


def get_aria_menu():
    msg = "❇️<b>Aria2 Settings</b>"
    msg += f"\n\n<b>State: {STATE.upper()} </b>"
    buttons = ButtonMaker()
    for k in list(aria2_options.keys())[START : 10 + START]:
        buttons.cb_buildbutton(k, f"ownersetmenu^aria^editaria^{k}")
    if STATE == "view":
        buttons.cb_buildbutton("📝Edit", "ownersetmenu^edit^aria")
    else:
        buttons.cb_buildbutton("🔍View", "ownersetmenu^view^aria")
    buttons.cb_buildbutton("Add new key", "ownersetmenu^aria^editaria^newkey")
    pages = 0
    for x in range(0, len(aria2_options) - 1, 10):
        pages = int(x / 10)
    buttons.cb_buildbutton(f"🗓 {int(START/10)}/{pages}", "ownersetmenu^page")
    buttons.cb_buildbutton("⏪ BACK", "ownersetmenu^back^aria", "footer")
    buttons.cb_buildbutton("NEXT ⏩", "ownersetmenu^next^aria", "footer")
    buttons.cb_buildbutton("⬅️ Back", "ownersetmenu^back_menu", "footer_second")
    buttons.cb_buildbutton("✘ Close Menu", "ownersetmenu^close", "footer_third")
    return msg, buttons


async def update_buttons(message, key, edit_type=None):
    buttons = ButtonMaker()
    msg = f"Select option for {key}"
    if edit_type == "editenv":
        buttons.cb_buildbutton("Send", f"ownersetmenu^send^env^{key}")
        if key not in ["TELEGRAM_HASH", "TELEGRAM_API", "OWNER_ID", "BOT_TOKEN"]:
            buttons.cb_buildbutton("Default", f"ownersetmenu^env^resetenv^{key}")
        buttons.cb_buildbutton("Back", "ownersetmenu^back^env", "footer")
        buttons.cb_buildbutton("Close", "ownersetmenu^close", "footer")
    elif edit_type == "editaria":
        buttons.cb_buildbutton("Send", f"ownersetmenu^send^aria^{key}")
        if key != "newkey":
            buttons.cb_buildbutton("Empty String", f"ownersetmenu^aria^emptyaria^{key}")
            buttons.cb_buildbutton("Default", f"ownersetmenu^aria^resetaria^{key}")
        buttons.cb_buildbutton("Back", "ownersetmenu^back^aria", "footer")
        buttons.cb_buildbutton("Close", "ownersetmenu^close", "footer")
    elif edit_type == "editqbit":
        buttons.cb_buildbutton("Send", f"ownersetmenu^send^qbit^{key}")
        buttons.cb_buildbutton("Empty String", f"ownersetmenu^qbit^emptyqbit^{key}")
        buttons.cb_buildbutton("Back", "ownersetmenu^back^qbit", "footer")
        buttons.cb_buildbutton("Close", "ownersetmenu^close", "footer")
    await editMarkup(msg, message, reply_markup=buttons.build_menu(2))


async def ownerset_callback(client, callback_query):
    query = callback_query
    data = query.data
    data = data.split("^")
    message = query.message
    user_id = query.from_user.id

    if data[1] == "env":
        if data[2] == "editenv" and STATE == "edit":
            if data[3] in [
                "PARALLEL_TASKS",
                "SUDO_USERS",
                "RC_INDEX_USER",
                "RC_INDEX_PASS",
                "RC_INDEX_URL",
                "RC_INDEX_PORT",
                "ALLOWED_CHATS",
                "USER_SESSION_STRING",
                "AUTO_MIRROR",
                "RSS_DELAY",
                "CMD_INDEX",
                "TELEGRAM_API_HASH",
                "TELEGRAM_API_ID",
                "BOT_TOKEN",
                "OWNER_ID",
                "DOWNLOAD_DIR",
                "DATABASE_URL",
            ]:
                await query.answer(
                    text="Restart required for this to apply!", show_alert=True
                )
            else:
                await query.answer()
            await update_buttons(message, data[3], data[2])
        elif data[2] == "editenv" and STATE == "view":
            value = config_dict[data[3]]
            if len(str(value)) > 200:
                await query.answer()
                filename = f"{data[2]}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"{value}")
                await sendFile(message, filename)
                return
            if value == "":
                value = None
            await query.answer(text=f"{value}", show_alert=True)
        elif data[2] == "resetenv":
            value = ""
            if data[3] in default_values:
                value = default_values[data[3]]
                if data[3] == "STATUS_UPDATE_INTERVAL" and len(status_dict) != 0:
                    async with status_reply_dict_lock:
                        if Interval:
                            Interval[0].cancel()
                            Interval.clear()
                            Interval.append(setInterval(value, update_all_messages))
            elif data[3] == "DEFAULT_OWNER_REMOTE":
                update_rclone_data("MIRROR_SELECT_REMOTE", value, user_id)
                update_rclone_data("MIRROR_SELECT_BASE_DIR", value, user_id)
            elif data[3] == "EXTENSION_FILTER":
                GLOBAL_EXTENSION_FILTER.clear()
                GLOBAL_EXTENSION_FILTER.extend([".aria2", "!qB"])
            elif data[3] == "TORRENT_TIMEOUT":
                downloads = await run_sync(aria2.get_downloads)
                for download in downloads:
                    if not download.is_complete:
                        try:
                            await run_sync(
                                aria2.client.change_option,
                                download.gid,
                                {"bt-stop-timeout": "0"},
                            )
                        except Exception as e:
                            LOGGER.error(e)
                aria2_options["bt-stop-timeout"] = "0"
                if DATABASE_URL:
                    await DbManager().update_aria2("bt-stop-timeout", "0")
            elif data[3] == "QB_BASE_URL":
                await (
                    await create_subprocess_exec("pkill", "-9", "-f", "gunicorn")
                ).wait()
            elif data[3] == "QB_SERVER_PORT":
                if config_dict["BASE_URL"]:
                    await (
                        await create_subprocess_exec("pkill", "-9", "-f", "gunicorn")
                    ).wait()
                    await create_subprocess_shell(
                        f"gunicorn qbitweb.wserver:app --bind 0.0.0.0:80 --worker-class gevent"
                    )
            await query.answer("Reseted")
            config_dict[data[3]] = value
            if DATABASE_URL:
                await DbManager().update_config({data[3]: value})
            if data[3] in ["SEARCH_PLUGINS", "SEARCH_API_LINK"]:
                await initiate_search_tools()
            await edit_menus(message, "env")
    elif data[1] == "aria":
        if data[2] == "aria_menu":
            globals()["START"] = 0
            await edit_menus(message, "aria")
        elif data[2] == "editaria" and (STATE == "edit" or data[3] == "newkey"):
            await update_buttons(message, data[3], data[2])
        elif data[2] == "editaria" and STATE == "view":
            value = aria2_options[data[3]]
            if len(value) > 200:
                await query.answer()
                filename = f"{data[2]}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"{value}")
                await sendFile(message, filename)
                return
            elif value == "":
                value = None
            await query.answer(text=f"{value}", show_alert=True)
        elif data[2] == "resetaria":
            aria2_defaults = await run_sync(aria2.client.get_global_option)
            if aria2_defaults[data[3]] == aria2_options[data[3]]:
                await query.answer(
                    text="Value already same as you added in aria.sh!", show_alert=True
                )
                return
            await query.answer()
            value = aria2_defaults[data[3]]
            aria2_options[data[3]] = value
            await edit_menus(message, "aria")
            downloads = await run_sync(aria2.get_downloads)
            for download in downloads:
                if not download.is_complete:
                    try:
                        await run_sync(
                            aria2.client.change_option, download.gid, {data[2]: value}
                        )
                    except Exception as e:
                        LOGGER.error(e)
            if DATABASE_URL:
                await DbManager().update_aria2(data[3], value)
        elif data[2] == "emptyaria":
            await query.answer()
            aria2_options[data[3]] = ""
            await edit_menus(message, "aria")
            downloads = await run_sync(aria2.get_downloads)
            for download in downloads:
                if not download.is_complete:
                    try:
                        await run_sync(
                            aria2.client.change_option, download.gid, {data[2]: ""}
                        )
                    except Exception as e:
                        LOGGER.error(e)
            if DATABASE_URL:
                await DbManager().update_aria2(data[3], "")
    elif data[1] == "qbit":
        if data[2] == "qbit_menu":
            globals()["START"] = 0
            await edit_menus(message, "qbit")
        elif data[2] == "editqbit" and STATE == "edit":
            await update_buttons(message, data[3], data[2])
        elif data[2] == "editqbit" and STATE == "view":
            value = qbit_options[data[3]]
            if len(str(value)) > 200:
                await query.answer()
                filename = f"{data[2]}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"{value}")
                await sendFile(message, filename)
                return
            if value == "":
                value = None
            await query.answer(text=f"{value}", show_alert=True)
        elif data[2] == "emptyqbit":
            await query.answer()
            await run_sync(get_client().app_set_preferences, {data[3]: ""})
            qbit_options[data[3]] = ""
            await edit_menus(message, "qbit")
            if DATABASE_URL:
                await DbManager().update_qbittorrent(data[2], "")
    elif data[1] == "edit":
        await query.answer()
        globals()["STATE"] = "edit"
        await edit_menus(message, data[2])
    elif data[1] == "view":
        await query.answer()
        globals()["STATE"] = "view"
        await edit_menus(message, data[2])
    elif data[1] == "next":
        await query.answer()
        globals()["START"] += 10
        if START > len(config_dict):
            globals()["START"] = START - 10
        await edit_menus(message, data[2])
    elif data[1] == "back":
        await query.answer()
        globals()["START"] -= 10
        if START < 0:
            globals()["START"] += 10
        await edit_menus(message, data[2])
    elif data[1] == "send":
        if data[2] == "env":
            await start_env_listener(client, query, user_id, data[3])
        elif data[2] == "aria":
            await start_aria_listener(client, query, user_id, data[3])
        else:
            await start_qbit_listener(client, query, user_id, data[3])
    elif data[1] == "back_menu":
        await query.answer()
        globals()["START"] = 0
        key = data[2] if len(data) == 3 else "env"
        await edit_menus(message, key)
    elif data[1] == "page":
        await query.answer()
    elif data[1] == "close":
        globals()["START"] = 0
        globals()["STATE"] = "view"
        await query.answer()
        await message.delete()


async def start_env_listener(client, query, user_id, key):
    message = query.message
    question = await sendMessage(
        "Send valid value for selected variable, /ignore to cancel. Timeout: 60 sec",
        message,
    )
    try:
        response = await client.listen.Message(
            filters.text, id=filters.user(user_id), timeout=60
        )
    except TimeoutError:
        await client.send_message(message.chat.id, text="Too late 60s gone, try again!")
        return
    else:
        if response:
            try:
                if "/ignore" in response.text:
                    await client.listen.Cancel(filters.user(user_id))
                else:
                    value = response.text.strip()
                    if value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    elif key == "STATUS_LIMIT":
                        value = int(value)
                        async with status_reply_dict_lock:
                            try:
                                if Interval:
                                    Interval[0].cancel()
                                    Interval.clear()
                            except:
                                pass
                            finally:
                                Interval.append(setInterval(value, update_all_messages))
                    elif key == "STATUS_UPDATE_INTERVAL":
                        value = int(value)
                        if len(status_dict) != 0:
                            async with status_reply_dict_lock:
                                if Interval:
                                    Interval[0].cancel()
                                    Interval.clear()
                                    Interval.append(
                                        setInterval(value, update_all_messages)
                                    )
                    elif key == "TORRENT_TIMEOUT":
                        value = int(value)
                        downloads = await run_sync(aria2.get_downloads)
                        for download in downloads:
                            if not download.is_complete:
                                try:
                                    await run_sync(
                                        aria2.client.change_option,
                                        download.gid,
                                        {"bt-stop-timeout": f"{value}"},
                                    )
                                except Exception as e:
                                    LOGGER.error(e)
                        aria2_options["bt-stop-timeout"] = f"{value}"
                    elif key == "DEFAULT_OWNER_REMOTE":
                        update_rclone_data("MIRROR_SELECT_REMOTE", value, user_id)
                    elif key == "RSS_DELAY":
                        value = int(value)
                        addJob(value)
                    elif key == "RSS_CHAT_ID":
                        value = int(value)
                    elif key == "DOWNLOAD_DIR":
                        if not value.endswith("/"):
                            value = f"{value}/"
                    elif key == "LEECH_SPLIT_SIZE":
                        value = min(int(value), TG_MAX_FILE_SIZE)
                    elif key == "LEECH_LOG":
                        leech_log.clear()
                        aid = value.split()
                        for id_ in aid:
                            leech_log.append(int(id_.strip()))
                    elif key == "QB_SERVER_PORT":
                        value = int(value)
                        if config_dict["BASE_URL"]:
                            await (
                                await create_subprocess_exec(
                                    "pkill", "-9", "-f", "gunicorn"
                                )
                            ).wait()
                            await create_subprocess_shell(
                                f"gunicorn qbitweb.wserver:app --bind 0.0.0.0:{value} --worker-class gevent"
                            )
                    elif key == "EXTENSION_FILTER":
                        fx = value.split()
                        GLOBAL_EXTENSION_FILTER.clear()
                        GLOBAL_EXTENSION_FILTER.extend([".aria2", "!qB"])
                        for x in fx:
                            if x.strip().startswith("."):
                                x = x.lstrip(".")
                            GLOBAL_EXTENSION_FILTER.append(x.strip().lower())
                    config_dict[key] = value
                    await edit_menus(message, "env")
                    if DATABASE_URL:
                        await DbManager().update_config({key: value})
                    if key in ["SEARCH_PLUGINS", "SEARCH_API_LINK"]:
                        await initiate_search_tools()
            except KeyError:
                await query.answer("Value doesn't exist")
    finally:
        await question.delete()


async def start_aria_listener(client, query, user_id, key):
    message = query.message
    if key == "newkey":
        question = await sendMessage(
            "Send a key with value. Example: https-proxy-user:value', /ignore to cancel. Timeout: 60 sec",
            message,
        )
    else:
        question = await sendMessage(
            "Send valid value for selected variable, /ignore to cancel. Timeout: 60 sec",
            message,
        )
    try:
        response = await client.listen.Message(
            filters.text, id=filters.user(user_id), timeout=60
        )
    except TimeoutError:
        await client.send_message(message.chat.id, text="Too late 60s gone, try again!")
        return
    else:
        if response:
            try:
                if "/ignore" in response.text:
                    await client.listen.Cancel(filters.user(user_id))
                    return
                else:
                    value = response.text.strip()
                    if key == "newkey":
                        key, value = [x.strip() for x in value.split(":", 1)]
                    elif value.lower() == "true":
                        value = "true"
                    elif value.lower() == "false":
                        value = "false"
                    if key in aria2c_global:
                        await run_sync(aria2.set_global_options, {key: value})
                    else:
                        downloads = await run_sync(aria2.get_downloads)
                        for download in downloads:
                            if not download.is_complete:
                                try:
                                    await run_sync(
                                        aria2.client.change_option,
                                        download.gid,
                                        {key: value},
                                    )
                                except Exception as e:
                                    LOGGER.error(e)
                    aria2_options[key] = value
                    await edit_menus(message, "aria")
                    if DATABASE_URL:
                        await DbManager().update_aria2(key, value)
            except KeyError:
                await query.answer("Value doesn't exist")
    finally:
        await question.delete()


async def start_qbit_listener(client, query, user_id, key):
    message = query.message
    question = await sendMessage(
        "Send valid value for selected variable, /ignore to cancel. Timeout: 60 sec",
        message,
    )
    try:
        response = await client.listen.Message(
            filters.text, id=filters.user(user_id), timeout=60
        )
    except TimeoutError:
        await client.send_message(message.chat.id, text="Too late 60s gone, try again!")
        return
    else:
        if response:
            try:
                if "/ignore" in response.text:
                    await client.listen.Cancel(filters.user(user_id))
                    return
                else:
                    value = response.text.strip()
                    if value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    elif key == "max_ratio":
                        value = float(value)
                    elif value.isdigit():
                        value = int(value)
                    await run_sync(get_client().app_set_preferences, {key: value})
                    qbit_options[key] = value
                    await edit_menus(message, "qbit")
                    if DATABASE_URL:
                        await DbManager().update_qbittorrent(key, value)
            except KeyError:
                await query.answer("Value doesn't exist")
    finally:
        await question.delete()


owner_settings_handler = MessageHandler(
    handle_ownerset,
    filters=command(BotCommands.OwnerSetCommand) & (CustomFilters.owner_filter),
)
owner_settings_cb = CallbackQueryHandler(
    ownerset_callback, filters=regex(r"ownersetmenu")
)


bot.add_handler(owner_settings_handler)
bot.add_handler(owner_settings_cb)
