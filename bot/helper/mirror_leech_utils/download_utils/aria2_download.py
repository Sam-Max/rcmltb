from os import path as ospath, remove as osremove

from bot import LOGGER, config_dict, status_dict_lock, status_dict, aria2_options
from bot.core.torrent_manager import TorrentManager, aria2_name
from bot.helper.telegram_helper.message_utils import sendMessage, sendStatusMessage
from bot.helper.mirror_leech_utils.status_utils.aria_status import AriaStatus


async def add_aria2c_download(link, path, listener, filename, auth):
    a2c_opt = {**aria2_options}
    a2c_opt["dir"] = path
    if filename:
        a2c_opt["out"] = filename
    if auth:
        a2c_opt["header"] = f"authorization: {auth}"
    if TORRENT_TIMEOUT := config_dict["TORRENT_TIMEOUT"]:
        a2c_opt["bt-stop-timeout"] = f"{TORRENT_TIMEOUT}"
    try:
        if ospath.exists(link):
            gid = await TorrentManager.aria2.addUri(uris=[], options=a2c_opt)
        else:
            gid = await TorrentManager.aria2.addUri(uris=[link], options=a2c_opt)
    except Exception as e:
        LOGGER.info(f"Aria2c Download Error: {e}")
        await sendMessage(f"{e}", listener.message)
        return

    if ospath.exists(link):
        osremove(link)

    download = await TorrentManager.aria2.tellStatus(gid)
    if download.get("errorMessage"):
        error = str(download["errorMessage"]).replace("<", " ").replace(">", " ")
        LOGGER.info(f"Aria2c Download Error: {error}")
        await sendMessage(error, listener.message)
        return

    name = aria2_name(download)
    async with status_dict_lock:
        status_dict[listener.uid] = AriaStatus(gid, listener)

    if not config_dict["NO_TASKS_LOGS"]:
        LOGGER.info(f"Aria2Download started: {name}. Gid: {gid}")

    await listener.onDownloadStart()
    await sendStatusMessage(listener.message)


# Backward compatibility: re-export start_aria2_listener for old imports
from bot.helper.listeners.aria2_listener import add_aria2_callbacks as start_aria2_listener
