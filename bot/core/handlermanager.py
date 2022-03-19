from telethon import TelegramClient, events
from bot.core.get_vars import get_val
from bot.core.handlers.handle_cancel import handle_cancel
from bot.core.handlers.handle_cleardata import cleardata_handler
from bot.core.handlers.handle_copy_cm import handle_copy_command
from bot.core.handlers.handle_download_cm import handle_download_command
from bot.core.handlers.handle_exec_cm import handle_exec_message_f
from bot.core.handlers.handle_getlogs import get_logs_f
from bot.core.handlers.handle_leech_cm import handle_leech_command
from bot.core.handlers.handle_restart_cm import handle_restart
from bot.core.handlers.handle_server_cm import handle_server_command
from bot.core.handlers.handle_config_cm import handle_config_command
from bot.core.handlers.handle_speedtest import speed_handler
from bot.core.handlers.handle_start import start_handler
from bot.core.handlers.handle_test_cm import handle_test_command
from bot.core.handlers_callback.handle_download_cb import handle_download_cb
from bot.core.handlers_callback.handle_nextpage_main_menu_cb import next_page_menu
from bot.core.handlers_callback.handle_nextpage_leech_menu_cb import next_page_leech
from bot.core.handlers_callback.handle_nextpage_copy_menu_cb import next_page_copy
from bot.core.handlers_callback.handle_settings_copy_menu_cb import handle_setting_copy_menu_callback
from bot.core.handlers_callback.handle_settings_leech_menu_cb import handle_setting_leech_menu_callback
from bot.core.handlers_callback.handle_settings_main_menu_cb import handle_setting_main_menu_callback
from .get_commands import get_command, get_command_p
from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
import re, logging
from os import path as ospath, remove as osremove
from bot import __version__

torlog = logging.getLogger(__name__)


def add_handlers(bot: TelegramClient):

    #pyrogram handlers
    download_handlers = MessageHandler(
        handle_download_command,
        filters=filters.command([get_command_p("MIRROR")])
    )
    bot.pyro.add_handler(download_handlers)


    leech_handlers = MessageHandler(
        handle_leech_command,
        filters=filters.command([get_command_p("LEECH")])
    )
    bot.pyro.add_handler(leech_handlers)


    test_handlers = MessageHandler(
        handle_test_command,
        filters=filters.command([get_command_p("TEST")])
        )
    
    bot.pyro.add_handler(test_handlers)

   # telethon handlerss
    bot.add_event_handler(
        handle_copy_command,
        events.NewMessage(pattern=command_process(get_command("COPY")))
    )
    
    bot.add_event_handler(
        handle_exec_message_f,
        events.NewMessage(pattern=command_process(get_command("EXEC")))
    )

    bot.add_event_handler(
        handle_restart,
        events.NewMessage(pattern=command_process(get_command("RESTART")))
    )


    bot.add_event_handler(
        get_logs_f,
        events.NewMessage(pattern=command_process(get_command("GETLOGS")))
    )

    bot.add_event_handler(
        handle_server_command,
        events.NewMessage(pattern=command_process(get_command("SERVER")))
    )

    bot.add_event_handler(
        start_handler,
        events.NewMessage(pattern=command_process(get_command("START")))
    )

    bot.add_event_handler(
        speed_handler,
        events.NewMessage(pattern=command_process(get_command("SPEEDTEST")))
    )

    bot.add_event_handler(
        cleardata_handler,
        events.NewMessage(pattern=command_process(get_command("CRLDATA")))
    )

    bot.add_event_handler(
        handle_config_command,
        events.NewMessage(pattern=command_process(get_command("CONFIG")))
    )

    bot.loop.run_until_complete(booted(bot))

   
    # *********** Callback Handlerss ***********  

    bot.pyro.add_handler(
        CallbackQueryHandler(
        handle_download_cb, 
        filters= filters.regex("renaming"))
        )

    bot.pyro.add_handler(
         CallbackQueryHandler(
            handle_setting_leech_menu_callback, 
            filters= filters.regex("leechmenu"))
        )        

    bot.add_event_handler(
        next_page_menu,
        events.CallbackQuery(pattern="next")
        )

    bot.add_event_handler(
        next_page_copy,
        events.CallbackQuery(pattern="n_copy")
        )

    bot.pyro.add_handler(
         CallbackQueryHandler(
            next_page_leech, 
            filters= filters.regex("n_leech"))
        )         
    
    bot.add_event_handler(
        handle_cancel,
        events.CallbackQuery(pattern="upcancel")
    )

    bot.add_event_handler(
        handle_server_command,
        events.CallbackQuery(pattern="fullserver")
    )
    bot.add_event_handler(
        cleardata_handler,
        events.CallbackQuery(pattern="cleardata")
    )

    bot.add_event_handler(
        handle_setting_main_menu_callback,
        events.CallbackQuery(pattern="mainmenu")
    )

    bot.add_event_handler(
        handle_setting_copy_menu_callback,
        events.CallbackQuery(pattern="copymenu")
    )

async def booted(client):
    if ospath.isfile(".updatemsg"):
        with open(".updatemsg") as f:
            chat_id, msg_id = map(int, f)
        await client.edit_message(chat_id, msg_id, "Restarted successfully!")
        osremove(".updatemsg")

    await client.send_message(get_val("OWNER_ID"), "The bot is ready to use")


def command_process(command):
    return re.compile(command, re.IGNORECASE)
