__version__ = "2.0"
__author__ = "Sam-Max"

from logging import getLogger, FileHandler, StreamHandler, INFO, basicConfig
import os
from time import sleep, time
import sys
import time
from os import environ
from dotenv import load_dotenv
from aria2p import API as ariaAPI, Client as ariaClient
from qbittorrentapi import Client as qbitClient
from bot.utils.load_rclone import load_rclone
from subprocess import Popen, run as srun
from bot.client import RcloneTgClient
from bot.core.var_holder import VarHolder
from megasdkrestclient import MegaSdkRestClient, errors
from pyrogram import Client
from convopyro import Conversation

basicConfig(level= INFO,
    format= "%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    handlers=[StreamHandler(), FileHandler("botlog.txt")])

LOGGER = getLogger(__name__)

def getConfig(name: str):
    return environ[name]

def get_client():
    return qbitClient(host="localhost", port=8090)

uptime = time.time()

GLOBAL_RCLONE= set()
GLOBAL_TG_DOWNLOADER= set()
GLOBAL_QBIT= set()

SessionVars = VarHolder()

load_dotenv('config.env', override=True)
load_rclone()

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
    TORRENT_TIMEOUT = getConfig('TORRENT_TIMEOUT')
    if len(TORRENT_TIMEOUT) == 0:
        raise KeyError
    TORRENT_TIMEOUT = int(TORRENT_TIMEOUT)
except:
    TORRENT_TIMEOUT = None

try:
    LOGGER.info("Initializing Aria2c")
    link = "https://linuxmint.com/torrents/lmde-5-cinnamon-64bit.iso.torrent"
    dire = os.path.join(os.getcwd(), "Downloads")
    aria2.add_uris([link], {'dir': dire})
    sleep(3)
    downloads = aria2.get_downloads()
    sleep(20)
    for download in downloads:
        aria2.remove([download], force=True, files=True)
except Exception as e:
    LOGGER.error(f"Aria2c initializing error: {e}")
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

try:
    API_ID = int(getConfig("API_ID"))
    API_HASH = getConfig("API_HASH")
    BOT_TOKEN = getConfig("BOT_TOKEN")
except:
    LOGGER.error("One or more env variables missing! Exiting now")
    exit(1)

#---------------------------

bot = RcloneTgClient("bot", API_ID, API_HASH, timeout=20, retry_delay=3,
                        request_retries=10, connection_retries=10)

try:
    bot.start(bot_token=BOT_TOKEN)
    LOGGER.info("Telethon client created.")
except Exception as e:
    print(e)
    sys.exit(1)

#---------------------------

Bot = Client("pyrogram", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
Conversation(Bot)  
try:
    Bot.start()
    LOGGER.info("pyro Bot client created")
    bot.pyro = Bot
except Exception as e:
    print(e)
    sys.exit(1)

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
        LOGGER.info("pyrogram_session client created")
    except Exception as e:
        print(e)
        sys.exit(1)

try:
    TG_MAX_FILE_SIZE= 4194304000 if IS_PREMIUM_USER else 2097152000
    TG_SPLIT_SIZE = getConfig('TG_SPLIT_SIZE')
    if len(TG_SPLIT_SIZE) == 0 or int(TG_SPLIT_SIZE) > TG_MAX_FILE_SIZE:
        raise KeyError
    TG_SPLIT_SIZE = int(TG_SPLIT_SIZE)
except:
    TG_SPLIT_SIZE = TG_MAX_FILE_SIZE









