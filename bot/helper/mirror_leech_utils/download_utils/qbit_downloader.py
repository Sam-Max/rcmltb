from hashlib import sha1
from base64 import b16encode, b32decode
from bencoding import bencode, bdecode
from time import time
from asyncio import Lock, sleep
from re import search as re_search
from os import remove
from bot import QbInterval, status_dict, status_dict_lock, get_client, config_dict, LOGGER
from bot.helper.ext_utils.bot_utils import get_readable_time, run_sync, setInterval
from bot.helper.ext_utils.message_utils import deleteMessage, sendMarkup, sendMessage, sendStatusMessage, update_all_messages
from bot.helper.ext_utils.misc_utils import bt_selection_buttons, getDownloadByGid
from bot.helper.mirror_leech_utils.status_utils.qbit_status import QbDownloadStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import clean_unwanted


qb_download_lock = Lock()
STALLED_TIME = {}
RECHECKED = set()
UPLOADED = set()
SEEDING = set()


def __get_hash_magnet(mgt: str):
    hash_ = re_search(r'(?<=xt=urn:btih:)[a-zA-Z0-9]+', mgt).group(0)
    if len(hash_) == 32:
        hash_ = b16encode(b32decode(str(hash_))).decode()
    return str(hash_)

def __get_hash_file(path):
    with open(path, "rb") as f:
        decodedDict = bdecode(f.read())
        hash_ = sha1(bencode(decodedDict[b'info'])).hexdigest()
    return str(hash_)

async def add_qb_torrent(link, path, listener):
    client = await run_sync(get_client)
    ADD_TIME = time()
    try:
        if link.startswith('magnet:'):
            ext_hash = await run_sync(__get_hash_magnet, link)  
        else:
            ext_hash = await run_sync(__get_hash_file, link)
        if ext_hash is None or len(ext_hash) < 30:
            return await sendMessage("Not a torrent! Qbittorrent only for torrents!", listener.message)
        tor_info = client.torrents_info(torrent_hashes=ext_hash)
        if len(tor_info) > 0:
            return await sendMessage("This Torrent already added!", listener.message)
        if link.startswith('magnet:'):
            op = await run_sync(client.torrents_add, link, save_path=path)
        else:
            op = await run_sync(client.torrents_add, torrent_files=[link], save_path=path)
        await sleep(0.3)
        if op.lower() == "ok.":
            tor_info = await run_sync(client.torrents_info, torrent_hashes=ext_hash)
            if len(tor_info) == 0:
                while True:
                    tor_info = await run_sync(client.torrents_info, torrent_hashes=ext_hash)
                    if len(tor_info) > 0:
                        break
                    elif time() - ADD_TIME >= 120:
                        msg = msg = "Not added! Check if the link is valid or not. If it's torrent file then report, this happens if torrent file size above 10mb."
                        await sendMessage(msg, listener.message)
                        await __remove_torrent(client, ext_hash)
                        await run_sync(client.auth_log_out)
                        return
        else:
            await sendMessage("This is an unsupported/invalid link.", listener.message)
            await __remove_torrent(client, ext_hash)
            return
        tor_info = tor_info[0]
        ext_hash = tor_info.hash
        async with status_dict_lock:
            status_dict[listener.uid] = QbDownloadStatus(listener, ext_hash)
        async with qb_download_lock:
            STALLED_TIME[ext_hash] = time()
            if not QbInterval:
                periodic = setInterval(5, __qb_listener)
                QbInterval.append(periodic)
        LOGGER.info(f"QbitDownload started: {tor_info.name} - Hash: {ext_hash}")
        if config_dict['QB_BASE_URL'] and listener.select:
            if link.startswith('magnet:'):
                metamsg = "Downloading Metadata, wait then you can select files. Use torrent file to avoid this wait."
                meta = await sendMessage(metamsg, listener.message)
                while True:
                    tor_info = await run_sync(client.torrents_info, torrent_hashes=ext_hash)
                    if len(tor_info) == 0:
                        return await deleteMessage(meta)
                    try:
                        tor_info = tor_info[0]
                        if tor_info.state not in ["metaDL", "checkingResumeData", "pausedDL"]:
                            await deleteMessage(meta)
                            break
                    except:
                        return await deleteMessage(meta)
            await run_sync(client.torrents_pause, torrent_hashes=ext_hash)
            SBUTTONS = bt_selection_buttons(ext_hash)
            msg = "Your download paused. Choose files then press Done Selecting button to start downloading."
            await sendMarkup(msg, listener.message, SBUTTONS)
        else:
            await sendStatusMessage(listener.message)
    except Exception as e:
        await sendMessage(str(e), listener.message)
    finally:
        if not link.startswith('magnet:'):
            remove(link)
        await run_sync(client.auth_log_out)    
        

