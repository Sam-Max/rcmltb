from asyncio import TimeoutError, create_subprocess_exec, create_subprocess_shell
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from bot.modules.debrid import debrid_data, load_debrid_token
from pyrogram.filters import regex, command
from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from os import environ, getcwd, makedirs, path as ospath, remove as osremove
from dotenv import load_dotenv
from subprocess import run as srun
from shutil import copyfile
from bot import (
    DATABASE_URL,
    GLOBAL_EXTENSION_FILTER,
    IS_PREMIUM_USER,
    LOGGER,
    OWNER_ID,
    Interval,
    aria2_options,
    bot,
    config_dict,
    status_dict,
    status_reply_dict_lock,
    user_data,
    leech_log,
)
from bot.core.torrent_manager import TorrentManager
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import setInterval
from bot.helper.ext_utils.db_handler import database
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (
    editMarkup,
    sendMarkup,
    sendMessage,
    update_all_messages,
)
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.modules.torr_search import initiate_search_tools


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

    TG_MAX_SPLIT_SIZE = 4194304000 if IS_PREMIUM_USER else 2097152000

    LEECH_SPLIT_SIZE = environ.get("LEECH_SPLIT_SIZE", "")
    if len(LEECH_SPLIT_SIZE) == 0 or int(LEECH_SPLIT_SIZE) > TG_MAX_SPLIT_SIZE:
        LEECH_SPLIT_SIZE = TG_MAX_SPLIT_SIZE
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
    if len(TORRENT_TIMEOUT) == 0:
        await TorrentManager.change_aria2_option("bt-stop-timeout", "0")
        aria2_options["bt-stop-timeout"] = "0"
        if DATABASE_URL:
            await database.update_aria2("bt-stop-timeout", "0")
        TORRENT_TIMEOUT = ""
    else:
        await TorrentManager.change_aria2_option("bt-stop-timeout", TORRENT_TIMEOUT)
        aria2_options["bt-stop-timeout"] = TORRENT_TIMEOUT
        if DATABASE_URL:
            await database.update_aria2("bt-stop-timeout", TORRENT_TIMEOUT)
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
            "USER_SESSION_STRING": USER_SESSION_STRING,
            "USE_SERVICE_ACCOUNTS": USE_SERVICE_ACCOUNTS,
            "VIEW_LINK": VIEW_LINK,
            "YT_DLP_OPTIONS": YT_DLP_OPTIONS,
            "WEB_PINCODE": WEB_PINCODE,
        }
    )

    if DATABASE_URL:
        await database.update_config(config_dict)
    await initiate_search_tools()


def _can_manage_global(user_id):
    return user_id == OWNER_ID or bool(user_data.get(user_id, {}).get("is_sudo"))


def _section_title(section):
    return {
        "rclone": "👤 My rclone config",
        "token": "🔑 Google Drive token",
        "rclone_global": "🌐 Global rclone config",
        "debrid": "🧪 Debrid token",
        "config": "🛠 Bot config",
        "accounts": "📦 Service accounts",
    }[section]


def _section_path(section, user_id):
    return {
        "rclone": f"rclone/{user_id}/rclone.conf",
        "token": f"tokens/{user_id}.pickle",
        "rclone_global": "rclone/rclone_global/rclone.conf",
        "debrid": "debrid/debrid_token.txt",
        "config": "config.env",
        "accounts": "accounts",
    }[section]


def _overview_sections(user_id):
    sections = ["rclone", "token"]
    if _can_manage_global(user_id):
        sections.extend(["rclone_global", "debrid", "config", "accounts"])
    return sections


async def _rclone_remotes(path, message):
    cmd = ["rclone", "listremotes", f"--config={path}"]
    process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = await process.communicate()
    if await process.wait() != 0:
        err = stderr.decode().strip() or "Unknown rclone error"
        await sendMessage(f"Error: {err}", message)
        return None
    remotes = [remote.replace(":", "").strip() for remote in stdout.decode().splitlines()]
    remotes = [remote for remote in remotes if remote]
    if not remotes:
        return "- No remotes found"
    return "\n".join(f"- {remote}" for remote in remotes)


