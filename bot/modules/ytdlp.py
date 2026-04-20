from asyncio import Event, wait_for
from functools import partial
from time import time
from yt_dlp import YoutubeDL

from pyrogram.filters import regex, user
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram.filters import command

from bot import DOWNLOAD_DIR, LOGGER, config_dict, user_data, bot_loop, bot
from bot.helper.ext_utils.bot_utils import is_url, new_task, run_sync_to_async
from bot.helper.ext_utils.human_format import get_readable_file_size, human_readable_timedelta
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (
    editMessage,
    sendMessage,
    deleteMessage,
)
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.mirror_leech_utils.download_utils.yt_dlp_helper import YoutubeDLHelper
from bot.helper.listeners.task_listener import TaskListener
from bot.helper.ext_utils.links_utils import is_gdrive_link, is_rclone_path


@new_task
async def select_format(_, query, obj):
    data = query.data.split()
    message = query.message
    await query.answer()

    if data[1] == "dict":
        b_name = data[2]
        await obj.qual_subbuttons(b_name)
    elif data[1] == "mp3":
        await obj.mp3_subbuttons()
    elif data[1] == "audio":
        await obj.audio_format()
    elif data[1] == "aq":
        if data[2] == "back":
            await obj.audio_format()
        else:
            await obj.audio_quality(data[2])
    elif data[1] == "back":
        await obj.back_to_main()
    elif data[1] == "cancel":
        await editMessage(message, "Task has been cancelled.")
        obj.qual = None
        obj.listener.is_cancelled = True
        obj.event.set()
    else:
        if data[1] == "sub":
            obj.qual = obj.formats[data[2]][data[3]][1]
        elif "|" in data[1]:
            obj.qual = obj.formats[data[1]]
        else:
            obj.qual = data[1]
        obj.event.set()