async def __remove_torrent(client, hash_):
    await run_sync(client.torrents_delete, torrent_hashes=hash_, delete_files=True)    
    async with qb_download_lock:
        if hash_ in STALLED_TIME:
            del STALLED_TIME[hash_]
        if hash_ in RECHECKED:
            RECHECKED.remove(hash_)
        if hash_ in UPLOADED:
            UPLOADED.remove(hash_)
        if hash_ in SEEDING:
            SEEDING.remove(hash_)

async def __onDownloadError(err, client, tor):
    LOGGER.info(f"Cancelling Download: {tor.name}")
    await run_sync(client.torrents_pause, torrent_hashes=tor.hash)    
    await sleep(0.3)
    download = await getDownloadByGid(tor.hash[:12])
    try:
        listener = download.listener()
        await listener.onDownloadError(err)
    except:
        pass
    await __remove_torrent(client, tor.hash)

async def __onSeedFinish(client, tor):
    LOGGER.info(f"Cancelling Seed: {tor.name}")
    download = await getDownloadByGid(tor.hash[:12])
    try:
        listener = download.listener()
        await listener.onUploadError(f"Seeding stopped with Ratio: {round(tor.ratio, 3)} and Time: {get_readable_time(tor.seeding_time)}")
    except:
        pass
    await __remove_torrent(client, tor.hash)

async def __onDownloadComplete(client, tor):
    await sleep(2)
    download = await getDownloadByGid(tor.hash[:12])
    try:
        listener = download.listener()
    except:
        return
    if not listener.seed:
        await run_sync(client.torrents_pause, torrent_hashes=tor.hash)
    if listener.select:
        await clean_unwanted(listener.dir)
    await listener.onDownloadComplete()
    if listener.seed:
        async with status_dict_lock:
            if listener.uid in status_dict:
                removed = False
                status_dict[listener.uid] = QbDownloadStatus(listener, tor.hash, True)
            else:
                removed = True
        if removed:
            await __remove_torrent(client, tor.hash)
            return
        async with qb_download_lock:
            SEEDING.add(tor.hash)
        await update_all_messages()
        LOGGER.info(f"Seeding started: {tor.name} - Hash: {tor.hash}")
    else:
       await __remove_torrent(client, tor.hash)

async def __qb_listener():
    client = await run_sync(get_client)
    if len(await run_sync(client.torrents_info)) == 0:
        QbInterval[0].cancel()
        QbInterval.clear()
        await run_sync(client.auth_log_out)
        return
    try:
        for tor_info in await run_sync(client.torrents_info):
            if tor_info.state == "metaDL":
                STALLED_TIME[tor_info.hash] = time()
                TORRENT_TIMEOUT = config_dict['TORRENT_TIMEOUT']
                if TORRENT_TIMEOUT and time() - tor_info.added_on >= TORRENT_TIMEOUT:
                    await __onDownloadError("Dead Torrent!", client, tor_info)
                else:
                    await run_sync(client.torrents_reannounce, torrent_hashes=tor_info.hash)
            elif tor_info.state == "downloading":
                STALLED_TIME[tor_info.hash] = time()
            elif tor_info.state == "stalledDL":
                TORRENT_TIMEOUT = config_dict['TORRENT_TIMEOUT']
                if tor_info.hash not in RECHECKED and 0.99989999999999999 < tor_info.progress < 1:
                    msg = f"Force recheck - Name: {tor_info.name} Hash: "
                    msg += f"{tor_info.hash} Downloaded Bytes: {tor_info.downloaded} "
                    msg += f"Size: {tor_info.size} Total Size: {tor_info.total_size}"
                    LOGGER.error(msg)
                    await run_sync(client.torrents_recheck, torrent_hashes=tor_info.hash)
                    RECHECKED.add(tor_info.hash)
                elif TORRENT_TIMEOUT and time() - STALLED_TIME.get(tor_info.hash, 0) >= TORRENT_TIMEOUT:
                    await __onDownloadError("Dead Torrent!", client, tor_info)
                else:
                    await run_sync(client.torrents_reannounce, torrent_hashes=tor_info.hash)
            elif tor_info.state == "missingFiles":
                client.torrents_recheck(torrent_hashes=tor_info.hash)
            elif tor_info.state == "error":
                await __onDownloadError("No enough space for this torrent on device", client, tor_info)
            elif (tor_info.completion_on != 0 or tor_info.state.endswith("UP") or tor_info.state == "uploading") \
                    and tor_info.hash not in UPLOADED and tor_info.state not in ['checkingUP', 'checkingDL']:
                UPLOADED.add(tor_info.hash)
                await __onDownloadComplete(client, tor_info)
            elif tor_info.state in ['pausedUP', 'pausedDL'] and tor_info.hash in SEEDING:
                SEEDING.remove(tor_info.hash)
                await __onSeedFinish(client, tor_info)
    except Exception as e:
        LOGGER.error(str(e))
    finally:
        await run_sync(client.auth_log_out)
