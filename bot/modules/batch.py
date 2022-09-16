#Tg:MaheshChauhan/DroneBots
#Github.com/Vasusen-code

import asyncio
from bot import Bot, bot, app
from telethon import Button
from telethon.events import NewMessage
from pyrogram.errors import FloodWait
from bot.helper.ext_utils.batch_helper import check, get_bulk_msg, get_link
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import command_process

batch = []

async def get_pvt_content(event, chat, id):
    msg = await app.get_messages(chat, ids=id)
    await event.client.send_message(event.chat_id, msg) 
    
async def leech_batch(e):
    await _batch(e, isLeech= True)

async def mirror_batch(e):
    await _batch(e)

async def _batch(event, isLeech= False):
    if app is None:
         return await event.reply("Set USER_SESSION_STRING variable to use this command!")
    else:
        if not event.is_private:
            return
        if f'{event.sender_id}' in batch:
            return await event.reply("You've already started one batch, wait for it to complete!")
        async with bot.conversation(event.chat_id) as conv: 
                await conv.send_message("Send me the message link you want to start saving from, as a reply to this message.", buttons=Button.force_reply())
                try:
                    link = await conv.get_reply()
                    try:
                        _link = get_link(link.text)
                    except Exception:
                        await conv.send_message("No link found.")
                except Exception as e:
                    print(e)
                    return await conv.send_message("Cannot wait more longer for your response!")
                await conv.send_message("Send me the number of files/range you want to save from the given message, as a reply to this message.", buttons=Button.force_reply())
                try:
                    _range = await conv.get_reply()
                except Exception as e:
                    print(e)
                    return await conv.send_message("Cannot wait more longer for your response!")
                try:
                    value = int(_range.text)
                    if value > 100:
                        return await conv.send_message("You can only get upto 100 files in a single batch.")
                except ValueError:
                    return await conv.send_message("Range must be an integer!")
                s, r = await check(app, Bot, _link)
                if s != True:
                    await conv.send_message(r)
                    return
                batch.append(f'{event.sender_id}')
                await run_batch(app, Bot, event.sender_id, _link, value, isLeech= isLeech) 
                conv.cancel()
                batch.pop(0)
                
async def run_batch(userbot, client, sender, link, _range, isLeech):
    for i in range(_range):
        timer = 60
        if i < 25:
            timer = 5
        if i < 50 and i > 25:
            timer = 10
        if i < 100 and i > 50:
            timer = 15
        if not 't.me/c/' in link:
            if i < 25:
                timer = 2
            else:
                timer = 3
        try:
            await get_bulk_msg(userbot, client, sender, link, i, isLeech= isLeech) 
        except FloodWait as fw:
            await asyncio.sleep(fw.seconds + 5)
            await get_bulk_msg(userbot, client, sender, link, i, isLeech= isLeech)
        await asyncio.sleep(timer)
        

mirrorbatch_event= NewMessage(incoming=True, pattern= command_process(f"/{BotCommands.MirrorBatchCommand}"))
bot.add_event_handler(mirror_batch, event= mirrorbatch_event)              

leechbatch_event= NewMessage(incoming=True, pattern= command_process(f"/{BotCommands.LeechBatchCommand}"))
bot.add_event_handler(leech_batch, event= leechbatch_event)   

