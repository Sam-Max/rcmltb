# Source: https://github.com/anasty17/mirror-leech-telegram-bot/blob/master/bot/modules/ytdlp.py
# Adapted for asyncio framework and pyrogram library

from functools import partial
from logging import getLogger
from random import SystemRandom
from string import ascii_letters, digits
from os import listdir, path as ospath
from yt_dlp import YoutubeDL, DownloadError
from re import search as re_search
from bot import status_dict_lock, status_dict, botloop
from bot.helper.ext_utils.message_utils import sendStatusMessage
from bot.helper.mirror_leech_utils.status_utils.yt_dlp_status import YtDlpDownloadStatus

LOGGER = getLogger(__name__)

class MyLogger:
    def __init__(self, obj):
        self.obj = obj

    def debug(self, msg):
        # Hack to fix changing extension
        if not self.obj.is_playlist:
            if match := re_search(r'.Merger..Merging formats into..(.*?).$', msg) or \
                        re_search(r'.ExtractAudio..Destination..(.*?)$', msg):
                LOGGER.info(msg)
                newname = match.group(1)
                newname = newname.rsplit("/", 1)[-1]
                self.obj.name = newname

    @staticmethod
    def warning(msg):
        LOGGER.warning(msg)

    @staticmethod
    def error(msg):
        if msg != "ERROR: Cancelling...":
            LOGGER.error(msg)


