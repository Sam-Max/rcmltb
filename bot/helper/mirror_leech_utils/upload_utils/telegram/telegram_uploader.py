from asyncio import sleep
from os import walk, rename, path as ospath
from time import time
from bot import AS_DOC_USERS, AS_DOCUMENT, AS_MEDIA_USERS, LOGGER, Bot, app, status_dict, status_dict_lock
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image
from bot.helper.ext_utils.message_utils import deleteMessage, editMessage, sendMessage
from bot.helper.ext_utils.misc_utils import clean, get_media_info
from bot.helper.ext_utils.screenshot import take_ss
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus
from bot.helper.mirror_leech_utils.status_utils.telegram_status import TelegramStatus

VIDEO_SUFFIXES = ["mkv", "mp4", "mov", "wmv", "3gp", "mpg", "webm", "avi", "flv", "m4v", "gif"]

class TelegramUploader():
    def __init__(self, path, message, tag) -> None:
        self._client= app if app is not None else Bot
        self._path = path
        self._message= message 
        self.id= self._message.id
        self._tag= tag
        self._chat_id= self._message.chat.id
        self.__total_files = 0
        self.__as_doc = AS_DOCUMENT
        self.__thumb = f"Thumbnails/{self._message.chat.id}.jpg"
        self.current_time= time()
        self._set_settings()

    async def upload(self):
        status= TelegramStatus(self._message)
        async with status_dict_lock:
            status_dict[self.id] = status
        name= str(self._path).split("/")[-1] 
        status_type= MirrorStatus.STATUS_UPLOADING
        inlineKeyboard= InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data=(f"cancel_telegram_{self.id}"))]])    
        status_msg= status.get_status_message(0, 0, 0, "", 0, name, status_type)
        await editMessage(status_msg, self._message, reply_markup=inlineKeyboard)
        if ospath.isdir(self._path):
            for dirpath, _, files in walk(self._path):
                for file in sorted(files):
                    self.__total_files += 1      
                    f_path = ospath.join(dirpath, file)
                    f_size = ospath.getsize(f_path)
                    if f_size == 0:
                        LOGGER.error(f"{f_size} size is zero, telegram don't upload zero size files")
                        continue
                    await self.__upload_file(f_path, inlineKeyboard, status_type, status)
                    clean(f_path)
                    await sleep(1)
        else:
           await self.__upload_file(self._path, inlineKeyboard, status_type, status)
           self.__total_files += 1  
           clean(self._path)
        async with status_dict_lock: 
            try:  
                del status_dict[self.id]
            except:
                pass 
        await deleteMessage(self._message)
        msg= ""
        if self.__total_files > 0:
            msg += f'**Total Files:** {self.__total_files}\n'
        msg += f'cc: {self._tag}\n'
        await self._client.send_message(self._chat_id, msg)
            
    async def __upload_file(self, up_path, inlineKeyboard, status_type, status):
        thumb_path = self.__thumb
        notMedia = False
        name= str(up_path).split("/")[-1]  
        try:
            if not self.__as_doc:
                if str(up_path).split(".")[-1] in VIDEO_SUFFIXES:
                        if not str(up_path).split(".")[-1] in ['mp4', 'mkv']:
                            new_path = str(up_path).split(".")[0] + ".mp4"
                            rename(up_path, new_path) 
                            up_path = new_path
                        duration= get_media_info(up_path)[0]
                        if thumb_path is None:
                            thumb_path = take_ss(up_path, duration)
                        if thumb_path is not None and ospath.isfile(thumb_path):
                            with Image.open(thumb_path) as img:
                                width, height = img.size
                        else:
                             width = 480
                             height = 320
                        await self._client.send_video(
                            chat_id= self._chat_id,
                            video= up_path,
                            width= width,
                            height= height,
                            caption= f'`{name}`',
                            parse_mode= ParseMode.MARKDOWN,
                            thumb= thumb_path,
                            supports_streaming= True,
                            duration= duration,
                            progress= status.progress,
                            progress_args=(name, 
                                status_type, 
                                self.current_time, 
                                inlineKeyboard))
                else:
                    notMedia = True
            if self.__as_doc or notMedia:
                if str(up_path).split(".")[-1] in VIDEO_SUFFIXES and thumb_path is None:
                    thumb_path = take_ss(up_path, None)
                await self._client.send_document(
                    chat_id= self._chat_id,
                    document= up_path, 
                    caption= f'`{name}`',
                    parse_mode= ParseMode.MARKDOWN,
                    force_document= True,
                    thumb= thumb_path,
                    progress= status.progress,
                    progress_args=(name, 
                        status_type, 
                        self.current_time, 
                        inlineKeyboard))
        except FloodWait as f:
            sleep(f.value)
        except Exception as ex:
            LOGGER.info(str(ex))
            await sendMessage(f"Failed to save: {self._path}", self._message)
        
    def _set_settings(self):
        if self._message.chat.id in AS_DOC_USERS:
            self.__as_doc = True
        elif self._message.chat.id in AS_MEDIA_USERS:
            self.__as_doc = False
        if not ospath.lexists(self.__thumb):
            self.__thumb = None