from random import SystemRandom
from string import ascii_letters, digits
from bot import status_dict, status_dict_lock, config_dict, LOGGER
from bot.helper.ext_utils.bot_utils import run_sync_to_async
from bot.helper.mirror_leech_utils.gd_utils.count import gdCount
from bot.helper.mirror_leech_utils.gd_utils.download import gdDownload
from bot.helper.telegram_helper.message_utils import sendMessage, sendStatusMessage
from bot.helper.mirror_leech_utils.status_utils.gdrive_status import GdriveStatus


async def add_gd_download(link, new_name, path, listener):
    drive = gdCount()
    name, mime_type, size, _, _ = await run_sync_to_async(
        drive.count, link, listener.user_id
    )
    if mime_type is None:
        await sendMessage(name, listener.message)
        return

    gid = "".join(SystemRandom().choices(ascii_letters + digits, k=12))
    name = new_name or name

    drive = gdDownload(listener, name, link, path)
    async with status_dict_lock:
        status_dict[listener.uid] = GdriveStatus(drive, size, listener.message, gid)

    if not config_dict["NO_TASKS_LOGS"]:
        LOGGER.info(f"Download from GDrive: {name}")

    await listener.onDownloadStart()
    await sendStatusMessage(listener.message)
    await run_sync_to_async(drive.download)
