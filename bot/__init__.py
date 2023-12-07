__version__ = "4.6"
__author__ = "Sam-Max"

from uvloop import install
from asyncio import Lock
from asyncio import Queue
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
from pyrogram import Client as tgClient
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

m_queue = Queue()
l_queue = Queue()

BOT_TOKEN = environ.get("BOT_TOKEN", "")
if len(BOT_TOKEN) == 0:
    LOGGER.error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

bot_id = BOT_TOKEN.split(":", 1)[0]

DATABASE_URL = environ.get("DATABASE_URL", "")
if len(DATABASE_URL) == 0:
    DATABASE_URL = None

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
    elif config_dict := db.settings.config.find_one({"_id": bot_id}):
        del config_dict["_id"]
        for key, value in config_dict.items():
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
    BOT_TOKEN = environ.get("BOT_TOKEN", "")
    bot_id = BOT_TOKEN.split(":", 1)[0]
    DATABASE_URL = environ.get("DATABASE_URL", "")
else:
    config_dict = {}

OWNER_ID = environ.get("OWNER_ID", "")
if len(OWNER_ID) == 0:
    LOGGER.error("OWNER_ID variable is missing! Exiting now")
    exit(1)
else:
    OWNER_ID = int(OWNER_ID)

TELEGRAM_API_ID = environ.get("TELEGRAM_API_ID", "")
if len(TELEGRAM_API_ID) == 0:
    LOGGER.error("TELEGRAM_API_ID variable is missing! Exiting now")
    exit(1)
else:
    TELEGRAM_API_ID = int(TELEGRAM_API_ID)

TELEGRAM_API_HASH = environ.get("TELEGRAM_API_HASH", "")
if len(TELEGRAM_API_HASH) == 0:
    LOGGER.error("TELEGRAM_API_HASH variable is missing! Exiting now")
    exit(1)

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

STATUS_LIMIT = environ.get("STATUS_LIMIT", "")
STATUS_LIMIT = 10 if len(STATUS_LIMIT) == 0 else int(STATUS_LIMIT)

STATUS_UPDATE_INTERVAL = environ.get("STATUS_UPDATE_INTERVAL", "")
if len(STATUS_UPDATE_INTERVAL) == 0:
    STATUS_UPDATE_INTERVAL = 10
else:
    STATUS_UPDATE_INTERVAL = int(STATUS_UPDATE_INTERVAL)

AUTO_DELETE_MESSAGE_DURATION = environ.get("AUTO_DELETE_MESSAGE_DURATION", "")
if len(AUTO_DELETE_MESSAGE_DURATION) == 0:
    AUTO_DELETE_MESSAGE_DURATION = 30
else:
    AUTO_DELETE_MESSAGE_DURATION = int(AUTO_DELETE_MESSAGE_DURATION)

PARALLEL_TASKS = environ.get("PARALLEL_TASKS", "")
PARALLEL_TASKS = "" if len(PARALLEL_TASKS) == 0 else int(PARALLEL_TASKS)

AS_DOCUMENT = environ.get("AS_DOCUMENT", "")
AS_DOCUMENT = AS_DOCUMENT.lower() == "true"

AUTO_MIRROR = environ.get("AUTO_MIRROR", "")
AUTO_MIRROR = AUTO_MIRROR.lower() == "true"

MULTI_REMOTE_UP = environ.get("MULTI_REMOTE_UP", "")
MULTI_REMOTE_UP = MULTI_REMOTE_UP.lower() == "true"

UPTOBOX_TOKEN = environ.get("UPTOBOX_TOKEN", "")
if len(UPTOBOX_TOKEN) == 0:
    UPTOBOX_TOKEN = ""

SEARCH_API_LINK = environ.get("SEARCH_API_LINK", "").rstrip("/")
if len(SEARCH_API_LINK) == 0:
    SEARCH_API_LINK = ""

