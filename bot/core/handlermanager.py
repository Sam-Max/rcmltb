import re, logging
from os import path as ospath, remove as osremove
from telethon import events
from bot.core.get_commands import get_command_pyro, get_command_tele
from bot.core.get_vars import get_val
from bot.core.handlers.callbacks.handle_download_cb import handle_download_cb
from bot.core.handlers.handle_cancel import handle_cancel
from bot.core.handlers.handle_cleardata import cleardata_handler
from bot.core.handlers.handle_copy_cm import handle_copy_command
from bot.core.handlers.handle_download_cm import handle_download_command
from bot.core.handlers.handle_exec_cm import handle_exec_message_f
from bot.core.handlers.handle_getlogs import get_logs_f
from bot.core.handlers.handle_leech_cm import handle_leech_command
from bot.core.handlers.handle_myfiles_cm import handle_myfiles
from bot.core.handlers.handle_restart_cm import handle_restart
from bot.core.handlers.handle_server_cm import handle_server_command
from bot.core.handlers.handle_config_cm import handle_config_command
from bot.core.handlers.handle_speedtest import speed_handler
from bot.core.handlers.handle_start import start_handler
from bot.core.handlers.handle_test_cm import handle_test_command
from bot.core.handlers import handle_batch
from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from bot.core.menus.callbacks.handle_copy_menu_cb import handle_setting_copy_menu_callback
from bot.core.menus.callbacks.handle_leech_menu_cb import handle_setting_leech_menu_callback
from bot.core.menus.callbacks.handle_main_menu_cb import handle_setting_main_menu_callback
from bot.core.menus.callbacks.handle_myfiles_menu_cb import handle_setting_myfiles_menu_callback
from bot.core.menus.callbacks.nextpage.handle_nextpage_copy_menu_cb import next_page_copy
from bot.core.menus.callbacks.nextpage.handle_nextpage_leech_menu_cb import next_page_leech
from bot.core.menus.callbacks.nextpage.handle_nextpage_main_menu_cb import next_page_menu
from bot.core.menus.callbacks.nextpage.handle_nextpage_myfiles_menu_cb import next_page_myfiles

torlog = logging.getLogger(__name__)


def add_handlers(bot):
         
    #pyrogram handlers
    download_handlers = MessageHandler(
        handle_download_command,
        filters=filters.command([get_command_pyro("MIRROR")]) 
    )
    bot.pyro.add_handler(download_handlers)


    leech_handlers = MessageHandler(
        handle_leech_command,
        filters=filters.command([get_command_pyro("LEECH")]) 
    )
    bot.pyro.add_handler(leech_handlers)

    myfiles_handlers = MessageHandler(
        handle_myfiles,
        filters=filters.command([get_command_pyro("MYFILES")])
    )
    bot.pyro.add_handler(myfiles_handlers)


    test_handlers = MessageHandler(
        handle_test_command,
        filters=filters.command([get_command_pyro("TEST")])
        )

    bot.pyro.add_handler(test_handlers)

    # telethon handlers
    bot.add_event_handler(
        handle_copy_command,
        events.NewMessage(pattern=command_process(get_command_tele("COPY")))
    )

    bot.add_event_handler(
        handle_exec_message_f,
        events.NewMessage(pattern=command_process(get_command_tele("EXEC")))
    )

    bot.add_event_handler(
        handle_restart,
        events.NewMessage(pattern=command_process(get_command_tele("RESTART")))
    )

    bot.add_event_handler(
        get_logs_f,
        events.NewMessage(pattern=command_process(get_command_tele("GETLOGS")))
    )

    bot.add_event_handler(
        handle_server_command,
        events.NewMessage(pattern=command_process(get_command_tele("SERVER")))
    )

    bot.add_event_handler(
        start_handler,
        events.NewMessage(pattern=command_process(get_command_tele("START")))
    )

    bot.add_event_handler(
        speed_handler,
        events.NewMessage(pattern=command_process(get_command_tele("SPEEDTEST")))
    )

    bot.add_event_handler(
        cleardata_handler,
        events.NewMessage(pattern=command_process(get_command_tele("CRLDATA")))
    )

    bot.add_event_handler(
        handle_config_command,
        events.NewMessage(pattern=command_process(get_command_tele("CONFIG")))
    )

    bot.loop.run_until_complete(booted(bot))


    # *********** Callback Handlerss ***********  

    bot.pyro.add_handler(
        CallbackQueryHandler(
        handle_download_cb, 
        filters= filters.regex("renaming"))
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
        next_page_myfiles, 
        filters= filters.regex("n_myfiles"))
        )

    bot.pyro.add_handler(
        CallbackQueryHandler(
        next_page_leech, 
        filters= filters.regex("n_leech"))
        )

    bot.pyro.add_handler(
        CallbackQueryHandler(
        handle_setting_myfiles_menu_callback, 
        filters= filters.regex("myfilesmenu"))
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

    bot.pyro.add_handler(
        CallbackQueryHandler(
        handle_setting_leech_menu_callback, 
        filters= filters.regex("leechmenu"))
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
            user_id, msg_id = map(int, f)
        await client.edit_message(user_id, msg_id, "Restarted successfully!")
        osremove(".updatemsg")

    await client.send_message(get_val("OWNER_ID"), "The bot is ready to use")


def command_process(command):
    return re.compile(command, re.IGNORECASE)



