__version__ = "2.0"
__author__ = "Sam-Max"

from asyncio import Lock
from logging import getLogger, FileHandler, StreamHandler, INFO, basicConfig
from os import environ
from json import loads as jsonloads
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

basicConfig(level= INFO,
    format= "%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    handlers=[StreamHandler(), FileHandler("botlog.txt")])

LOGGER = getLogger(__name__)

def getConfig(name: str):
    return environ[name]

def get_client():
    return qbitClient(host="localhost", port=8090)

botUptime = time()

DOWNLOAD_DIR = None
ALLOWED_CHATS= set()
ALLOWED_USERS= set()

status_dict_lock = Lock()
status_reply_dict_lock = Lock()

# Key: update.message.id
# Value: An object of Status
status_dict = {}

# Key: update.chat.id
# Value: telegram.Message
status_reply_dict = {}

AS_DOC_USERS = set()
AS_MEDIA_USERS = set()

load_dotenv('config.env', override=True)

try:
    EDIT_SLEEP_SECS = getConfig('EDIT_SLEEP_SECS')
    if len(EDIT_SLEEP_SECS) == 0:
        raise KeyError
    EDIT_SLEEP_SECS = int(EDIT_SLEEP_SECS)
except:
    EDIT_SLEEP_SECS = 10

try:
    AS_DOCUMENT = getConfig('AS_DOCUMENT')
    AS_DOCUMENT = AS_DOCUMENT.lower() == 'true'
except:
    AS_DOCUMENT = False

try:
    DUMP_CHAT = getConfig('DUMP_CHAT')
    if len(DUMP_CHAT) == 0:
        raise KeyError
    DUMP_CHAT = int(DUMP_CHAT)
except:
    DUMP_CHAT = None

try:
    UPTOBOX_TOKEN = getConfig('UPTOBOX_TOKEN')
    if len(UPTOBOX_TOKEN) == 0:
        raise KeyError
except:
    UPTOBOX_TOKEN = None

try:
    SEARCH_API_LINK = getConfig('SEARCH_API_LINK').rstrip("/")
    if len(SEARCH_API_LINK) == 0:
        raise KeyError
except:
    SEARCH_API_LINK = None
try:
    SEARCH_LIMIT = getConfig('SEARCH_LIMIT')
    if len(SEARCH_LIMIT) == 0:
        raise KeyError
    SEARCH_LIMIT = int(SEARCH_LIMIT)
except:
    SEARCH_LIMIT = 0
    
try:
    SEARCH_PLUGINS = getConfig('SEARCH_PLUGINS')
    if len(SEARCH_PLUGINS) == 0:
        raise KeyError
    SEARCH_PLUGINS = jsonloads(SEARCH_PLUGINS)
except:
    SEARCH_PLUGINS = None    

try:
    TORRENT_TIMEOUT = getConfig('TORRENT_TIMEOUT')
    if len(TORRENT_TIMEOUT) == 0:
        raise KeyError
    TORRENT_TIMEOUT = int(TORRENT_TIMEOUT)
except:
    TORRENT_TIMEOUT = None

try:
    WEB_PINCODE = getConfig('WEB_PINCODE')
    WEB_PINCODE = WEB_PINCODE.lower() == 'true'
except:
    WEB_PINCODE = False

try:
    CMD_INDEX = getConfig('CMD_INDEX')
    if len(CMD_INDEX) == 0:
        raise KeyError
except:
    CMD_INDEX = ''

try:
    BASE_URL = getConfig('BASE_URL_OF_BOT')
    if len(BASE_URL) == 0:
        raise KeyError
except:
    LOGGER.warning('BASE_URL_OF_BOT not provided!')
    BASE_URL = None

try:
    SERVER_PORT = getConfig('SERVER_PORT')
    if len(SERVER_PORT) == 0:
        raise KeyError
except:
    SERVER_PORT = 80

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

try:
    aid = getConfig('ALLOWED_CHATS')
    aid = aid.split()
    for _id in aid:
        ALLOWED_CHATS.add(int(_id.strip()))
except:
    pass

try:
    aid = getConfig('ALLOWED_USERS')
    aid = aid.split()
    for _id in aid:
        ALLOWED_USERS.add(int(_id.strip()))
except:
    pass

try:
    API_ID = int(getConfig("API_ID"))
    API_HASH = getConfig("API_HASH")
    BOT_TOKEN = getConfig("BOT_TOKEN")
    OWNER_ID= int(getConfig('OWNER_ID'))
    DOWNLOAD_DIR = getConfig('DOWNLOAD_DIR')
    if not DOWNLOAD_DIR.endswith("/"):
        DOWNLOAD_DIR = DOWNLOAD_DIR + '/'
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
    
try:
    MEGA_KEY = getConfig('MEGA_API_KEY')
    if len(MEGA_KEY) == 0:
        raise KeyError
except:
    MEGA_KEY = None
    LOGGER.info('MEGA_API_KEY not provided!')

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
    bot.pyro = Bot
except Exception as e:
    print(e)
    exit(1)

#---------------------------
try:
    IS_PREMIUM_USER = False
    USER_SESSION_STRING = getConfig('USER_SESSION_STRING')
    if len(USER_SESSION_STRING) == 0:
        raise KeyError
    app = Client(name="pyrogram_session", api_id=API_ID, api_hash=API_HASH, session_string=USER_SESSION_STRING)
    with app:
        IS_PREMIUM_USER = app.get_me().is_premium
except Exception as e:
    LOGGER.info(e)
    app = None

if app is not None:
    try:
        app.start()
        LOGGER.info("Pyrogram Session client created")
        bot.pyro = app
    except Exception as e:
        print(e)
        exit(1)

try:
    TG_MAX_FILE_SIZE= 4194304000 if IS_PREMIUM_USER else 2097152000
    TG_SPLIT_SIZE = getConfig('TG_SPLIT_SIZE')
    if len(TG_SPLIT_SIZE) == 0 or int(TG_SPLIT_SIZE) > TG_MAX_FILE_SIZE:
        raise KeyError
    TG_SPLIT_SIZE = int(TG_SPLIT_SIZE)
except:
    TG_SPLIT_SIZE = TG_MAX_FILE_SIZE
