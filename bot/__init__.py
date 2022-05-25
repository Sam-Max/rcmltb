__version__ = "1.0"
__author__ = "Sam-Max"

from logging import getLogger, FileHandler, StreamHandler, INFO, basicConfig
from os import environ
import sys
import time
from dotenv import load_dotenv
from bot.client import RcloneTgClient
from bot.core.var_holder import VarHolder
from bot.utils.load_rclone import load_rclone

from pyrogram import Client

from convopyro import Conversation

basicConfig(level= INFO,
    format= "%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    handlers=[StreamHandler(), FileHandler("botlog.txt")])

LOGGER = getLogger(__name__)

def getConfig(name: str):
    return environ[name]

uptime = time.time()
GLOBAL_RC_INST= []
SessionVars = VarHolder()

load_dotenv('config.env', override=True)
load_rclone()

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









