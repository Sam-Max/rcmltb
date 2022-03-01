
#**************************************************
# Based on:
# Source: https://github.com/EvamariaTG/EvaMaria/blob/master/utils.py
#**************************************************/

from pyrogram.types import Message

def get_message_type(msg: Message):
    if msg.media:
        for message_type in (
            "photo",
            "audio",
            "document",
            "video",
            "video_note",
            "voice",
            "sticker"
        ):
            obj = getattr(msg, message_type)
            if obj:
                setattr(obj, "message_type", message_type)
                return obj
