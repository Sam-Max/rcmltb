from logging import getLogger
from os import path as ospath, listdir
from re import search as re_search
from secrets import token_urlsafe
from yt_dlp import YoutubeDL, DownloadError

from bot import status_dict_lock, config_dict, status_dict, LOGGER
from bot.helper.ext_utils.bot_utils import run_async_to_sync, run_sync_to_async
from bot.helper.ext_utils.task_manager import check_running_tasks, stop_duplicate_check
from bot.helper.mirror_leech_utils.status_utils.yt_dlp_status import YtDlpDownloadStatus
from bot.helper.mirror_leech_utils.status_utils.queue_status import QueueStatus
from bot.helper.telegram_helper.message_utils import sendStatusMessage

_LOGGER = getLogger(__name__)


class MyLogger:
    def __init__(self, obj, listener):
        self._obj = obj
        self._listener = listener

    def debug(self, msg):
        if not self._obj.is_playlist:
            if match := re_search(
                r".Merger..Merging formats into..(.*?).$", msg
            ) or re_search(r".ExtractAudio..Destination..(.*?)$", msg):
                newname = match.group(1)
                newname = newname.rsplit("/", 1)[-1]
                self._listener.name = newname

    @staticmethod
    def warning(msg):
        _LOGGER.warning(msg)

    @staticmethod
    def error(msg):
        if msg != "ERROR: Cancelling...":
            _LOGGER.error(msg)


