from re import match as re_match

from bot.helper.ext_utils.exceptions import TgLinkException


def is_magnet(url: str):
    return bool(
        re_match(
            r"^magnet:\?.*xt=urn:(btih|btmh):([a-zA-Z0-9]{32,40}|[a-z2-7]{32}).*", url
        )
    )


def is_url(url: str):
    return bool(
        re_match(
            r"^(?!\/)(rtmps?:\/\/|mms:\/\/|rtsp:\/\/|https?:\/\/|ftp:\/\/)?([^\/:]+:[^\/@]+@)?(www\.)?(?=[^\/:\s]+\.[^\/:\s]+)([^\/:\s]+\.[^\/:\s]+)(:\d+)?(\/[^#\s]*[\s\S]*)?(\?[^#\s]*)?(#.*)?$",
            url,
        )
    )


def is_gdrive_link(url: str):
    return "drive.google.com" in url or "drive.usercontent.google.com" in url


def is_telegram_link(url: str):
    return url.startswith(("https://t.me/", "tg://openmessage?user_id="))


def is_share_link(url: str):
    return bool(
        re_match(
            r"https?:\/\/.+\.gdtot\.\S+|https?:\/\/(filepress|filebee|appdrive|gdflix)\.\S+",
            url,
        )
    )


def is_rclone_path(path: str):
    return bool(
        re_match(
            r"^(mrcc:)?(?!(magnet:|mtp:|sa:|tp:))(?![- ])[a-zA-Z0-9_\. -]+(?<! ):(?!.*\/\/).*$|^rcl$",
            path,
        )
    )


def is_gdrive_id(id_: str):
    return bool(
        re_match(
            r"^(tp:|sa:|mtp:)?(?:[a-zA-Z0-9-_]{33}|[a-zA-Z0-9_-]{19})$|^gdl$|^(tp:|mtp:)?root$",
            id_,
        )
    )


def is_mega_link(url: str):
    return "mega.nz" in url or "mega.co.nz" in url


async def get_tg_link_message(link):
    from bot import bot, app

    if link.startswith("tg://openmessage?user_id="):
        params = {}
        for param in link.split("?")[1].split("&"):
            key, _, val = param.partition("=")
            params[key] = val
        chat_id = int(params.get("user_id", 0))
        msg_id = int(params.get("message_id", 0))
        private = True
    elif "t.me/c/" in link:
        parts = link.split("/")
        chat_id = int("-100" + parts[-2])
        msg_id = int(parts[-1])
        private = True
    else:
        parts = link.rstrip("/").split("/")
        chat_id = parts[-2]
        msg_id = int(parts[-1])
        private = False

    if not private:
        try:
            msg = await bot.get_messages(chat_id, msg_id)
            if msg and not msg.empty:
                return msg, bot
        except Exception:
            pass
        if app:
            try:
                msg = await app.get_messages(chat_id, msg_id)
                if msg and not msg.empty:
                    return msg, app
            except Exception:
                pass
        raise TgLinkException("Bot can't access this chat! Make sure it's a member or set USER_SESSION_STRING.")
    else:
        if not app:
            raise TgLinkException("Private channel link requires USER_SESSION_STRING!")
        try:
            msg = await app.get_messages(chat_id, msg_id)
            if msg and not msg.empty:
                return msg, app
        except Exception as e:
            raise TgLinkException(f"Can't access this private chat: {e}")
    raise TgLinkException("Failed to get message from Telegram link.")
