__version__ = "4.6"
__author__ = "Sam-Max"

from uvloop import install
from asyncio import Lock
from socket import setdefaulttimeout
from logging import getLogger, FileHandler, StreamHandler, INFO, basicConfig
from os import environ, getcwd, remove as osremove, path as ospath
from threading import Thread
from faulthandler import enable as faulthandler_enable
from time import sleep, time
from sys import exit
from dotenv import load_dotenv, dotenv_values
from pymongo import MongoClient
from aria2p import API as ariaAPI, Client as ariaClient
from qbittorrentapi import Client as qbitClient
from subprocess import Popen, run as srun
from pyrogram import Client as tgClient, enums
from pyrogram.types import LinkPreviewOptions
from bot.conv_pyrogram import Conversation
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tzlocal import get_localzone

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

load_dotenv("config.env", override=True)

Interval = []
QbInterval = []
GLOBAL_EXTENSION_FILTER = [".aria2", "!qB"]
QbTorrents = {}
qb_listener_lock = Lock()
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

from bot.core.config_manager import Config

Config.load()

BOT_TOKEN = Config.BOT_TOKEN
if len(BOT_TOKEN) == 0:
    LOGGER.error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

bot_id = BOT_TOKEN.split(":", 1)[0]

DATABASE_URL = Config.DATABASE_URL or ""
if len(DATABASE_URL) == 0:
    Config.DATABASE_URL = ""
    DATABASE_URL = ""

if DATABASE_URL:
    conn = MongoClient(DATABASE_URL)
    db = conn.rcmltb
    current_config = dict(dotenv_values("config.env"))
    old_config = db.settings.deployConfig.find_one({"_id": bot_id})
    if old_config is None:
        db.settings.deployConfig.replace_one(
            {"_id": bot_id}, current_config, upsert=True
        )
    else:
        del old_config["_id"]
    if old_config and old_config != current_config:
        db.settings.deployConfig.replace_one(
            {"_id": bot_id}, current_config, upsert=True
        )
    elif saved_config := db.settings.config.find_one({"_id": bot_id}):
        del saved_config["_id"]
        Config.load_dict(saved_config)
        for key, value in saved_config.items():
            environ[key] = str(value)
    if pf_dict := db.settings.files.find_one({"_id": bot_id}):
        del pf_dict["_id"]
        for key, value in pf_dict.items():
            if value:
                file_ = key.replace("__", ".")
                with open(file_, "wb+") as f:
                    f.write(value)
    if a2c_options := db.settings.aria2c.find_one({"_id": bot_id}):
        del a2c_options["_id"]
        aria2_options = a2c_options
    if qbit_opt := db.settings.qbittorrent.find_one({"_id": bot_id}):
        del qbit_opt["_id"]
        qbit_options = qbit_opt
    conn.close()
    BOT_TOKEN = Config.BOT_TOKEN
    bot_id = BOT_TOKEN.split(":", 1)[0]
    DATABASE_URL = Config.DATABASE_URL

OWNER_ID = Config.OWNER_ID
if OWNER_ID == 0:
    LOGGER.error("OWNER_ID variable is missing! Exiting now")
    exit(1)

TELEGRAM_API_ID = Config.TELEGRAM_API_ID
if TELEGRAM_API_ID == 0:
    LOGGER.error("TELEGRAM_API_ID variable is missing! Exiting now")
    exit(1)

TELEGRAM_API_HASH = Config.TELEGRAM_API_HASH
if len(TELEGRAM_API_HASH) == 0:
    LOGGER.error("TELEGRAM_API_HASH variable is missing! Exiting now")
    exit(1)

ALLOWED_CHATS = Config.ALLOWED_CHATS
if len(ALLOWED_CHATS) != 0:
    aid = ALLOWED_CHATS.split()
    for id_ in aid:
        user_data[int(id_.strip())] = {"is_auth": True}

SUDO_USERS = Config.SUDO_USERS
if len(SUDO_USERS) != 0:
    aid = SUDO_USERS.split()
    for id_ in aid:
        user_data[int(id_.strip())] = {"is_sudo": True}

