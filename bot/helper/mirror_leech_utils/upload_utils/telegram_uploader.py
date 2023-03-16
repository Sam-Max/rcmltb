from asyncio import sleep
from os import walk, rename, path as ospath, remove as osremove
from time import time
from bot import GLOBAL_EXTENSION_FILTER, LOGGER, config_dict, bot, app, user_data, leech_log
from pyrogram.errors import FloodWait
from PIL import Image
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.misc_utils import get_document_type, get_media_info
from bot.helper.ext_utils.screenshot import take_ss




class TelegramUploader():
    def __init__(self, path, name, size, listener= None) -> None:
        self.__path = path
        self.__listener = listener
        self.name= name
        self.__size= size
        self.__total_files = 0
        self.__corrupted = 0
        self.__is_corrupted = False
        self.__is_cancelled = False
        self.__msgs_dict = {}
        self.__as_doc = config_dict['AS_DOCUMENT']
        self.__thumb = f"Thumbnails/{listener.message.chat.id}.jpg"
        self.__start_time= time()
        self.uploaded_bytes = 0
        self._last_uploaded = 0
        self.__user_id = listener.message.from_user.id
        self.client= app if app is not None else bot 
        self.__sent_msg= None
        self.__set__user_settings()

    async def upload(self):
        self.__sent_msg = await bot.get_messages(self.__listener.message.chat.id, self.__listener.uid)
        if ospath.isdir(self.__path):
            for dirpath, _, filenames in sorted(walk(self.__path)):
                for file in sorted(filenames):
                    if file.lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                        continue
                    f_path = ospath.join(dirpath, file)
                    f_size = ospath.getsize(f_path)
                    self.__total_files += 1   
                    if f_size == 0:
                        LOGGER.error(f"{f_size} size is zero, telegram don't upload zero size files")
                        self.__corrupted += 1
                        continue
                    await self.__upload_file(f_path, file)
                    if self.__is_cancelled:
                        return
                    if (not self.__listener.isPrivate or config_dict['LEECH_LOG']) and not self.__is_corrupted:
                        self.__msgs_dict[self.__sent_msg.link] = file
                    self._last_uploaded = 0
                    await sleep(1)
        if self.__total_files <= self.__corrupted:
            return await self.__listener.onUploadError('Files Corrupted. Check logs')
        size = get_readable_file_size(self.__size)
        await self.__listener.onUploadComplete(None, size, self.__msgs_dict, self.__total_files, self.__corrupted, self.name)    
    
    async def __upload_file(self, up_path, file):
        thumb_path = self.__thumb
        notMedia = False
        self.__is_corrupted = False
        cap= f"<code>{file}</code>"
        try:
            is_video, is_audio, is_image = await get_document_type(up_path)
            if not self.__as_doc:
                if is_video:
                    if not str(up_path).split(".")[-1] in ['mp4', 'mkv']:
                        new_path = str(up_path).split(".")[0] + ".mp4"
                        rename(up_path, new_path) 
                        up_path = new_path
                    duration= (await get_media_info(up_path))[0]
                    if thumb_path is None:
                        thumb_path = await take_ss(up_path, duration)
                        if self.__is_cancelled:
                            if self.__thumb is None and thumb_path is not None and ospath.lexists(thumb_path):
                                osremove(thumb_path)
                            return
                    if thumb_path is not None:
                        with Image.open(thumb_path) as img:
                            width, height = img.size
                    else:
                        width = 480
                        height = 320
                    if config_dict['LEECH_LOG']:
                        for chat in leech_log:
                            self.__sent_msg = await self.client.send_video(
                                chat_id= int(chat),
                                video=up_path,
                                caption=cap,
                                duration=duration,
                                width=width,
                                height=height,
                                thumb=thumb_path,
                                supports_streaming=True,
                                disable_notification=True,
                                progress=self.__upload_progress)
                            if config_dict['BOT_PM']:
                                try:
                                    await bot.copy_message(
                                        chat_id= self.__user_id, 
                                        from_chat_id= self.__sent_msg.chat.id, 
                                        message_id= self.__sent_msg.id)
                                except Exception as err:
                                    LOGGER.error(f"Failed To Send Video in PM:\n {err}")
                    else:
                        self.__sent_msg= await self.__sent_msg.reply_video(
                            video= up_path,
                            width= width,
                            height= height,
                            caption= cap,
                            quote=True,
                            disable_notification=True,
                            thumb= thumb_path,
                            supports_streaming= True,
                            duration= duration,
                            progress= self.__upload_progress)
                elif is_audio:
                    duration, artist, title = await get_media_info(up_path)
                    if config_dict['LEECH_LOG']:
                        for chat in leech_log:
                            self.__sent_msg = await self.client.send_audio(
                                chat_id= int(chat),
                                audio=up_path,
                                duration=duration,
                                performer=artist,
                                title=title,
                                thumb=thumb_path,
                                progress=self.__upload_progress)
                            if config_dict['BOT_PM']:
                                try:
                                    await bot.copy_message(
                                        chat_id= self.__user_id, 
                                        from_chat_id= self.__sent_msg.chat.id, 
                                        message_id= self.__sent_msg.id)
                                except Exception as err:
                                    LOGGER.error(f"Failed To Send Video in PM:\n {err}")
                    else:
                        self.__sent_msg = await self.__sent_msg.reply_audio(
                            audio=up_path,
                            quote=True,
                            caption=cap,
                            duration=duration,
                            performer=artist,
                            title=title,
                            thumb= thumb_path,
                            disable_notification=True,
                            progress=self.__upload_progress)    
                elif is_image:
                    if config_dict['LEECH_LOG']:
                        for chat in leech_log:
                            self.__sent_msg = await self.client.send_photo(
                                chat_id= int(chat),
                                photo=up_path,
                                caption=cap,
                                disable_notification=True,
                                progress=self.__upload_progress)
                            if config_dict['BOT_PM']:
                                try:
                                    await bot.copy_message(
                                        chat_id= self.__user_id, 
                                        from_chat_id= self.__sent_msg.chat.id, 
                                        message_id= self.__sent_msg.id)
                                except Exception as err:
                                    LOGGER.error(f"Failed To Send Video in PM:\n {err}")
                    else:
                        self.__sent_msg = await self.__sent_msg.reply_photo(
                            photo=up_path,
                            caption=cap,
                            quote=True,
                            disable_notification=True,
                            progress= self.__upload_progress)
                else:
                    notMedia = True
            if self.__as_doc or notMedia:
                if is_video and thumb_path is None:
                    thumb_path = await take_ss(up_path, None)
                    if self.__is_cancelled:
                        if self.__thumb is None and thumb_path is not None and ospath.lexists(thumb_path):
                            osremove(thumb_path)
                        return
                if config_dict['LEECH_LOG']:
                    for chat in leech_log:
                        self.__sent_msg = await self.client.send_document(
                            chat_id= int(chat),
                            document=up_path,
                            caption=cap,
                            thumb=thumb_path,
                            disable_notification=True,
                            progress=self.__upload_progress)
                        if config_dict['BOT_PM']:
                            try:
                                await bot.copy_message(
                                    chat_id= self.__user_id, 
                                    from_chat_id= self.__sent_msg.chat.id, 
                                    message_id= self.__sent_msg.id)
                            except Exception as err:
                                LOGGER.error(f"Failed To Send Video in PM:\n {err}")
                else:
                    self.__sent_msg= await self.__sent_msg.reply_document(
                        document= up_path, 
                        caption= cap,
                        quote=True,
                        thumb= thumb_path,
                        disable_notification=True,
                        progress= self.__upload_progress)
        except FloodWait as f:
            LOGGER.warning(str(f))
            await sleep(f.value)
        except Exception as ex:
            LOGGER.error(f"{ex} Path: {up_path}")
            self.__corrupted += 1
            self.__is_corrupted = True
        finally:
            if self.__thumb is None and thumb_path is not None and ospath.lexists(thumb_path):
                osremove(thumb_path)
        if not self.__is_cancelled :
            try:
                osremove(up_path)
            except:
                pass

    async def __upload_progress(self, current, total):
        if self.__is_cancelled:
            self.client.stop_transmission()
            return
        chunk_size = current - self._last_uploaded
        self._last_uploaded = current
        self.uploaded_bytes += chunk_size
        
    def __set__user_settings(self):
        user_id = self.__listener.message.from_user.id
        user_dict = user_data.get(user_id, False)
        if user_dict:
            self.__as_doc = user_dict.get('as_doc', False)
        if not ospath.lexists(self.__thumb):
            self.__thumb = None

    @property
    def speed(self):
        try:
            return self.uploaded_bytes / (time() - self.__start_time)
        except:
            return 0

    async def cancel_download(self):
        self.__is_cancelled = True
        LOGGER.info(f"Cancelling Upload: {self.name}")
        await self.__listener.onUploadError('Your upload has been stopped!')