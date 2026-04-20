from time import time
from asyncio import sleep

from bot import (
    QbTorrents,
    status_dict,
    status_dict_lock,
    qb_listener_lock,
    config_dict,
    bot_loop,
    LOGGER,
)
from bot.core.torrent_manager import TorrentManager
from bot.helper.ext_utils.bot_utils import get_readable_time, new_task
from bot.helper.ext_utils.misc_utils import getTaskByGid
from bot.helper.mirror_leech_utils.status_utils.qbit_status import QbitTorrentStatus
from bot.helper.telegram_helper.message_utils import update_all_messages


def _get_tag(tags):
    return tags[0] if isinstance(tags, list) else tags


async def __remove_torrent(hash_, tag):
    tag = _get_tag(tag)
    await TorrentManager.qbittorrent.torrents.delete(
        hashes=[hash_], delete_files=True
    )
    async with qb_listener_lock:
        if tag in QbTorrents:
            del QbTorrents[tag]
    try:
        await TorrentManager.qbittorrent.torrents.delete_tags(tags=[tag])
    except Exception:
        pass


@new_task
async def __onDownloadError(err, tor):
    LOGGER.info(f"Cancelling Download: {tor.name}")
    ext_hash = tor.hash
    download = await getTaskByGid(ext_hash[:12])
    if not hasattr(download, "client"):
        return
    listener = download.listener()
    await listener.onDownloadError(err)
    await TorrentManager.qbittorrent.torrents.stop(hashes=[ext_hash])
    await sleep(0.3)
    await __remove_torrent(ext_hash, tor.tags)


@new_task
async def __onSeedFinish(tor):
    ext_hash = tor.hash
    LOGGER.info(f"Cancelling Seed: {tor.name}")
    download = await getTaskByGid(ext_hash[:12])
    if not hasattr(download, "client"):
        return
    listener = download.listener()
    msg = f"Seeding stopped with Ratio: {round(tor.ratio, 3)} and Time: {get_readable_time(tor.seeding_time)}"
    await listener.onUploadError(msg)
    await __remove_torrent(ext_hash, tor.tags)


@new_task
async def __onDownloadComplete(tor):
    ext_hash = tor.hash
    tag = _get_tag(tor.tags)
    await sleep(2)
    download = await getTaskByGid(ext_hash[:12])
    if not hasattr(download, "client"):
        return
    listener = download.listener()
    if not listener.seed:
        await TorrentManager.qbittorrent.torrents.stop(hashes=[ext_hash])
    if listener.select:
        from bot.helper.mirror_leech_utils.status_utils.status_utils import (
            clean_unwanted,
        )

        await clean_unwanted(listener.dir)
    await listener.onDownloadComplete()
    if listener.seed:
        async with status_dict_lock:
            if listener.uid in status_dict:
                status_dict[listener.uid] = QbitTorrentStatus(listener, True)
                removed = False
            else:
                removed = True
        if removed:
            await __remove_torrent(ext_hash, tag)
            return
        async with qb_listener_lock:
            if tag in QbTorrents:
                QbTorrents[tag]["seeding"] = True
            else:
                return
        await update_all_messages()
        if not config_dict["NO_TASKS_LOGS"]:
            LOGGER.info(f"Seeding started: {tor.name} - Hash: {ext_hash}")
    else:
        await __remove_torrent(ext_hash, tag)


async def __qb_listener():
    while True:
        async with qb_listener_lock:
            try:
                torrents = await TorrentManager.qbittorrent.torrents.info()
                if len(torrents) == 0:
                    from bot import QbInterval

                    QbInterval.clear()
                    break
                for tor_info in torrents:
                    tag = _get_tag(tor_info.tags)
                    if tag not in QbTorrents:
                        continue
                    state = tor_info.state
                    if state == "metaDL":
                        TORRENT_TIMEOUT = config_dict["TORRENT_TIMEOUT"]
                        QbTorrents[tag]["stalled_time"] = time()
                        if (
                            TORRENT_TIMEOUT
                            and time() - tor_info.added_on >= TORRENT_TIMEOUT
                        ):
                            __onDownloadError("Dead Torrent!", tor_info)
                        else:
                            await TorrentManager.qbittorrent.torrents.reannounce(
                                hashes=[tor_info.hash]
                            )
                    elif state == "downloading":
                        QbTorrents[tag]["stalled_time"] = time()
                    elif state == "stalledDL":
                        TORRENT_TIMEOUT = config_dict["TORRENT_TIMEOUT"]
                        if (
                            not QbTorrents[tag]["rechecked"]
                            and 0.99989999999999999 < tor_info.progress < 1
                        ):
                            msg = f"Force recheck - Name: {tor_info.name} Hash: "
                            msg += f"{tor_info.hash} Downloaded Bytes: {tor_info.downloaded} "
                            msg += f"Size: {tor_info.size} Total Size: {tor_info.total_size}"
                            LOGGER.warning(msg)
                            await TorrentManager.qbittorrent.torrents.recheck(
                                hashes=[tor_info.hash]
                            )
                            QbTorrents[tag]["rechecked"] = True
                        elif (
                            TORRENT_TIMEOUT
                            and time() - QbTorrents[tag]["stalled_time"]
                            >= TORRENT_TIMEOUT
                        ):
                            __onDownloadError("Dead Torrent!", tor_info)
                        else:
                            await TorrentManager.qbittorrent.torrents.reannounce(
                                hashes=[tor_info.hash]
                            )
                    elif state == "missingFiles":
                        await TorrentManager.qbittorrent.torrents.recheck(
                            hashes=[tor_info.hash]
                        )
                    elif state == "error":
                        __onDownloadError(
                            "No enough space for this torrent on device", tor_info
                        )
                    elif (
                        tor_info.completion_on != 0
                        and not QbTorrents[tag]["uploaded"]
                        and state
                        not in ["checkingUP", "checkingDL", "checkingResumeData"]
                    ):
                        QbTorrents[tag]["uploaded"] = True
                        __onDownloadComplete(tor_info)
                    elif (
                        state in ["pausedUP", "pausedDL"] and QbTorrents[tag]["seeding"]
                    ):
                        QbTorrents[tag]["seeding"] = False
                        __onSeedFinish(tor_info)
            except Exception as e:
                LOGGER.error(str(e))
        await sleep(3)


async def onDownloadStart(tag):
    async with qb_listener_lock:
        QbTorrents[tag] = {
            "stalled_time": time(),
            "stop_dup_check": False,
            "rechecked": False,
            "uploaded": False,
            "seeding": False,
        }
        if not __import__("bot").QbInterval:
            periodic = bot_loop.create_task(__qb_listener())
            __import__("bot").QbInterval.append(periodic)
