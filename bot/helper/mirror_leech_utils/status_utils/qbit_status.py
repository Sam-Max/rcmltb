from asyncio import sleep
from bot import LOGGER, QbTorrents, qb_listener_lock, config_dict
from bot.core.torrent_manager import TorrentManager
from bot.helper.ext_utils.bot_utils import (
    MirrorStatus,
    get_readable_file_size,
    get_readable_time,
)


class QbitTorrentStatus:
    def __init__(self, listener, seeding=False):
        self.__listener = listener
        self.__info = None
        self.seeding = seeding
        self.message = listener.message

    async def __update(self):
        try:
            tor_info = await TorrentManager.qbittorrent.torrents.info(
                tag=f"{self.__listener.uid}"
            )
            if tor_info:
                self.__info = tor_info[0]
        except Exception as e:
            LOGGER.error(f"{e}: Qbittorrent, Error while getting torrent info")

    async def progress(self):
        await self.__update()
        if self.__info is None:
            return "0%"
        return f"{round(self.__info.progress * 100, 2)}%"

    def processed_bytes(self):
        if self.__info is None:
            return "0B"
        return get_readable_file_size(self.__info.downloaded)

    def speed(self):
        if self.__info is None:
            return "0B/s"
        return f"{get_readable_file_size(self.__info.dlspeed)}/s"

    def name(self):
        if self.__info is None:
            return "N/A"
        if self.__info.state in ["metaDL", "checkingResumeData"]:
            return f"[METADATA]{self.__info.name}"
        return self.__info.name

    def size(self):
        if self.__info is None:
            return "0B"
        return get_readable_file_size(self.__info.size)

    def eta(self):
        if self.__info is None:
            return "-"
        return get_readable_time(self.__info.eta)

    async def status(self):
        await self.__update()
        if self.__info is None:
            return MirrorStatus.STATUS_DOWNLOADING
        state = self.__info.state
        if state == "queuedDL":
            return MirrorStatus.STATUS_QUEUEDL
        elif state == "queuedUP":
            return MirrorStatus.STATUS_QUEUEUP
        elif state in ["pausedDL", "pausedUP"]:
            return MirrorStatus.STATUS_PAUSED
        elif state in ["checkingUP", "checkingDL"]:
            return MirrorStatus.STATUS_CHECKING
        elif state in ["stalledUP", "uploading"] and self.seeding:
            return MirrorStatus.STATUS_SEEDING
        else:
            return MirrorStatus.STATUS_DOWNLOADING

    def seeders_num(self):
        if self.__info is None:
            return 0
        return self.__info.num_seeds

    def leechers_num(self):
        if self.__info is None:
            return 0
        return self.__info.num_leechs

    def uploaded_bytes(self):
        if self.__info is None:
            return "0B"
        return get_readable_file_size(self.__info.uploaded)

    def upload_speed(self):
        if self.__info is None:
            return "0B/s"
        return f"{get_readable_file_size(self.__info.upspeed)}/s"

    def ratio(self):
        if self.__info is None:
            return "0.0"
        return f"{round(self.__info.ratio, 3)}"

    def seeding_time(self):
        if self.__info is None:
            return "0s"
        return get_readable_time(self.__info.seeding_time)

    def task(self):
        return self

    def gid(self):
        return self.hash()[:12]

    async def hash(self):
        await self.__update()
        if self.__info is None:
            return ""
        return self.__info.hash

    def client(self):
        return TorrentManager.qbittorrent

    def listener(self):
        return self.__listener

    def type(self):
        return "Qbit"

    async def cancel_task(self):
        await self.__update()
        if self.__info is None:
            return
        await TorrentManager.qbittorrent.torrents.stop(hashes=[self.__info.hash])
        if await self.status() != MirrorStatus.STATUS_SEEDING:
            if not config_dict["NO_TASKS_LOGS"]:
                LOGGER.info(f"Cancelling Download: {self.__info.name}")
            await sleep(0.3)
            await self.__listener.onDownloadError("Download stopped by user!")
            await TorrentManager.qbittorrent.torrents.delete(
                hashes=[self.__info.hash], delete_files=True
            )
            try:
                await TorrentManager.qbittorrent.torrents.delete_tags(
                    tags=[self.__info.tags]
                )
            except Exception:
                pass
            async with qb_listener_lock:
                if self.__info.tags in QbTorrents:
                    del QbTorrents[self.__info.tags]
