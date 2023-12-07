from asyncio import TimeoutError, create_subprocess_exec, create_subprocess_shell
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from pyrogram.filters import regex, command
from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from os import environ, getcwd, path as ospath, remove as osremove
from dotenv import load_dotenv
from subprocess import run as srun
from bot import (
    DATABASE_URL,
    GLOBAL_EXTENSION_FILTER,
    IS_PREMIUM_USER,
    LOGGER,
    OWNER_ID,
    Interval,
    aria2,
    aria2_options,
    bot,
    config_dict,
    status_dict,
    status_reply_dict_lock,
    user_data,
    leech_log,
)
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import run_sync, setInterval
from bot.helper.ext_utils.db_handler import DbManager
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (
    editMarkup,
    sendMarkup,
    sendMessage,
    update_all_messages,
)
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.rclone_utils import get_rclone_path
from bot.modules.search import initiate_search_tools


async def load_config():
    BOT_TOKEN = environ.get("BOT_TOKEN", "")
    if len(BOT_TOKEN) == 0:
        BOT_TOKEN = config_dict["BOT_TOKEN"]

    TELEGRAM_API_ID = environ.get("TELEGRAM_API", "")
    if len(TELEGRAM_API_ID) == 0:
        TELEGRAM_API_ID = config_dict["TELEGRAM_API_ID"]
    else:
        TELEGRAM_API_ID = int(TELEGRAM_API_ID)

    TELEGRAM_API_HASH = environ.get("TELEGRAM_API_HASH", "")
    if len(TELEGRAM_API_HASH) == 0:
        TELEGRAM_API_HASH = config_dict["TELEGRAM_API_HASH"]

    OWNER_ID = environ.get("OWNER_ID", "")
    if len(OWNER_ID) == 0:
        OWNER_ID = config_dict["OWNER_ID"]
    else:
        OWNER_ID = int(OWNER_ID)

    DATABASE_URL = environ.get("DATABASE_URL", "")
    if len(DATABASE_URL) == 0:
        DATABASE_URL = ""

    DOWNLOAD_DIR = environ.get("DOWNLOAD_DIR", "")
    if len(DOWNLOAD_DIR) == 0:
        DOWNLOAD_DIR = "/usr/src/app/downloads/"
    elif not DOWNLOAD_DIR.endswith("/"):
        DOWNLOAD_DIR = f"{DOWNLOAD_DIR}/"

    GDRIVE_FOLDER_ID = environ.get("GDRIVE_FOLDER_ID", "")
    if len(GDRIVE_FOLDER_ID) == 0:
        GDRIVE_FOLDER_ID = ""

    ALLOWED_CHATS = environ.get("ALLOWED_CHATS", "")
    if len(ALLOWED_CHATS) != 0:
        aid = ALLOWED_CHATS.split()
        for id_ in aid:
            user_data[int(id_.strip())] = {"is_auth": True}

    SUDO_USERS = environ.get("SUDO_USERS", "")
    if len(SUDO_USERS) != 0:
        aid = SUDO_USERS.split()
        for id_ in aid:
            user_data[int(id_.strip())] = {"is_sudo": True}

    LEECH_LOG = environ.get("LEECH_LOG", "")
    if len(LEECH_LOG) != 0:
        leech_log.clear()
        aid = LEECH_LOG.split()
        for id_ in aid:
            leech_log.append(int(id_.strip()))

    NO_TASKS_LOGS = environ.get("NO_TASKS_LOGS", "")
    NO_TASKS_LOGS = NO_TASKS_LOGS.lower() == "true"

    BOT_PM = environ.get("BOT_PM", "")
    BOT_PM = BOT_PM.lower() == "true"

    EXTENSION_FILTER = environ.get("EXTENSION_FILTER", "")
    if len(EXTENSION_FILTER) > 0:
        fx = EXTENSION_FILTER.split()
        GLOBAL_EXTENSION_FILTER.clear()
        GLOBAL_EXTENSION_FILTER.extend([".aria2", "!qB"])
        for x in fx:
            if x.strip().startswith("."):
                x = x.lstrip(".")
            GLOBAL_EXTENSION_FILTER.append(x.strip().lower())

    MEGA_EMAIL = environ.get("MEGA_EMAIL", "")
    MEGA_PASSWORD = environ.get("MEGA_PASSWORD", "")
    if len(MEGA_EMAIL) == 0 or len(MEGA_PASSWORD) == 0:
        MEGA_EMAIL = ""
        MEGA_PASSWORD = ""

    UPTOBOX_TOKEN = environ.get("UPTOBOX_TOKEN", "")
    if len(UPTOBOX_TOKEN) == 0:
        UPTOBOX_TOKEN = ""

    TMDB_API_KEY = environ.get("TMDB_API_KEY", "")
    if len(TMDB_API_KEY) == 0:
        TMDB_API_KEY = ""

    TMDB_LANGUAGE = environ.get("TMDB_LANGUAGE", "")
    if len(TMDB_LANGUAGE) == 0:
        TMDB_LANGUAGE = "en"

    SEARCH_API_LINK = environ.get("SEARCH_API_LINK", "").rstrip("/")
    if len(SEARCH_API_LINK) == 0:
        SEARCH_API_LINK = ""

    SEARCH_PLUGINS = environ.get("SEARCH_PLUGINS", "")
    if len(SEARCH_PLUGINS) == 0:
        SEARCH_PLUGINS = ""

    TG_MAX_FILE_SIZE = 4194304000 if IS_PREMIUM_USER else 2097152000

    LEECH_SPLIT_SIZE = environ.get("LEECH_SPLIT_SIZE", "")
    if len(LEECH_SPLIT_SIZE) == 0 or int(LEECH_SPLIT_SIZE) > TG_MAX_FILE_SIZE:
        LEECH_SPLIT_SIZE = TG_MAX_FILE_SIZE
    else:
        LEECH_SPLIT_SIZE = int(LEECH_SPLIT_SIZE)

    STATUS_UPDATE_INTERVAL = environ.get("STATUS_UPDATE_INTERVAL", "")
    if len(STATUS_UPDATE_INTERVAL) == 0:
        STATUS_UPDATE_INTERVAL = 10
    else:
        STATUS_UPDATE_INTERVAL = int(STATUS_UPDATE_INTERVAL)
    if len(status_dict) != 0:
        async with status_reply_dict_lock:
            if Interval:
                Interval[0].cancel()
                Interval.clear()
                Interval.append(
                    setInterval(STATUS_UPDATE_INTERVAL, update_all_messages)
                )

    AUTO_DELETE_MESSAGE_DURATION = environ.get("AUTO_DELETE_MESSAGE_DURATION", "")
    if len(AUTO_DELETE_MESSAGE_DURATION) == 0:
        AUTO_DELETE_MESSAGE_DURATION = 30
    else:
        AUTO_DELETE_MESSAGE_DURATION = int(AUTO_DELETE_MESSAGE_DURATION)

    SEARCH_LIMIT = environ.get("SEARCH_LIMIT", "")
    SEARCH_LIMIT = 0 if len(SEARCH_LIMIT) == 0 else int(SEARCH_LIMIT)

    STATUS_LIMIT = environ.get("STATUS_LIMIT", "")
    STATUS_LIMIT = "" if len(STATUS_LIMIT) == 0 else int(STATUS_LIMIT)

    PARALLEL_TASKS = environ.get("PARALLEL_TASKS", "")
    PARALLEL_TASKS = "" if len(PARALLEL_TASKS) == 0 else int(PARALLEL_TASKS)

    YT_DLP_OPTIONS = environ.get("YT_DLP_OPTIONS", "")
    if len(YT_DLP_OPTIONS) == 0:
        YT_DLP_OPTIONS = ""

    RSS_CHAT_ID = environ.get("RSS_CHAT_ID", "")
    RSS_CHAT_ID = "" if len(RSS_CHAT_ID) == 0 else int(RSS_CHAT_ID)

    RSS_DELAY = environ.get("RSS_DELAY", "")
    RSS_DELAY = 900 if len(RSS_DELAY) == 0 else int(RSS_DELAY)

    USER_SESSION_STRING = environ.get("USER_SESSION_STRING", "")

    TORRENT_TIMEOUT = environ.get("TORRENT_TIMEOUT", "")
    downloads = await run_sync(aria2.get_downloads)
    if len(TORRENT_TIMEOUT) == 0:
        for download in downloads:
            if not download.is_complete:
                try:
                    await run_sync(
                        aria2.client.change_option(
                            download.gid, {"bt-stop-timeout": "0"}
                        )
                    )
                except Exception as e:
                    LOGGER.error(e)
        aria2_options["bt-stop-timeout"] = "0"
        if DATABASE_URL:
            await DbManager().update_aria2("bt-stop-timeout", "0")
        TORRENT_TIMEOUT = ""
    else:
        for download in downloads:
            if not download.is_complete:
                try:
                    await run_sync(
                        aria2.client.change_option(
                            download.gid, {"bt-stop-timeout": TORRENT_TIMEOUT}
                        )
                    )
                except Exception as e:
                    LOGGER.error(e)
        aria2_options["bt-stop-timeout"] = TORRENT_TIMEOUT
        if DATABASE_URL:
            await DbManager().update_aria2("bt-stop-timeout", TORRENT_TIMEOUT)
        TORRENT_TIMEOUT = int(TORRENT_TIMEOUT)

    IS_TEAM_DRIVE = environ.get("IS_TEAM_DRIVE", "")
    IS_TEAM_DRIVE = IS_TEAM_DRIVE.lower() == "true"

    USE_SERVICE_ACCOUNTS = environ.get("USE_SERVICE_ACCOUNTS", "")
    USE_SERVICE_ACCOUNTS = USE_SERVICE_ACCOUNTS.lower() == "true"

    WEB_PINCODE = environ.get("WEB_PINCODE", "")
    WEB_PINCODE = WEB_PINCODE.lower() == "true"

    AS_DOCUMENT = environ.get("AS_DOCUMENT", "")
    AS_DOCUMENT = AS_DOCUMENT.lower() == "true"

    EQUAL_SPLITS = environ.get("EQUAL_SPLITS", "")
    EQUAL_SPLITS = EQUAL_SPLITS.lower() == "true"

    QB_SERVER_PORT = environ.get("QB_SERVER_PORT", "")
    if len(QB_SERVER_PORT) == 0:
        QB_SERVER_PORT = 80

    QB_BASE_URL = environ.get("QB_BASE_URL", "").rstrip("/")
    if len(QB_BASE_URL) == 0:
        QB_BASE_URL = ""
        await (await create_subprocess_exec("pkill", "-9", "-f", "gunicorn")).wait()
    else:
        await (await create_subprocess_exec("pkill", "-9", "-f", "gunicorn")).wait()
        await create_subprocess_shell(
            f"gunicorn qbitweb.wserver:app --bind 0.0.0.0:{QB_SERVER_PORT} --worker-class gevent"
        )

    UPSTREAM_REPO = environ.get("UPSTREAM_REPO", "")
    if len(UPSTREAM_REPO) == 0:
        UPSTREAM_REPO = ""

    UPSTREAM_BRANCH = environ.get("UPSTREAM_BRANCH", "")
    if len(UPSTREAM_BRANCH) == 0:
        UPSTREAM_BRANCH = "master"

    AUTO_MIRROR = environ.get("AUTO_MIRROR", "")
    AUTO_MIRROR = AUTO_MIRROR.lower() == "true"

    MULTI_REMOTE_UP = environ.get("MULTI_REMOTE_UP", "")
    MULTI_REMOTE_UP = MULTI_REMOTE_UP.lower() == "true"

    DEFAULT_OWNER_REMOTE = environ.get("DEFAULT_OWNER_REMOTE", "")

    REMOTE_SELECTION = environ.get("REMOTE_SELECTION", "")
    REMOTE_SELECTION = REMOTE_SELECTION.lower() == "true"

    MULTI_RCLONE_CONFIG = environ.get("MULTI_RCLONE_CONFIG", "")
    MULTI_RCLONE_CONFIG = MULTI_RCLONE_CONFIG.lower() == "true"

    SERVER_SIDE = environ.get("SERVER_SIDE", "")
    SERVER_SIDE = SERVER_SIDE.lower() == "true"

    SERVICE_ACCOUNTS_REMOTE = environ.get("SERVICE_ACCOUNTS_REMOTE", "")

    GD_INDEX_URL = environ.get("GD_INDEX_URL", "").rstrip("/")
    if len(GD_INDEX_URL) == 0:
        GD_INDEX_URL = ""

    VIEW_LINK = environ.get("VIEW_LINK", "")
    VIEW_LINK = VIEW_LINK.lower() == "true"

    LOCAL_MIRROR = environ.get("LOCAL_MIRROR", "")
    LOCAL_MIRROR = LOCAL_MIRROR.lower() == "true"

    RCLONE_COPY_FLAGS = environ.get("RCLONE_COPY_FLAGS", "")
    if len(RCLONE_COPY_FLAGS) == 0:
        RCLONE_COPY_FLAGS = ""

    RCLONE_UPLOAD_FLAGS = environ.get("RCLONE_UPLOAD_FLAGS", "")
    if len(RCLONE_UPLOAD_FLAGS) == 0:
        RCLONE_UPLOAD_FLAGS = ""

    RCLONE_DOWNLOAD_FLAGS = environ.get("RCLONE_DOWNLOAD_FLAGS", "")
    if len(RCLONE_DOWNLOAD_FLAGS) == 0:
        RCLONE_DOWNLOAD_FLAGS = ""

    RC_INDEX_USER = environ.get("RC_INDEX_USER", "")
    RC_INDEX_USER = "admin" if len(RC_INDEX_USER) == 0 else RC_INDEX_USER

    RC_INDEX_PASS = environ.get("RC_INDEX_PASS", "")
    RC_INDEX_PASS = "admin" if len(RC_INDEX_PASS) == 0 else RC_INDEX_PASS

    RC_INDEX_URL = environ.get("RC_INDEX_URL", "")
    RC_INDEX_URL = "" if len(RC_INDEX_URL) == 0 else RC_INDEX_URL

    RC_INDEX_PORT = environ.get("RC_INDEX_PORT", "")
    RC_INDEX_PORT = 8080 if len(RC_INDEX_PORT) == 0 else int(RC_INDEX_PORT)

    CMD_INDEX = environ.get("CMD_INDEX", "")

    config_dict.update(
        {
            "AS_DOCUMENT": AS_DOCUMENT,
            "ALLOWED_CHATS": ALLOWED_CHATS,
            "AUTO_DELETE_MESSAGE_DURATION": AUTO_DELETE_MESSAGE_DURATION,
            "AUTO_MIRROR": AUTO_MIRROR,
            "NO_TASKS_LOGS": NO_TASKS_LOGS,
            "BOT_PM": BOT_PM,
            "BOT_TOKEN": BOT_TOKEN,
            "CMD_INDEX": CMD_INDEX,
            "DOWNLOAD_DIR": DOWNLOAD_DIR,
            "DATABASE_URL": DATABASE_URL,
            "DEFAULT_OWNER_REMOTE": DEFAULT_OWNER_REMOTE,
            "EQUAL_SPLITS": EQUAL_SPLITS,
            "EXTENSION_FILTER": EXTENSION_FILTER,
            "GDRIVE_FOLDER_ID": GDRIVE_FOLDER_ID,
            "IS_TEAM_DRIVE": IS_TEAM_DRIVE,
            "GD_INDEX_URL": GD_INDEX_URL,
            "LOCAL_MIRROR": LOCAL_MIRROR,
            "LEECH_LOG": LEECH_LOG,
            "LEECH_SPLIT_SIZE": LEECH_SPLIT_SIZE,
            "MEGA_EMAIL": MEGA_EMAIL,
            "MEGA_PASSWORD": MEGA_PASSWORD,
            "MULTI_REMOTE_UP": MULTI_REMOTE_UP,
            "MULTI_RCLONE_CONFIG": MULTI_RCLONE_CONFIG,
            "OWNER_ID": OWNER_ID,
            "RCLONE_COPY_FLAGS": RCLONE_COPY_FLAGS,
            "RCLONE_UPLOAD_FLAGS": RCLONE_UPLOAD_FLAGS,
            "RCLONE_DOWNLOAD_FLAGS": RCLONE_DOWNLOAD_FLAGS,
            "REMOTE_SELECTION": REMOTE_SELECTION,
            "PARALLEL_TASKS": PARALLEL_TASKS,
            "QB_BASE_URL": QB_BASE_URL,
            "QB_SERVER_PORT": QB_SERVER_PORT,
            "RSS_CHAT_ID": RSS_CHAT_ID,
            "RSS_DELAY": RSS_DELAY,
            "SEARCH_PLUGINS": SEARCH_PLUGINS,
            "SEARCH_API_LINK": SEARCH_API_LINK,
            "SEARCH_LIMIT": SEARCH_LIMIT,
            "SERVICE_ACCOUNTS_REMOTE": SERVICE_ACCOUNTS_REMOTE,
            "SERVER_SIDE": SERVER_SIDE,
            "RC_INDEX_URL": RC_INDEX_URL,
            "RC_INDEX_PORT": RC_INDEX_PORT,
            "RC_INDEX_USER": RC_INDEX_USER,
            "RC_INDEX_PASS": RC_INDEX_PASS,
            "STATUS_LIMIT": STATUS_LIMIT,
            "STATUS_UPDATE_INTERVAL": STATUS_UPDATE_INTERVAL,
            "SUDO_USERS": SUDO_USERS,
            "TELEGRAM_API_ID": TELEGRAM_API_ID,
            "TELEGRAM_API_HASH": TELEGRAM_API_HASH,
            "TMDB_API_KEY": TMDB_API_KEY,
            "TMDB_LANGUAGE": TMDB_LANGUAGE,
            "TORRENT_TIMEOUT": TORRENT_TIMEOUT,
            "UPSTREAM_REPO": UPSTREAM_REPO,
            "UPSTREAM_BRANCH": UPSTREAM_BRANCH,
            "UPTOBOX_TOKEN": UPTOBOX_TOKEN,
            "USER_SESSION_STRING": USER_SESSION_STRING,
            "USE_SERVICE_ACCOUNTS": USE_SERVICE_ACCOUNTS,
            "VIEW_LINK": VIEW_LINK,
            "YT_DLP_OPTIONS": YT_DLP_OPTIONS,
            "WEB_PINCODE": WEB_PINCODE,
        }
    )

    if DATABASE_URL:
        await DbManager().update_config(config_dict)
    await initiate_search_tools()


