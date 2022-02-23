#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bot.core.get_vars import get_val
import logging
from pyrogram import Client
from bot.client import RcloneTgClient
from convopyro import Conversation

from bot.core.handlermanager import add_handlers

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s"
    )
    logging.getLogger("pyrogram").setLevel(logging.ERROR)

    bot = RcloneTgClient("telethonsession", get_val("API_ID"), get_val("API_HASH"), timeout=20, retry_delay=3,
                         request_retries=10, connection_retries=10)
    bot.start(bot_token=get_val("BOT_TOKEN"))
    logging.info("Telethon Client created.")

    pyroclient = Client("pyrosession", api_id=get_val("API_ID"), api_hash=get_val("API_HASH"),
                        bot_token=get_val("BOT_TOKEN"), workers=20)
    Conversation(pyroclient)                    
    pyroclient.start()
    bot.pyro = pyroclient
    logging.info("Pryogram Client created.")

    add_handlers(bot)

    try:
        bot.loop.run_until_complete()
    except:pass

    bot.run_until_disconnected()