async def files_menu(user_id, message, edit=False):
    buttons = ButtonMaker()
    msg = (
        "⚙️ <b>Files manager</b>\n\n"
        "Manage the files used by the bot. Tap a card to open its submenu."
    )

    for section in _overview_sections(user_id):
        exists = ospath.exists(_section_path(section, user_id))
        status = "✅" if exists else "➕"
        buttons.cb_buildbutton(
            f"{status} {_section_title(section)}",
            f"configmenu^section^{section}^{user_id}",
        )

    buttons.cb_buildbutton("✘ Close Menu", f"configmenu^close^{user_id}", "footer")
    markup = buttons.build_menu(2)
    if edit:
        await editMarkup(msg, message, reply_markup=markup)
    else:
        await sendMarkup(msg, message, reply_markup=markup)


async def files_section_menu(user_id, message, section, edit=False):
    if section in {"rclone_global", "debrid", "config", "accounts"} and not _can_manage_global(
        user_id
    ):
        await sendMessage("🚫 <b>Not allowed to use</b>", message)
        return

    path = _section_path(section, user_id)
    exists = ospath.exists(path)
    buttons = ButtonMaker()
    msg = (
        f"{_section_title(section)}\n\n"
        f"<b>Status:</b> {'✅ Present' if exists else '➕ Missing'}\n"
        f"<b>Path:</b> <code>{path}</code>"
    )

    if section in {"rclone", "rclone_global"} and exists:
        remotes = await _rclone_remotes(path, message)
        if remotes:
            msg += f"\n\n<b>Remotes:</b>\n{remotes}"

    if section == "accounts":
        if exists:
            buttons.cb_buildbutton(
                "📤 Replace accounts.zip", f"configmenu^upload^{section}^{user_id}"
            )
            buttons.cb_buildbutton(
                "🗑 Delete accounts", f"configmenu^delete^{section}^{user_id}"
            )
        else:
            buttons.cb_buildbutton(
                "📤 Upload accounts.zip", f"configmenu^upload^{section}^{user_id}"
            )
    else:
        file_name = path.rsplit("/", 1)[-1]
        if exists:
            buttons.cb_buildbutton(
                f"📥 View {file_name}", f"configmenu^view^{section}^{user_id}"
            )
            buttons.cb_buildbutton(
                f"📤 Replace {file_name}", f"configmenu^upload^{section}^{user_id}"
            )
            buttons.cb_buildbutton(
                f"🗑 Delete {file_name}", f"configmenu^delete^{section}^{user_id}"
            )
        else:
            buttons.cb_buildbutton(
                f"📤 Upload {file_name}", f"configmenu^upload^{section}^{user_id}"
            )

    buttons.cb_buildbutton("⬅️ Back", f"configmenu^back^{user_id}", "footer")
    buttons.cb_buildbutton("✘ Close Menu", f"configmenu^close^{user_id}", "footer_second")
    markup = buttons.build_menu(2)
    if edit:
        await editMarkup(msg, message, reply_markup=markup)
    else:
        await sendMarkup(msg, message, reply_markup=markup)


async def _view_section_file(client, message, user_id, section):
    if section == "accounts":
        await sendMessage("📦 <b>Service accounts are stored as a folder.</b>", message)
        return

    path = _section_path(section, user_id)
    if not ospath.exists(path):
        await sendMessage("File not found.", message)
        return
    await client.send_document(document=path, chat_id=message.chat.id)


async def _delete_section_file(user_id, section):
    path = _section_path(section, user_id)

    if section == "accounts":
        if ospath.exists(path):
            srun(["rm", "-rf", path])
        config_dict["USE_SERVICE_ACCOUNTS"] = False
        if DATABASE_URL:
            await database.update_config({"USE_SERVICE_ACCOUNTS": False})
            await database.update_private_file("accounts.zip")
        return

    if ospath.exists(path):
        osremove(path)

    if section == "debrid":
        debrid_data.pop("token", None)

    if DATABASE_URL:
        await database.update_private_file(path)


async def _start_upload_listener(client, query, message, user_id, section):
    await query.answer("📁 Send the file", show_alert=False)
    await set_config_listener(
        client,
        query,
        message,
        rclone_global=section == "rclone_global",
        forced_section=section,
        target_user_id=user_id,
    )