async def config_menu(user_id, message, edit=False):
    path = f"{getcwd()}/rclone/"
    path = ospath.join(path, f"{user_id}", "rclone.conf")
    buttons = ButtonMaker()
    fstr = ""
    msg = "❇️ **Rclone configuration**"
    if ospath.exists(path):
        cmd = ["rclone", "listremotes", f"--config={path}"]
        process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = await process.communicate()
        return_code = await process.wait()
        if return_code != 0:
            err = stderr.decode().strip()
            await sendMessage(f"Error: {err}", message)
            return
        stdout = stdout.decode().strip()
        info = stdout.split("\n")
        for i in info:
            rstr = i.replace(":", "")
            fstr += f"- {rstr}\n"
        msg += "\n\n**Here is list of drives in config file:**"
        msg += f"\n{fstr}"
        buttons.cb_buildbutton("🗂 rclone.conf", f"configmenu^get_rclone_conf^{user_id}")
        buttons.cb_buildbutton("🗑 rclone.conf", f"configmenu^delete_config^{user_id}")
    else:
        buttons.cb_buildbutton(
            "📃rclone.conf", f"configmenu^change_rclone_conf^{user_id}" ,"footer"
        )
    if CustomFilters._owner_query(user_id):
        path = f"{getcwd()}/rclone/"
        global_rc = ospath.join(path, "rclone_global", "rclone.conf")
        if ospath.exists(global_rc):
            buttons.cb_buildbutton(
                "🗂 rclone.conf (🌐)", f"configmenu^get_grclone_conf^{user_id}"
            )
            buttons.cb_buildbutton(
                "🗑 rclone.conf (🌐)", f"configmenu^delete_grclone_conf^{user_id}"
            )
        else:
            buttons.cb_buildbutton(
                "📃 rclone.conf (🌐)",
                f"configmenu^change_grclone_conf^{user_id}",
                "footer",
            )
        if ospath.exists("token.pickle"):
            buttons.cb_buildbutton("🗂 token.pickle", f"configmenu^get_pickle^{user_id}")
            buttons.cb_buildbutton(
                "🗑 token.pickle", f"configmenu^delete_pickle^{user_id}"
            )
        else:
            buttons.cb_buildbutton(
                "📃 token.pickle", f"configmenu^change_pickle^{user_id}" ,"footer_second"
            )
        if ospath.exists("accounts"):
            buttons.cb_buildbutton(
                "🗑 accounts folder", f"configmenu^delete_acc^{user_id}"
            )
        else:
            buttons.cb_buildbutton(
                "📃 accounts.zip", f"configmenu^change_acc^{user_id}" ,"footer_second"
            )
        if ospath.exists("config.env"):
            buttons.cb_buildbutton(
                "🗂 config.env", f"configmenu^get_config_env^{user_id}"
            )
            buttons.cb_buildbutton(
                "🗑 config.env", f"configmenu^delete_config_env^{user_id}"
            )
        else:
            buttons.cb_buildbutton(
                "📃config.env", f"configmenu^change_config_env^{user_id}", "footer"
            )
    buttons.cb_buildbutton(
        "✘ Close Menu", f"configmenu^close^{user_id}", "footer_third"
    )
    if edit:
        await editMarkup(msg, message, reply_markup=buttons.build_menu(2))
    else:
        await sendMarkup(msg, message, reply_markup=buttons.build_menu(2))