STATUS_LIMIT = Config.STATUS_LIMIT
STATUS_UPDATE_INTERVAL = Config.STATUS_UPDATE_INTERVAL
AUTO_DELETE_MESSAGE_DURATION = Config.AUTO_DELETE_MESSAGE_DURATION
PARALLEL_TASKS = Config.PARALLEL_TASKS
AS_DOCUMENT = Config.AS_DOCUMENT
AUTO_MIRROR = Config.AUTO_MIRROR
MULTI_REMOTE_UP = Config.MULTI_REMOTE_UP
SEARCH_API_LINK = Config.SEARCH_API_LINK
TMDB_API_KEY = Config.TMDB_API_KEY
TMDB_LANGUAGE = Config.TMDB_LANGUAGE
SEARCH_LIMIT = Config.SEARCH_LIMIT
SEARCH_PLUGINS = Config.SEARCH_PLUGINS
TORRENT_TIMEOUT = Config.TORRENT_TIMEOUT
WEB_PINCODE = Config.WEB_PINCODE
EQUAL_SPLITS = Config.EQUAL_SPLITS
DEFAULT_OWNER_REMOTE = Config.DEFAULT_OWNER_REMOTE
DEFAULT_GLOBAL_REMOTE = Config.DEFAULT_GLOBAL_REMOTE
GD_INDEX_URL = Config.GD_INDEX_URL
YT_DLP_OPTIONS = Config.YT_DLP_OPTIONS
VIEW_LINK = Config.VIEW_LINK
LOCAL_MIRROR = Config.LOCAL_MIRROR
RC_INDEX_USER = Config.RC_INDEX_USER
RC_INDEX_PASS = Config.RC_INDEX_PASS
RC_INDEX_URL = Config.RC_INDEX_URL
RC_INDEX_PORT = Config.RC_INDEX_PORT
USE_SERVICE_ACCOUNTS = Config.USE_SERVICE_ACCOUNTS
SERVICE_ACCOUNTS_REMOTE = Config.SERVICE_ACCOUNTS_REMOTE
MULTI_RCLONE_CONFIG = Config.MULTI_RCLONE_CONFIG
REMOTE_SELECTION = Config.REMOTE_SELECTION
RCLONE_COPY_FLAGS = Config.RCLONE_COPY_FLAGS
RCLONE_UPLOAD_FLAGS = Config.RCLONE_UPLOAD_FLAGS
RCLONE_DOWNLOAD_FLAGS = Config.RCLONE_DOWNLOAD_FLAGS
SERVER_SIDE = Config.SERVER_SIDE
CMD_INDEX = Config.CMD_INDEX
RSS_CHAT_ID = Config.RSS_CHAT_ID
RSS_DELAY = Config.RSS_DELAY
QB_BASE_URL = Config.QB_BASE_URL
QB_SERVER_PORT = Config.QB_SERVER_PORT
UPSTREAM_REPO = Config.UPSTREAM_REPO
UPSTREAM_BRANCH = Config.UPSTREAM_BRANCH
IS_TEAM_DRIVE = Config.IS_TEAM_DRIVE
GDRIVE_FOLDER_ID = Config.GDRIVE_FOLDER_ID
DOWNLOAD_DIR = Config.DOWNLOAD_DIR
EXTENSION_FILTER = Config.EXTENSION_FILTER
MEGA_EMAIL = Config.MEGA_EMAIL
MEGA_PASSWORD = Config.MEGA_PASSWORD
LEECH_LOG = Config.LEECH_LOG
NO_TASKS_LOGS = Config.NO_TASKS_LOGS
BOT_PM = Config.BOT_PM
USER_SESSION_STRING = Config.USER_SESSION_STRING

if len(EXTENSION_FILTER) > 0:
    fx = EXTENSION_FILTER.split()
    for x in fx:
        x = x.lstrip(".")
        GLOBAL_EXTENSION_FILTER.append(x.strip().lower())

if len(LEECH_LOG) != 0:
    leech_log.clear()
    aid = LEECH_LOG.split()
    for id_ in aid:
        leech_log.append(int(id_.strip()))

IS_PREMIUM_USER = False
app = ""
if len(USER_SESSION_STRING) != 0:
    LOGGER.info("Creating Pyrogram client from USER_SESSION_STRING")
    app = tgClient(
        "pyrogram_session",
        api_id=TELEGRAM_API_ID,
        api_hash=TELEGRAM_API_HASH,
        session_string=USER_SESSION_STRING,
        max_concurrent_transmissions=10,
        parse_mode=enums.ParseMode.HTML,
        max_message_cache_size=15000,
        max_topic_cache_size=15000,
        sleep_threshold=60,
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    ).start()
    IS_PREMIUM_USER = app.me.is_premium

