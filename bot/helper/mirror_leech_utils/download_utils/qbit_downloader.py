from time import time
from asyncio import sleep
from os import path as ospath, remove as osremove
from bot import (
    QbInterval,
    QbTorrents,
    status_dict,
    status_dict_lock,
    qb_listener_lock,
    get_client,
    config_dict,
    botloop,
    LOGGER,
)
from bot.helper.ext_utils.bot_utils import get_readable_time, new_task, run_sync
from bot.helper.telegram_helper.message_utils import (
    deleteMessage,
    sendMarkup,
    sendMessage,
    sendStatusMessage,
    update_all_messages,
)
from bot.helper.ext_utils.misc_utils import bt_selection_buttons, getDownloadByGid
from bot.helper.mirror_leech_utils.status_utils.qbit_status import QbitTorrentStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import clean_unwanted


async def add_qb_torrent(link, path, listener, ratio, seed_time):
    client = await run_sync(get_client)
    ADD_TIME = time()
    try:
        url = link
        tpath = None
        if ospath.exists(link):
            url = None
            tpath = link
        op = await run_sync(
            client.torrents_add,
            url,
            tpath,
            path,
            tags=f"{listener.uid}",
            ratio_limit=ratio,
            seeding_time_limit=seed_time,
            headers={"user-agent": "Wget/1.12"},
        )
        if op.lower() == "ok.":
            tor_info = await run_sync(client.torrents_info, tag=f"{listener.uid}")
            if len(tor_info) == 0:
                while True:
                    tor_info = await run_sync(
                        client.torrents_info, tag=f"{listener.uid}"
                    )
                    if len(tor_info) > 0:
                        break
                    elif time() - ADD_TIME >= 120:
                        msg = "Not added! Check if the link is valid or not. If it's torrent file then report, this happens if torrent file size above 10mb."
                        await sendMessage(msg, listener.message)
                        return
            tor_info = tor_info[0]
            ext_hash = tor_info.hash
        else:
            await sendMessage(
                "This Torrent already added or unsupported/invalid link/file.",
                listener.message,
            )
            return

        async with status_dict_lock:
            status_dict[listener.uid] = QbitTorrentStatus(listener)
        await onDownloadStart(f"{listener.uid}")

        if not config_dict["NO_TASKS_LOGS"]:
            LOGGER.info(f"QbitDownload started: {tor_info.name} - Hash: {ext_hash}")

        if config_dict["QB_BASE_URL"] and listener.select:
            if link.startswith("magnet:"):
                metamsg = "Downloading Metadata, wait then you can select files. Use torrent file to avoid this wait."
                meta = await sendMessage(metamsg, listener.message)
                while True:
                    tor_info = await run_sync(
                        client.torrents_info, tag=f"{listener.uid}"
                    )
                    if len(tor_info) == 0:
                        await deleteMessage(meta)
                        return
                    try:
                        tor_info = tor_info[0]
                        if tor_info.state not in [
                            "metaDL",
                            "checkingResumeData",
                            "pausedDL",
                        ]:
                            await deleteMessage(meta)
                            break
                    except:
                        await deleteMessage(meta)
                        return

            ext_hash = tor_info.hash
            await run_sync(client.torrents_pause, torrent_hashes=ext_hash)
            SBUTTONS = bt_selection_buttons(ext_hash)
            msg = "Your download paused. Choose files then press Done Selecting button to start downloading."
            await sendMarkup(msg, listener.message, SBUTTONS)
        else:
            await sendStatusMessage(listener.message)
    except Exception as e:
        await sendMessage(str(e), listener.message)
    finally:
        if ospath.exists(link):
            osremove(link)


#### QBIT_LISTENER ####


async def __remove_torrent(client, hash_, tag):
    await run_sync(client.torrents_delete, torrent_hashes=hash_, delete_files=True)
    async with qb_listener_lock:
        if tag in QbTorrents:
            del QbTorrents[tag]
    await run_sync(client.torrents_delete_tags, tags=tag)


@new_task
async def __onDownloadError(err, tor):
    LOGGER.info(f"Cancelling Download: {tor.name}")
    ext_hash = tor.hash
    download = await getDownloadByGid(ext_hash[:12])
    if not hasattr(download, "client"):
        return
    listener = download.listener()
    client = download.client()
    await listener.onDownloadError(err)
    await run_sync(client.torrents_pause, torrent_hashes=ext_hash)
    await sleep(0.3)
    await __remove_torrent(client, ext_hash, tor.tags)


@new_task
async def __onSeedFinish(tor):
    ext_hash = tor.hash
    LOGGER.info(f"Cancelling Seed: {tor.name}")
    download = await getDownloadByGid(ext_hash[:12])
    if not hasattr(download, "client"):
        return
    listener = download.listener()
    client = download.client()
    msg = f"Seeding stopped with Ratio: {round(tor.ratio, 3)} and Time: {get_readable_time(tor.seeding_time)}"
    await listener.onUploadError(msg)
    await __remove_torrent(client, ext_hash, tor.tags)


@new_task
async def __onDownloadComplete(tor):
    ext_hash = tor.hash
    tag = tor.tags
    await sleep(2)
    download = await getDownloadByGid(ext_hash[:12])
    if not hasattr(download, "client"):
        return
    listener = download.listener()
    client = download.client()
    if not listener.seed:
        await run_sync(client.torrents_pause, torrent_hashes=ext_hash)
    if listener.select:
        await clean_unwanted(listener.dir)
    await listener.onDownloadComplete()
    client = await run_sync(get_client)
    if listener.seed:
        async with status_dict_lock:
            if listener.uid in status_dict:
                removed = False
                status_dict[listener.uid] = QbitTorrentStatus(listener, True)
            else:
                removed = True
        if removed:
            await __remove_torrent(client, ext_hash, tag)
            return
        async with qb_listener_lock:
            if tag in QbTorrents:
                QbTorrents[tag]["seeding"] = True
            else:
                return
        await update_all_messages()
        if not config_dict["NO_TASKS_LOGS"]:
            LOGGER.info(f"Seeding started: {tor.name} - Hash: {ext_hash}")
        await run_sync(client.auth_log_out)
    else:
        await __remove_torrent(client, ext_hash, tag)


async def __qb_listener():
    client = await run_sync(get_client)
    while True:
        async with qb_listener_lock:
            try:
                if len(await run_sync(client.torrents_info)) == 0:
                    QbInterval.clear()
                    await run_sync(client.auth_log_out)
                    break
                for tor_info in await run_sync(client.torrents_info):
                    tag = tor_info.tags
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
                            await run_sync(
                                client.torrents_reannounce, torrent_hashes=tor_info.hash
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
                            await run_sync(
                                client.torrents_recheck, torrent_hashes=tor_info.hash
                            )
                            QbTorrents[tag]["rechecked"] = True
                        elif (
                            TORRENT_TIMEOUT
                            and time() - QbTorrents[tag]["stalled_time"]
                            >= TORRENT_TIMEOUT
                        ):
                            __onDownloadError("Dead Torrent!", tor_info)
                        else:
                            await run_sync(
                                client.torrents_reannounce, torrent_hashes=tor_info.hash
                            )
                    elif state == "missingFiles":
                        await run_sync(
                            client.torrents_recheck, torrent_hashes=tor_info.hash
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
                client = await run_sync(get_client)
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
        if not QbInterval:
            periodic = botloop.create_task(__qb_listener())
            QbInterval.append(periodic)
