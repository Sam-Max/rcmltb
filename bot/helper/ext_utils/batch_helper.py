#Source: Tg:MaheshChauhan/DroneBots Github.com/Vasusen-code

from re import findall
from bot import app, bot

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

async def check_link(link):
    msg_id = int(link.split("/")[-1])
    if 't.me/c/' in link:
        try:
            chat = int('-100' + str(link.split("/")[-2]))
            await app.get_messages(chat, msg_id)
            return True, None
        except Exception:
            msg= "Make sure you joined the channel and set USER_SESSION_STRING!!"
            return False, msg
    else:
        try:
            chat = str(link.split("/")[-2])
            await bot.get_messages(chat, msg_id)
            return True, None
        except Exception:
            msg= "Bot needs to join chat to download!!"
            return False, msg

