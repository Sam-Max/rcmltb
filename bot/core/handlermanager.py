import re, logging
from os import path as ospath, remove as osremove
from telethon import events
from bot.core.get_commands import get_command_pyro, get_command_tele
from bot.core.get_vars import get_val
from bot.core.handlers.handle_cancel import handle_cancel
from bot.core.handlers.handle_copy_cm import handle_copy_command
from bot.core.handlers.handle_mirror_cm import handle_mirror_command, handle_unzip_mirror_command, handle_zip_mirror_command
from bot.core.handlers.handle_exec_cm import handle_exec_message_f
from bot.core.handlers.handle_getlogs import get_logs_f
from bot.core.handlers.handle_leech_cm import handle_leech_command
from bot.core.handlers.handle_myfiles_cm import handle_myfiles
from bot.core.handlers.handle_restart_cm import handle_restart
from bot.core.handlers.handle_server_cm import handle_server_command
from bot.core.handlers.handle_mirrorset_cm import handle_mirrorset_command
from bot.core.handlers.handle_speedtest import speed_handler
from bot.core.handlers.handle_start import start_handler
from bot.core.handlers.handle_test_cm import handle_test_command
from bot.core.handlers import handle_batch
from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from bot.core.menus.callbacks.handle_copy_menu_cb import handle_setting_copy_menu_callback
from bot.core.menus.callbacks.handle_leech_menu_cb import handle_setting_leech_menu_callback
from bot.core.menus.callbacks.handle_mirror_menu_cb import handle_mirror_menu_callback
from bot.core.menus.callbacks.handle_mirrorset_menu_cb import handle_setting_mirroset_callback
from bot.core.menus.callbacks.handle_myfiles_menu_cb import handle_setting_myfiles_menu_callback
from bot.core.menus.callbacks.nextpage.handle_nextpage_copy_menu_cb import next_page_copy
from bot.core.menus.callbacks.nextpage.handle_nextpage_leech_menu_cb import next_page_leech
from bot.core.menus.callbacks.nextpage.handle_nextpage_mirrorset_menu_cb import next_page_mirrorset
from bot.core.menus.callbacks.nextpage.handle_nextpage_myfiles_menu_cb import next_page_myfiles

torlog = logging.getLogger(__name__)


def add_handlers(bot):
         
    #pyrogram handlers
    download_handlers = MessageHandler(
        handle_mirror_command,
        filters=filters.command([get_command_pyro("MIRROR")]) 
    )
    bot.pyro.add_handler(download_handlers)

    download_handlers = MessageHandler(
        handle_zip_mirror_command,
        filters=filters.command([get_command_pyro("ZIPMIRROR")]) 
    )
    bot.pyro.add_handler(download_handlers)

    download_handlers = MessageHandler(
        handle_unzip_mirror_command,
        filters=filters.command([get_command_pyro("UNZIPMIRROR")]) 
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
        handle_mirrorset_command,
        events.NewMessage(pattern=command_process(get_command_tele("MIRRORSET")))
    )

    bot.loop.run_until_complete(booted(bot))


    # *********** Callback Handlerss ***********  

    #next    
    bot.add_event_handler(
    next_page_mirrorset,
    events.CallbackQuery(pattern="n_mirrorset")
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

    #menus
    bot.pyro.add_handler(
    CallbackQueryHandler(
    handle_setting_myfiles_menu_callback, 
    filters= filters.regex("myfilesmenu"))
    )  

    bot.add_event_handler(
    handle_setting_mirroset_callback,
    events.CallbackQuery(pattern="mirrorsetmenu")
    )

    bot.pyro.add_handler(
    CallbackQueryHandler(
    handle_setting_leech_menu_callback, 
    filters= filters.regex("leechmenu"))
    )

    bot.add_event_handler(
    handle_setting_copy_menu_callback,
    events.CallbackQuery(pattern="copymenu")
    )

    bot.pyro.add_handler(
    CallbackQueryHandler(
    handle_mirror_menu_callback,
    filters= filters.regex("mirrormenu"))
    )

    #others
    bot.add_event_handler(
    handle_cancel,
    events.CallbackQuery(pattern="upcancel")
    )

    bot.add_event_handler(
    handle_server_command,
    events.CallbackQuery(pattern="fullserver")
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