class YtSelection:
    def __init__(self, listener):
        self.listener = listener
        self._is_m4a = False
        self._reply_to = None
        self._time = time()
        self._timeout = 120
        self._is_playlist = False
        self._main_buttons = None
        self.event = Event()
        self.formats = {}
        self.qual = None

    async def _event_handler(self):
        pfunc = partial(select_format, obj=self)
        handler = self.listener.client.add_handler(
            CallbackQueryHandler(
                pfunc, filters=regex("^ytq") & user(self.listener.user_id)
            ),
            group=-1,
        )
        try:
            await wait_for(self.event.wait(), timeout=self._timeout)
        except Exception:
            await editMessage(self._reply_to, "Timed Out. Task has been cancelled!")
            self.qual = None
            self.listener.is_cancelled = True
            self.event.set()
        finally:
            self.listener.client.remove_handler(*handler)

    async def get_quality(self, result):
        buttons = ButtonMaker()
        if "entries" in result:
            self._is_playlist = True
            for i in ["144", "240", "360", "480", "720", "1080", "1440", "2160"]:
                video_format = f"bv*[height<=?{i}][ext=mp4]+ba[ext=m4a]/b[height<=?{i}]"
                b_data = f"{i}|mp4"
                self.formats[b_data] = video_format
                buttons.cb_buildbutton(f"{i}-mp4", f"ytq {b_data}")
                video_format = f"bv*[height<=?{i}][ext=webm]+ba/b[height<=?{i}]"
                b_data = f"{i}|webm"
                self.formats[b_data] = video_format
                buttons.cb_buildbutton(f"{i}-webm", f"ytq {b_data}")
            buttons.cb_buildbutton("MP3", "ytq mp3")
            buttons.cb_buildbutton("Audio Formats", "ytq audio")
            buttons.cb_buildbutton("Best Videos", "ytq bv*+ba/b")
            buttons.cb_buildbutton("Best Audios", "ytq ba/b")
            buttons.cb_buildbutton("Cancel", "ytq cancel", "footer")
            self._main_buttons = buttons.build_menu(3)
            msg = f"Choose Playlist Videos Quality:\nTimeout: {human_readable_timedelta(self._timeout - (time() - self._time))}"
        else:
            format_dict = result.get("formats")
            if format_dict is not None:
                for item in format_dict:
                    if item.get("tbr"):
                        format_id = item["format_id"]

                        if item.get("filesize"):
                            size = item["filesize"]
                        elif item.get("filesize_approx"):
                            size = item["filesize_approx"]
                        else:
                            size = 0

                        if item.get("video_ext") == "none" and (
                            item.get("resolution") == "audio only"
                            or item.get("acodec") != "none"
                        ):
                            if item.get("audio_ext") == "m4a":
                                self._is_m4a = True
                            b_name = f"{item.get('acodec') or format_id}-{item['ext']}"
                            v_format = format_id
                        elif item.get("height"):
                            height = item["height"]
                            ext = item["ext"]
                            fps = item["fps"] if item.get("fps") else ""
                            b_name = f"{height}p{fps}-{ext}"
                            ba_ext = "[ext=m4a]" if self._is_m4a and ext == "mp4" else ""
                            v_format = f"{format_id}+ba{ba_ext}/b[height=?{height}]"
                        else:
                            continue

                        self.formats.setdefault(b_name, {})[f"{item['tbr']}"] = [
                            size,
                            v_format,
                        ]

                for b_name, tbr_dict in self.formats.items():
                    if len(tbr_dict) == 1:
                        tbr, v_list = next(iter(tbr_dict.items()))
                        buttonName = f"{b_name} ({get_readable_file_size(v_list[0])})"
                        buttons.cb_buildbutton(buttonName, f"ytq sub {b_name} {tbr}")
                    else:
                        buttons.cb_buildbutton(b_name, f"ytq dict {b_name}")
            buttons.cb_buildbutton("MP3", "ytq mp3")
            buttons.cb_buildbutton("Audio Formats", "ytq audio")
            buttons.cb_buildbutton("Best Video", "ytq bv*+ba/b")
            buttons.cb_buildbutton("Best Audio", "ytq ba/b")
            buttons.cb_buildbutton("Cancel", "ytq cancel", "footer")
            self._main_buttons = buttons.build_menu(2)
            msg = f"Choose Video Quality:\nTimeout: {human_readable_timedelta(self._timeout - (time() - self._time))}"

        self._reply_to = await sendMessage(msg, self.listener.message, self._main_buttons)
        await self._event_handler()
        if not self.listener.is_cancelled:
            await deleteMessage(self._reply_to)
        return self.qual

    async def back_to_main(self):
        if self._is_playlist:
            msg = f"Choose Playlist Videos Quality:\nTimeout: {human_readable_timedelta(self._timeout - (time() - self._time))}"
        else:
            msg = f"Choose Video Quality:\nTimeout: {human_readable_timedelta(self._timeout - (time() - self._time))}"
        await editMessage(msg, self._reply_to, self._main_buttons)

    async def qual_subbuttons(self, b_name):
        buttons = ButtonMaker()
        tbr_dict = self.formats[b_name]
        for tbr, d_data in tbr_dict.items():
            button_name = f"{tbr}K ({get_readable_file_size(d_data[0])})"
            buttons.cb_buildbutton(button_name, f"ytq sub {b_name} {tbr}")
        buttons.cb_buildbutton("Back", "ytq back", "footer")
        buttons.cb_buildbutton("Cancel", "ytq cancel", "footer")
        subbuttons = buttons.build_menu(2)
        msg = f"Choose Bit rate for <b>{b_name}</b>:\nTimeout: {human_readable_timedelta(self._timeout - (time() - self._time))}"
        await editMessage(msg, self._reply_to, subbuttons)

    async def mp3_subbuttons(self):
        i = "s" if self._is_playlist else ""
        buttons = ButtonMaker()
        audio_qualities = [64, 128, 320]
        for q in audio_qualities:
            audio_format = f"ba/b-mp3-{q}"
            buttons.cb_buildbutton(f"{q}K-mp3", f"ytq {audio_format}")
        buttons.cb_buildbutton("Back", "ytq back")
        buttons.cb_buildbutton("Cancel", "ytq cancel")
        subbuttons = buttons.build_menu(3)
        msg = f"Choose mp3 Audio{i} Bitrate:\nTimeout: {human_readable_timedelta(self._timeout - (time() - self._time))}"
        await editMessage(msg, self._reply_to, subbuttons)

    async def audio_format(self):
        i = "s" if self._is_playlist else ""
        buttons = ButtonMaker()
        for frmt in ["aac", "alac", "flac", "m4a", "opus", "vorbis", "wav"]:
            audio_format = f"ba/b-{frmt}-"
            buttons.cb_buildbutton(frmt, f"ytq aq {audio_format}")
        buttons.cb_buildbutton("Back", "ytq back", "footer")
        buttons.cb_buildbutton("Cancel", "ytq cancel", "footer")
        subbuttons = buttons.build_menu(3)
        msg = f"Choose Audio{i} Format:\nTimeout: {human_readable_timedelta(self._timeout - (time() - self._time))}"
        await editMessage(msg, self._reply_to, subbuttons)

    async def audio_quality(self, format):
        i = "s" if self._is_playlist else ""
        buttons = ButtonMaker()
        for qual in range(11):
            audio_format = f"{format}{qual}"
            buttons.cb_buildbutton(qual, f"ytq {audio_format}")
        buttons.cb_buildbutton("Back", "ytq aq back")
        buttons.cb_buildbutton("Cancel", "ytq aq cancel")
        subbuttons = buttons.build_menu(5)
        msg = f"Choose Audio{i} Quality:\n0 is best and 10 is worst\nTimeout: {human_readable_timedelta(self._timeout - (time() - self._time))}"
        await editMessage(msg, self._reply_to, subbuttons)


