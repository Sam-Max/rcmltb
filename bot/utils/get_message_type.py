from pyrogram.types import Message

def get_media_type(msg: Message):
    if msg.media:
        for message_type in ("photo", "audio", "document", "video", "voice"):
            obj = getattr(msg, message_type)
            if obj:
                return obj
