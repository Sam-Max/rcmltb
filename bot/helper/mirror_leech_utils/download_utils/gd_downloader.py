from random import SystemRandom
from string import ascii_letters, digits
from bot import status_dict, status_dict_lock, LOGGER
from bot.helper.ext_utils.message_utils import sendMessage, sendStatusMessage
from bot.helper.mirror_leech_utils.status_utils.gd_download_status import GdDownloadStatus
from bot.helper.mirror_leech_utils.upload_utils.gdriveTools import GoogleDriveHelper


async def add_gd_download(link, path, listener, newname):
    res, size, name, files = GoogleDriveHelper().helper(link)
    if res != "":
        return await sendMessage(res, listener.message)
    if newname:
        name = newname
    LOGGER.info(f"Download Name: {name}")
    drive = GoogleDriveHelper(name, path, listener)
    gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=12))
    download_status = GdDownloadStatus(drive, size, listener, gid)
    async with status_dict_lock:
        status_dict[listener.uid] = download_status
    await sendStatusMessage(listener.message)
    await drive.download(link)
