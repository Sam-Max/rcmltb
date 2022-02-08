#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bot.core.HandleManager import add_handlers
from bot.core.getVars import get_val
import logging
from pyrogram import Client
from bot.client import RcloneTgClient

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s"
    )
    logging.getLogger("pyrogram").setLevel(logging.ERROR)

    # Telethon client creation
    bot = RcloneTgClient("telethonsession", get_val("API_ID"), get_val("API_HASH"), timeout=20, retry_delay=3,
                         request_retries=10, connection_retries=10)
    bot.start(bot_token=get_val("BOT_TOKEN"))
    logging.info("Telethon Client created.")

    # Pyro Client creation and linking
    pyroclient = Client("pyrosession", api_id=get_val("API_ID"), api_hash=get_val("API_HASH"),
                        bot_token=get_val("BOT_TOKEN"), workers=10)
    pyroclient.start()
    bot.pyro = pyroclient
    logging.info("Pryogram Client created.")

    # Associate the handlers
    add_handlers(bot)

    try:
        bot.loop.run_until_complete()
    except:pass

    bot.run_until_disconnected()