TMDB_API_KEY = environ.get("TMDB_API_KEY", "")
if len(TMDB_API_KEY) == 0:
    TMDB_API_KEY = ""

TMDB_LANGUAGE = environ.get("TMDB_LANGUAGE", "")
if len(TMDB_LANGUAGE) == 0:
    TMDB_LANGUAGE = "en"

SEARCH_LIMIT = environ.get("SEARCH_LIMIT", "")
SEARCH_LIMIT = 0 if len(SEARCH_LIMIT) == 0 else int(SEARCH_LIMIT)

SEARCH_PLUGINS = environ.get("SEARCH_PLUGINS", "")
if len(SEARCH_PLUGINS) == 0:
    SEARCH_PLUGINS = ""

TORRENT_TIMEOUT = environ.get("TORRENT_TIMEOUT", "")
TORRENT_TIMEOUT = "" if len(TORRENT_TIMEOUT) == 0 else int(TORRENT_TIMEOUT)

WEB_PINCODE = environ.get("WEB_PINCODE", "")
WEB_PINCODE = WEB_PINCODE.lower() == "true"

EQUAL_SPLITS = environ.get("EQUAL_SPLITS", "")
EQUAL_SPLITS = EQUAL_SPLITS.lower() == "true"

DEFAULT_OWNER_REMOTE = environ.get("DEFAULT_OWNER_REMOTE", "")

DEFAULT_GLOBAL_REMOTE = environ.get("DEFAULT_GLOBAL_REMOTE", "")

GD_INDEX_URL = environ.get("GD_INDEX_URL", "").rstrip("/")
if len(GD_INDEX_URL) == 0:
    GD_INDEX_URL = ""

YT_DLP_OPTIONS = environ.get("YT_DLP_OPTIONS", "")
if len(YT_DLP_OPTIONS) == 0:
    YT_DLP_OPTIONS = ""

VIEW_LINK = environ.get("VIEW_LINK", "")
VIEW_LINK = VIEW_LINK.lower() == "true"

LOCAL_MIRROR = environ.get("LOCAL_MIRROR", "")
LOCAL_MIRROR = LOCAL_MIRROR.lower() == "true"

RC_INDEX_USER = environ.get("RC_INDEX_USER", "")
RC_INDEX_USER = "admin" if len(RC_INDEX_USER) == 0 else RC_INDEX_USER

RC_INDEX_PASS = environ.get("RC_INDEX_PASS", "")
RC_INDEX_PASS = "admin" if len(RC_INDEX_PASS) == 0 else RC_INDEX_PASS

RC_INDEX_URL = environ.get("RC_INDEX_URL", "")
RC_INDEX_URL = "" if len(RC_INDEX_URL) == 0 else RC_INDEX_URL

RC_INDEX_PORT = environ.get("RC_INDEX_PORT", "")
RC_INDEX_PORT = 8080 if len(RC_INDEX_PORT) == 0 else int(RC_INDEX_PORT)

USE_SERVICE_ACCOUNTS = environ.get("USE_SERVICE_ACCOUNTS", "")
USE_SERVICE_ACCOUNTS = USE_SERVICE_ACCOUNTS.lower() == "true"

SERVICE_ACCOUNTS_REMOTE = environ.get("SERVICE_ACCOUNTS_REMOTE", "")

MULTI_RCLONE_CONFIG = environ.get("MULTI_RCLONE_CONFIG", "")
MULTI_RCLONE_CONFIG = MULTI_RCLONE_CONFIG.lower() == "true"

REMOTE_SELECTION = environ.get("REMOTE_SELECTION", "")
REMOTE_SELECTION = REMOTE_SELECTION.lower() == "true"

RCLONE_COPY_FLAGS = environ.get("RCLONE_COPY_FLAGS", "")
if len(RCLONE_COPY_FLAGS) == 0:
    RCLONE_COPY_FLAGS = ""