async def handle_botfiles(client, message):
    user_id = message.from_user.id
    if config_dict["MULTI_RCLONE_CONFIG"]:
        await config_menu(user_id, message)
    else:
        if CustomFilters._owner_query(user_id):
            await config_menu(user_id, message)
        else:
            await sendMessage("Not allowed to use", message)


async def botfiles_callback(client, callback_query):
    query = callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id = query.from_user.id

    if int(cmd[-1]) != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
        return
    if cmd[1] == "get_rclone_conf":
        path = await get_rclone_path(user_id, message)
        await client.send_document(document=path, chat_id=message.chat.id)
        await query.answer()
    elif cmd[1] == "get_grclone_conf":
        path = ospath.join("rclone/rclone_global", "rclone.conf")
        try:
            await client.send_document(document=path, chat_id=message.chat.id)
        except ValueError as err:
            await sendMessage(str(err), message)
        await query.answer()
    elif cmd[1] == "get_pickle":
        try:
            await client.send_document(document="token.pickle", chat_id=message.chat.id)
        except ValueError as err:
            await sendMessage(str(err), message)
        await query.answer()
    elif cmd[1] == "get_config_env":
        try:
            await client.send_document(document="config.env", chat_id=message.chat.id)
        except ValueError as err:
            await sendMessage(str(err), message)
        await query.answer()
    elif cmd[1] == "change_rclone_conf":
        await set_config_listener(client, query, message)
        await config_menu(user_id, message, True)
    elif cmd[1] == "change_grclone_conf" and user_id == OWNER_ID:
        await set_config_listener(client, query, message, True)
        await config_menu(user_id, message, True)
    elif (
        cmd[1] == "change_pickle"
        or cmd[1] == "change_acc"
        or cmd[1] == "change_config_env"
        and user_id == OWNER_ID
    ):
        await set_config_listener(client, query, message)
        await config_menu(user_id, message, True)
    elif cmd[1] == "delete_config":
        path = await get_rclone_path(user_id, message)
        osremove(path)
        await query.answer()
        await config_menu(user_id, message, True)
    elif cmd[1] == "delete_grclone_conf":
        path = ospath.join("rclone/rclone_global", "rclone.conf")
        try:
            osremove(path)
        except Exception as err:
            await sendMessage(str(err), message)
        await query.answer()
        await config_menu(user_id, message, True)
    elif cmd[1] == "delete_config_env":
        try:
            osremove("config.env")
        except Exception as err:
            await sendMessage(str(err), message)
        await query.answer()
        await config_menu(user_id, message, True)
    elif cmd[1] == "delete_pickle":
        try:
            osremove("token.pickle")
        except Exception as err:
            await sendMessage(str(err), message)
        await query.answer()
        await config_menu(user_id, message, True)
    elif cmd[1] == "delete_acc":
        if ospath.exists("accounts"):
            srun(["rm", "-rf", "accounts"])
        config_dict["USE_SERVICE_ACCOUNTS"] = False
        if DATABASE_URL:
            await DbManager().update_config({"USE_SERVICE_ACCOUNTS": False})
        await query.answer()
        await config_menu(user_id, message, True)
    else:
        await query.answer()
        await message.delete()


