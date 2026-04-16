from asyncio import sleep
from os import path as ospath, remove as osremove
from time import time

from bot import LOGGER, config_dict, status_dict_lock, status_dict
from bot.core.torrent_manager import TorrentManager, aria2_name
from bot.helper.telegram_helper.message_utils import (
    sendStatusMessage,
    update_all_messages,
)
from bot.helper.ext_utils.misc_utils import getTaskByGid
from bot.helper.mirror_leech_utils.status_utils.aria_status import AriaStatus


async def __onDownloadStarted(api, data):
    gid = data["params"][0]["gid"]
    try:
        download = await api.tellStatus(gid)
        if not config_dict["NO_TASKS_LOGS"]:
            LOGGER.info(f"onDownloadStarted: {aria2_name(download)} - Gid: {gid}")
    except Exception as e:
        LOGGER.error(f"onDownloadStarted error: {e}")


async def __onDownloadComplete(api, data):
    gid = data["params"][0]["gid"]
    try:
        download = await api.tellStatus(gid)
    except Exception:
        return
    if not config_dict["NO_TASKS_LOGS"]:
        LOGGER.info(f"onDownloadComplete: {aria2_name(download)} - Gid: {gid}")
    if dl := await getTaskByGid(gid):
        listener = dl.listener()
        await listener.onDownloadComplete()
        await TorrentManager.aria2_remove(download)


async def __onBtDownloadComplete(api, data):
    gid = data["params"][0]["gid"]
    seed_start_time = time()
    await sleep(1)
    try:
        download = await api.tellStatus(gid)
    except Exception:
        return
    if not config_dict["NO_TASKS_LOGS"]:
        LOGGER.info(f"onBtDownloadComplete: {aria2_name(download)} - Gid: {gid}")
    if dl := await getTaskByGid(gid):
        listener = dl.listener()
        if listener.select:
            files = download.get("files", [])
            for file_o in files:
                f_path = file_o.get("path", "")
                if not file_o.get("selected", True) and ospath.exists(f_path):
                    try:
                        osremove(f_path)
                    except Exception:
                        pass
            dir_path = download.get("dir", "")
            if dir_path:
                from bot.helper.mirror_leech_utils.status_utils.status_utils import (
                    clean_unwanted,
                )

                await clean_unwanted(dir_path)
        if listener.seed:
            try:
                await api.changeOption(gid, {"max-upload-limit": "0"})
            except Exception as e:
                LOGGER.error(
                    f"{e} You are not able to seed because you added global option seed-time=0 without adding specific seed_time for this torrent GID: {gid}"
                )
        else:
            try:
                await api.forcePause(gid)
            except Exception as e:
                LOGGER.error(f"{e} GID: {gid}")
        await listener.onDownloadComplete()
        if listener.seed:
            download = await api.tellStatus(gid)
            if download.get("status") == "complete":
                if dl := await getTaskByGid(gid):
                    if not config_dict["NO_TASKS_LOGS"]:
                        LOGGER.info(f"Cancelling Seed: {aria2_name(download)}")
                    await listener.onUploadError(
                        f"Seeding stopped with Ratio: {dl.ratio()} and Time: {dl.seeding_time()}"
                    )
                    await TorrentManager.aria2_remove(download)
            else:
                async with status_dict_lock:
                    if listener.uid not in status_dict:
                        await TorrentManager.aria2_remove(download)
                        return
                    status_dict[listener.uid] = AriaStatus(gid, listener, True)
                    status_dict[listener.uid].start_time = seed_start_time
                if not config_dict["NO_TASKS_LOGS"]:
                    LOGGER.info(
                        f"Seeding started: {aria2_name(download)} - Gid: {gid}"
                    )
                await update_all_messages()
        else:
            try:
                download = await api.tellStatus(gid)
                await TorrentManager.aria2_remove(download)
            except Exception:
                pass


async def __onDownloadStopped(api, data):
    gid = data["params"][0]["gid"]
    await sleep(6)
    if dl := await getTaskByGid(gid):
        listener = dl.listener()
        await listener.onDownloadError("Dead torrent!")


async def __onDownloadError(api, data):
    gid = data["params"][0]["gid"]
    LOGGER.info(f"onDownloadError: {gid}")
    error = "None"
    try:
        download = await TorrentManager.aria2.tellStatus(gid)
        error = download.get("errorMessage", "None")
        LOGGER.info(f"Download Error: {error}")
    except Exception:
        pass
    if dl := await getTaskByGid(gid):
        listener = dl.listener()
        await listener.onDownloadError(error)


def add_aria2_callbacks():
    """Register aria2 event callbacks."""
    TorrentManager.aria2.onDownloadStart(__onDownloadStarted)
    TorrentManager.aria2.onDownloadComplete(__onDownloadComplete)
    TorrentManager.aria2.onBtDownloadComplete(__onBtDownloadComplete)
    TorrentManager.aria2.onDownloadStop(__onDownloadStopped)
    TorrentManager.aria2.onDownloadError(__onDownloadError)