class YoutubeDLHelper:
    def __init__(self, listener):
        self.name = ""
        self.__listener= listener
        self.is_playlist = False
        self._last_downloaded = 0
        self.__size = 0
        self.__downloaded_bytes = 0
        self.__download_speed = 0
        self.__eta = '-'
        self.__progress = 0
        self.__gid = ""
        self.is_cancelled = False
        self.__downloading = False
        self.opts = {'progress_hooks': [self.__onDownloadProgress],
                     'logger': MyLogger(self),
                     'usenetrc': True,
                     'cookiefile': 'cookies.txt',
                     'allow_multiple_video_streams': True,
                     'allow_multiple_audio_streams': True,
                     'noprogress': True,
                     'allow_playlist_files': True,
                     'overwrites': True,
                     'trim_file_name': 200}

    @property
    def download_speed(self):
        return self.__download_speed

    @property
    def downloaded_bytes(self):
        return self.__downloaded_bytes

    @property
    def size(self):
        return self.__size

    @property
    def progress(self):
        return self.__progress

    @property
    def eta(self):
        return self.__eta

    def __onDownloadProgress(self, d):
        self.__downloading = True
        if self.is_cancelled:
            raise ValueError("Cancelling...")
        if d['status'] == "finished":
            if self.is_playlist:
                self._last_downloaded = 0
        elif d['status'] == "downloading":
                self.__download_speed = d['speed']
                if self.is_playlist:
                    downloadedBytes = d['downloaded_bytes']
                    chunk_size = downloadedBytes - self._last_downloaded
                    self._last_downloaded = downloadedBytes
                    self.__downloaded_bytes += chunk_size
                else:
                    if d.get('total_bytes'):
                        self.__size = d['total_bytes']
                    elif d.get('total_bytes_estimate'):
                        self.__size = d['total_bytes_estimate']
                    self.__downloaded_bytes = d['downloaded_bytes']
                    self.__eta = d.get('eta', '-')
                try:
                    self.__progress = (self.__downloaded_bytes / self.__size) * 100
                except:
                    pass

    async def __onDownloadError(self, error):
        self.is_cancelled = True
        await self.__listener.onDownloadError(error)

    def extractMetaData(self, link, name, args, get_info=False):
        if args:
            self.__set_args(args)
        if get_info:
            self.opts['playlist_items'] = '0'
        if link.startswith(('rtmp', 'mms', 'rstp', 'rtmps')):
            self.opts['external_downloader'] = 'ffmpeg'
        with YoutubeDL(self.opts) as ydl:
            try:
                result = ydl.extract_info(link, download=False)
                if get_info:
                    return result
                elif result is None:
                    raise ValueError('Info result is None')
                realName = ydl.prepare_filename(result)
            except Exception as e:
                if get_info:
                    raise e
                botloop.create_task(self.__onDownloadError("Download cancelled by user")) 
                return
        if 'entries' in result:
            for v in result['entries']:
                if not v:
                    continue
                elif 'filesize_approx' in v:
                    self.__size += v['filesize_approx']
                elif 'filesize' in v:
                    self.__size += v['filesize']
            if name == "":
                self.name = realName.split(f" [{result['id'].replace('*', '_')}]")[0]
            else:
                self.name = name
        else:
            outtmpl_ ='%(title,fulltitle,alt_title)s%(season_number& |)s%(season_number&S|)s%(season_number|)02d%(episode_number&E|)s%(episode_number|)02d%(height& |)s%(height|)s%(height&p|)s%(fps|)s%(fps&fps|)s%(tbr& |)s%(tbr|)d.%(ext)s'
            realName = ydl.prepare_filename(result, outtmpl=outtmpl_)
            if name == "":
                self.name = realName
            else:
                ext = realName.rsplit('.', 1)[-1]
                self.name = f"{name}.{ext}"


    async def __onDownloadStart(self):
        async with status_dict_lock:
            status_dict[self.__listener.uid] = YtDlpDownloadStatus(self, self.__listener, self.__gid)
        await sendStatusMessage(self.__listener.message)

    async def add_download(self, link, path, name, qual, playlist, args):
        if playlist:
            self.opts['ignoreerrors'] = True
            self.is_playlist = True
        self.__gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=10))    
        await self.__onDownloadStart()
        if qual.startswith('ba/b-'):
            mp3_info = qual.split('-')
            qual = mp3_info[0]
            rate = mp3_info[1]
            self.opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': rate}]
        self.opts['format'] = qual
        await botloop.run_in_executor(None, partial(self.extractMetaData, link, name, args))
        if self.is_cancelled:
            return
        if self.is_playlist:
            self.opts['outtmpl'] = f"{path}/{self.name}/%(title,fulltitle,alt_title)s%(season_number& |)s%(season_number&S|)s%(season_number|)02d%(episode_number&E|)s%(episode_number|)02d%(height& |)s%(height|)s%(height&p|)s%(fps|)s%(fps&fps|)s%(tbr& |)s%(tbr|)d.%(ext)s"
        elif args is None:
            self.opts['outtmpl'] = f"{path}/{self.name}"
        else:
            folder_name = self.name.rsplit('.', 1)[0]
            self.opts['outtmpl'] = f"{path}/{folder_name}/{self.name}"
            self.name = folder_name
        await self.__download(link, path)

    async def __download(self, link, path):
        try:
            with YoutubeDL(self.opts) as ydl:
                try:
                    await botloop.run_in_executor(None, ydl.download, [link]) 
                    if self.is_playlist and (not ospath.exists(path) or len(listdir(path)) == 0):
                        await self.__onDownloadError("No video available to download from this playlist. Check logs for more details")
                        return
                except DownloadError as e:
                    if not self.is_cancelled:
                        await self.__onDownloadError(str(e))
                    return
            if self.is_cancelled:
                raise ValueError
            await self.__listener.onDownloadComplete()
        except ValueError:
            await self.__onDownloadError("Download cancelled by user")

    async def cancel_download(self):
        self.is_cancelled = True
        LOGGER.info(f"Cancelling Download: {self.name}")
        if not self.__downloading:
            await self.__onDownloadError("Download cancelled by user")

    def __set_args(self, args):
        args = args.split('|')
        for arg in args:
            xy = arg.split(':', 1)
            karg = xy[0].strip()
            if karg == 'format':
                continue
            varg = xy[1].strip()    
            if varg.startswith('^'):
                varg = int(varg.split('^')[1])
            elif varg.lower() == 'true':
                varg = True
            elif varg.lower() == 'false':
                varg = False
            elif varg.startswith(('{', '[', '(')) and varg.endswith(('}', ']', ')')):
                varg = eval(varg)
            self.opts[karg] = varg