def _resolve_action(action):
    aliases = {
        "get_rclone_conf": ("view", "rclone"),
        "get_global_rclone_conf": ("view", "rclone_global"),
        "get_token_pickle": ("view", "token"),
        "get_debrid_token": ("view", "debrid"),
        "get_config_env": ("view", "config"),
        "add_rclone_conf": ("upload", "rclone"),
        "add_global_rclone_conf": ("upload", "rclone_global"),
        "add_token_pickle": ("upload", "token"),
        "add_debrid_token": ("upload", "debrid"),
        "add_config_env": ("upload", "config"),
        "add_accounts": ("upload", "accounts"),
        "delete_clone_conf": ("delete", "rclone"),
        "delete_global_rclone_conf": ("delete", "rclone_global"),
        "delete_token_pickle": ("delete", "token"),
        "delete_debrid_token": ("delete", "debrid"),
        "delete_config_env": ("delete", "config"),
        "delete_accounts": ("delete", "accounts"),
    }
    return aliases.get(action, (action, None))


async def handle_botfiles(client, message):
    user_id = message.from_user.id
    if config_dict["MULTI_RCLONE_CONFIG"] or await CustomFilters.sudo_filter("", message):
        await files_menu(user_id, message)
    else:
        await sendMessage("🚫 <b>Not allowed to use</b>", message)


async def botfiles_callback(client, callback_query):
    query = callback_query
    cmd = query.data.split("^")
    message = query.message
    user_id = query.from_user.id

    if int(cmd[-1]) != user_id:
        await query.answer("⛔ This menu is not for you!", show_alert=True)
        return

    action, section = _resolve_action(cmd[1])
    if action in {"section", "view", "upload", "delete"} and len(cmd) > 2:
        section = cmd[2]

    if section in {"rclone_global", "debrid", "config", "accounts"} and not _can_manage_global(
        user_id
    ):
        await query.answer("⛔ This menu is not for you!", show_alert=True)
        return

    try:
        if action == "section":
            await query.answer()
            await files_section_menu(user_id, message, cmd[2], True)
        elif action == "back":
            await query.answer()
            await files_menu(user_id, message, True)
        elif action == "close":
            await query.answer()
            await message.delete()
        elif action == "view":
            await _view_section_file(client, message, user_id, section)
            await query.answer()
            await files_menu(user_id, message, True)
        elif action == "upload":
            await _start_upload_listener(client, query, message, user_id, section)
            await files_menu(user_id, message, True)
        elif action == "delete":
            await _delete_section_file(user_id, section)
            await query.answer("🗑 Deleted", show_alert=False)
            await files_menu(user_id, message, True)
        else:
            await query.answer()
            await message.delete()
    except ValueError as err:
        await sendMessage(str(err), message)
    except Exception as err:
        await sendMessage(str(err), message)


