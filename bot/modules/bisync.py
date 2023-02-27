from configparser import ConfigParser
from pyrogram.filters import command, regex
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from bot import bot, config_dict
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.rclone_utils import get_rclone_config, is_rclone_config
from bot.helper.ext_utils.message_utils import editMarkup, sendMarkup, sendMessage
from bot.helper.ext_utils.button_build import ButtonMaker

sync_dict= {}

async def handle_bisync(client, message):
    user_id= message.from_user.id
    if await is_rclone_config(user_id, message):
        button= await list_remotes(user_id)
        msg= "Select <b>origin</b> cloud"
        msg+= "<b>\n\nNote</b>: Bisync check for changes on each side and propagate changes on Origin to Destination, and vice-versa."
        await sendMarkup(msg, message, reply_markup= button.build_menu(2))

async def bysync_cb(client, callbackQuery):
    query= callbackQuery
    data= query.data
    data = data.split("^")
    message= query.message
    user_id= query.from_user.id
    path = get_rclone_config(user_id)

    if data[1] == "origin":
        await query.answer()
        sync_dict['origin']= data[2]
        button= await list_remotes(user_id, drive_type='destination')
        await editMarkup("Select <b>destination</b> cloud", message, reply_markup= button.build_menu(2))
    elif data[1] == "destination":  
        await query.answer()
        sync_dict["destination"]= data[2]
        await start_rc_bisync(message, path)
    else:
        await query.answer()
        await message.delete()

async def start_rc_bisync(message, path):
    origin= sync_dict['origin']
    destination= sync_dict["destination"]
    if config_dict["SERVER_SIDE"]:
        cmd = ["rclone", "bisync ", "--server-side-across-configs", "--remove-empty-dirs", "--resync", f'--config={path}', f"{origin}:", f"{destination}:"] 
    else:
        cmd = ["rclone", "bisync", "--remove-empty-dirs", "--resync", f'--config={path}', f"{origin}:", f"{destination}:"] 
    process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
    button= ButtonMaker()
    msg= f"Syncing: {origin} 🔄 {destination}"
    button.cb_buildbutton("Stop", 'bisync^stop')
    await editMarkup(msg, message, button.build_menu(1))
    return_code = await process.wait()
    if return_code != 0:
        err= await process.stderr.read()
        msg= f'Error: {err}'
        await sendMessage(msg, message)
    await message.delete()

async def list_remotes(user_id, drive_type='origin'):
    button = ButtonMaker()
    path= get_rclone_config(user_id)
    conf = ConfigParser()
    conf.read(path)
    for remote in conf.sections():
        button.cb_buildbutton(f"📁{remote}", f"bisync^{drive_type}^{remote}")
    button.cb_buildbutton("✘ Close Menu", f"bisync^close")
    return button

bisync = MessageHandler(handle_bisync, filters=command(BotCommands.BiSyncCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
bysync_callback= CallbackQueryHandler(bysync_cb, filters= regex("bisync"))

bot.add_handler(bisync)
bot.add_handler(bysync_callback)