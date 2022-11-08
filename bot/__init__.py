__version__ = "3.0"
__author__ = "Sam-Max"

from asyncio import Lock
from logging import getLogger, FileHandler, StreamHandler, INFO, basicConfig
from os import environ, path as ospath
from threading import Thread
from time import sleep, time
from sys import exit
from dotenv import load_dotenv
from aria2p import API as ariaAPI, Client as ariaClient
from qbittorrentapi import Client as qbitClient
from subprocess import Popen, run as srun
from megasdkrestclient import MegaSdkRestClient, errors
from pyrogram import Client
from bot.conv_pyrogram import Conversation
from asyncio import get_event_loop

botloop = get_event_loop()

basicConfig(level= INFO,
    format= "%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    handlers=[StreamHandler(), FileHandler("botlog.txt")])

LOGGER = getLogger(__name__)

def getConfig(name: str):
    return environ[name]

def get_client():
    return qbitClient(host="localhost", port=8090)

botUptime = time()
Interval = []
QbInterval = []
GLOBAL_EXTENSION_FILTER = ['.aria2']
aria2_options = {}
qbit_options = {}
DOWNLOAD_DIR = None

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

config_dict = {}

AS_DOC_USERS = set()
AS_MEDIA_USERS = set()

load_dotenv('config.env')

STATUS_LIMIT = environ.get('STATUS_LIMIT', '')
STATUS_LIMIT = '' if len(STATUS_LIMIT) == 0 else int(STATUS_LIMIT)

STATUS_UPDATE_INTERVAL = environ.get('STATUS_UPDATE_INTERVAL', '')
if len(STATUS_UPDATE_INTERVAL) == 0:
    STATUS_UPDATE_INTERVAL = 10
else:
    STATUS_UPDATE_INTERVAL = int(STATUS_UPDATE_INTERVAL)

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

DEFAULT_REMOTE = environ.get('DEFAULT_REMOTE', '')

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

SERVER_SIDE_COPY = environ.get('SERVER_SIDE_COPY', '')
SERVER_SIDE_COPY = SERVER_SIDE_COPY.lower() == 'true' 

aid = environ.get('ALLOWED_CHATS', '')
if len(aid) != 0:
    aid = aid.split()
    ALLOWED_CHATS = {int(_id.strip()) for _id in aid}
else:
    ALLOWED_CHATS= set()

aid = environ.get('SUDO_USERS', '')
if len(aid) != 0:
    aid = aid.split()
    SUDO_USERS = {int(_id.strip()) for _id in aid}
else:
    SUDO_USERS = set()

CMD_INDEX = environ.get('CMD_INDEX', '')

DB_URI = environ.get('DATABASE_URL', '')
if len(DB_URI) == 0:
    DB_URI = None

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

Popen(f"gunicorn web.wserver:app --bind 0.0.0.0:{SERVER_PORT}", shell=True)
srun(["qbittorrent-nox", "-d", "--profile=."])
if not ospath.exists('.netrc'):
    srun(["touch", ".netrc"])
srun(["cp", ".netrc", "/root/.netrc"])
srun(["chmod", "600", ".netrc"])
srun(["chmod", "+x", "aria.sh"])
srun("./aria.sh", shell=True)
sleep(0.5)

aria2 = ariaAPI(
    ariaClient(
        host="http://localhost",
        port=6800,
        secret="",
    )
)

EXTENSION_FILTER = environ.get('EXTENSION_FILTER', '')
if len(EXTENSION_FILTER) > 0:
    fx = EXTENSION_FILTER.split()
    for x in fx:
        GLOBAL_EXTENSION_FILTER.append(x.strip().lower())

try:
    TELEGRAM_API_ID = int(getConfig("TELEGRAM_API_ID"))
    TELEGRAM_API_HASH = getConfig("TELEGRAM_API_HASH")
    BOT_TOKEN = getConfig("BOT_TOKEN")
    OWNER_ID= int(getConfig('OWNER_ID'))
except:
    LOGGER.error("One or more env variables missing! Exiting now")
    exit(1)

def aria2c_init():
    try:
        LOGGER.info("Initializing Aria2c")
        link = "https://linuxmint.com/torrents/lmde-5-cinnamon-64bit.iso.torrent"
        dire = DOWNLOAD_DIR.rstrip("/")
        aria2.add_uris([link], {'dir': dire})
        sleep(3)
        downloads = aria2.get_downloads()
        sleep(20)
        for download in downloads:
            aria2.remove([download], force=True, files=True)
    except Exception as e:
        LOGGER.error(f"Aria2c initializing error: {e}")
Thread(target=aria2c_init).start()
sleep(1.5)
    
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

#---------------------------

bot = Client(name="pyrogram", api_id=TELEGRAM_API_ID, api_hash=TELEGRAM_API_HASH, bot_token=BOT_TOKEN)
Conversation(bot) 
try:
    bot.start()
    LOGGER.info("Pyrogram client created")
except Exception as e:
    print(e)
    exit(1)

#---------------------------

RSS_USER_SESSION_STRING = environ.get('RSS_USER_SESSION_STRING', '')
if len(RSS_USER_SESSION_STRING) == 0:
    rss_session = None
else:
    LOGGER.info("Creating client from RSS_USER_SESSION_STRING")
    rss_session = Client(name='rss_session', api_id=TELEGRAM_API_ID, api_hash=TELEGRAM_API_HASH, session_string=RSS_USER_SESSION_STRING, no_updates=True)

#---------------------------
IS_PREMIUM_USER = False
USER_SESSION_STRING = environ.get('USER_SESSION_STRING', '')
if len(USER_SESSION_STRING) == 0:
    app = None
else:
    LOGGER.info("Pyrogram client created from USER_SESSION_STRING")
    app = Client(name="pyrogram_session", api_id=TELEGRAM_API_ID, api_hash=TELEGRAM_API_HASH, session_string=USER_SESSION_STRING)
    with app:
        IS_PREMIUM_USER = app.me.is_premium

if app is not None:
    try:
        app.start()
    except Exception as e:
        print(e)
        exit(1)

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
                   'CMD_INDEX': CMD_INDEX,
                   'DUMP_CHAT': DUMP_CHAT,
                   'DEFAULT_REMOTE': DEFAULT_REMOTE,
                   'EQUAL_SPLITS': EQUAL_SPLITS,
                   'EXTENSION_FILTER': EXTENSION_FILTER,
                   'GDRIVE_FOLDER_ID': GDRIVE_FOLDER_ID,
                   'IS_TEAM_DRIVE': IS_TEAM_DRIVE,
                   'LEECH_SPLIT_SIZE': LEECH_SPLIT_SIZE,
                   'MEGA_API_KEY': MEGA_API_KEY,
                   'MEGA_EMAIL_ID': MEGA_EMAIL_ID,
                   'MEGA_PASSWORD': MEGA_PASSWORD,
                   'MULTI_RCLONE_CONFIG': MULTI_RCLONE_CONFIG, 
                   'SERVER_SIDE_COPY': SERVER_SIDE_COPY,
                   'RSS_USER_SESSION_STRING': RSS_USER_SESSION_STRING,
                   'RSS_CHAT_ID': RSS_CHAT_ID,
                   'RSS_COMMAND': RSS_COMMAND,
                   'RSS_DELAY': RSS_DELAY,
                   'SEARCH_API_LINK': SEARCH_API_LINK,
                   'SEARCH_LIMIT': SEARCH_LIMIT,
                   'SERVER_PORT': SERVER_PORT,
                   'SERVICE_ACCOUNTS_REMOTE': SERVICE_ACCOUNTS_REMOTE,
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

aria2c_global = ['bt-max-open-files', 'download-result', 'keep-unfinished-download-result', 'log', 'log-level',
                 'max-concurrent-downloads', 'max-download-result', 'max-overall-download-limit', 'save-session',
                 'max-overall-upload-limit', 'optimize-concurrent-downloads', 'save-cookies', 'server-stat-of']
                                    
if not aria2_options:
    aria2_options = aria2.client.get_global_option()
    del aria2_options['dir']
    del aria2_options['max-download-limit']
    del aria2_options['lowest-speed-limit']

qb_client = get_client()
if not qbit_options:
    qbit_options = dict(qb_client.app_preferences())
    del qbit_options['scan_dirs']
else:
    qb_client.app_set_preferences(qbit_options)