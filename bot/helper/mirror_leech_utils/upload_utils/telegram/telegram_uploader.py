from asyncio import sleep
from html import escape
from os import walk, rename, path as ospath, remove as osremove
from time import time
from bot import AS_DOC_USERS, AS_DOCUMENT, AS_MEDIA_USERS, DUMP_CHAT, LOGGER, Bot, app, status_dict, status_dict_lock
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.errors import FloodWait
from pyrogram.enums import ChatType
from PIL import Image
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.message_utils import deleteMessage, editMessage, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, clean, get_media_info
from bot.helper.ext_utils.screenshot import take_ss
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus
from bot.helper.mirror_leech_utils.status_utils.telegram_status import TelegramStatus

VIDEO_SUFFIXES = ("mkv", "mp4", "mov", "wmv", "3gp", "mpg", "webm", "avi", "flv", "m4v", "gif")
IMAGE_SUFFIXES = ("jpg", "jpx", "png", "cr2", "tif", "bmp", "jxr", "psa", "ico", "heic", "jpeg")

class TelegramUploader():
    def __init__(self, path, name, size, message, tag) -> None:
        self.client= app if app is not None else Bot
        self.__path = path
        self.__message= message 
        self.id= self.__message.id
        self.__name= name
        self.__size= size
        self.__tag= tag
        self.__total_files = 0
        self.__corrupted = 0
        self.__is_corrupted = False
        self.__msgs_dict = {}
        self.__as_doc = AS_DOCUMENT
        self.__isPrivate = self.__message.chat.type == ChatType.PRIVATE
        self.__thumb = f"Thumbnails/{self.__message.chat.id}.jpg"
        self.__time= time()
        self.__set_settings()

    async def upload(self):
        await self.__msg_to_reply() 
        status= TelegramStatus(self.__message)
        async with status_dict_lock:
            status_dict[self.id] = status
        await self.__create_empty_status(status)
        if ospath.isdir(self.__path):
            for dirpath, _, files in walk(self.__path):
                for file in sorted(files):
                    self.__total_files += 1      
                    f_path = ospath.join(dirpath, file)
                    f_size = ospath.getsize(f_path)
                    if f_size == 0:
                        LOGGER.error(f"{f_size} size is zero, telegram don't upload zero size files")
                        self.__corrupted += 1
                        continue
                    await self.__upload_file(f_path, file, status)
                    if (not self.__isPrivate or DUMP_CHAT is not None) and not self.__is_corrupted:
                        self.__msgs_dict[self.__sent_msg.link] = file
                    clean(f_path)
                    await sleep(1)
        await deleteMessage(status._status_msg)
        size = get_readable_file_size(self.__size)
        msg = f"<b>Name: </b><code>{escape(self.__name)}</code>\n\n<b>Size: </b>{size}"
        if self.__total_files > 0:
            msg += f'<b>\nTotal Files:</b> {self.__total_files}'
        if self.__corrupted != 0:
            msg += f'\n<b>Corrupted Files: </b>{self.__corrupted}'
        msg += f'\ncc: {self.__tag}\n\n'
        if not self.__msgs_dict:
            await sendMessage(msg, self.__message)
        else:
            fmsg = ''
            for index, (link, name) in enumerate(self.__msgs_dict.items(), start=1):
                fmsg += f"{index}. <a href='{link}'>{name}</a>\n"
                if len(fmsg.encode() + msg.encode()) > 4000:
                    await sendMessage(msg + fmsg, self.__message)
                    sleep(1)
                    fmsg = ''
            if fmsg != '':
                await sendMessage(msg + fmsg, self.__message) 
        async with status_dict_lock: 
            try:  
                del status_dict[self.id]
            except:
                pass    

    async def __upload_file(self, up_path, file, status):
        thumb_path = self.__thumb
        notMedia = False
        cap= f"<code>{file}</code>"
        status_type= MirrorStatus.STATUS_UPLOADING
        try:
            if not self.__as_doc:
                if file.endswith(VIDEO_SUFFIXES):
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
                    self.__sent_msg= await self.__sent_msg.reply_video(
                        video= up_path,
                        width= width,
                        height= height,
                        caption= cap,
                        disable_notification=True,
                        parse_mode= ParseMode.HTML,
                        thumb= thumb_path,
                        supports_streaming= True,
                        duration= duration,
                        progress= status.start,
                        progress_args=(file, status_type, self.__time))
                elif file.endswith(IMAGE_SUFFIXES):
                    self.__sent_msg = await self.__sent_msg.reply_photo(
                        photo=up_path,
                        caption=cap,
                        parse_mode= ParseMode.HTML,
                        disable_notification=True,
                        progress=status.start,
                        progress_args=(file, status_type, self.__time))
                else:
                    notMedia = True
            if self.__as_doc or notMedia:
                if file.endswith(VIDEO_SUFFIXES) and thumb_path is None:
                    thumb_path = take_ss(up_path, None)
                self.__sent_msg= await self.__sent_msg.reply_document(
                    document= up_path, 
                    caption= cap,
                    parse_mode= ParseMode.HTML,
                    force_document= True,
                    thumb= thumb_path,
                    progress= status.start,
                    progress_args=(file, status_type, self.__time))
        except FloodWait as f:
            LOGGER.warning(str(f))
            sleep(f.value)
        except Exception as ex:
            LOGGER.error(f"{ex} Path: {up_path}")
            self.__is_corrupted = True
        if thumb_path is not None and ospath.lexists(thumb_path):
            osremove(thumb_path)
        
    async def __create_empty_status(self, status):
        button= ButtonMaker()
        button.cb_buildbutton('Cancel', data=(f"cancel_telegram_{self.id}"))    
        status_text= status.get_status_text(0, 0, 0, "", 0, self.__name, MirrorStatus.STATUS_UPLOADING)
        await editMessage(status_text, self.__message, reply_markup=button.build_menu(1))
             
    def __set_settings(self):
        if self.__message.chat.id in AS_DOC_USERS:
            self.__as_doc = True
        elif self.__message.chat.id in AS_MEDIA_USERS:
            self.__as_doc = False
        if not ospath.lexists(self.__thumb):
            self.__thumb = None

    async def __msg_to_reply(self):
        if DUMP_CHAT is not None:
            msg = self.__message.date
            self.__sent_msg = await self.client.send_message(DUMP_CHAT, msg, disable_web_page_preview=True)
        else:
            self.__sent_msg = await self.client.get_messages(self.__message.chat.id, self.__message.id)