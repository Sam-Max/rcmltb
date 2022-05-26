#Tg:MaheshChauhan/DroneBots
#Github.com/Vasusen-code


import re
import time
from bot.downloaders.progress_for_pyrogram import progress_for_pyrogram
from bot.uploaders.rclone.rclone_mirror import RcloneMirror
from .. import GLOBAL_RC_INST

from pyrogram.errors import ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid

VIDEO_SUFFIXES = ["mkv", "mp4", "mov", "wmv", "3gp", "mpg", "webm", "avi", "flv", "m4v", "gif"]

def get_link(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)   
    try:
        link = [x[0] for x in url][0]
        if link:
            return link
        else:
            return False
    except Exception:
        return False

async def check(userbot, client, link):
    msg_id = int(link.split("/")[-1])
    if 't.me/c/' in link:
        try:
            chat = int('-100' + str(link.split("/")[-2]))
            await userbot.get_messages(chat, msg_id)
            return True, None
        except ValueError:
            return False, "**Invalid Link!**"
        except Exception:
            return False, "Have you joined the channel?"
    else:
        try:
            chat = str(link.split("/")[-2])
            await client.get_messages(chat, msg_id)
            return True, None
        except Exception:
            return False, "Maybe bot is banned from the chat, or your link is invalid!"

async def get_msg(userbot, client, sender, edit_id, msg_link, i):
    edit = ""
    chat = ""
    msg_id = int(msg_link.split("/")[-1]) + int(i)
    if 't.me/c/' in msg_link:
        chat = int('-100' + str(msg_link.split("/")[-2]))
        try:
            msg = await userbot.get_messages(chat, msg_id)
            print(msg)
            if not msg.media:
                if msg.text:
                    edit = await client.edit_message_text(sender, edit_id, "Cloning.")
                    await client.send_message(sender, msg.text.markdown)
                    await edit.delete()
                    return
            edit = await client.edit_message_text(sender, edit_id, "Trying to Download.")
            file = await userbot.download_media(
                msg,
                progress=progress_for_pyrogram,
                progress_args=(
                    "",
                    "**DOWNLOADING:**",
                    edit,
                    time.time()
                )
            )
            await edit.edit('Preparing to Upload!')
            rclone_mirror= RcloneMirror(file, edit, "", "", False)
            GLOBAL_RC_INST.append(rclone_mirror)
            await rclone_mirror.mirror()
            GLOBAL_RC_INST.remove(rclone_mirror)
        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid):
            await client.edit_message_text(sender, edit_id, "Have you joined the channel?")
            #return 
        except Exception as e:
            logging.info(str(e))
            await client.edit_message_text(sender, edit_id, f'Failed to save: `{e}`')
            #return 
    else:
        chat =  msg_link.split("/")[-2]
        try:
            msg = await userbot.get_messages(chat, msg_id)
            print(msg)
            if not msg.media:
                if msg.text:
                    edit = await client.edit_message_text(sender, edit_id, "Cloning.")
                    await client.send_message(sender, msg.text.markdown)
                    await edit.delete()
                    return
            edit = await client.edit_message_text(sender, edit_id, "Trying to Download.")
            file = await userbot.download_media(
                msg,
                progress=progress_for_pyrogram,
                progress_args=(
                    "",
                    "**DOWNLOADING:**",
                    edit,
                    time.time()
                )
            )
            await edit.edit('Preparing to Upload!')
            rclone_mirror= RcloneMirror(file, edit, "", "", False)
            GLOBAL_RC_INST.append(rclone_mirror)
            await rclone_mirror.download()
            GLOBAL_RC_INST.remove(rclone_mirror)
        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid):
            await client.edit_message_text(sender, edit_id, "Have you joined the channel?")
            return 
        except Exception as e:
            logging.info(str(e))
            await client.edit_message_text(sender, edit_id, f'Failed to save: `{e}`')
            return 

async def get_bulk_msg(userbot, client, sender, msg_link, i):
    x = await client.send_message(sender, "Processing!")
    await get_msg(userbot, client, sender, x.id, msg_link, i) 