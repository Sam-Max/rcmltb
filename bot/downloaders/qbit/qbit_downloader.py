#**************************************************
# Modified from:
# Source: https://github.com/anasty17/mirror-leech-telegram-bot/blob/master/bot/helper/mirror_utils/download_utils/qbit_downloader.py
#**************************************************/

import asyncio
from hashlib import sha1
from base64 import b16encode, b32decode
import os
import shutil
from time import sleep, time
from psutil import cpu_percent, virtual_memory
from bencoding import bencode, bdecode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot import GLOBAL_QBIT, uptime
from re import search as re_search
from bot import get_client, TORRENT_TIMEOUT, LOGGER
from bot.utils.bot_utils import human_format
from bot.utils.bot_utils.bot_utils import get_readable_file_size, get_readable_time, setInterval

class QbDownloader:
    POLLING_INTERVAL = 3

    def __init__(self, message):
        self.__path = ''
        self.__name = ''
        self.__message= message
        self.__error_message= ''
        self.client = None
        self.ext_hash = ''
        self.__periodic = None
        self.__stalled_time = time()
        self.__cancel= False
        self.__completed = False
        self.__rechecked = False

    async def add_qb_torrent(self, link):
        self.__path =  os.path.join(os.getcwd(), "Downloads", str(time()).replace(".",""))
        self.client = get_client()
        try:
            if link.startswith('magnet:'):
                LOGGER.info("_get_hash_magnet")     
                self.ext_hash = _get_hash_magnet(link)
            else:
                self.ext_hash = _get_hash_file(link)
            
            tor_info = self.client.torrents_info(torrent_hashes=self.ext_hash)
            if len(tor_info) > 0:
                self.client.auth_log_out()
                return False, "This Torrent already added!", "", ""
            
            if link.startswith('magnet:'):
                op = self.client.torrents_add(link, save_path=self.__path)
            else:
                op = self.client.torrents_add(torrent_files=[link], save_path=self.__path)
            sleep(0.3)

            if op.lower() == "ok.":
                tor_info = self.client.torrents_info(torrent_hashes=self.ext_hash)
                if len(tor_info) == 0:
                    while True:
                        tor_info = self.client.torrents_info(torrent_hashes=self.ext_hash)
                        if len(tor_info) > 0:
                            break
                        elif time() - self.__stalled_time >= 30:
                            msg = "Not a torrent. If something wrong please report."
                            self.client.torrents_delete(torrent_hashes=self.ext_hash, delete_files=True)
                            self.client.auth_log_out()
                            return False, msg, "", ""
            else:
                self.client.auth_log_out()
                return False, "This is an unsupported/invalid link.", "", ""

            tor_info = tor_info[0]
            self.__name = tor_info.name
            self.ext_hash = tor_info.hash

            LOGGER.info(f"QbitDownload started: {self.__name} - Hash: {self.ext_hash}")
            self.__periodic = setInterval(self.POLLING_INTERVAL, self.__qb_listener)
            GLOBAL_QBIT.add(self) 
            status, msg= await self.qbit_progress_update()
            GLOBAL_QBIT.remove(self)  
            if not status:
                return False, msg, self.__path, self.__name
            else:
                return True, msg, self.__path, self.__name

        except Exception as e:
            await self.__message.edit(str(e))
            self.client.auth_log_out()

    async def qbit_progress_update(self):
        update_message1= ""
        sleeps= False
        while True:
            sleeps = True
            update_message= self.create_update_message()
            if update_message1 != update_message:
                try:
                    data = "cancel_qbitdl_{}".format(self.ext_hash)
                    await self.__message.edit(text=update_message, reply_markup=(InlineKeyboardMarkup([
                                            [InlineKeyboardButton('Cancel', callback_data=data.encode("UTF-8"))]
                                            ])))
                except Exception:
                    pass

                if sleeps:
                    if self.__cancel:     
                        return False, self.__error_message
                    if self.__completed:
                        return True, "Successfully Downloaded!"        
                    sleeps = False
                    await asyncio.sleep(5)

    def create_update_message(self):
        try:
            self.__info = self.client.torrents_info(torrent_hashes=self.ext_hash)[0]
        except Exception as e:
            LOGGER.error(f'{e}: while getting torrent info')

        bottom_status= ''
        diff = time() - uptime
        diff = human_format.human_readable_timedelta(diff)
        usage = shutil.disk_usage("/")
        free = human_format.human_readable_bytes(usage.free) 
        bottom_status += f"\n<b>CPU:</b> {cpu_percent()}% | <b>FREE:</b> {free}" + f"\n<b>RAM:</b> {virtual_memory().percent}% | <b>UPTIME:</b> {diff}"
       
        msg = "<b>Name:</b>{}\n".format(self.__info.name)
        msg += "<b>Status:</b> Downloading...\n"
        msg += "{}\n".format(self.get_progress_bar_string())
        msg += "<b>P:</b>{}\n".format(f'{round(self.__info.progress*100, 2)}%')
        msg += "<b>Downloaded:</b> {} <b>of:</b> {}\n".format(get_readable_file_size(self.__info.downloaded), get_readable_file_size(self.__info.total_size))
        msg += "<b>Speed:</b> {}".format(f"{get_readable_file_size(self.__info.dlspeed)}/s") + "|" + "<b>ETA: {}\n</b>".format(get_readable_time(self.__info.eta))
        try:
            msg += f"<b>Seeders:</b> {self.__info.num_seeds}" \
                    f" | <b>Leechers:</b> {self.__info.num_leechs}\n"
        except:
            pass
        return msg + bottom_status

    def get_progress_bar_string(self):
        completed = self.__info.downloaded / 8
        total = self.__info.total_size / 8
        p = 0 if total == 0 else round(completed * 100 / total)
        p = min(max(p, 0), 100)
        cFull = p // 8
        p_str = '■' * cFull
        p_str += '□' * (12 - cFull)
        p_str = f"[{p_str}]"
        return p_str

    def __qb_listener(self):
        try:
            tor_info = self.client.torrents_info(torrent_hashes=self.ext_hash)
            if len(tor_info) == 0:
                return
            tor_info = tor_info[0]
            if tor_info.state_enum.is_complete:
                LOGGER.info(f'Qbit download completed.')        
                self.__completed = True     
                self.__periodic.cancel()
            elif tor_info.state == "metaDL":
                self.__stalled_time = time()
                if TORRENT_TIMEOUT is not None and time() - tor_info.added_on >= TORRENT_TIMEOUT:
                    self.__onDownloadError("Dead Torrent!")
            elif tor_info.state == "downloading":
                self.__stalled_time = time()
            elif tor_info.state == "stalledDL":
                if not self.__rechecked and 0.99989999999999999 < tor_info.progress < 1:
                    msg = f"Force recheck - Name: {self.__name} Hash: "
                    msg += f"{self.ext_hash} Downloaded Bytes: {tor_info.downloaded} "
                    msg += f"Size: {tor_info.size} Total Size: {tor_info.total_size}"
                    LOGGER.info(msg)
                    self.client.torrents_recheck(torrent_hashes=self.ext_hash)
                    self.__rechecked = True
                elif TORRENT_TIMEOUT is not None and time() - self.__stalled_time >= TORRENT_TIMEOUT:
                    self.__onDownloadError("Dead Torrent!")
            elif tor_info.state == "missingFiles":
                self.client.torrents_recheck(torrent_hashes=self.ext_hash)
            elif tor_info.state == "error":
                self.__onDownloadError("No enough space for this torrent on device")
        except Exception as e:
            LOGGER.error(str(e))

    def __onDownloadError(self, err):
        LOGGER.info(f"Cancelling Download: {self.__name}")
        self.__error_message= err
        self.__cancel= True
        LOGGER.info(err)
        self.client.torrents_pause(torrent_hashes=self.ext_hash)
        sleep(0.3)
        self.client.torrents_delete(torrent_hashes=self.ext_hash, delete_files=True)
        self.client.auth_log_out()
        self.__periodic.cancel()

    def cancel_download(self):
        self.__onDownloadError("Download stopped by user!")     

def _get_hash_magnet(mgt: str):
    hash_ = re_search(r'(?<=xt=urn:btih:)[a-zA-Z0-9]+', mgt).group(0)
    if len(hash_) == 32:
        hash_ = b16encode(b32decode(str(hash_))).decode()
    return str(hash_)

def _get_hash_file(path):
    with open(path, "rb") as f:
        decodedDict = bdecode(f.read())
        hash_ = sha1(bencode(decodedDict[b'info'])).hexdigest()
    return str(hash_)

