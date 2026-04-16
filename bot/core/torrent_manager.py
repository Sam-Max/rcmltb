from aioaria2 import Aria2WebsocketClient
from aioqbt.client import create_client
from asyncio import gather, TimeoutError
from aiohttp import ClientError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from time import time

from bot import LOGGER, aria2_options


def wrap_with_retry(obj, max_retries=3):
    for attr_name in dir(obj):
        if attr_name.startswith("_"):
            continue
        attr = getattr(obj, attr_name)
        if callable(attr) and not isinstance(attr, type):
            try:
                from inspect import iscoroutinefunction
                if iscoroutinefunction(attr):
                    retry_policy = retry(
                        stop=stop_after_attempt(max_retries),
                        wait=wait_exponential(multiplier=1, min=1, max=5),
                        retry=retry_if_exception_type(
                            (ClientError, TimeoutError, RuntimeError)
                        ),
                    )
                    setattr(obj, attr_name, retry_policy(attr))
            except (AttributeError, TypeError):
                pass
    return obj


aria2c_global = [
    "bt-max-open-files",
    "download-result",
    "keep-unfinished-download-result",
    "log",
    "log-level",
    "max-concurrent-downloads",
    "max-download-result",
    "max-overall-download-limit",
    "save-session",
    "max-overall-upload-limit",
    "optimize-concurrent-downloads",
    "save-cookies",
    "server-stat-of",
]


def is_metadata(download):
    return "bittorrent" in download and download["bittorrent"].get("mode") == "none"


def aria2_name(download):
    if "bittorrent" in download:
        return download["bittorrent"].get("info", {}).get("name") or download.get(
            "files", [{}]
        )[0].get("path", "").split("/")[-1]
    return download.get("files", [{}])[0].get("path", "").split("/")[-1]


class TorrentManager:
    aria2 = None
    qbittorrent = None

    @classmethod
    async def initiate(cls):
        cls.aria2, cls.qbittorrent = await gather(
            Aria2WebsocketClient.new("http://localhost:6800/jsonrpc"),
            create_client("http://localhost:8090/api/v2/"),
        )
        cls.qbittorrent = wrap_with_retry(cls.qbittorrent)

    @classmethod
    async def close_all(cls):
        if cls.aria2:
            await cls.aria2.close()
        if cls.qbittorrent:
            await cls.qbittorrent.close()

    @classmethod
    async def aria2_remove(cls, download):
        if download.get("status", "") in ["active", "paused", "waiting"]:
            await cls.aria2.forceRemove(download.get("gid", ""))
        else:
            try:
                await cls.aria2.removeDownloadResult(download.get("gid", ""))
            except Exception:
                pass

    @classmethod
    async def remove_all(cls):
        await cls.pause_all()
        await gather(
            cls.qbittorrent.torrents.delete("all", False),
            cls.aria2.purgeDownloadResult(),
        )
        downloads = []
        results = await gather(
            cls.aria2.tellActive(), cls.aria2.tellWaiting(0, 1000)
        )
        for res in results:
            downloads.extend(res)
        tasks = [
            cls.aria2.forceRemove(download.get("gid")) for download in downloads
        ]
        try:
            await gather(*tasks)
        except Exception:
            pass

    @classmethod
    async def overall_speed(cls):
        try:
            s1, s2 = await gather(
                cls.qbittorrent.transfer.info(), cls.aria2.getGlobalStat()
            )
            dl_speed = s1.dl_info_speed + int(s2.get("downloadSpeed", "0"))
            up_speed = s1.up_info_speed + int(s2.get("uploadSpeed", "0"))
            return dl_speed, up_speed
        except Exception:
            return 0, 0

    @classmethod
    async def pause_all(cls):
        await gather(cls.aria2.forcePauseAll(), cls.qbittorrent.torrents.stop("all"))

    @classmethod
    async def change_aria2_option(cls, key, value):
        downloads = []
        results = await gather(
            cls.aria2.tellActive(), cls.aria2.tellWaiting(0, 1000)
        )
        for res in results:
            downloads.extend(res)
        tasks = [
            cls.aria2.changeOption(download.get("gid"), {key: value})
            for download in downloads
        ]
        try:
            await gather(*tasks)
        except Exception:
            pass

    @classmethod
    async def get_aria2_options(cls):
        try:
            return await cls.aria2.getGlobalOption()
        except Exception:
            return {}

    @classmethod
    async def set_aria2_options(cls, options):
        try:
            await cls.aria2.changeGlobalOption(options)
        except Exception as e:
            LOGGER.error(f"Error setting aria2 options: {e}")

    @classmethod
    async def get_qbit_preferences(cls):
        try:
            return await cls.qbittorrent.app.preferences()
        except Exception:
            return {}

    @classmethod
    async def set_qbit_preferences(cls, preferences):
        try:
            await cls.qbittorrent.app.set_preferences(preferences)
        except Exception as e:
            LOGGER.error(f"Error setting qbit preferences: {e}")

    @classmethod
    async def aria2_init(cls):
        try:
            from bot import DOWNLOAD_DIR
            LOGGER.info("Initializing Aria2c")
            link = "https://linuxmint.com/torrents/lmde-5-cinnamon-64bit.iso.torrent"
            dire = DOWNLOAD_DIR.rstrip("/")
            gid = await cls.aria2.addUri(uris=[link], options={"dir": dire})
            import asyncio
            await asyncio.sleep(3)
            await asyncio.sleep(10)
            await cls.aria2.removeDownloadResult(gid)
            try:
                await cls.aria2.forceRemove(gid)
            except Exception:
                pass
        except Exception as e:
            LOGGER.error(f"Aria2c initializing error: {e}")
