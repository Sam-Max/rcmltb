from asyncio import create_subprocess_exec, sleep
from asyncio.subprocess import PIPE
from html import escape
from json import loads
from os import listdir, path as ospath, remove as osremove, walk
from re import search
from bot import DOWNLOAD_DIR, LOGGER, SERVER_PORT, TG_MAX_FILE_SIZE, Interval, status_dict, status_dict_lock, aria2, config_dict
from pyrogram.enums import ChatType
from bot.helper.ext_utils.bot_utils import add_index_link, is_archive, is_archive_split, is_first_archive_split
from bot.helper.ext_utils.exceptions import NotSupportedExtractionArchive
from bot.helper.ext_utils.human_format import get_readable_file_size, human_readable_bytes
from bot.helper.ext_utils.message_utils import delete_all_messages, sendMarkup, sendMessage, update_all_messages
from bot.helper.ext_utils.button_build import ButtonMaker
from bot.helper.ext_utils.misc_utils import clean_download, clean_target, split_file
from bot.helper.ext_utils.rclone_utils import get_gdlink
from bot.helper.ext_utils.zip_utils import get_base_name, get_path_size
from bot.helper.mirror_leech_utils.status_utils.tg_upload_status import TgUploadStatus
from bot.helper.mirror_leech_utils.upload_utils.rclone_upload import RcloneMirror
from bot.helper.mirror_leech_utils.status_utils.extract_status import ExtractStatus
from bot.helper.mirror_leech_utils.status_utils.split_status import SplitStatus
from bot.helper.mirror_leech_utils.status_utils.zip_status import ZipStatus
from bot.helper.mirror_leech_utils.upload_utils.telegram_uploader import TelegramUploader



