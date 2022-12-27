from configparser import ConfigParser
from bot import LOGGER, OWNER_ID, RC_INDEX_PASS, RC_INDEX_PORT, RC_INDEX_URL, RC_INDEX_USER, bot
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from asyncio.subprocess import PIPE, create_subprocess_exec as subprocess_exec
from pyrogram import filters
from subprocess import run as srun
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import editMarkup, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker
from bot.helper.ext_utils.rclone_utils import get_rclone_config

SREMOTE = []
process_dict= {'state': "inactive", 'pid': 0}


async def serve(client, message):
  if process_dict['state'] == 'inactive':
    await list_remotes(message)
  else:
    button= ButtonMaker()
    url= f"{RC_INDEX_URL}:{RC_INDEX_PORT}"
    msg= f'Serving on <a href={url}>{url}</a>'
    button.cb_buildbutton("Stop", "servemenu^stop")
    await sendMarkup(msg, message, button.build_menu(1))

async def protocol_selection(message):
  button= ButtonMaker()
  button.cb_buildbutton("HTTP", "servemenu^http")
  button.cb_buildbutton("WEBDAV", "servemenu^webdav")
  await editMarkup("Choose protocol to serve the remote", message, button.build_menu(2))

async def serve_cb(client, callbackQuery):
  query= callbackQuery
  data= query.data
  data = data.split("^")
  message= query.message
  path = get_rclone_config(OWNER_ID)
  
  if data[1] == "drive":
    SREMOTE.append(data[2]) 
    await protocol_selection(message)
  elif data[1] == "all":
    cmd = ["rclone", "rcd", "--rc-serve", f"--rc-addr=:{RC_INDEX_PORT}", f"--rc-user={RC_INDEX_USER}", f"--rc-pass={RC_INDEX_PASS}", f'--config={path}'] 
    await rclone_serve(cmd, message)
  elif data[1] == "http":
    cmd = ["rclone", "serve", "http", f"--addr=:{RC_INDEX_PORT}", f"--user={RC_INDEX_USER}", f"--pass={RC_INDEX_PASS}", f'--config={path}', f"{SREMOTE[0]}:"] 
    await rclone_serve(cmd, message)
  elif data[1] == "webdav":
    cmd = ["rclone", "serve", "webdav", f"--addr=:{RC_INDEX_PORT}", f"--user={RC_INDEX_USER}", f"--pass={RC_INDEX_PASS}", f'--config={path}', f"{SREMOTE[0]}:"] 
    await rclone_serve(cmd, message)
  elif data[1] == "stop":
    LOGGER.info(f"Killing process...")
    process_dict['state'] = 'inactive'
    status= srun(["kill", "-9", f"{process_dict['pid']}"])
    if status.returncode == 0:
        await query.answer('Server stopped', show_alert=True)
  elif data[1] == "close":
    await query.answer()
    await message.delete()
  
async def rclone_serve(cmd, message):
  process = await subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
  process_dict['pid']= process.pid
  button= ButtonMaker()
  url= f"{RC_INDEX_URL}:{RC_INDEX_PORT}"
  msg= f'Serving on <a href={url}>{url}</a>'
  msg+= f'\n<b>User</b>: <code>{RC_INDEX_USER}</code>'
  msg+= f'\n<b>Pass</b>: <code>{RC_INDEX_PASS}</code>'
  button.cb_buildbutton("Stop", "servemenu^stop")
  await editMarkup(msg, message, button.build_menu(1))
  process_dict['state']= 'active'
  return_code = await process.wait()
  if return_code != 0:
    err= await process.stderr.read()
    err = err.decode()
    if process_dict['state'] == 'inactive':
      await message.delete()
    else:
      await sendMessage(f'Error: {err}', message)
      process_dict['state']= 'inactive'

async def list_remotes(message):
    SREMOTE.clear()
    button = ButtonMaker()
    path= get_rclone_config(OWNER_ID)
    conf = ConfigParser()
    conf.read(path)
    for remote in conf.sections():
        button.cb_buildbutton(f"📁{remote}", f"servemenu^drive^{remote}")
    button.cb_buildbutton("🌐 All", f"servemenu^all")
    button.cb_buildbutton("✘ Close Menu", f"servemenu^close")
    await sendMarkup("Select cloud to serve as index", message, reply_markup= button.build_menu(2))

serve_handler = MessageHandler(serve, filters= filters.command(BotCommands.ServeCommand) & (CustomFilters.owner_filter | CustomFilters.chat_filter))
serve_cb_handler = CallbackQueryHandler(serve_cb, filters= filters.regex("servemenu"))

bot.add_handler(serve_handler)
bot.add_handler(serve_cb_handler)
        