async def set_config_listener(client, query, message, rclone_global=False):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        user_id = message.from_user.id
    question = await client.send_message(
        message.chat.id, text="Send file, /ignore to cancel"
    )
    try:
        response = await client.listen.Message(
            filters.document | filters.text, id=filters.user(user_id), timeout=60
        )
    except TimeoutError:
        await client.send_message(message.chat.id, text="Too late 60s gone, try again!")
    else:
        try:
            if response.text and "/ignore" in response.text:
                await client.listen.Cancel(filters.user(user_id))
                await query.answer()
            else:
                file_name = response.document.file_name
                if file_name == "rclone.conf":
                    path = f"{getcwd()}/rclone/"
                    if rclone_global:
                        type = "rclone_global"
                        rclone_path = ospath.join(path, "rclone_global", "rclone.conf")
                    else:
                        type = "rclone"
                        rclone_path = ospath.join(path, f"{user_id}", "rclone.conf")
                    path = await client.download_media(response, file_name=rclone_path)
                    if DATABASE_URL:
                        await DbManager().update_user_doc(user_id, type, rclone_path)
                else:
                    await client.download_media(response, file_name="./")
                    if file_name == "accounts.zip":
                        if ospath.exists("accounts"):
                            await (
                                await create_subprocess_exec("rm", "-rf", "accounts")
                            ).wait()
                        await (
                            await create_subprocess_exec(
                                "7z",
                                "x",
                                "-o.",
                                "-aoa",
                                "accounts.zip",
                                "accounts/*.json",
                            )
                        ).wait()
                        await (
                            await create_subprocess_exec(
                                "chmod", "-R", "777", "accounts"
                            )
                        ).wait()
                    elif file_name in [".netrc", "netrc"]:
                        await (await create_subprocess_exec("touch", ".netrc")).wait()
                        await (
                            await create_subprocess_exec("cp", ".netrc", "/root/.netrc")
                        ).wait()
                        await (
                            await create_subprocess_exec("chmod", "600", ".netrc")
                        ).wait()
                    elif file_name == "config.env":
                        load_dotenv("config.env", override=True)
                        await load_config()
                    if DATABASE_URL and file_name != "config.env":
                        await DbManager().update_private_file(file_name)
                if ospath.exists("accounts.zip"):
                    osremove("accounts.zip")
        except Exception as ex:
            await sendMessage(str(ex), message)
    finally:
        await question.delete()


bot.add_handler(
    MessageHandler(
        handle_botfiles,
        filters=command(BotCommands.BotFilesCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
bot.add_handler(CallbackQueryHandler(botfiles_callback, filters=regex(r"configmenu")))