RCLONE_UPLOAD_FLAGS = environ.get("RCLONE_UPLOAD_FLAGS", "")
if len(RCLONE_UPLOAD_FLAGS) == 0:
    RCLONE_UPLOAD_FLAGS = ""

RCLONE_DOWNLOAD_FLAGS = environ.get("RCLONE_DOWNLOAD_FLAGS", "")
if len(RCLONE_DOWNLOAD_FLAGS) == 0:
    RCLONE_DOWNLOAD_FLAGS = ""

SERVER_SIDE = environ.get("SERVER_SIDE", "")
SERVER_SIDE = SERVER_SIDE.lower() == "true"

CMD_INDEX = environ.get("CMD_INDEX", "")

RSS_CHAT_ID = environ.get("RSS_CHAT_ID", "")
RSS_CHAT_ID = "" if len(RSS_CHAT_ID) == 0 else int(RSS_CHAT_ID)

RSS_DELAY = environ.get("RSS_DELAY", "")
RSS_DELAY = 900 if len(RSS_DELAY) == 0 else int(RSS_DELAY)

QB_BASE_URL = environ.get("QB_BASE_URL", "").rstrip("/")
if len(QB_BASE_URL) == 0:
    LOGGER.warning("QB_BASE_URL not provided!")
    QB_BASE_URL = ""

QB_SERVER_PORT = environ.get("QB_SERVER_PORT", "")
if len(QB_SERVER_PORT) == 0:
    QB_SERVER_PORT = 80

UPSTREAM_REPO = environ.get("UPSTREAM_REPO", "")
if len(UPSTREAM_REPO) == 0:
    UPSTREAM_REPO = ""

UPSTREAM_BRANCH = environ.get("UPSTREAM_BRANCH", "")
if len(UPSTREAM_BRANCH) == 0:
    UPSTREAM_BRANCH = "master"

IS_TEAM_DRIVE = environ.get("IS_TEAM_DRIVE", "")
IS_TEAM_DRIVE = IS_TEAM_DRIVE.lower() == "true"

GDRIVE_FOLDER_ID = environ.get("GDRIVE_FOLDER_ID", "")
if len(GDRIVE_FOLDER_ID) == 0:
    GDRIVE_FOLDER_ID = ""

DOWNLOAD_DIR = environ.get("DOWNLOAD_DIR", "")
if len(DOWNLOAD_DIR) == 0:
    DOWNLOAD_DIR = "/usr/src/app/downloads/"
elif not DOWNLOAD_DIR.endswith("/"):
    DOWNLOAD_DIR = f"{DOWNLOAD_DIR}/"

EXTENSION_FILTER = environ.get("EXTENSION_FILTER", "")
if len(EXTENSION_FILTER) > 0:
    fx = EXTENSION_FILTER.split()
    for x in fx:
        x = x.lstrip(".")
        GLOBAL_EXTENSION_FILTER.append(x.strip().lower())

MEGA_EMAIL = environ.get("MEGA_EMAIL", "")
MEGA_PASSWORD = environ.get("MEGA_PASSWORD", "")
if len(MEGA_EMAIL) == 0 or len(MEGA_PASSWORD) == 0:
    LOGGER.warning("MEGA Credentials not provided!")
    MEGA_EMAIL = ""
    MEGA_PASSWORD = ""

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

IS_PREMIUM_USER = False
app = ""
USER_SESSION_STRING = environ.get("USER_SESSION_STRING", "")
if len(USER_SESSION_STRING) != 0:
    LOGGER.info("Creating Pyrogram client from USER_SESSION_STRING")
    app = tgClient(
        "pyrogram_session",
        api_id=TELEGRAM_API_ID,
        api_hash=TELEGRAM_API_HASH,
        session_string=USER_SESSION_STRING,
        max_concurrent_transmissions=10,
    ).start()
    IS_PREMIUM_USER = app.me.is_premium