def extract_info(link, options):
    with YoutubeDL(options) as ydl:
        result = ydl.extract_info(link, download=False)
        if result is None:
            raise ValueError("Info result is None")
        return result


class YtDlp(TaskListener):
    def __init__(
        self,
        client,
        message,
        is_leech=False,
        same_dir=None,
    ):
        self.client = client
        self.qual = ""
        self.multi = 0
        if same_dir is None:
            same_dir = {}
        super().__init__(
            message=message,
            tag="",
            user_id=message.from_user.id,
            compress=None,
            isLeech=is_leech,
            sameDir=same_dir,
        )
        self.is_ytdlp = True
        self.is_leech = is_leech

    async def new_event(self):
        input_list = self.message.text.split("\n")
        args = {}
        args["-s"] = False
        args["-z"] = None
        args["-i"] = 0
        args["link"] = ""
        args["-m"] = ""
        args["-opt"] = {}
        args["-n"] = ""
        args["-up"] = ""
        args["-rcf"] = ""
        args["-sp"] = 0
        args["-t"] = ""
        args["-ns"] = ""
        args["-doc"] = False
        args["-med"] = False
        args["-ut"] = False
        args["-bt"] = False
        args["-f"] = False
        args["-fd"] = False
        args["-fu"] = False
        args["-hl"] = False
        arg_parser(input_list[0].split(" ")[1:], args)

        self.multi = int(args["-i"]) if args["-i"] else 0
        self.name = args["-n"]
        self.up_dest = args["-up"]
        self.rc_flags = args["-rcf"]
        self.link = args["link"]
        self.compress = args["-z"]
        self.select = args["-s"]
        self.split_size = args["-sp"]
        self.thumb = args["-t"] if args["-t"] else None
        self.name_sub = args["-ns"]
        self.as_doc = args["-doc"]
        self.as_med = args["-med"]
        self.user_transmission = args["-ut"]
        self.bot_transmission = args["-bt"]
        self.force_run = args["-f"]
        self.force_download = args["-fd"]
        self.force_upload = args["-fu"]
        self.hybrid_leech = args["-hl"]
        self.folder_name = f"/{args['-m']}".rstrip("/") if args["-m"] else ""

        if self.folder_name:
            if self.sameDir:
                self.sameDir[self.folder_name] = {
                    "total": self.multi,
                    "tasks": {self.uid},
                }
            else:
                self.sameDir = {
                    self.folder_name: {
                        "total": self.multi,
                        "tasks": {self.uid},
                    }
                }

        if not self.is_leech and not self.up_dest:
            from bot.helper.ext_utils.rclone_utils import is_rclone_config, is_remote_selected
            if not await is_rclone_config(self.user_id, self.message):
                return
            if not await is_remote_selected(self.user_id, self.message):
                return

        path = f"{DOWNLOAD_DIR}{self.uid}{self.folder_name}"
        self.dir = path

        self.tag, _ = self._get_tag(input_list)

        opt = args["-opt"] or self.user_dict.get("YT_DLP_OPTIONS") or config_dict.get("YT_DLP_OPTIONS", "")

        if not self.link and (reply_to := self.message.reply_to_message):
            self.link = reply_to.text.split("\n", 1)[0].strip()

        if not is_url(self.link):
            await sendMessage(
                YT_HELP_DICT["Cmd"],
                self.message,
                YT_HELP_DICT.get("Menu"),
            )
            return

        if "mdisk.me" in self.link:
            name, link = await _mdisk(self.link, self.name)
            self.name = name or self.name
            self.link = link or self.link

        try:
            await self.before_start()
        except Exception as e:
            await sendMessage(self.message, str(e))
            return

        options = {"usenetrc": True, "cookiefile": "cookies.txt"}
        if opt:
            if isinstance(opt, str):
                yt_opt = opt.split("|")
                for ytopt in yt_opt:
                    key, value = map(str.strip, ytopt.split(":", 1))
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
                    if key in ("postprocessors", "download_ranges"):
                        continue
                    if key == "format" and not self.select:
                        self.qual = value
                        continue
                    options[key] = value
            elif isinstance(opt, dict):
                for key, value in opt.items():
                    if key in ("postprocessors", "download_ranges"):
                        continue
                    if key == "format" and not self.select:
                        self.qual = value
                        continue
                    options[key] = value

        options["playlist_items"] = "0"

        try:
            result = await run_sync_to_async(extract_info, self.link, options)
        except Exception as e:
            msg = str(e).replace("<", " ").replace(">", " ")
            await sendMessage(f"{self.tag} {msg}", self.message)
            return

        await self.run_multi(input_list)

        qual = getattr(self, "qual", "")
        if not qual:
            qual = await YtSelection(self).get_quality(result)
            if qual is None:
                return

        LOGGER.info(f"Downloading with YT-DLP: {self.link}")
        playlist = "entries" in result
        ydl = YoutubeDLHelper(self)
        await ydl.add_download(path, qual, playlist, opt)

    def _get_tag(self, input_list):
        username = self.message.from_user.username
        tag = f"@{username}" if username else self.message.from_user.mention
        return tag, input_list

    async def run_multi(self, input_list):
        if self.multi > 1:
            if self.folder_name and self.sameDir:
                self.sameDir[self.folder_name]["total"] -= 1
                if self.sameDir[self.folder_name]["total"] == 0:
                    del self.sameDir[self.folder_name]


