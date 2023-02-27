from asyncio import run_coroutine_threadsafe, sleep
from bot import LOGGER, config_dict, status_dict_lock, status_dict, aria2, botloop, aria2c_global, aria2_options
from bot.helper.ext_utils.bot_utils import is_magnet, run_sync, run_thread_dec
from bot.helper.ext_utils.message_utils import sendMessage, sendStatusMessage
from bot.helper.ext_utils.misc_utils import getDownloadByGid
from bot.helper.mirror_leech_utils.status_utils.aria_status import AriaDownloadStatus



@run_thread_dec
async def __onDownloadStarted(api, gid):
    download = await run_sync(api.get_download, gid)
    if download.is_metadata:
        LOGGER.info(f'onDownloadStarted: {gid} METADATA')
        await sleep(1)
    else:
        LOGGER.info(f'onDownloadStarted: {download.name} - Gid: {gid}')

@run_thread_dec
async def __onDownloadComplete(api, gid):
    try:
        download = await run_sync(api.get_download, gid)
    except:
        return
    if download.followed_by_ids:
        new_gid = download.followed_by_ids[0]
        LOGGER.info(f'Gid changed from {gid} to {new_gid}')
    else:
        LOGGER.info(f"onDownloadComplete: {download.name} - Gid: {gid}")
        if dl := await getDownloadByGid(gid):
            listener = dl.listener()
            await listener.onDownloadComplete()
            await run_sync(api.remove, [download], force=True, files=True)

@run_thread_dec
async def __onBtDownloadComplete(api, gid):
    await sleep(1)
    download = await run_sync(api.get_download, gid)
    LOGGER.info(f"onBtDownloadComplete: {download.name} - Gid: {gid}")
    if dl := await getDownloadByGid(gid):
        listener = dl.listener()
        try:
            await run_sync(api.client.force_pause, gid)
        except Exception as e:
            LOGGER.error(f"{e} GID: {gid}" )
        await listener.onDownloadComplete()
        download = download.live
        await run_sync(api.remove, [download], force=True, files=True)

@run_thread_dec
async def __onDownloadStopped(api, gid):
    await sleep(6)
    if dl := await getDownloadByGid(gid):
        listener = dl.listener()
        await listener.onDownloadError('Dead torrent!')

@run_thread_dec      
async def __onDownloadError(api, gid):
    LOGGER.info(f"onDownloadError: {gid}")
    error = "None"
    try:
        download = await run_sync(api.get_download, gid)
        error = download.error_message
        LOGGER.info(f"Download Error: {error}")
    except:
        pass
    if dl := await getDownloadByGid(gid):
        listener = dl.listener()
        await listener.onDownloadError(error)

def start_listener():
    aria2.listen_to_notifications(threaded=True,
                                  on_download_start= __onDownloadStarted,
                                  on_download_error=__onDownloadError,
                                  on_download_stop=__onDownloadStopped,
                                  on_download_complete=__onDownloadComplete,
                                  on_bt_download_complete=__onBtDownloadComplete,
                                  timeout=60)

async def add_aria2c_download(link: str, path, listener, filename, auth):
    args = {'dir': path, 'max-upload-limit': '1K', 'netrc-path': '/usr/src/app/.netrc'}
    a2c_opt = {**aria2_options}
    [a2c_opt.pop(k) for k in aria2c_global if k in aria2_options]
    args.update(a2c_opt)
    if filename:
        args['out'] = filename
    if auth:
        args['header'] = f"authorization: {auth}"
    if TORRENT_TIMEOUT := config_dict['TORRENT_TIMEOUT']:
        args['bt-stop-timeout'] = str(TORRENT_TIMEOUT)
    if is_magnet(link):
        download = await run_sync(aria2.add_magnet, link, args)
    else:
        download = await run_sync(aria2.add_uris, [link], args)
    if download.error_message:
        error = str(download.error_message).replace('<', ' ').replace('>', ' ')
        LOGGER.info(f"Download Error: {error}")
        return await sendMessage(error, listener.message)
    async with status_dict_lock:
        status_dict[listener.uid] = AriaDownloadStatus(download.gid, listener)
        LOGGER.info(f"Aria2Download started: {download.gid}")
    await sendStatusMessage(listener.message)


start_listener()
