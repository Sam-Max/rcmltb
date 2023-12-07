from asyncio import sleep
from os import path as ospath, remove as osremove
from bot import (
    LOGGER,
    config_dict,
    status_dict_lock,
    status_dict,
    aria2,
    aria2c_global,
    aria2_options,
)
from bot.helper.ext_utils.bot_utils import clean_unwanted, new_thread, run_sync
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    sendStatusMessage,
    update_all_messages,
)
from bot.helper.ext_utils.misc_utils import getDownloadByGid
from bot.helper.mirror_leech_utils.status_utils.aria_status import AriaStatus


async def add_aria2c_download(link, path, listener, filename, auth):
    a2c_opt = {**aria2_options}
    [a2c_opt.pop(k) for k in aria2c_global if k in aria2_options]
    a2c_opt["dir"] = path
    if filename:
        a2c_opt["out"] = filename
    if auth:
        a2c_opt["header"] = f"authorization: {auth}"
    if TORRENT_TIMEOUT := config_dict["TORRENT_TIMEOUT"]:
        a2c_opt["bt-stop-timeout"] = f"{TORRENT_TIMEOUT}"
    try:
        download = (await run_sync(aria2.add, link, a2c_opt))[0]
    except Exception as e:
        LOGGER.info(f"Aria2c Download Error: {e}")
        await sendMessage(f"{e}", listener.message)
        return
    if ospath.exists(link):
        osremove(link)
    if download.error_message:
        error = str(download.error_message).replace("<", " ").replace(">", " ")
        LOGGER.info(f"Aria2c Download Error: {error}")
        await sendMessage(error, listener.message)
        return

    gid = download.gid
    name = download.name
    async with status_dict_lock:
        status_dict[listener.uid] = AriaStatus(gid, listener)

    if not config_dict["NO_TASKS_LOGS"]:
        LOGGER.info(f"Aria2Download started: {name}. Gid: {gid}")

    await listener.onDownloadStart()
    await sendStatusMessage(listener.message)


###### ARIA LISTENER #######


@new_thread
async def __onDownloadStarted(api, gid):
    download = await run_sync(api.get_download, gid)
    if not config_dict["NO_TASKS_LOGS"]:
        LOGGER.info(f"onDownloadStarted: {download.name} - Gid: {gid}")


@new_thread
async def __onDownloadComplete(api, gid):
    try:
        download = await run_sync(api.get_download, gid)
    except:
        return
    if not config_dict["NO_TASKS_LOGS"]:
        LOGGER.info(f"onDownloadComplete: {download.name} - Gid: {gid}")
    if dl := await getDownloadByGid(gid):
        listener = dl.listener()
        await listener.onDownloadComplete()
        await run_sync(api.remove, [download], force=True, files=True)


@new_thread
async def __onBtDownloadComplete(api, gid):
    seed_start_time = time()
    await sleep(1)
    download = await run_sync(api.get_download, gid)
    if not config_dict["NO_TASKS_LOGS"]:
        LOGGER.info(f"onBtDownloadComplete: {download.name} - Gid: {gid}")
    if dl := await getDownloadByGid(gid):
        listener = dl.listener()
        if listener.select:
            res = download.files
            for file_o in res:
                f_path = file_o.path
                if not file_o.selected and ospath.exists(f_path):
                    try:
                        osremove(f_path)
                    except:
                        pass
            await clean_unwanted(download.dir)
        if listener.seed:
            try:
                await run_sync(api.set_options, {"max-upload-limit": "0"}, [download])
            except Exception as e:
                LOGGER.error(
                    f"{e} You are not able to seed because you added global option seed-time=0 without adding specific seed_time for this torrent GID: {gid}"
                )
        else:
            try:
                await run_sync(api.client.force_pause, gid)
            except Exception as e:
                LOGGER.error(f"{e} GID: {gid}")
        await listener.onDownloadComplete()
        download = download.live
        if listener.seed:
            if download.is_complete:
                if dl := await getDownloadByGid(gid):
                    if not config_dict["NO_TASKS_LOGS"]:
                        LOGGER.info(f"Cancelling Seed: {download.name}")
                    await listener.onUploadError(
                        f"Seeding stopped with Ratio: {dl.ratio()} and Time: {dl.seeding_time()}"
                    )
                    await run_sync(api.remove, [download], force=True, files=True)
            else:
                async with status_dict_lock:
                    if listener.uid not in status_dict:
                        await run_sync(api.remove, [download], force=True, files=True)
                        return
                    status_dict[listener.uid] = AriaStatus(gid, listener, True)
                    status_dict[listener.uid].start_time = seed_start_time
                if not config_dict["NO_TASKS_LOGS"]:
                    LOGGER.info(f"Seeding started: {download.name} - Gid: {gid}")
                await update_all_messages()
        else:
            await run_sync(api.remove, [download], force=True, files=True)


@new_thread
async def __onDownloadStopped(api, gid):
    await sleep(6)
    if dl := await getDownloadByGid(gid):
        listener = dl.listener()
        await listener.onDownloadError("Dead torrent!")


@new_thread
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


def start_aria2_listener():
    aria2.listen_to_notifications(
        threaded=False,
        on_download_start=__onDownloadStarted,
        on_download_error=__onDownloadError,
        on_download_stop=__onDownloadStopped,
        on_download_complete=__onDownloadComplete,
        on_bt_download_complete=__onBtDownloadComplete,
        timeout=60,
    )
