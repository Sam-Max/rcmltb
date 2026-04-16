__version__ = "4.6"
__author__ = "Sam-Max"

from uvloop import install
from asyncio import Lock, new_event_loop, set_event_loop
from socket import setdefaulttimeout
from logging import getLogger, FileHandler, StreamHandler, INFO, basicConfig
from time import time
from faulthandler import enable as faulthandler_enable

faulthandler_enable()

install()

setdefaulttimeout(600)

botUptime = time()

basicConfig(
    level=INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[StreamHandler(), FileHandler("botlog.txt")],
)

LOGGER = getLogger(__name__)

from dotenv import load_dotenv
load_dotenv("config.env", override=True)

from bot.core.config_manager import Config
Config.load()

bot_id = Config.BOT_TOKEN.split(":", 1)[0]

GLOBAL_EXTENSION_FILTER = [".aria2", "!qB"]
user_data = {}
leech_log = []
tmdb_titles = {}
remotes_multi = []
aria2_options = {}
qbit_options = {}
rss_dict = {}

status_dict_lock = Lock()
status_dict = {}
status_reply_dict_lock = Lock()
status_reply_dict = {}

queued_dl = {}
queued_up = {}
non_queued_dl = set()
non_queued_up = set()
queue_dict_lock = Lock()
same_directory_lock = Lock()

Interval = []
QbInterval = []
QbTorrents = {}
qb_listener_lock = Lock()

config_dict = Config.get_all()

TG_MAX_SPLIT_SIZE = 2097152000
LEECH_SPLIT_SIZE = Config.LEECH_SPLIT_SIZE
if LEECH_SPLIT_SIZE == 0:
    LEECH_SPLIT_SIZE = TG_MAX_SPLIT_SIZE

bot_loop = new_event_loop()
set_event_loop(bot_loop)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tzlocal import get_localzone
scheduler = AsyncIOScheduler(timezone=str(get_localzone()), event_loop=bot_loop)


class _BotProxy:
    """Proxy that delegates to TgClient.bot once it's initialized.
    Buffers add_handler() calls made before bot is ready and replays them later."""

    def __init__(self):
        self._pending_handlers = []

    def __getattr__(self, name):
        from bot.core.telegram_manager import TgClient
        if TgClient.bot is None:
            raise RuntimeError("Bot client not initialized yet. Call TgClient.start_bot() first.")
        return getattr(TgClient.bot, name)

    def add_handler(self, handler, group=0):
        from bot.core.telegram_manager import TgClient
        if TgClient.bot is not None:
            TgClient.bot.add_handler(handler, group)
        else:
            self._pending_handlers.append((handler, group))

    def _flush_pending_handlers(self):
        """Replay all buffered handler registrations to the real bot client."""
        from bot.core.telegram_manager import TgClient
        if TgClient.bot is None:
            return
        for handler, group in self._pending_handlers:
            TgClient.bot.add_handler(handler, group)
        count = len(self._pending_handlers)
        self._pending_handlers.clear()
        if count:
            LOGGER.info(f"Flushed {count} deferred handler registrations")

    def __bool__(self):
        from bot.core.telegram_manager import TgClient
        return TgClient.bot is not None


class _AppProxy:
    """Proxy that delegates to TgClient.user once it's initialized."""

    def __getattr__(self, name):
        from bot.core.telegram_manager import TgClient
        if TgClient.user is None:
            raise RuntimeError("User client not initialized yet.")
        return getattr(TgClient.user, name)

    def __bool__(self):
        from bot.core.telegram_manager import TgClient
        return TgClient.user is not None


bot = _BotProxy()
app = _AppProxy()


