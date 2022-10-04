# Source: Tg:MaheshChauhan/DroneBots
# Github.com/Vasusen-code

from re import findall
from time import time
from bot.helper.mirror_leech_utils.mirror_leech import MirrorLeech
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus
from bot.helper.mirror_leech_utils.status_utils.telegram_status import TelegramStatus
from bot import LOGGER, status_dict, status_dict_lock
from pyrogram.errors import ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid

VIDEO_SUFFIXES = ["mkv", "mp4", "mov", "wmv", "3gp", "mpg", "webm", "avi", "flv", "m4v", "gif"]

def get_link(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = findall(regex, string)   
    try:
        link = [x[0] for x in url][0]
        if link:
            return link
        else:
            return False
    except Exception:
        return False

async def check(app, client, link):
    msg_id = int(link.split("/")[-1])
    if 't.me/c/' in link:
        try:
            chat = int('-100' + str(link.split("/")[-2]))
            await app.get_messages(chat, msg_id)
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

async def get_msg(app, client, sender, edit_id, message, msg_link, i, isLeech):
    edit = ""
    chat = ""
    msg_id = int(msg_link.split("/")[-1]) + int(i)
    if 't.me/c/' in msg_link:
        chat = int('-100' + str(msg_link.split("/")[-2]))
        try:
            msg = await app.get_messages(chat, msg_id)
            if msg.media:
                caption= msg.video.file_name
            if not msg.media:
                if msg.text:
                    edit = await client.edit_message_text(sender, edit_id, "Cloning.")
                    await client.send_message(sender, msg.text.markdown)
                    await edit.delete()
                    return
            user_id= message.chat.id
            status= TelegramStatus(message)
            async with status_dict_lock:
                status_dict[message.id] = status
            file_path = await app.download_media(
                msg,
                progress=status.start,
                progress_args=(caption, MirrorStatus.STATUS_DOWNLOADING, time()))
            ml= MirrorLeech(file_path, message, tag="N/A", user_id= user_id, isLeech= isLeech)
            await ml.execute()
        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid):
            await client.edit_message_text(sender, edit_id, "Have you joined the channel?")
        except Exception as e:
            LOGGER.info(str(e))
            await client.edit_message_text(sender, edit_id, f'Failed to save: `{e}`')
    else:
        chat =  msg_link.split("/")[-2]
        try:
            msg = await app.get_messages(chat, msg_id)
            if msg.media:
                caption= msg.video.file_name
            if not msg.media:
                if msg.text:
                    edit = await client.edit_message_text(sender, edit_id, "Cloning.")
                    await client.send_message(sender, msg.text.markdown)
                    await edit.delete()
                    return
            user_id= message.chat.id
            status= TelegramStatus(message)
            async with status_dict_lock:
                status_dict[message.id] = status
            file_path = await app.download_media(
                msg,
                progress=status.start,
                progress_args=(caption, MirrorStatus.STATUS_DOWNLOADING, time()))
            ml= MirrorLeech(file_path, message, tag="N/A", user_id= user_id, isLeech= isLeech)
            await ml.execute()
        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid):
            await client.edit_message_text(sender, edit_id, "Have you joined the channel?")
            return 
        except Exception as e:
            LOGGER.info(str(e))
            await client.edit_message_text(sender, edit_id, f'Failed to save: `{e}`')
            return 

async def get_bulk_msg(app, client, sender, msg_link, i, isLeech):
    x = await client.send_message(sender, "Processing")
    await get_msg(app, client, sender, x.id, x, msg_link, i, isLeech= isLeech) 