__version__ = "2.0"
__author__ = "Sam-Max"

from logging import getLogger, FileHandler, StreamHandler, INFO, basicConfig
from time import sleep, time
import sys
import time
from os import environ
from dotenv import load_dotenv
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
GLOBAL_RCLONE= []
GLOBAL_QBIT= []
SessionVars = VarHolder()

load_dotenv('config.env', override=True)
load_rclone()

srun(["qbittorrent-nox", "-d", "--profile=."])
sleep(0.5)

try:
    TORRENT_TIMEOUT = getConfig('TORRENT_TIMEOUT')
    if len(TORRENT_TIMEOUT) == 0:
        raise KeyError
    TORRENT_TIMEOUT = int(TORRENT_TIMEOUT)
except:
    TORRENT_TIMEOUT = None
    
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
            LOGGER.info("Mega username and password not not provided. Starting mega in anonymous mode!")
    except:
            LOGGER.info("Mega username and password not not provided. Starting mega in anonymous mode!")
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

bot.start(bot_token=BOT_TOKEN)

LOGGER.info("Telethon client created.")

#---------------------------

try:
    SESSION = getConfig("SESSION")  
    if len(SESSION) == 0:
        raise KeyError 
    userbot = Client("userbot", session_string=SESSION, api_hash=API_HASH, api_id=API_ID)
    LOGGER.info("Pyro userbot client created.")
except:
    SESSION = None
    userbot= None
    print("Userbot Error ! Have you added SESSION while deploying??")

if userbot is not None:
    try:
        userbot.start()
    except Exception as e:
      print(e)
      sys.exit(1)      
        
#---------------------------

Bot = Client("pyrosession", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workers=20)
Conversation(Bot)  
try:
    Bot.start()
    bot.pyro = Bot
    LOGGER.info("Pyro client created.")
except Exception as e:
    print(e)
    sys.exit(1)









