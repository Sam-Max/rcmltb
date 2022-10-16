__version__ = "2.0"
__author__ = "Sam-Max"

from asyncio import Lock
from logging import getLogger, FileHandler, StreamHandler, INFO, basicConfig
from os import environ
from json import loads as jsonloads
from requests import get as rget
from threading import Thread
from time import sleep, time
from sys import exit
from dotenv import load_dotenv
from aria2p import API as ariaAPI, Client as ariaClient
from qbittorrentapi import Client as qbitClient
from subprocess import Popen, run as srun
from megasdkrestclient import MegaSdkRestClient, errors
from pyrogram import Client
from telethon import TelegramClient
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
EXTENSION_FILTER = {'.aria2'}
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

rclone_user_dict = {}

AS_DOC_USERS = set()
AS_MEDIA_USERS = set()

load_dotenv('config.env')

EDIT_SLEEP_SECS = environ.get('EDIT_SLEEP_SECS', '')  
EDIT_SLEEP_SECS = 8 if len(EDIT_SLEEP_SECS) == 0 else int(EDIT_SLEEP_SECS)

STATUS_LIMIT = environ.get('STATUS_LIMIT', '')
STATUS_LIMIT = None if len(STATUS_LIMIT) == 0 else int(STATUS_LIMIT)

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
DUMP_CHAT= None if len(DUMP_CHAT) == 0 else int(DUMP_CHAT)

UPTOBOX_TOKEN = environ.get('UPTOBOX_TOKEN', '')
if len(UPTOBOX_TOKEN) == 0:
    UPTOBOX_TOKEN = None

SEARCH_API_LINK = environ.get('SEARCH_API_LINK', '').rstrip("/")
if len(SEARCH_API_LINK) == 0:
    SEARCH_API_LINK = None

SEARCH_LIMIT = environ.get('SEARCH_LIMIT', '')
SEARCH_LIMIT= 0 if len(SEARCH_LIMIT) == 0 else int(SEARCH_LIMIT)
    
SEARCH_PLUGINS = environ.get('SEARCH_PLUGINS', '')
SEARCH_PLUGINS= None if len(SEARCH_PLUGINS) == 0 else jsonloads(SEARCH_PLUGINS)

TORRENT_TIMEOUT = environ.get('TORRENT_TIMEOUT', '')
TORRENT_TIMEOUT= None if len(TORRENT_TIMEOUT) == 0 else int(TORRENT_TIMEOUT)

WEB_PINCODE = environ.get('WEB_PINCODE', '')
WEB_PINCODE = WEB_PINCODE.lower() == 'true'

EQUAL_SPLITS = environ.get('EQUAL_SPLITS', '')
EQUAL_SPLITS = EQUAL_SPLITS.lower() == 'true'

DEFAULT_DRIVE = environ.get('DEFAULT_DRIVE', '')

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

YT_COOKIES_URL = environ.get('YT_COOKIES_URL', '')
if len(YT_COOKIES_URL) != 0:
    try:
        res = rget(YT_COOKIES_URL)
        if res.status_code == 200:
            with open('cookies.txt', 'wb+') as f:
                f.write(res.content)
        else:
            LOGGER.error(f"Failed to download cookies.txt, link got HTTP response: {res.status_code}")
    except Exception as e:
        LOGGER.error(f"YT_COOKIES_URL: {e}")

DB_URI = environ.get('DATABASE_URL', '')
if len(DB_URI) == 0:
    DB_URI = None

RSS_CHAT_ID = environ.get('RSS_CHAT_ID', '')
RSS_CHAT_ID = None if len(RSS_CHAT_ID) == 0 else int(RSS_CHAT_ID)

RSS_DELAY = environ.get('RSS_DELAY', '')
RSS_DELAY = 900 if len(RSS_DELAY) == 0 else int(RSS_DELAY)

RSS_COMMAND = environ.get('RSS_COMMAND', '')
if len(RSS_COMMAND) == 0:
    RSS_COMMAND = None

BASE_URL = environ.get('BASE_URL_OF_BOT', '')
if len(BASE_URL) == 0:
    LOGGER.warning('BASE_URL_OF_BOT not provided!')
    BASE_URL = None

SERVER_PORT = environ.get('SERVER_PORT', '')
if len(SERVER_PORT) == 0:
    SERVER_PORT = 80

IS_TEAM_DRIVE = environ.get('IS_TEAM_DRIVE', '')
IS_TEAM_DRIVE = IS_TEAM_DRIVE.lower() == 'true'    

PARENT_ID = environ.get('GDRIVE_FOLDER_ID', '')
if len(PARENT_ID) == 0:
    PARENT_ID = None

DOWNLOAD_DIR = environ.get('DOWNLOAD_DIR', '')
if len(DOWNLOAD_DIR) == 0:
    DOWNLOAD_DIR = '/usr/src/app/downloads/'
else:
    if not DOWNLOAD_DIR.endswith("/"):
        DOWNLOAD_DIR = DOWNLOAD_DIR + '/'

Popen(f"gunicorn web.wserver:app --bind 0.0.0.0:{SERVER_PORT}", shell=True)
srun(["qbittorrent-nox", "-d", "--profile=."])
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

fx = environ.get('EXTENSION_FILTER', '')
if len(fx) > 0:
    fx = fx.split()
    for x in fx:
        EXTENSION_FILTER.add(x.strip().lower())

try:
    API_ID = int(getConfig("API_ID"))
    API_HASH = getConfig("API_HASH")
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
    
MEGA_KEY = environ.get('MEGA_API_KEY', '')
if len(MEGA_KEY) == 0:
    LOGGER.warning('MEGA_API_KEY not provided!')
    MEGA_KEY = None

if MEGA_KEY is not None:
    Popen(["megasdkrest", "--apikey", MEGA_KEY])
    sleep(3)
    mega_client = MegaSdkRestClient('http://localhost:6090')
    try:
        MEGA_USERNAME = getConfig('MEGA_EMAIL_ID')
        MEGA_PASSWORD = getConfig('MEGA_PASSWORD')
        if len(MEGA_USERNAME) > 0 and len(MEGA_PASSWORD) > 0:
            try:
                mega_client.login(MEGA_USERNAME, MEGA_PASSWORD)
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

bot = TelegramClient("telethon", API_ID, API_HASH, timeout=20, retry_delay=3,
                        request_retries=10, connection_retries=10)
try:
    bot.start(bot_token=BOT_TOKEN)
    LOGGER.info("Telethon client created.")
except Exception as e:
    print(e)
    exit(1)

#---------------------------

Bot = Client("pyrogram", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
Conversation(Bot) 
try:
    Bot.start()
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
    rss_session = Client(name='rss_session', api_id=API_ID, api_hash=API_HASH, session_string=RSS_USER_SESSION_STRING, no_updates=True)

#---------------------------
IS_PREMIUM_USER = False
USER_SESSION_STRING = environ.get('USER_SESSION_STRING', '')
if len(USER_SESSION_STRING) == 0:
    app = None
else:
    LOGGER.info("Pyrogram client created from USER_SESSION_STRING")
    app = Client(name="pyrogram_session", api_id=API_ID, api_hash=API_HASH, session_string=USER_SESSION_STRING)
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
