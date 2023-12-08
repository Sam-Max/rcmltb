from asyncio import sleep
from aiofiles.os import remove as aioremove, path as aiopath
from os import walk, rename as osrename, path as ospath, remove as osremove
from bot.helper.ext_utils.media_utils import create_thumb, take_ss
from pyrogram.types import InputMediaPhoto
from time import time
from re import match as re_match
from PIL import Image
from bot import (
    GLOBAL_EXTENSION_FILTER,
    IS_PREMIUM_USER,
    LOGGER,
    config_dict,
    bot,
    app,
    user_data,
    leech_log,
)
from pyrogram.errors import FloodWait, RPCError
from bot.helper.ext_utils.bot_utils import clean_unwanted, is_archive
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.misc_utils import (
    get_base_name,
    get_document_type,
    get_media_info,
)


class TelegramUploader:
    def __init__(self, path, name, size, listener=None) -> None:
        self.__path = path
        self.__listener = listener
        self.name = name
        self.__size = size
        self.__total_files = 0
        self.__corrupted = 0
        self.__is_corrupted = False
        self.__is_cancelled = False
        self.__msgs_dict = {}
        self.__as_doc = config_dict["AS_DOCUMENT"]
        self.__thumb = f"Thumbnails/{listener.message.from_user.id}.jpg"
        self.__start_time = time()
        self.__processed_bytes = 0
        self._last_uploaded = 0
        self._iteration = 0
        self.__user_id = listener.message.from_user.id
        self.client = app if app else bot
        self.__upload_path = ""
        self.__sent_msg = None

    async def upload(self):
        res = await self.__msg_to_reply()
        if not res:
            return
        self.__user_settings()
        if await aiopath.isdir(self.__path):
            for dirpath, _, filenames in sorted(walk(self.__path)):
                if dirpath.endswith("/yt-dlp-thumb"):
                    continue
                if self._iteration != 0:
                    folder_name = ospath.basename(dirpath)
                    if config_dict["LEECH_LOG"]:
                        for chat in leech_log:
                            await self.client.send_message(
                                text=f"<b>📂 Folder: </b> {folder_name}", chat_id=chat)
                    else:
                        await self.client.send_message(
                            text=f"<b>📂 Folder: </b> {folder_name}",
                            chat_id=self.__sent_msg.chat.id)
                self._iteration += 1
                for file in sorted(filenames):
                    self.__upload_path = ospath.join(dirpath, file)
                    if file.lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                        try:
                            osremove(self.__upload_path)
                        except:
                            pass
                        continue
                    f_size = ospath.getsize(self.__upload_path)
                    self.__total_files += 1
                    if f_size == 0:
                        LOGGER.error(
                            f"{f_size} size is zero, telegram don't upload zero size files"
                        )
                        self.__corrupted += 1
                        continue
                    if self.__is_cancelled:
                        return
                    self._last_uploaded = 0
                    await self.__prepare_file(file, dirpath)
                    await self.__upload_file(self.__upload_path, file)
                    if self.__is_cancelled:
                        return
                    if not self.__is_corrupted and (
                        self.__listener.isSuperGroup or config_dict["LEECH_LOG"]
                    ):
                        self.__msgs_dict[self.__sent_msg.link] = file
                    await sleep(1)
                    if (
                        not self.__is_cancelled
                        and ospath.exists(self.__upload_path)
                        and (not self.__listener.seed or self.__listener.newDir)
                    ):
                        try:
                            osremove(self.__upload_path)
                        except:
                            pass
        if self.__is_cancelled:
            return
        if self.__listener.seed and not self.__listener.newDir:
            await clean_unwanted(self.__path)
        if self.__total_files == 0:
            await self.__listener.onUploadError(
                "No files to upload. In case you have filled EXTENSION_FILTER, then check if all files have those extensions or not."
            )
            return
        if self.__total_files <= self.__corrupted:
            await self.__listener.onUploadError(
                "Files Corrupted or unable to upload. Check logs"
            )
            return
        if not config_dict["NO_TASKS_LOGS"]:
            LOGGER.info(f"Leech Completed: {self.name}")
        size = get_readable_file_size(self.__size)
        await self.__listener.onUploadComplete(
            None,
            size,
            self.__msgs_dict,
            self.__total_files,
            self.__corrupted,
            self.name,
        )

    async def __upload_file(self, up_path, file):
        thumb = self.__thumb
        self.__is_corrupted = False
        cap_mono = f"<code>{file}</code>"
        try:
            is_video, is_audio, is_image = await get_document_type(up_path)

            if not is_image and thumb is None:
                file_name = ospath.splitext(file)[0]
                thumb_path = f"{self.__path}/yt-dlp-thumb/{file_name}.jpg"
                if await aiopath.isfile(thumb_path):
                    thumb = thumb_path

            if self.__as_doc or (not is_video and not is_audio and not is_image):
                if is_video:
                    if self.__listener.screenshots:
                        await self._send_screenshots()
                    if thumb is None:
                        thumb = await create_thumb(up_path, None)
                if self.__is_cancelled:
                    return
                if config_dict["LEECH_LOG"]:
                    for chat in leech_log:
                        self.__sent_msg = await self.client.send_document(
                            chat_id=int(chat),
                            document=up_path,
                            caption=cap_mono,
                            thumb=thumb,
                            disable_notification=True,
                            progress=self.__upload_progress,
                        )
                        if config_dict["BOT_PM"]:
                            try:
                                await self.client.copy_message(
                                    chat_id=self.__user_id,
                                    from_chat_id=self.__sent_msg.chat.id,
                                    message_id=self.__sent_msg.id,
                                )
                            except Exception as err:
                                LOGGER.error(f"Failed To Send Video in PM:\n {err}")
                else:
                    self.__sent_msg = await self.__sent_msg.reply_document(
                        document=up_path,
                        caption=cap_mono,
                        quote=True,
                        thumb=thumb,
                        disable_notification=True,
                        progress=self.__upload_progress,
                    )
            if is_video:
                if self.__listener.screenshots:
                    await self._send_screenshots()
                if not up_path.upper().endswith(("MKV", "MP4")):
                    new_path = up_path.split(".")[0] + ".mp4"
                    osrename(up_path, new_path)
                    up_path = new_path
                duration = (await get_media_info(up_path))[0]
                if thumb is None:
                    thumb = await create_thumb(up_path, duration)
                if thumb is not None:
                    with Image.open(thumb) as img:
                        width, height = img.size
                else:
                    width = 480
                    height = 320
                if self.__is_cancelled:
                    return
                if config_dict["LEECH_LOG"]:
                    for chat in leech_log:
                        self.__sent_msg = await self.client.send_video(
                            chat_id=int(chat),
                            video=up_path,
                            caption=cap_mono,
                            duration=duration,
                            width=width,
                            height=height,
                            thumb=thumb,
                            supports_streaming=True,
                            disable_notification=True,
                            progress=self.__upload_progress,
                        )
                        if config_dict["BOT_PM"]:
                            try:
                                await self.client.copy_message(
                                    chat_id=self.__user_id,
                                    from_chat_id=self.__sent_msg.chat.id,
                                    message_id=self.__sent_msg.id,
                                )
                            except Exception as err:
                                LOGGER.error(f"Failed To Send Video in PM:\n {err}")
                else:
                    self.__sent_msg = await self.__sent_msg.reply_video(
                        video=up_path,
                        width=width,
                        height=height,
                        caption=cap_mono,
                        quote=True,
                        disable_notification=True,
                        thumb=thumb,
                        supports_streaming=True,
                        duration=duration,
                        progress=self.__upload_progress,
                    )
            elif is_audio:
                duration, artist, title = await get_media_info(up_path)
                if self.__is_cancelled:
                    return
                if config_dict["LEECH_LOG"]:
                    for chat in leech_log:
                        self.__sent_msg = await self.client.send_audio(
                            chat_id=int(chat),
                            audio=up_path,
                            duration=duration,
                            performer=artist,
                            title=title,
                            thumb=thumb,
                            progress=self.__upload_progress,
                        )
                        if config_dict["BOT_PM"]:
                            try:
                                await self.client.copy_message(
                                    chat_id=self.__user_id,
                                    from_chat_id=self.__sent_msg.chat.id,
                                    message_id=self.__sent_msg.id,
                                )
                            except Exception as err:
                                LOGGER.error(f"Failed To Send Video in PM:\n {err}")
                else:
                    self.__sent_msg = await self.__sent_msg.reply_audio(
                        audio=up_path,
                        quote=True,
                        caption=cap_mono,
                        duration=duration,
                        performer=artist,
                        title=title,
                        thumb=thumb,
                        disable_notification=True,
                        progress=self.__upload_progress,
                    )
            elif is_image:
                if self.__is_cancelled:
                    return
                if config_dict["LEECH_LOG"]:
                    for chat in leech_log:
                        self.__sent_msg = await self.client.send_photo(
                            chat_id=int(chat),
                            photo=up_path,
                            caption=cap_mono,
                            disable_notification=True,
                            progress=self.__upload_progress,
                        )
                        if config_dict["BOT_PM"]:
                            try:
                                await self.client.copy_message(
                                    chat_id=self.__user_id,
                                    from_chat_id=self.__sent_msg.chat.id,
                                    message_id=self.__sent_msg.id,
                                )
                            except Exception as err:
                                LOGGER.error(f"Failed To Send Video in PM:\n {err}")
                else:
                    self.__sent_msg = await self.__sent_msg.reply_photo(
                        photo=up_path,
                        caption=cap_mono,
                        quote=True,
                        disable_notification=True,
                        progress=self.__upload_progress,
                    )
            if self.__thumb is None and thumb is not None and await aiopath.exists(thumb):
                osremove(thumb)
        except FloodWait as f:
            LOGGER.warning(str(f))
            await sleep(f.value)
        except Exception as err:
            if self.__thumb is None and thumb is not None and await aiopath.exists(thumb):
                osremove(thumb)
            err_type = "RPCError: " if isinstance(err, RPCError) else ""
            LOGGER.error(f"{err_type}{err}. Path: {up_path}")
            raise err

    async def __upload_progress(self, current, total):
        if self.__is_cancelled:
            self.client.stop_transmission()
            return
        chunk_size = current - self._last_uploaded
        self._last_uploaded = current
        self.__processed_bytes += chunk_size

    async def __msg_to_reply(self):
        if IS_PREMIUM_USER:
            if not self.__listener.isSuperGroup:
                await self.__listener.onUploadError(
                    "Use supergroup to leech with user_session_string"
                )
                return False
            self.__sent_msg = await app.get_messages(
                chat_id=self.__listener.message.chat.id, message_ids=self.__listener.uid
            )
        else:
            self.__sent_msg = self.__listener.message
        return True

    def __user_settings(self):
        user_id = self.__listener.message.from_user.id
        user_dict = user_data.get(user_id, {})
        self.__as_doc = user_dict.get("as_doc") or config_dict["AS_DOCUMENT"]
        if not ospath.exists(self.__thumb):
            self.__thumb = None

    async def _send_screenshots(self):
        if isinstance(self.__listener.screenshots, str):
            ss_nb = int(self.__listener.screenshots)
        else:
            ss_nb = 10
        outputs = await take_ss(self.__upload_path, ss_nb)
        inputs = []
        if outputs:
            for m in outputs:
                if await aiopath.exists(m):
                    cap = m.rsplit("/", 1)[-1]
                    inputs.append(InputMediaPhoto(m, cap))
                else:
                    outputs.remove(m)
            if outputs:
                self.__sent_msg = (await self.__sent_msg.reply_media_group(
                    media=inputs,
                    quote=True,
                    disable_notification=True,
                ))[-1]
                for m in outputs:
                    await aioremove(m)

    async def __prepare_file(self, file_, dirpath):
        if len(file_) > 60:
            if is_archive(file_):
                name = get_base_name(file_)
                ext = file_.split(name, 1)[1]
            elif match := re_match(r".+(?=\..+\.0*\d+$)|.+(?=\.part\d+\..+)", file_):
                name = match.group(0)
                ext = file_.split(name, 1)[1]
            elif len(fsplit := ospath.splitext(file_)) > 1:
                name = fsplit[0]
                ext = fsplit[1]
            else:
                name = file_
                ext = ""
            extn = len(ext)
            remain = 60 - extn
            name = name[:remain]
            new_path = ospath.join(dirpath, f"{name}{ext}")
            osrename(self.__upload_path, new_path)
            self.__upload_path = new_path

    @property
    def speed(self):
        try:
            return self.__processed_bytes / (time() - self.__start_time)
        except:
            return 0

    @property
    def processed_bytes(self):
        return self.__processed_bytes

    async def cancel_download(self):
        self.__is_cancelled = True
        if not config_dict["NO_TASKS_LOGS"]:
            LOGGER.info(f"Cancelling Upload: {self.name}")
        await self.__listener.onUploadError("Your upload has been stopped!")