async def ytdl(client, message):
    bot_loop.create_task(YtDlp(client, message).new_event())


async def ytdl_leech(client, message):
    bot_loop.create_task(YtDlp(client, message, is_leech=True).new_event())


async def _mdisk(link, name):
    from aiohttp import ClientSession
    key = link.split("/")[-1]
    async with ClientSession() as session:
        async with session.get(
            f"https://diskuploader.entertainvideo.com/v1/file/cdnurl?param={key}"
        ) as resp:
            if resp.status == 200:
                resp_json = await resp.json()
                link = resp_json["source"]
                if not name:
                    name = resp_json["filename"]
            return name, link


def arg_parser(items, args):
    Booleans = ["-s", "-doc", "-med", "-ut", "-bt", "-f", "-fd", "-fu", "-hl"]
    key_mapping = {
        "-s": "-s",
        "-z": "-z",
        "-i": "-i",
        "-m": "-m",
        "-n": "-n",
        "-up": "-up",
        "-rcf": "-rcf",
        "-opt": "-opt",
        "-sp": "-sp",
        "-t": "-t",
        "-ns": "-ns",
        "-doc": "-doc",
        "-med": "-med",
        "-ut": "-ut",
        "-bt": "-bt",
        "-f": "-f",
        "-fd": "-fd",
        "-fu": "-fu",
        "-hl": "-hl",
    }
    i = 0
    while i < len(items):
        item = items[i]
        if item in key_mapping:
            key = key_mapping[item]
            if key in Booleans:
                args[key] = True
                i += 1
            elif key == "-i":
                i += 1
                if i < len(items):
                    args[key] = int(items[i])
                i += 1
            elif key == "-sp":
                i += 1
                if i < len(items) and not items[i].startswith("-"):
                    args[key] = items[i]
                i += 1
            elif key == "-z":
                i += 1
                if i < len(items) and not items[i].startswith("-"):
                    args[key] = items[i]
                    i += 1
                else:
                    args[key] = ""
            elif key == "-opt":
                i += 1
                opt_str = ""
                while i < len(items) and not items[i].startswith("-"):
                    if opt_str:
                        opt_str += " "
                    opt_str += items[i]
                    i += 1
                if opt_str:
                    try:
                        args[key] = eval(opt_str)
                    except Exception:
                        args[key] = opt_str
            else:
                i += 1
                if i < len(items) and not items[i].startswith("-"):
                    args[key] = items[i]
                    i += 1
        else:
            args["link"] = (args["link"] + " " + item).strip() if args["link"] else item
            i += 1


from bot.helper.ext_utils.help_messages import YT_HELP_DICT

bot.add_handler(
    MessageHandler(
        ytdl,
        filters=command(BotCommands.YtdlMirrorCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
bot.add_handler(
    MessageHandler(
        ytdl_leech,
        filters=command(BotCommands.YtdlLeechCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
bot.add_handler(CallbackQueryHandler(select_format, filters=regex("^ytq")))