class MirrorLeechListener:
    def __init__(self, message, tag, user_id, isZip=False, isMultiZip= False, extract=False, pswd=None, isLeech= False, select=False, seed=False):
        self.message = message
        self.uid = self.message.id
        self.user_id = user_id
        self.__isZip = isZip
        self.__isMultiZip = isMultiZip
        self.extract = extract
        self.__pswd = pswd
        self.tag = tag
        self.seed = seed
        self.select = select
        self.dir = f"{DOWNLOAD_DIR}{self.uid}"
        self.multizip_dir = f"{DOWNLOAD_DIR}{self.user_id}/multizip/"
        self.isPrivate = message.chat.type in [ChatType.PRIVATE, ChatType.GROUP]
        self.__isLeech = isLeech
        self.__suproc = None

    async def clean(self):
        try:
            Interval[0].cancel()
            Interval.clear()
            aria2.autopurge()
            await delete_all_messages()
        except:
            pass

    async def onDownloadStart(self):
        pass
        
    async def onMultiZipComplete(self):
        async with status_dict_lock:
            download = status_dict[self.uid]
            name = str(download.name())
            gid = download.gid()
        f_path= self.multizip_dir
        f_size = get_path_size(f_path)
        path = f"{f_path}{name}.zip" 
        async with status_dict_lock:
            status_dict[self.uid] = ZipStatus(name, f_size, gid, self)
        LEECH_SPLIT_SIZE = config_dict['LEECH_SPLIT_SIZE']  
        if self.__pswd is not None:
            if self.__isLeech and int(f_size) > LEECH_SPLIT_SIZE:
                cmd = ["7z", f"-v{LEECH_SPLIT_SIZE}b", "a", "-mx=0", f"-p{self.__pswd}", path, f_path]
                self.__suproc = await create_subprocess_exec(*cmd)
                LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}.0*')
            else:
                LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}')
                cmd =  ["7z", "a", "-mx=0", f"-p{self.__pswd}", path, f_path]
                self.__suproc = await create_subprocess_exec(*cmd)
        elif self.__isLeech and int(f_size) > LEECH_SPLIT_SIZE:
            LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}.0*')
            cmd= ["7z", f"-v{LEECH_SPLIT_SIZE}b", "a", "-mx=0", path, f_path]
            self.__suproc = await create_subprocess_exec(*cmd)
        else:
            LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}')
            cmd= ["7z", "a", "-mx=0", path, f_path]
            self.__suproc = await create_subprocess_exec(*cmd)
        await self.__suproc.wait()
        if self.__suproc.returncode == -9:
            return
        for dirpath, _, files in walk(f_path, topdown=False):        
            for file in files:
                if search(r'\.part0*1\.rar$|\.7z\.0*1$|\.zip\.0*1$|\.zip$|\.7z$|^.(?!.*\.part\d+\.rar)(?=.*\.rar$)', file) is None:    
                    del_path = ospath.join(dirpath, file)
                    try:
                        osremove(del_path)
                    except:
                        return
        up_dir, up_name = path.rsplit('/', 1)
        size = get_path_size(up_dir)
        if self.__isLeech:
            LOGGER.info(f"Leech Name: {up_name}")
            tg_up= TelegramUploader(up_dir, up_name, size, self)
            async with status_dict_lock:
                status_dict[self.uid] = TgUploadStatus(tg_up, size, gid, self)
            await update_all_messages()
            await tg_up.upload()    
        else:
            await RcloneMirror(up_dir, up_name, size, self.user_id, self).mirror()

    async def onDownloadComplete(self):
        async with status_dict_lock:
            download = status_dict[self.uid]
            name = str(download.name())
            gid = download.gid()
        LOGGER.info(f"Download completed: {name}")
        if name == "None" or not ospath.exists(f"{self.dir}/{name}"):
            name = listdir(f"{self.dir}")[-1]
        f_path = f'{self.dir}/{name}'
        f_size = get_path_size(f_path)
        if self.__isZip:
            path = f"{f_path}.zip" 
            async with status_dict_lock:
                status_dict[self.uid] = ZipStatus(name, f_size, gid, self)
            LEECH_SPLIT_SIZE = config_dict['LEECH_SPLIT_SIZE']    
            if self.__pswd is not None:
                if self.__isLeech and int(f_size) > LEECH_SPLIT_SIZE:
                    LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}.0*')
                    cmd= ["7z", f"-v{LEECH_SPLIT_SIZE}b", "a", "-mx=0", f"-p{self.__pswd}", path, f_path]
                    self.__suproc = await create_subprocess_exec(*cmd)
                else:
                    LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}')
                    cmd= ["7z", "a", "-mx=0", f"-p{self.__pswd}", path, f_path]
                    self.__suproc = await create_subprocess_exec(*cmd)
            elif self.__isLeech and int(f_size) > LEECH_SPLIT_SIZE:
                LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}.0*')
                cmd= ["7z", f"-v{LEECH_SPLIT_SIZE}b", "a", "-mx=0", path, f_path]
                self.__suproc = await create_subprocess_exec(*cmd)
            else:
                LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}')
                cmd= ["7z", "a", "-mx=0", path, f_path]
                self.__suproc = await create_subprocess_exec(*cmd)
            await self.__suproc.wait()
            if self.__suproc.returncode == -9:
                return
            await clean_target(f_path)
        elif self.extract:
            try:
                if ospath.isfile(f_path):
                    path = get_base_name(f_path)
                LOGGER.info(f"Extracting: {name}")
                async with status_dict_lock:
                    status_dict[self.uid] = ExtractStatus(name, f_size, gid, self)
                if ospath.isdir(f_path):
                    path = f_path    
                    for dirpath, _, files in walk(f_path, topdown=False):
                        for file in files:
                            if is_first_archive_split(file) or is_archive(file) and not file.endswith('.rar'):
                                t_path = ospath.join(dirpath, file)
                                if self.__pswd is not None:
                                    cmd= ["7z", "x", f"-p{self.__pswd}", t_path, f"-o{dirpath}", "-aot"]
                                else:
                                    cmd= ["7z", "x", t_path, f"-o{dirpath}", "-aot"]
                                self.__suproc = await create_subprocess_exec(*cmd)
                                await self.__suproc.wait()
                                if self.__suproc.returncode == -9:
                                    return
                                elif self.__suproc.returncode != 0:
                                    LOGGER.error('Unable to extract archive splits!')
                        if self.__suproc is not None and self.__suproc.returncode == 0:
                            for file in files:
                                if is_archive_split(file) or is_archive(file):
                                    del_path = ospath.join(dirpath, file)
                                    try:
                                        osremove(del_path)
                                    except:
                                        return
                else:
                    path = self.dir
                    if self.__pswd is not None:
                        cmd= ["7z", "x", f"-p{self.__pswd}", f_path, f"-o{path}", "-aot", "-xr!@PaxHeader"]
                    else:
                        cmd= ["7z", "x", f_path, f"-o{path}", "-aot", "-xr!@PaxHeader"]
                    self.__suproc = await create_subprocess_exec(*cmd)
                    await self.__suproc.wait()
                    if self.__suproc.returncode == -9:
                        return
                    elif self.__suproc.returncode == 0:
                        LOGGER.info(f"Extracted Path: {path}")
                        path= f_path 
                        try:
                            osremove(f_path)
                        except:
                            return
                    else:
                        LOGGER.error('Unable to extract archive! Uploading anyway')
                        path = f_path
            except NotSupportedExtractionArchive:
                LOGGER.info("Not any valid archive, uploading file as it is.")
                path = f_path
        else:
            path= f_path 
        up_dir, up_name = path.rsplit('/', 1)
        size = get_path_size(up_dir)
        if self.__isLeech:
            m_size = []
            o_files = []
            if not self.__isZip:
                checked = False
                LEECH_SPLIT_SIZE = config_dict['LEECH_SPLIT_SIZE']
                for dirpath, _, files in walk(up_dir, topdown=False):
                    for file_ in files:
                        f_path = ospath.join(dirpath, file_)
                        f_size = ospath.getsize(f_path)
                        if f_size > LEECH_SPLIT_SIZE:
                            if not checked:
                                checked = True
                                async with status_dict_lock:
                                    status_dict[self.uid] = SplitStatus(up_name, f_size, gid, self)
                                LOGGER.info(f"Splitting: {up_name}")
                            res = await split_file(f_path, f_size, file_, dirpath, LEECH_SPLIT_SIZE, self)
                            if not res:
                                return
                            if res == "errored":
                                if f_size <= TG_MAX_FILE_SIZE:
                                    continue
                                else:
                                    try:
                                        osremove(f_path)
                                    except:
                                        return
                            elif res != "errored":
                                m_size.append(f_size)
                                o_files.append(file_)
            for s in m_size:
                size = size - s
            LOGGER.info(f"Leech Name: {up_name}")
            tg_up= TelegramUploader(up_dir, up_name, size, self)
            async with status_dict_lock:
                status_dict[self.uid] = TgUploadStatus(tg_up, size, gid, self)
            await update_all_messages()
            await tg_up.upload()    
        else:
            if config_dict['LOCAL_MIRROR']:
                if BASE_URL:= config_dict['BASE_URL']:
                    buttons= ButtonMaker()
                    server_url = f'{BASE_URL}:{SERVER_PORT}/downloads/'
                    buttons.url_buildbutton("🖥 Local Server", server_url)
                    size = get_readable_file_size(size)
                    msg = f"<b>Name: </b><code>{escape(name)}</code>\n\n<b>Size: </b>{size}"
                    msg += f'\n<b>cc: </b>{self.tag}\n\n'
                    await sendMarkup(msg, self.message, reply_markup= buttons.build_menu(1))
                    async with status_dict_lock:
                        try:
                            del status_dict[self.uid]
                        except Exception as e:
                            LOGGER.error(str(e))
                        count = len(status_dict)
                    if count == 0:
                        await self.clean()
                    else:
                        await update_all_messages()
            else:
                await RcloneMirror(up_dir, up_name, size, self.user_id, self).mirror()

    async def onRcloneCopyComplete(self, conf, origin_dir, dest_drive, dest_dir):
        #Calculate Size
        cmd = ["rclone", "size", f'--config={conf}', "--json", f"{dest_drive}:{dest_dir}{origin_dir}"]
        process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        out, err = await process.communicate()
        output = out.decode().strip()
        return_code = await process.wait()
        if return_code != 0:
            return await sendMessage(err.decode().strip(), self.message)
        data = loads(output)   
        files = data["count"]
        size = human_readable_bytes(data["bytes"])
        format_out = f"**Total Files** {files}" 
        format_out += f"\n**Total Size**: {size}"
        format_out += f"\n<b>cc: </b>{self.tag}"
        #Get Link
        cmd = ["rclone", "link", f'--config={conf}', f"{dest_drive}:{dest_dir}{origin_dir}"]
        process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        out, err = await process.communicate()
        url = out.decode().strip()
        return_code = await process.wait()
        if return_code == 0:
            button= ButtonMaker()
            button.url_buildbutton("Cloud Link 🔗", url)
            await sendMarkup(format_out, self.message, reply_markup= button.build_menu(1))
        else:
            LOGGER.info(err.decode().strip())
            await sendMessage(format_out, self.message)
        await clean_download(self.dir)
        async with status_dict_lock:
            try:
                del status_dict[self.uid]
            except Exception as e:
                LOGGER.error(str(e))
            count = len(status_dict)
        if count == 0:
            await self.clean()
        else:
            await update_all_messages()

    async def onRcloneSyncComplete(self, msg):
        await sendMessage(msg, self.message)
        await clean_download(self.dir)
        async with status_dict_lock:
            try:
                del status_dict[self.uid]
            except Exception as e:
                LOGGER.error(str(e))
            count = len(status_dict)
        if count == 0:
            await self.clean()
        else:
            await update_all_messages()

    async def onRcloneUploadComplete(self, name, size, conf, remote, base, type, isGdrive):
        msg = f"<b>Name: </b><code>{escape(name)}</code>\n\n<b>Size: </b>{size}"
        msg += f'\n<b>cc: </b>{self.tag}\n\n'
        buttons= ButtonMaker()
        cmd = ["rclone", "link", f'--config={conf}', f"{remote}:{base}/{name}"]
        process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        out, _ = await process.communicate()
        url = out.decode().strip()
        return_code = await process.wait()
        if return_code == 0:
            buttons.url_buildbutton("Cloud Link 🔗", url)
            if isGdrive:
                await add_index_link(name, type, buttons)
            await sendMarkup(msg, self.message, buttons.build_menu(2))
        else:
            if isGdrive:
                await get_gdlink(remote, base, name, conf, type, buttons)
                await add_index_link(name, type, buttons)
                await sendMarkup(msg, self.message, buttons.build_menu(2))   
            else:
                await sendMessage(msg, self.message)   
        if self.__isMultiZip:
            await clean_download(self.multizip_dir)
        else:
            if not config_dict['MULTI_REMOTE_UP']:
                await clean_download(self.dir)
        async with status_dict_lock:
            try:
                del status_dict[self.uid]
            except Exception as e:
                LOGGER.error(str(e))
            count = len(status_dict)
        if count == 0:
            await self.clean()
        else:
            await update_all_messages()

    async def onUploadComplete(self, link, size, files, folders, typ, name):
        msg = f"<b>Name: </b><code>{escape(name)}</code>\n\n<b>Size: </b>{size}"
        msg += f'\n<b>Total Files: </b>{folders}'
        if typ != 0:
            msg += f'\n<b>Corrupted Files: </b>{typ}'
        msg += f'\n<b>cc: </b>{self.tag}\n\n'
        if not files:
            await sendMessage(msg, self.message)
        else:
            fmsg = ''
            for index, (link, name) in enumerate(files.items(), start=1):
                fmsg += f"{index}. <a href='{link}'>{name}</a>\n"
                if len(fmsg.encode() + msg.encode()) > 4000:
                    await sendMessage(msg + fmsg, self.message)
                    await sleep(1)
                    fmsg = ''
            if fmsg != '':
                await sendMessage(msg + fmsg, self.message)
        if self.__isMultiZip:
            await clean_download(self.multizip_dir)
        else:
            await clean_download(self.dir)
        async with status_dict_lock:
            try:
                del status_dict[self.uid]
            except Exception as e:
                LOGGER.error(str(e))
            count = len(status_dict)
        if count == 0:
            await self.clean()
        else:
            await update_all_messages()

    async def onDownloadError(self, error):
        error = error.replace('<', ' ').replace('>', ' ')
        if self.__isMultiZip:
            await clean_download(self.multizip_dir)
        else:
            await clean_download(self.dir)
        async with status_dict_lock:
            if self.uid in status_dict.keys():
                del status_dict[self.uid]
            count = len(status_dict)
        msg = f"{self.tag} your download has been stopped due to: {error}"
        await sendMessage(msg, self.message)
        if count == 0:
            await self.clean()
        else:
            await update_all_messages()

    async def onUploadError(self, error):
        e_str = error.replace('<', '').replace('>', '')
        await clean_download(self.dir)
        async with status_dict_lock:
            try:
                del status_dict[self.uid]
            except Exception as e:
                LOGGER.error(str(e))
            count = len(status_dict)
        await sendMessage(f"{self.tag} {e_str}", self.message)
        if count == 0:
            await self.clean()
        else:
            await update_all_messages()