TG_MAX_FILE_SIZE = 4194304000 if IS_PREMIUM_USER else 2097152000
LEECH_SPLIT_SIZE = environ.get("LEECH_SPLIT_SIZE", "")
if len(LEECH_SPLIT_SIZE) == 0 or int(LEECH_SPLIT_SIZE) > TG_MAX_FILE_SIZE:
    LEECH_SPLIT_SIZE = TG_MAX_FILE_SIZE
else:
    LEECH_SPLIT_SIZE = int(LEECH_SPLIT_SIZE)

config_dict = {
    "AS_DOCUMENT": AS_DOCUMENT,
    "ALLOWED_CHATS": ALLOWED_CHATS,
    "AUTO_DELETE_MESSAGE_DURATION": AUTO_DELETE_MESSAGE_DURATION,
    "AUTO_MIRROR": AUTO_MIRROR,
    "NO_TASKS_LOGS": NO_TASKS_LOGS,
    "BOT_TOKEN": BOT_TOKEN,
    "BOT_PM": BOT_PM,
    "CMD_INDEX": CMD_INDEX,
    "DATABASE_URL": DATABASE_URL,
    "DEFAULT_OWNER_REMOTE": DEFAULT_OWNER_REMOTE,
    "DEFAULT_GLOBAL_REMOTE": DEFAULT_GLOBAL_REMOTE,
    "DOWNLOAD_DIR": DOWNLOAD_DIR,
    "EQUAL_SPLITS": EQUAL_SPLITS,
    "EXTENSION_FILTER": EXTENSION_FILTER,
    "GDRIVE_FOLDER_ID": GDRIVE_FOLDER_ID,
    "IS_TEAM_DRIVE": IS_TEAM_DRIVE,
    "GD_INDEX_URL": GD_INDEX_URL,
    "LOCAL_MIRROR": LOCAL_MIRROR,
    "LEECH_SPLIT_SIZE": LEECH_SPLIT_SIZE,
    "LEECH_LOG": LEECH_LOG,
    "MEGA_EMAIL": MEGA_EMAIL,
    "MEGA_PASSWORD": MEGA_PASSWORD,
    "MULTI_REMOTE_UP": MULTI_REMOTE_UP,
    "MULTI_RCLONE_CONFIG": MULTI_RCLONE_CONFIG,
    "OWNER_ID": OWNER_ID,
    "PARALLEL_TASKS": PARALLEL_TASKS,
    "QB_BASE_URL": QB_BASE_URL,
    "QB_SERVER_PORT": QB_SERVER_PORT,
    "RCLONE_COPY_FLAGS": RCLONE_COPY_FLAGS,
    "RCLONE_UPLOAD_FLAGS": RCLONE_UPLOAD_FLAGS,
    "RCLONE_DOWNLOAD_FLAGS": RCLONE_DOWNLOAD_FLAGS,
    "REMOTE_SELECTION": REMOTE_SELECTION,
    "RSS_CHAT_ID": RSS_CHAT_ID,
    "RSS_DELAY": RSS_DELAY,
    "RC_INDEX_URL": RC_INDEX_URL,
    "RC_INDEX_PORT": RC_INDEX_PORT,
    "RC_INDEX_USER": RC_INDEX_USER,
    "RC_INDEX_PASS": RC_INDEX_PASS,
    "SEARCH_PLUGINS": SEARCH_PLUGINS,
    "SERVER_SIDE": SERVER_SIDE,
    "SEARCH_API_LINK": SEARCH_API_LINK,
    "SEARCH_LIMIT": SEARCH_LIMIT,
    "SERVICE_ACCOUNTS_REMOTE": SERVICE_ACCOUNTS_REMOTE,
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
    "WEB_PINCODE": WEB_PINCODE,
    "YT_DLP_OPTIONS": YT_DLP_OPTIONS,
}

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
)
Conversation(bot)
bot.start()
botloop = bot.loop

scheduler = AsyncIOScheduler(timezone=str(get_localzone()), event_loop=botloop)
