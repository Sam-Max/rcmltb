__version__ = "3.1"
__author__ = "Sam-Max"

from asyncio import Lock
from asyncio import Queue
from logging import getLogger, FileHandler, StreamHandler, INFO, basicConfig
from os import environ, remove as osremove, path as ospath
from threading import Thread
from time import sleep, time
from sys import exit
from dotenv import load_dotenv
from pymongo import MongoClient
from aria2p import API as ariaAPI, Client as ariaClient
from qbittorrentapi import Client as qbitClient
from subprocess import Popen, run as srun
from megasdkrestclient import MegaSdkRestClient, errors
from pyrogram import Client
from bot.conv_pyrogram import Conversation
from asyncio import get_event_loop

botloop = get_event_loop()

botUptime = time()

LOGGER = getLogger(__name__)

load_dotenv('config.env', override=True)

basicConfig(level= INFO,
    format= "%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    handlers=[StreamHandler(), FileHandler("botlog.txt")])

def get_client():
    return qbitClient(host="localhost", port=8090)

Interval = []
QbInterval = []
GLOBAL_EXTENSION_FILTER = ['.aria2']
user_data = {}
aria2_options = {}
qbit_options = {}

status_dict_lock = Lock()
status_reply_dict_lock = Lock()

# Key: update.message.id
# Value: An object of Status
status_dict = {}

# Key: update.chat.id
# Value: telegram.Message
status_reply_dict = {}

# key: rss_title
# value: [rss_feed, last_link, last_title, filter]
rss_dict = {}

m_queue = Queue()
l_queue = Queue()

BOT_TOKEN = environ.get('BOT_TOKEN', '')
if len(BOT_TOKEN) == 0:
    LOGGER.error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

bot_id = int(BOT_TOKEN.split(':', 1)[0])

DATABASE_URL = environ.get('DATABASE_URL', '')
if len(DATABASE_URL) == 0:
    DATABASE_URL = None

if DATABASE_URL:
    conn = MongoClient(DATABASE_URL)
    db = conn.rcmltb
    if config_dict := db.settings.config.find_one({'_id': bot_id}):  #return config dict (all env vars)
        del config_dict['_id']
        for key, value in config_dict.items():
            environ[key] = str(value)
    if pf_dict := db.settings.files.find_one({'_id': bot_id}):
        del pf_dict['_id']
        for key, value in pf_dict.items():
            if value:
                file_ = key.replace('__', '.')
                with open(file_, 'wb+') as f:
                    f.write(value)
    if a2c_options := db.settings.aria2c.find_one({'_id': bot_id}):
        del a2c_options['_id']
        aria2_options = a2c_options
    if qbit_opt := db.settings.qbittorrent.find_one({'_id': bot_id}):
        del qbit_opt['_id']
        qbit_options = qbit_opt
    conn.close()
    BOT_TOKEN = environ.get('BOT_TOKEN', '')
    bot_id = int(BOT_TOKEN.split(':', 1)[0])
    DATABASE_URL = environ.get('DATABASE_URL', '')
else:
    config_dict = {}

OWNER_ID = environ.get('OWNER_ID', '')
if len(OWNER_ID) == 0:
    LOGGER.error("OWNER_ID variable is missing! Exiting now")
    exit(1)
else:
    OWNER_ID = int(OWNER_ID)

TELEGRAM_API_ID = environ.get('TELEGRAM_API_ID', '')
if len(TELEGRAM_API_ID) == 0:
    LOGGER.error("TELEGRAM_API_ID variable is missing! Exiting now")
    exit(1)
else:
    TELEGRAM_API_ID = int(TELEGRAM_API_ID)

TELEGRAM_API_HASH = environ.get('TELEGRAM_API_HASH', '')
if len(TELEGRAM_API_HASH) == 0:
    LOGGER.error("TELEGRAM_API_HASH variable is missing! Exiting now")
    exit(1)

ALLOWED_CHATS = environ.get('ALLOWED_CHATS', '')
if len(ALLOWED_CHATS) != 0:
    aid = ALLOWED_CHATS.split()
    for id_ in aid:
        user_data[int(id_.strip())] = {'is_auth': True}

SUDO_USERS = environ.get('SUDO_USERS', '')
if len(SUDO_USERS) != 0:
    aid = SUDO_USERS.split()
    for id_ in aid:
        user_data[int(id_.strip())] = {'is_sudo': True}

STATUS_LIMIT = environ.get('STATUS_LIMIT', '')
STATUS_LIMIT = '' if len(STATUS_LIMIT) == 0 else int(STATUS_LIMIT)

STATUS_UPDATE_INTERVAL = environ.get('STATUS_UPDATE_INTERVAL', '')
if len(STATUS_UPDATE_INTERVAL) == 0:
    STATUS_UPDATE_INTERVAL = 10
else:
    STATUS_UPDATE_INTERVAL = int(STATUS_UPDATE_INTERVAL)

PARALLEL_TASKS = environ.get('PARALLEL_TASKS', '')
PARALLEL_TASKS = "" if len(PARALLEL_TASKS) == 0 else int(PARALLEL_TASKS)

AS_DOCUMENT = environ.get('AS_DOCUMENT', '')
AS_DOCUMENT = AS_DOCUMENT.lower() == 'true'

AUTO_MIRROR= environ.get('AUTO_MIRROR', '')  
AUTO_MIRROR= AUTO_MIRROR.lower() == 'true'

DUMP_CHAT = environ.get('DUMP_CHAT', '')
DUMP_CHAT= '' if len(DUMP_CHAT) == 0 else int(DUMP_CHAT)

UPTOBOX_TOKEN = environ.get('UPTOBOX_TOKEN', '')
if len(UPTOBOX_TOKEN) == 0:
    UPTOBOX_TOKEN = ''

SEARCH_API_LINK = environ.get('SEARCH_API_LINK', '').rstrip("/")
if len(SEARCH_API_LINK) == 0:
    SEARCH_API_LINK = ''

SEARCH_LIMIT = environ.get('SEARCH_LIMIT', '')
SEARCH_LIMIT= 0 if len(SEARCH_LIMIT) == 0 else int(SEARCH_LIMIT)
    
SEARCH_PLUGINS = environ.get('SEARCH_PLUGINS', '')
if len(SEARCH_PLUGINS) == 0:
    SEARCH_PLUGINS = ''

TORRENT_TIMEOUT = environ.get('TORRENT_TIMEOUT', '')
TORRENT_TIMEOUT= '' if len(TORRENT_TIMEOUT) == 0 else int(TORRENT_TIMEOUT)

WEB_PINCODE = environ.get('WEB_PINCODE', '')
WEB_PINCODE = WEB_PINCODE.lower() == 'true'

EQUAL_SPLITS = environ.get('EQUAL_SPLITS', '')
EQUAL_SPLITS = EQUAL_SPLITS.lower() == 'true'

DEFAULT_OWNER_REMOTE = environ.get('DEFAULT_OWNER_REMOTE', '')

DEFAULT_GLOBAL_REMOTE = environ.get('DEFAULT_GLOBAL_REMOTE', '')

SERVE_USER = environ.get('SERVE_USER', '')
SERVE_USER = 'admin' if len(SERVE_USER) == 0 else SERVE_USER

SERVE_PASS= environ.get('SERVE_PASS', '')
SERVE_PASS = 'admin' if len(SERVE_PASS) == 0 else SERVE_PASS

SERVE_IP = environ.get('SERVE_IP', '')
SERVE_IP = '' if len(SERVE_IP) == 0 else SERVE_IP

SERVE_PORT = environ.get('SERVE_PORT', '')
SERVE_PORT= 8080 if len(SERVE_PORT) == 0 else int(SERVE_PORT)

USE_SERVICE_ACCOUNTS = environ.get('USE_SERVICE_ACCOUNTS', '')
USE_SERVICE_ACCOUNTS = USE_SERVICE_ACCOUNTS.lower() == 'true'

SERVICE_ACCOUNTS_REMOTE = environ.get('SERVICE_ACCOUNTS_REMOTE', '')

MULTI_RCLONE_CONFIG = environ.get('MULTI_RCLONE_CONFIG', '')
MULTI_RCLONE_CONFIG = MULTI_RCLONE_CONFIG.lower() == 'true' 

SERVER_SIDE = environ.get('SERVER_SIDE', '')
SERVER_SIDE = SERVER_SIDE.lower() == 'true' 

CMD_INDEX = environ.get('CMD_INDEX', '')

RSS_CHAT_ID = environ.get('RSS_CHAT_ID', '')
RSS_CHAT_ID = '' if len(RSS_CHAT_ID) == 0 else int(RSS_CHAT_ID)

RSS_DELAY = environ.get('RSS_DELAY', '')
RSS_DELAY = 900 if len(RSS_DELAY) == 0 else int(RSS_DELAY)

RSS_COMMAND = environ.get('RSS_COMMAND', '')
if len(RSS_COMMAND) == 0:
    RSS_COMMAND = ''

BASE_URL = environ.get('BASE_URL', '').rstrip("/")
if len(BASE_URL) == 0:
    LOGGER.warning('BASE_URL not provided!')
    BASE_URL = ''

SERVER_PORT = environ.get('SERVER_PORT', '')
if len(SERVER_PORT) == 0:
    SERVER_PORT = 80

UPSTREAM_REPO = environ.get('UPSTREAM_REPO', '')
if len(UPSTREAM_REPO) == 0:
   UPSTREAM_REPO = ''

UPSTREAM_BRANCH = environ.get('UPSTREAM_BRANCH', '')
if len(UPSTREAM_BRANCH) == 0:
    UPSTREAM_BRANCH = 'master'

IS_TEAM_DRIVE = environ.get('IS_TEAM_DRIVE', '')
IS_TEAM_DRIVE = IS_TEAM_DRIVE.lower() == 'true'   

GDRIVE_FOLDER_ID = environ.get('GDRIVE_FOLDER_ID', '')
if len(GDRIVE_FOLDER_ID) == 0:
    GDRIVE_FOLDER_ID = ''

DOWNLOAD_DIR = environ.get('DOWNLOAD_DIR', '')
if len(DOWNLOAD_DIR) == 0:
    DOWNLOAD_DIR = '/usr/src/app/downloads/'
else:
    if not DOWNLOAD_DIR.endswith("/"):
        DOWNLOAD_DIR = DOWNLOAD_DIR + '/'

EXTENSION_FILTER = environ.get('EXTENSION_FILTER', '')
if len(EXTENSION_FILTER) > 0:
    fx = EXTENSION_FILTER.split()
    for x in fx:
        GLOBAL_EXTENSION_FILTER.append(x.strip().lower())

MEGA_API_KEY = environ.get('MEGA_API_KEY', '')
if len(MEGA_API_KEY) == 0:
    LOGGER.warning('MEGA_API_KEY not provided!')
    MEGA_API_KEY = ''

MEGA_EMAIL_ID = environ.get('MEGA_EMAIL_ID', '')
MEGA_PASSWORD = environ.get('MEGA_PASSWORD', '')
if len(MEGA_EMAIL_ID) == 0 or len(MEGA_PASSWORD) == 0:
    LOGGER.warning('MEGA Credentials not provided!')
    MEGA_EMAIL_ID = ''
    MEGA_PASSWORD = ''

bot = Client(name="pyrogram", api_id=TELEGRAM_API_ID, api_hash=TELEGRAM_API_HASH, bot_token=BOT_TOKEN)
Conversation(bot) 
LOGGER.info("Creating Pyrogram client")

IS_PREMIUM_USER = False
USER_SESSION_STRING = environ.get('USER_SESSION_STRING', '')
if len(USER_SESSION_STRING) == 0:
    app = None
else:
    LOGGER.info("Creating Pyrogram client from USER_SESSION_STRING")
    app = Client(name="pyrogram_session", api_id=TELEGRAM_API_ID, api_hash=TELEGRAM_API_HASH, session_string=USER_SESSION_STRING)
    with app:
        IS_PREMIUM_USER = app.me.is_premium

RSS_USER_SESSION_STRING = environ.get('RSS_USER_SESSION_STRING', '')
if len(RSS_USER_SESSION_STRING) == 0:
    rss_session = None
else:
    LOGGER.info("Creating client from RSS_USER_SESSION_STRING")
    rss_session = Client(name='rss_session', api_id=TELEGRAM_API_ID, api_hash=TELEGRAM_API_HASH, session_string=RSS_USER_SESSION_STRING, no_updates=True)

TG_MAX_FILE_SIZE= 4194304000 if IS_PREMIUM_USER else 2097152000
LEECH_SPLIT_SIZE = environ.get('LEECH_SPLIT_SIZE', '')
if len(LEECH_SPLIT_SIZE) == 0 or int(LEECH_SPLIT_SIZE) > TG_MAX_FILE_SIZE:
    LEECH_SPLIT_SIZE = TG_MAX_FILE_SIZE
else:
    LEECH_SPLIT_SIZE = int(LEECH_SPLIT_SIZE)

if not config_dict:
    config_dict = {'AS_DOCUMENT': AS_DOCUMENT,
                   'ALLOWED_CHATS': ALLOWED_CHATS,
                   'AUTO_MIRROR': AUTO_MIRROR,
                   'BASE_URL': BASE_URL,
                   'BOT_TOKEN': BOT_TOKEN,
                   'CMD_INDEX': CMD_INDEX,
                   'DATABASE_URL': DATABASE_URL,
                   'DUMP_CHAT': DUMP_CHAT,
                   'DEFAULT_OWNER_REMOTE': DEFAULT_OWNER_REMOTE,
                   'DEFAULT_GLOBAL_REMOTE':DEFAULT_GLOBAL_REMOTE,
                   'EQUAL_SPLITS': EQUAL_SPLITS,
                   'EXTENSION_FILTER': EXTENSION_FILTER,
                   'GDRIVE_FOLDER_ID': GDRIVE_FOLDER_ID,
                   'IS_TEAM_DRIVE': IS_TEAM_DRIVE,
                   'LEECH_SPLIT_SIZE': LEECH_SPLIT_SIZE,
                   'MEGA_API_KEY': MEGA_API_KEY,
                   'MEGA_EMAIL_ID': MEGA_EMAIL_ID,
                   'MEGA_PASSWORD': MEGA_PASSWORD,
                   'MULTI_RCLONE_CONFIG': MULTI_RCLONE_CONFIG, 
                   'OWNER_ID': OWNER_ID,
                   'PARALLEL_TASKS': PARALLEL_TASKS,
                   'RSS_USER_SESSION_STRING': RSS_USER_SESSION_STRING,
                   'RSS_CHAT_ID': RSS_CHAT_ID,
                   'RSS_COMMAND': RSS_COMMAND,
                   'RSS_DELAY': RSS_DELAY,
                   'SERVER_SIDE': SERVER_SIDE,
                   'SEARCH_API_LINK': SEARCH_API_LINK,
                   'SEARCH_LIMIT': SEARCH_LIMIT,
                   'SERVER_PORT': SERVER_PORT,
                   'SERVICE_ACCOUNTS_REMOTE': SERVICE_ACCOUNTS_REMOTE,
                   'SERVE_USER':SERVE_USER,
                   'SERVE_PASS': SERVE_PASS,
                   'SERVE_IP': SERVE_IP,
                   'SERVE_PORT': SERVE_PORT,
                   'STATUS_LIMIT': STATUS_LIMIT,
                   'STATUS_UPDATE_INTERVAL': STATUS_UPDATE_INTERVAL,
                   'SUDO_USERS': SUDO_USERS,
                   'TELEGRAM_API_ID': TELEGRAM_API_ID,
                   'TELEGRAM_API_HASH': TELEGRAM_API_HASH,
                   'TORRENT_TIMEOUT': TORRENT_TIMEOUT,
                   'UPSTREAM_REPO': UPSTREAM_REPO,
                   'UPSTREAM_BRANCH': UPSTREAM_BRANCH,
                   'UPTOBOX_TOKEN': UPTOBOX_TOKEN,
                   'USER_SESSION_STRING': USER_SESSION_STRING,
                   'USE_SERVICE_ACCOUNTS': USE_SERVICE_ACCOUNTS,
                   'WEB_PINCODE': WEB_PINCODE}

Popen(f"gunicorn web.wserver:app --bind 0.0.0.0:{SERVER_PORT}", shell=True)
srun(["qbittorrent-nox", "-d", "--profile=."])
if not ospath.exists('.netrc'):
    srun(["touch", ".netrc"])
srun(["cp", ".netrc", "/root/.netrc"])
srun(["chmod", "600", ".netrc"])
srun(["chmod", "+x", "aria.sh"])
srun("./aria.sh", shell=True)
sleep(0.5)
if ospath.exists('accounts.zip'):
    if ospath.exists('accounts'):
        srun(["rm", "-rf", "accounts"])
    srun(["unzip", "-q", "-o", "accounts.zip", "-x", "accounts/emails.txt"])
    srun(["chmod", "-R", "777", "accounts"])
    osremove('accounts.zip')
if not ospath.exists('accounts'):
    config_dict['USE_SERVICE_ACCOUNTS'] = False

if len(MEGA_API_KEY) > 0:
    Popen(["megasdkrest", "--apikey", MEGA_API_KEY])
    sleep(3)
    mega_client = MegaSdkRestClient('http://localhost:6090')
    try:
        if len(MEGA_EMAIL_ID) > 0 and len(MEGA_PASSWORD) > 0:
            try:
                mega_client.login(MEGA_EMAIL_ID, MEGA_PASSWORD)
            except errors.MegaSdkRestClientException as e:
                LOGGER.error(e.message['message'])
                exit(0)
        else:
            LOGGER.info("Mega username and password not provided. Starting mega in anonymous mode!")
    except:
            LOGGER.info("Mega username and password not provided. Starting mega in anonymous mode!")
else:
    sleep(1.5)

aria2 = ariaAPI(ariaClient(host="http://localhost", port=6800, secret=""))

def aria2c_init():
    try:
        LOGGER.info("Initializing Aria2c")
        link = "https://linuxmint.com/torrents/lmde-5-cinnamon-64bit.iso.torrent"
        dire = DOWNLOAD_DIR.rstrip("/")
        aria2.add_uris([link], {'dir': dire})
        sleep(3)
        downloads = aria2.get_downloads()
        sleep(15)
        for download in downloads:
            aria2.remove([download], force=True, files=True)
    except Exception as e:
        LOGGER.error(f"Aria2c initializing error: {e}")
Thread(target=aria2c_init).start()
sleep(1.5)
    
aria2c_global = ['bt-max-open-files', 'download-result', 'keep-unfinished-download-result', 'log', 'log-level',
                 'max-concurrent-downloads', 'max-download-result', 'max-overall-download-limit', 'save-session',
                 'max-overall-upload-limit', 'optimize-concurrent-downloads', 'save-cookies', 'server-stat-of']
                                    
if not aria2_options:
    aria2_options = aria2.client.get_global_option()
    del aria2_options['dir']
    del aria2_options['max-download-limit']
    del aria2_options['lowest-speed-limit']
else:
    a2c_glo = {}
    for op in aria2c_global:
        if op in aria2_options:
            a2c_glo[op] = aria2_options[op]
    aria2.set_global_options(a2c_glo)
   
qb_client = get_client()
if not qbit_options:
    qbit_options = dict(qb_client.app_preferences())
    del qbit_options['listen_port']
    for k in list(qbit_options.keys()):
        if k.startswith('rss'):
            del qbit_options[k]
else:
    qb_opt = {**qbit_options}
    for k, v in list(qb_opt.items()):
        if v in ["", "*"]:
            del qb_opt[k]
    qb_client.app_set_preferences(qb_opt)