# Backward compatibility: map removed module-level variables to Config attributes
_CONFIG_ALIASES = {
    "OWNER_ID": "OWNER_ID",
    "DATABASE_URL": "DATABASE_URL",
    "TELEGRAM_API_ID": "TELEGRAM_API_ID",
    "TELEGRAM_API_HASH": "TELEGRAM_API_HASH",
    "BOT_TOKEN": "BOT_TOKEN",
    "DOWNLOAD_DIR": "DOWNLOAD_DIR",
    "AUTO_MIRROR": "AUTO_MIRROR",
    "PARALLEL_TASKS": "PARALLEL_TASKS",
    "STATUS_LIMIT": "STATUS_LIMIT",
    "STATUS_UPDATE_INTERVAL": "STATUS_UPDATE_INTERVAL",
    "AUTO_DELETE_MESSAGE_DURATION": "AUTO_DELETE_MESSAGE_DURATION",
    "AS_DOCUMENT": "AS_DOCUMENT",
    "MULTI_REMOTE_UP": "MULTI_REMOTE_UP",
    "SEARCH_API_LINK": "SEARCH_API_LINK",
    "TMDB_API_KEY": "TMDB_API_KEY",
    "TMDB_LANGUAGE": "TMDB_LANGUAGE",
    "SEARCH_LIMIT": "SEARCH_LIMIT",
    "SEARCH_PLUGINS": "SEARCH_PLUGINS",
    "TORRENT_TIMEOUT": "TORRENT_TIMEOUT",
    "WEB_PINCODE": "WEB_PINCODE",
    "EQUAL_SPLITS": "EQUAL_SPLITS",
    "DEFAULT_OWNER_REMOTE": "DEFAULT_OWNER_REMOTE",
    "DEFAULT_GLOBAL_REMOTE": "DEFAULT_GLOBAL_REMOTE",
    "GD_INDEX_URL": "GD_INDEX_URL",
    "YT_DLP_OPTIONS": "YT_DLP_OPTIONS",
    "VIEW_LINK": "VIEW_LINK",
    "LOCAL_MIRROR": "LOCAL_MIRROR",
    "RC_INDEX_USER": "RC_INDEX_USER",
    "RC_INDEX_PASS": "RC_INDEX_PASS",
    "RC_INDEX_URL": "RC_INDEX_URL",
    "RC_INDEX_PORT": "RC_INDEX_PORT",
    "USE_SERVICE_ACCOUNTS": "USE_SERVICE_ACCOUNTS",
    "SERVICE_ACCOUNTS_REMOTE": "SERVICE_ACCOUNTS_REMOTE",
    "MULTI_RCLONE_CONFIG": "MULTI_RCLONE_CONFIG",
    "REMOTE_SELECTION": "REMOTE_SELECTION",
    "RCLONE_COPY_FLAGS": "RCLONE_COPY_FLAGS",
    "RCLONE_UPLOAD_FLAGS": "RCLONE_UPLOAD_FLAGS",
    "RCLONE_DOWNLOAD_FLAGS": "RCLONE_DOWNLOAD_FLAGS",
    "SERVER_SIDE": "SERVER_SIDE",
    "CMD_INDEX": "CMD_INDEX",
    "RSS_CHAT_ID": "RSS_CHAT_ID",
    "RSS_DELAY": "RSS_DELAY",
    "QB_BASE_URL": "QB_BASE_URL",
    "QB_SERVER_PORT": "QB_SERVER_PORT",
    "UPSTREAM_REPO": "UPSTREAM_REPO",
    "UPSTREAM_BRANCH": "UPSTREAM_BRANCH",
    "IS_TEAM_DRIVE": "IS_TEAM_DRIVE",
    "GDRIVE_FOLDER_ID": "GDRIVE_FOLDER_ID",
    "EXTENSION_FILTER": "EXTENSION_FILTER",
    "MEGA_EMAIL": "MEGA_EMAIL",
    "MEGA_PASSWORD": "MEGA_PASSWORD",
    "LEECH_LOG": "LEECH_LOG",
    "NO_TASKS_LOGS": "NO_TASKS_LOGS",
    "BOT_PM": "BOT_PM",
    "USER_SESSION_STRING": "USER_SESSION_STRING",
    "LEECH_SPLIT_SIZE": "LEECH_SPLIT_SIZE",
    "JD_EMAIL": "JD_EMAIL",
    "JD_PASSWORD": "JD_PASSWORD",
    "QUEUE_ALL": "QUEUE_ALL",
    "QUEUE_DOWNLOAD": "QUEUE_DOWNLOAD",
    "QUEUE_UPLOAD": "QUEUE_UPLOAD",
    "NAME_SUBSTITUTE": "NAME_SUBSTITUTE",
}


def __getattr__(name):
    if name in _CONFIG_ALIASES:
        return getattr(Config, _CONFIG_ALIASES[name])
    if name == "IS_PREMIUM_USER":
        from bot.core.telegram_manager import TgClient
        return TgClient.IS_PREMIUM_USER
    if name == "aria2c_global":
        from bot.core.torrent_manager import aria2c_global
        return aria2c_global
    raise AttributeError(f"module 'bot' has no attribute '{name}'")
