from pyrogram.types import Message

def get_media_type(msg: Message):
    if msg.media:
        for message_type in ("audio", "document", "video"):
            obj = getattr(msg, message_type)
            if obj:
                return obj

def get_file(replied_message):
    media_array = [replied_message.document, replied_message.video, replied_message.audio]
    for i in media_array:
        if i is not None:
            file = i
            return file