class YoutubeDLHelper:
    def __init__(self, listener):
        self._last_downloaded = 0
        self._progress = 0
        self._downloaded_bytes = 0
        self._download_speed = 0
        self._eta = "-"
        self._listener = listener
        self._gid = ""
        self._ext = ""
        self._is_cancelled = False
        self._downloading = False
        self.is_playlist = False
        self.keep_thumb = False
        self.name = ""
        self.opts = {
            "progress_hooks": [self._on_download_progress],
            "logger": MyLogger(self, self._listener),
            "usenetrc": True,
            "cookiefile": "cookies.txt",
            "allow_multiple_video_streams": True,
            "allow_multiple_audio_streams": True,
            "noprogress": True,
            "allow_playlist_files": True,
            "overwrites": True,
            "writethumbnail": True,
            "trim_file_name": 220,
            "fragment_retries": 10,
            "retries": 10,
            "retry_sleep_functions": {
                "http": lambda n: 3,
                "fragment": lambda n: 3,
                "file_access": lambda n: 3,
                "extractor": lambda n: 3,
            },
        }

    @property
    def download_speed(self):
        return self._download_speed

    @property
    def downloaded_bytes(self):
        return self._downloaded_bytes

    @property
    def size(self):
        return self._listener.size

    @property
    def progress(self):
        return self._progress

    @property
    def eta(self):
        return self._eta

    def _on_download_progress(self, d):
        if self._listener.is_cancelled:
            raise ValueError("Cancelling...")
        if d["status"] == "finished":
            if self.is_playlist:
                self._last_downloaded = 0
        elif d["status"] == "downloading":
            self._download_speed = d.get("speed") or 0
            if self.is_playlist:
                downloaded_bytes = d.get("downloaded_bytes") or 0
                chunk_size = downloaded_bytes - self._last_downloaded
                self._last_downloaded = downloaded_bytes
                self._downloaded_bytes += chunk_size
            else:
                if d.get("total_bytes"):
                    self._listener.size = d["total_bytes"]
                elif d.get("total_bytes_estimate"):
                    self._listener.size = d["total_bytes_estimate"]
                self._downloaded_bytes = d.get("downloaded_bytes") or 0
                self._eta = d.get("eta", "-") or "-"
            try:
                self._progress = (self._downloaded_bytes / self._listener.size) * 100
            except Exception:
                pass

    async def _on_download_start(self, from_queue=False):
        async with status_dict_lock:
            status_dict[self._listener.uid] = YtDlpDownloadStatus(
                self, self._listener, self._gid
            )
        if not from_queue:
            await self._listener.onDownloadStart()
            if getattr(self._listener, "multi", 0) <= 1:
                await sendStatusMessage(self._listener.message)

    def _on_download_error(self, error):
        self._listener.is_cancelled = True
        run_async_to_sync(self._listener.onDownloadError, error)

    def _extract_meta_data(self):
        if self._listener.link.startswith(("rtmp", "mms", "rstp", "rtmps")):
            self.opts["external_downloader"] = "ffmpeg"
        with YoutubeDL(self.opts) as ydl:
            try:
                result = ydl.extract_info(self._listener.link, download=False)
                if result is None:
                    raise ValueError("Info result is None")
            except Exception as e:
                return self._on_download_error(str(e))
            if "entries" in result:
                for entry in result["entries"]:
                    if not entry:
                        continue
                    elif "filesize_approx" in entry:
                        self._listener.size += entry.get("filesize_approx", 0) or 0
                    elif "filesize" in entry:
                        self._listener.size += entry.get("filesize", 0) or 0
                    if not self._listener.name:
                        outtmpl_ = "%(series,playlist_title,channel)s%(season_number& |)s%(season_number&S|)s%(season_number|)02d.%(ext)s"
                        self._listener.name, ext = ospath.splitext(
                            ydl.prepare_filename(entry, outtmpl=outtmpl_)
                        )
                        if not self._ext:
                            self._ext = ext
            else:
                outtmpl_ = "%(title,fulltitle,alt_title)s%(season_number& |)s%(season_number&S|)s%(season_number|)02d%(episode_number&E|)s%(episode_number|)02d%(height& |)s%(height|)s%(height&p|)s%(fps|)s%(fps&fps|)s%(tbr& |)s%(tbr|)d.%(ext)s"
                real_name = ydl.prepare_filename(result, outtmpl=outtmpl_)
                ext = ospath.splitext(real_name)[-1]
                self._listener.name = (
                    f"{self._listener.name}{ext}" if self._listener.name else real_name
                )
                if not self._ext:
                    self._ext = ext

    def _download(self, path):
        try:
            with YoutubeDL(self.opts) as ydl:
                try:
                    ydl.download([self._listener.link])
                except DownloadError as e:
                    if not self._listener.is_cancelled:
                        self._on_download_error(str(e))
                    return
            if self.is_playlist and (
                not ospath.exists(path) or len(listdir(path)) == 0
            ):
                self._on_download_error(
                    "No video available to download from this playlist. Check logs for more details"
                )
                return
            if self._listener.is_cancelled:
                return
            run_async_to_sync(self._listener.onDownloadComplete)
        except ValueError:
            pass

    async def add_download(self, path, qual, playlist, options):
        if playlist:
            self.opts["ignoreerrors"] = True
            self.is_playlist = True

        self._gid = token_urlsafe(10)

        await self._on_download_start()

        self.opts["postprocessors"] = [
            {
                "add_chapters": True,
                "add_infojson": "if_exists",
                "add_metadata": True,
                "key": "FFmpegMetadata",
            }
        ]

        if qual.startswith("ba/b-"):
            audio_info = qual.split("-")
            qual = audio_info[0]
            audio_format = audio_info[1]
            rate = audio_info[2]
            self.opts["postprocessors"].append(
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format,
                    "preferredquality": rate,
                }
            )
            if audio_format == "vorbis":
                self._ext = ".ogg"
            elif audio_format == "alac":
                self._ext = ".m4a"
            else:
                self._ext = f".{audio_format}"

        if not self._listener.is_leech and not getattr(self._listener, "thumbnail_layout", False):
            self.opts["writethumbnail"] = False

        if options:
            self._set_options(options)

        self.opts["format"] = qual

        await run_sync_to_async(self._extract_meta_data)
        if self._listener.is_cancelled:
            return

        base_name, ext = ospath.splitext(self._listener.name)
        trim_name = self._listener.name if self.is_playlist else base_name
        if len(trim_name.encode()) > 200:
            self._listener.name = (
                self._listener.name[:200]
                if self.is_playlist
                else f"{base_name[:200]}{ext}"
            )
            base_name = ospath.splitext(self._listener.name)[0]

        start_path = path if self.keep_thumb else f"{path}/yt-dlp-thumb"
        if self.is_playlist:
            self.opts["outtmpl"] = {
                "default": f"{path}/{self._listener.name}/%(title,fulltitle,alt_title)s%(season_number& |)s%(season_number&S|)s%(season_number|)02d%(episode_number&E|)s%(episode_number|)02d%(height& |)s%(height|)s%(height&p|)s%(fps|)s%(fps&fps|)s%(tbr& |)s%(tbr|)d.%(ext)s",
                "thumbnail": f"{start_path}/%(title,fulltitle,alt_title)s%(season_number& |)s%(season_number&S|)s%(season_number|)02d%(episode_number&E|)s%(episode_number|)02d%(height& |)s%(height|)s%(height&p|)s%(fps|)s%(fps&fps|)s%(tbr& |)s%(tbr|)d.%(ext)s",
            }
        elif "download_ranges" in self.opts:
            self.opts["outtmpl"] = {
                "default": f"{path}/{base_name}/%(section_number|)s%(section_number&.|)s%(section_title|)s%(section_title&-|)s%(title,fulltitle,alt_title)s %(section_start)s to %(section_end)s.%(ext)s",
                "thumbnail": f"{start_path}/%(section_number|)s%(section_number&.|)s%(section_title|)s%(section_title&-|)s%(title,fulltitle,alt_title)s %(section_start)s to %(section_end)s.%(ext)s",
            }
        elif any(
            key in self.opts
            for key in [
                "writedescription",
                "writeinfojson",
                "writeannotations",
                "writedesktoplink",
                "writewebloclink",
                "writeurllink",
                "writesubtitles",
                "writeautomaticsub",
            ]
        ):
            self.opts["outtmpl"] = {
                "default": f"{path}/{base_name}/{self._listener.name}",
                "thumbnail": f"{start_path}/{base_name}.%(ext)s",
            }
        else:
            self.opts["outtmpl"] = {
                "default": f"{path}/{self._listener.name}",
                "thumbnail": f"{start_path}/{base_name}.%(ext)s",
            }

        if qual.startswith("ba/b"):
            self._listener.name = f"{base_name}{self._ext}"

        if self.opts["writethumbnail"]:
            self.opts["postprocessors"].append(
                {
                    "format": "jpg",
                    "key": "FFmpegThumbnailsConvertor",
                    "when": "before_dl",
                }
            )
        if self._ext in [
            ".mp3",
            ".mkv",
            ".mka",
            ".ogg",
            ".opus",
            ".flac",
            ".m4a",
            ".mp4",
            ".mov",
            ".m4v",
        ]:
            self.opts["postprocessors"].append(
                {
                    "already_have_thumbnail": self.opts["writethumbnail"],
                    "key": "EmbedThumbnail",
                }
            )

        msg, button = await stop_duplicate_check(self._listener)
        if msg:
            await self._listener.onDownloadError(msg, button)
            return

        add_to_queue, event = await check_running_tasks(self._listener)
        if add_to_queue:
            _LOGGER.info(f"Added to Queue/Download: {self._listener.name}")
            async with status_dict_lock:
                status_dict[self._listener.uid] = QueueStatus(
                    self._listener, self._gid, "dl"
                )
            await event.wait()
            if self._listener.is_cancelled:
                return
            _LOGGER.info(f"Start Queued Download from YT_DLP: {self._listener.name}")
            await self._on_download_start(True)

        if not add_to_queue:
            _LOGGER.info(f"Download with YT_DLP: {self._listener.name}")

        await run_sync_to_async(self._download, path)

    async def cancel_task(self):
        self._listener.is_cancelled = True
        _LOGGER.info(f"Cancelling Download: {self._listener.name}")
        if not self._downloading:
            await self._listener.onDownloadError("Download Cancelled by User!")

    def _set_options(self, options):
        if isinstance(options, str):
            options_list = options.split("|")
            options = {}
            for opt in options_list:
                key, value = map(str.strip, opt.split(":", 1))
                if value.startswith("^"):
                    if "." in value or value == "^inf":
                        value = float(value.split("^")[1])
                    else:
                        value = int(value.split("^")[1])
                elif value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.startswith(("{", "[", "(")) and value.endswith(("}", "]", ")")):
                    value = eval(value)
                if key == "postprocessors":
                    if isinstance(value, list):
                        self.opts[key].extend(tuple(value))
                    elif isinstance(value, dict):
                        self.opts[key].append(value)
                elif key == "download_ranges":
                    if isinstance(value, list):
                        self.opts[key] = lambda info, ytdl: value
                else:
                    if key == "writethumbnail" and value is True:
                        self.keep_thumb = True
                    self.opts[key] = value
        elif isinstance(options, dict):
            for key, value in options.items():
                if key == "postprocessors":
                    if isinstance(value, list):
                        self.opts[key].extend(tuple(value))
                    elif isinstance(value, dict):
                        self.opts[key].append(value)
                elif key == "download_ranges":
                    if isinstance(value, list):
                        self.opts[key] = lambda info, ytdl: value
                else:
                    if key == "writethumbnail" and value is True:
                        self.keep_thumb = True
                    self.opts[key] = value