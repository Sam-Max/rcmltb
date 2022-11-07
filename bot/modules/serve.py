from configparser import ConfigParser
from bot import LOGGER, OWNER_ID, SERVE_IP, SERVE_PORT, SERVE_USER, SERVE_PASS, bot
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from asyncio.subprocess import PIPE, create_subprocess_exec as subprocess_exec
from pyrogram import filters
from subprocess import run as srun
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import editMarkup, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, get_rclone_config

SREMOTE = []
PID= 0
STATE= 'inactive'

async def serve(client, message):
  if STATE == 'inactive':
    await list_remotes(message)
  else:
    button= ButtonMaker()
    msg= f'Serving on <code>http://{SERVE_IP}:{SERVE_PORT}/</code>'
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
  elif data[1] == "http":
    await query.answer()
    cmd = ["rclone", "serve", "http", f"--addr={SERVE_IP}:{SERVE_PORT}", f"--user={SERVE_USER}", f"--pass={SERVE_PASS}", f'--config={path}', f"{SREMOTE[0]}:"] 
    await rclone_serve(cmd, data[1], message)
  elif data[1] == "webdav":
    await query.answer()
    cmd = ["rclone", "serve", "webdav", f"--addr={SERVE_IP}:{SERVE_PORT}", f"--user={SERVE_USER}", f"--pass={SERVE_PASS}", f'--config={path}', f"{SREMOTE[0]}:"] 
    await rclone_serve(cmd, data[1], message)
  elif data[1] == "stop":
    LOGGER.info(f"Killing process with pid: {PID}")
    srun(["kill", "-9", f"{PID}"])
    await query.answer()
  elif data[1] == "close":
    await query.answer()
    await message.delete()
  
async def rclone_serve(cmd, protocol, message):
  process = await subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
  button= ButtonMaker()
  msg= f'Serving {protocol} on <code>http://{SERVE_IP}:{SERVE_PORT}/</code>'
  msg+= f'\n<b>User</b>: <code>{SERVE_USER}</code>'
  msg+= f'\n<b>Pass</b>: <code>{SERVE_PASS}</code>'
  button.cb_buildbutton("Stop", "servemenu^stop")
  await sendMarkup(msg, message, button.build_menu(1))
  globals()['STATE']= 'active'
  globals()['PID'] = process.pid
  return_code = await process.wait()
  if return_code != 0:
    globals()['STATE']= 'inactive'
    err= await process.stderr.read()
    err = err.decode()
    await sendMessage(f'Error: {err}', message)

async def list_remotes(message):
    SREMOTE.clear()
    button = ButtonMaker()
    path= get_rclone_config(OWNER_ID)
    conf = ConfigParser()
    conf.read(path)
    for j in conf.sections():
        button.cb_buildbutton(f"📁{j}", f"servemenu^drive^{j}")
    button.cb_buildbutton("✘ Close Menu", f"servemenu^close")
    await sendMarkup("Select cloud to serve as a remote", message, reply_markup= button.build_menu(2))

serve_handler = MessageHandler(serve, filters= filters.command(BotCommands.ServeCommand) & (CustomFilters.owner_filter | CustomFilters.chat_filter))
serve_cb_handler = CallbackQueryHandler(serve_cb, filters= filters.regex("servemenu"))

bot.add_handler(serve_handler)
bot.add_handler(serve_cb_handler)
        