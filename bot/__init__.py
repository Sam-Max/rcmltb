__version__ = "1.0"
__author__ = "Sam-Max"

import logging
from os import environ
import sys
import time

from dotenv import load_dotenv
from bot.client import RcloneTgClient
from bot.core.var_holder import VarHolder
from bot.utils.load_rclone import load_rclone

from pyrogram import Client

from convopyro import Conversation

logging.basicConfig(level= logging.INFO,
    format= "%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("botlog.txt")])

def getConfig(name: str):
    return environ[name]

uptime = time.time()
GLOBAL_RC_INST= []
SessionVars = VarHolder()

load_dotenv('config.env', override=True)
load_rclone()

# variables
API_ID = int(getConfig("API_ID"))
API_HASH = getConfig("API_HASH")
BOT_TOKEN = getConfig("BOT_TOKEN")
SESSION = getConfig("SESSION")

#---------------------------

bot = RcloneTgClient("bot", API_ID, API_HASH, timeout=20, retry_delay=3,
                        request_retries=10, connection_retries=10)

bot.start(bot_token=BOT_TOKEN)

logging.info("Telethon Client created.")

#---------------------------

userbot = Client(session_name=SESSION, api_hash=API_HASH, api_id=API_ID)
try:
    userbot.start()
    logging.info("Pyro userbot client created.")
except BaseException:
    print("Userbot Error ! Have you added SESSION while deploying??")
    sys.exit(1)

#---------------------------

Bot = Client("pyrosession", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workers=20)
Conversation(Bot)  
try:
    Bot.start()
    bot.pyro = Bot
    logging.info("Pyro client created.")
except Exception as e:
    print(e)
    sys.exit(1)