async def set_config_listener(
    client,
    query,
    message,
    rclone_global=False,
    forced_section=None,
    target_user_id=None,
):
    if target_user_id is not None:
        user_id = target_user_id
    elif message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif message.from_user:
        user_id = message.from_user.id
    else:
        user_id = query.from_user.id

    question = None

    def _ensure_target_file(saved_path, target_path):
        if saved_path and ospath.exists(target_path):
            return True
        if saved_path and ospath.exists(saved_path):
            if saved_path != target_path:
                makedirs(ospath.dirname(target_path), exist_ok=True)
                copyfile(saved_path, target_path)
            return ospath.exists(target_path)
        return False

    try:
        question = await client.send_message(
            message.chat.id, text="📁 <b>Send file</b>, /ignore to cancel"
        )
        response = await client.listen.Message(
            filters.document | filters.text, id=filters.user(user_id), timeout=60
        )
        if response.text:
            if "/ignore" in response.text:
                await client.listen.Cancel(filters.user(user_id))
                return
            await sendMessage("📁 <b>Please send a supported file.</b>", message)
            return

        if not response.document:
            await sendMessage("📁 <b>Please send a supported file.</b>", message)
            return

        file_name = response.document.file_name
        target_section = forced_section

        if target_section is None:
            if file_name == "rclone.conf":
                target_section = "rclone_global" if rclone_global else "rclone"
            elif file_name == "token.pickle":
                target_section = "token"
            elif file_name == "debrid_token.txt":
                target_section = "debrid"
            elif file_name == "config.env":
                target_section = "config"
            elif file_name == "accounts.zip":
                target_section = "accounts"

        if target_section == "rclone" or target_section == "rclone_global":
            if target_section == "rclone_global":
                file_type = "rclone_global"
                rclone_path = "rclone/rclone_global/rclone.conf"
            else:
                file_type = "rclone"
                rclone_path = f"rclone/{user_id}/rclone.conf"
            makedirs(ospath.dirname(rclone_path), exist_ok=True)
            saved_path = await client.download_media(response, file_name=rclone_path)
            if not _ensure_target_file(saved_path, rclone_path):
                await sendMessage(
                    "❌ <b>Failed to save rclone.conf.</b>\n"
                    "Check disk space and write permissions.",
                    message,
                )
                return
            if DATABASE_URL:
                await database.update_user_doc(user_id, file_type, rclone_path)
            await sendMessage(
                f"✅ <b>rclone.conf uploaded successfully.</b>\n"
                f"<b>Saved to:</b> <code>{rclone_path}</code>",
                message,
            )
        elif target_section == "token":
            path = f"{getcwd()}/tokens/"
            makedirs(path, exist_ok=True)
            des_dir = f"{path}{user_id}.pickle"
            saved_path = await client.download_media(response, file_name=des_dir)
            if not _ensure_target_file(saved_path, des_dir):
                await sendMessage(
                    "❌ <b>Failed to save token.pickle.</b>\n"
                    "Check disk space and write permissions.",
                    message,
                )
                return
            if DATABASE_URL:
                await database.update_user_doc(user_id, "token_pickle", des_dir)
            await sendMessage("✅ <b>token.pickle uploaded successfully.</b>", message)
        elif target_section == "debrid":
            path = f"{getcwd()}/debrid/"
            makedirs(path, exist_ok=True)
            des_dir = f"{path}debrid_token.txt"
            saved_path = await client.download_media(response, file_name=des_dir)
            if not _ensure_target_file(saved_path, des_dir):
                await sendMessage(
                    "❌ <b>Failed to save debrid token.</b>\n"
                    "Check disk space and write permissions.",
                    message,
                )
                return
            await load_debrid_token()
            if DATABASE_URL:
                await database.update_private_file("debrid/debrid_token.txt")
            await sendMessage("✅ <b>debrid token uploaded successfully.</b>", message)
        elif target_section == "config":
            saved_path = await client.download_media(response, file_name="config.env")
            if not _ensure_target_file(saved_path, "config.env"):
                await sendMessage(
                    "❌ <b>Failed to save config.env.</b>\n"
                    "Check disk space and write permissions.",
                    message,
                )
                return
            load_dotenv("config.env", override=True)
            await load_config()
            if DATABASE_URL:
                await database.update_private_file("config.env")
            await sendMessage("✅ <b>config.env uploaded successfully.</b>", message)
        elif target_section == "accounts":
            saved_path = await client.download_media(response, file_name="accounts.zip")
            if not _ensure_target_file(saved_path, "accounts.zip"):
                await sendMessage(
                    "❌ <b>Failed to save accounts.zip.</b>\n"
                    "Check disk space and write permissions.",
                    message,
                )
                return
            if ospath.exists("accounts"):
                await (await create_subprocess_exec("rm", "-rf", "accounts")).wait()
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
            await (await create_subprocess_exec("chmod", "-R", "777", "accounts")).wait()
            if DATABASE_URL:
                await database.update_private_file("accounts.zip")
            await sendMessage("✅ <b>accounts.zip uploaded and extracted.</b>", message)
        else:
            await client.download_media(response, file_name="./")
            if file_name in [".netrc", "netrc"]:
                await (await create_subprocess_exec("touch", ".netrc")).wait()
                if environ.get("HOME") == "/root":
                    await (await create_subprocess_exec("cp", ".netrc", "/root/.netrc")).wait()
                await (await create_subprocess_exec("chmod", "600", ".netrc")).wait()
            if DATABASE_URL:
                await database.update_private_file(file_name)
            await sendMessage("✅ <b>File uploaded successfully.</b>", message)
        if ospath.exists("accounts.zip"):
            osremove("accounts.zip")
    except TimeoutError:
        await client.send_message(message.chat.id, text="⏰ Too late 60s gone, try again!")
    except Exception as ex:
        await sendMessage(str(ex), message)
    finally:
        if question is not None:
            await question.delete()


bot.add_handler(
    MessageHandler(
        handle_botfiles,
        filters=command(BotCommands.BotFilesCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
bot.add_handler(CallbackQueryHandler(botfiles_callback, filters=regex(r"configmenu")))
