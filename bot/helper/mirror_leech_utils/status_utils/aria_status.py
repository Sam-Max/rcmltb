from time import time
from bot import LOGGER
from bot.core.torrent_manager import TorrentManager, aria2_name
from bot.helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


def aria2_get_progress(download):
    total = int(download.get("totalLength", "0"))
    completed = int(download.get("completedLength", "0"))
    if total == 0:
        return "0%"
    return f"{round(completed / total * 100, 2)}%"


def aria2_get_size(download):
    total = int(download.get("totalLength", "0"))
    return get_readable_file_size(total)


def aria2_get_completed(download):
    completed = int(download.get("completedLength", "0"))
    return get_readable_file_size(completed)


def aria2_get_speed(download):
    speed = int(download.get("downloadSpeed", "0"))
    return f"{get_readable_file_size(speed)}/s"


def aria2_get_eta(download):
    total = int(download.get("totalLength", "0"))
    completed = int(download.get("completedLength", "0"))
    speed = int(download.get("downloadSpeed", "0"))
    if speed == 0:
        return "-"
    remaining = total - completed
    return get_readable_time(remaining // speed)


def aria2_get_upload_speed(download):
    speed = int(download.get("uploadSpeed", "0"))
    return f"{get_readable_file_size(speed)}/s"


def aria2_get_uploaded(download):
    uploaded = int(download.get("uploadLength", "0"))
    return get_readable_file_size(uploaded)


def aria2_get_ratio(download):
    completed = int(download.get("completedLength", "0"))
    uploaded = int(download.get("uploadLength", "0"))
    if completed == 0:
        return "0.0"
    return f"{round(uploaded / completed, 3)}"


class AriaStatus:
    def __init__(self, gid, listener, seeding=False):
        self.__gid = gid
        self.__listener = listener
        self.__download = None
        self.start_time = 0
        self.seeding = seeding
        self.message = listener.message

    async def __update(self):
        try:
            self.__download = await TorrentManager.aria2.tellStatus(self.__gid)
            followed_by = self.__download.get("followedBy", [])
            if followed_by:
                self.__gid = followed_by[0]
                self.__download = await TorrentManager.aria2.tellStatus(self.__gid)
        except Exception as e:
            LOGGER.error(f"{e}: Aria2c, Error while getting torrent info")

    async def progress(self):
        await self.__update()
        if self.__download is None:
            return "0%"
        return aria2_get_progress(self.__download)

    async def processed_bytes(self):
        await self.__update()
        if self.__download is None:
            return "0B"
        return aria2_get_completed(self.__download)

    async def speed(self):
        await self.__update()
        if self.__download is None:
            return "0B/s"
        return aria2_get_speed(self.__download)

    def name(self):
        if self.__download is None:
            return "N/A"
        return aria2_name(self.__download)

    def size(self):
        if self.__download is None:
            return "0B"
        return aria2_get_size(self.__download)

    def eta(self):
        if self.__download is None:
            return "-"
        return aria2_get_eta(self.__download)

    async def status(self):
        await self.__update()
        if self.__download is None:
            return MirrorStatus.STATUS_DOWNLOADING
        status = self.__download.get("status", "")
        if status == "waiting" or status == "paused":
            if self.seeding:
                return MirrorStatus.STATUS_QUEUEUP
            elif status == "paused":
                return MirrorStatus.STATUS_PAUSED
            else:
                return MirrorStatus.STATUS_QUEUEDL
        elif self.__download.get("seeder", False) and self.seeding:
            return MirrorStatus.STATUS_SEEDING
        else:
            return MirrorStatus.STATUS_DOWNLOADING

    def seeders_num(self):
        if self.__download is None:
            return 0
        return self.__download.get("bittorrent", {}).get("info", {}).get("numSeeders", 0)

    def leechers_num(self):
        if self.__download is None:
            return 0
        return self.__download.get("connections", "0")

    def uploaded_bytes(self):
        if self.__download is None:
            return "0B"
        return aria2_get_uploaded(self.__download)

    async def upload_speed(self):
        await self.__update()
        if self.__download is None:
            return "0B/s"
        return aria2_get_upload_speed(self.__download)

    def ratio(self):
        if self.__download is None:
            return "0.0"
        return aria2_get_ratio(self.__download)

    def seeding_time(self):
        return get_readable_time(time() - self.start_time)

    def listener(self):
        return self.__listener

    def task(self):
        return self

    async def gid(self):
        await self.__update()
        return self.__gid

    def type(self):
        return "Aria"

    async def cancel_task(self):
        await self.__update()
        if self.__download is None:
            return
        if self.__download.get("seeder", False) and self.seeding:
            LOGGER.info(f"Cancelling Seed: {self.name()}")
            await self.__listener.onUploadError(
                f"Seeding stopped with Ratio: {self.ratio()} and Time: {self.seeding_time()}"
            )
            await TorrentManager.aria2_remove(self.__download)
        elif self.__download.get("followedBy", []):
            LOGGER.info(f"Cancelling Download: {self.name()}")
            await self.__listener.onDownloadError("Download cancelled by user!")
            for gid in self.__download.get("followedBy", []):
                try:
                    dl = await TorrentManager.aria2.tellStatus(gid)
                    await TorrentManager.aria2_remove(dl)
                except Exception:
                    pass
            await TorrentManager.aria2_remove(self.__download)
        else:
            LOGGER.info(f"Cancelling Download: {self.name()}")
            await self.__listener.onDownloadError("Download stopped by user!")
            await TorrentManager.aria2_remove(self.__download)
