from random import SystemRandom
from string import ascii_letters, digits
from bot import status_dict, status_dict_lock, config_dict, LOGGER
from bot.helper.ext_utils.bot_utils import run_sync
from bot.helper.telegram_helper.message_utils import sendMessage, sendStatusMessage
from bot.helper.mirror_leech_utils.status_utils.gdrive_status import GdriveStatus
from bot.helper.mirror_leech_utils.upload_utils.gdriveTools import GoogleDriveHelper


async def add_gd_download(link, path, listener, newname):
    drive = GoogleDriveHelper()
    name, mime_type, size, _, _ = await run_sync(drive.count, link)
    if mime_type is None:
        await sendMessage(name, listener.message)
        return

    name = newname or name
    gid = "".join(SystemRandom().choices(ascii_letters + digits, k=12))

    drive = GoogleDriveHelper(name, path, listener)
    async with status_dict_lock:
        status_dict[listener.uid] = GdriveStatus(drive, size, listener.message, gid)

    if not config_dict["NO_TASKS_LOGS"]:
        LOGGER.info(f"Download from GDrive: {name}")

    await listener.onDownloadStart()
    await sendStatusMessage(listener.message)
    await run_sync(drive.download, link)