TG_MAX_SPLIT_SIZE = 4194304000 if IS_PREMIUM_USER else 2097152000
LEECH_SPLIT_SIZE = Config.LEECH_SPLIT_SIZE
if LEECH_SPLIT_SIZE == 0 or LEECH_SPLIT_SIZE > TG_MAX_SPLIT_SIZE:
    LEECH_SPLIT_SIZE = TG_MAX_SPLIT_SIZE
Config.LEECH_SPLIT_SIZE = LEECH_SPLIT_SIZE

config_dict = Config.get_all()

if QB_BASE_URL:
    Popen(
        f"gunicorn qbitweb.wserver:app --bind 0.0.0.0:{QB_SERVER_PORT} --worker-class gevent",
        shell=True,
    )

srun(["qbittorrent-nox", "-d", f"--profile={getcwd()}"])

if not ospath.exists(".netrc"):
    with open(".netrc", "w"):
        pass
srun(["chmod", "600", ".netrc"])
srun(["cp", ".netrc", "/root/.netrc"])
srun(["chmod", "+x", "aria.sh"])
srun("./aria.sh", shell=True)
if ospath.exists("accounts.zip"):
    if ospath.exists("accounts"):
        srun(["rm", "-rf", "accounts"])
    srun(["7z", "x", "-o.", "-aoa", "accounts.zip", "accounts/*.json"])
    srun(["chmod", "-R", "777", "accounts"])
    osremove("accounts.zip")
if not ospath.exists("accounts"):
    Config.USE_SERVICE_ACCOUNTS = False
    config_dict["USE_SERVICE_ACCOUNTS"] = False


aria2 = ariaAPI(ariaClient(host="http://localhost", port=6800, secret=""))


def aria2c_init():
    try:
        LOGGER.info("Initializing Aria2c")
        link = "https://linuxmint.com/torrents/lmde-5-cinnamon-64bit.iso.torrent"
        dire = DOWNLOAD_DIR.rstrip("/")
        aria2.add_uris([link], {"dir": dire})
        sleep(3)
        downloads = aria2.get_downloads()
        sleep(10)
        aria2.remove(downloads, force=True, files=True, clean=True)
    except Exception as e:
        LOGGER.error(f"Aria2c initializing error: {e}")


Thread(target=aria2c_init).start()
sleep(1.5)

aria2c_global = [
    "bt-max-open-files",
    "download-result",
    "keep-unfinished-download-result",
    "log",
    "log-level",
    "max-concurrent-downloads",
    "max-download-result",
    "max-overall-download-limit",
    "save-session",
    "max-overall-upload-limit",
    "optimize-concurrent-downloads",
    "save-cookies",
    "server-stat-of",
]

if not aria2_options:
    aria2_options = aria2.client.get_global_option()
else:
    a2c_glo = {}
    for op in aria2c_global:
        if op in aria2_options:
            a2c_glo[op] = aria2_options[op]
    aria2.set_global_options(a2c_glo)


def get_client():
    return qbitClient(
        host="localhost",
        port=8090,
        REQUESTS_ARGS={"timeout": (30, 60)},
    )


qb_client = get_client()
if not qbit_options:
    qbit_options = dict(qb_client.app_preferences())
    del qbit_options["listen_port"]
    for k in list(qbit_options.keys()):
        if k.startswith("rss"):
            del qbit_options[k]
else:
    qb_opt = {**qbit_options}
    for k, v in list(qb_opt.items()):
        if v in ["", "*"]:
            del qb_opt[k]
    qb_client.app_set_preferences(qb_opt)

LOGGER.info("Creating Pyrogram client")
bot = tgClient(
    "pyrogram",
    api_id=TELEGRAM_API_ID,
    api_hash=TELEGRAM_API_HASH,
    bot_token=BOT_TOKEN,
    workers=1000,
    max_concurrent_transmissions=10,
    parse_mode=enums.ParseMode.HTML,
    max_message_cache_size=15000,
    max_topic_cache_size=15000,
    sleep_threshold=0,
    link_preview_options=LinkPreviewOptions(is_disabled=True),
)
Conversation(bot)
bot.start()
bot_loop = bot.loop

scheduler = AsyncIOScheduler(timezone=str(get_localzone()), event_loop=bot_loop)
