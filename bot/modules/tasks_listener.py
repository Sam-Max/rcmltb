from html import escape
from json import loads
from re import search
from os import listdir, path as ospath, remove as osremove, walk
from asyncio import create_subprocess_exec, sleep
from asyncio.subprocess import PIPE
from bot import DOWNLOAD_DIR, LOGGER, TG_MAX_FILE_SIZE, Interval, status_dict, status_dict_lock, user_data, aria2, config_dict
from bot.helper.ext_utils.bot_utils import add_index_link, is_archive, is_archive_split, is_first_archive_split, run_sync
from bot.helper.ext_utils.exceptions import NotSupportedExtractionArchive
from bot.helper.ext_utils.human_format import get_readable_file_size, human_readable_bytes
from bot.helper.telegram_helper.message_utils import delete_all_messages, sendMarkup, sendMessage, update_all_messages
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.misc_utils import clean_download, clean_target, get_base_name, get_path_size, split_file
from bot.helper.ext_utils.rclone_utils import get_drive_link
from bot.helper.mirror_leech_utils.status_utils.tg_upload_status import TgUploadStatus
from bot.helper.mirror_leech_utils.upload_utils.rclone_upload import RcloneMirror
from bot.helper.mirror_leech_utils.status_utils.extract_status import ExtractStatus
from bot.helper.mirror_leech_utils.status_utils.split_status import SplitStatus
from bot.helper.mirror_leech_utils.status_utils.zip_status import ZipStatus
from bot.helper.mirror_leech_utils.upload_utils.telegram_uploader import TelegramUploader



class MirrorLeechListener:
    def __init__(self, message, tag, user_id, isZip=False, extract=False, pswd=None, select=False, seed=False, isLeech= False, isMultiZip= False, zip_name=None):
        self.message = message
        self.tag = tag
        self.uid = message.id
        self.user_id = user_id
        self.__isZip = isZip
        self.extract = extract
        self.__pswd = pswd
        self.__zip_name= zip_name
        self.isMultiZip = isMultiZip
        self.isLeech = isLeech
        self.seed = seed
        self.select = select
        self.dir = f"{DOWNLOAD_DIR}{self.uid}"
        self.newDir = ""
        self.multiZipDir = f"{DOWNLOAD_DIR}{self.__zip_name}/"
        self.isSuperGroup = message.chat.type.name in ['SUPERGROUP', 'CHANNEL']
        self.suproc = None

    async def clean(self):
        try:
            if Interval:
                Interval[0].cancel()
                Interval.clear()
            await run_sync(aria2.purge)
            await delete_all_messages()
        except:
            pass

    async def onDownloadStart(self):
        pass
        
    async def onMultiZipComplete(self):
        async with status_dict_lock:
            download = status_dict[self.uid]
            gid = download.gid()
            
        zip_path= self.multiZipDir
        path = f"{zip_path}{self.__zip_name}.zip" 
        size = get_path_size(zip_path)
        user_dict = user_data.get(self.message.from_user.id, {})
        async with status_dict_lock:
            status_dict[self.uid] = ZipStatus(self.__zip_name, size, gid, self)

        LEECH_SPLIT_SIZE = user_dict.get('split_size', False) or config_dict['LEECH_SPLIT_SIZE']  
        if self.__pswd is not None:
            if self.isLeech and int(size) > LEECH_SPLIT_SIZE:
                cmd = ["7z", f"-v{LEECH_SPLIT_SIZE}b", "a", "-mx=0", f"-p{self.__pswd}", path, zip_path]
                LOGGER.info(f'Zip: orig_path: {zip_path}, zip_path: {path}.0*')
            else:
                LOGGER.info(f'Zip: orig_path: {zip_path}, zip_path: {path}')
                cmd =  ["7z", "a", "-mx=0", f"-p{self.__pswd}", path, zip_path]
        elif self.isLeech and int(size) > LEECH_SPLIT_SIZE:
            LOGGER.info(f'Zip: orig_path: {zip_path}, zip_path: {path}.0*')
            cmd= ["7z", f"-v{LEECH_SPLIT_SIZE}b", "a", "-mx=0", path, zip_path]
        else:
            LOGGER.info(f'Zip: orig_path: {zip_path}, zip_path: {path}')
            cmd= ["7z", "a", "-mx=0", path, zip_path]
        self.suproc = await create_subprocess_exec(*cmd)
        await self.suproc.wait()
        if self.suproc.returncode == -9:
            return
        for dirpath, _, files in walk(zip_path, topdown=False):        
            for file in files:
                if search(r'\.part0*1\.rar$|\.7z\.0*1$|\.zip\.0*1$|\.zip$|\.7z$|^.(?!.*\.part\d+\.rar)(?=.*\.rar$)', file) is None:    
                    del_path = ospath.join(dirpath, file)
                    try:
                        osremove(del_path)
                    except:
                        return
        up_dir, up_name = path.rsplit('/', 1)
        size = get_path_size(up_dir)

        if self.isLeech:
            if not config_dict['NO_TASKS_LOGS']:
                LOGGER.info(f"Leech Name: {up_name}")
            tg_up= TelegramUploader(up_dir, up_name, size, self)
            async with status_dict_lock:
                status_dict[self.uid] = TgUploadStatus(tg_up, size, gid, self)
            await update_all_messages()
            await tg_up.upload()    
        else:
            if not config_dict['NO_TASKS_LOGS']:
                LOGGER.info(f"Upload Name: {up_name}")
            await RcloneMirror(up_dir, up_name, size, self.user_id, self).mirror()

    async def onDownloadComplete(self):
        async with status_dict_lock:
            download = status_dict[self.uid]
            name = str(download.name()).replace('/', '')
            gid = download.gid()

        if not config_dict['NO_TASKS_LOGS']:
            LOGGER.info(f"Download completed: {name}")
        if name == "None" or not ospath.exists(f"{self.dir}/{name}"):
            name = listdir(f"{self.dir}")[-1]
        path= ""
        m_path = f'{self.dir}/{name}'
        size = get_path_size(m_path)
        user_dict = user_data.get(self.message.from_user.id, {})
        if self.__isZip:
            if self.seed and self.isLeech:
                self.newDir = f"{self.dir}10000"
                path = f"{self.newDir}/{name}.zip"
            else:
                path = f"{m_path}.zip"
            async with status_dict_lock:
                status_dict[self.uid] = ZipStatus(name, size, gid, self)
            LEECH_SPLIT_SIZE = user_dict.get('split_size', False) or config_dict['LEECH_SPLIT_SIZE']      
            if self.__pswd is not None:
                if self.isLeech and int(size) > LEECH_SPLIT_SIZE:
                    LOGGER.info(f'Zip: orig_path: {m_path}, zip_path: {path}.0*')
                    cmd= ["7z", f"-v{LEECH_SPLIT_SIZE}b", "a", "-mx=0", f"-p{self.__pswd}", path, m_path]
                else:
                    LOGGER.info(f'Zip: orig_path: {m_path}, zip_path: {path}')
                    cmd= ["7z", "a", "-mx=0", f"-p{self.__pswd}", path, m_path]
            elif self.isLeech and int(size) > LEECH_SPLIT_SIZE:
                LOGGER.info(f'Zip: orig_path: {m_path}, zip_path: {path}.0*')
                cmd= ["7z", f"-v{LEECH_SPLIT_SIZE}b", "a", "-mx=0", path, m_path]
            else:
                LOGGER.info(f'Zip: orig_path: {m_path}, zip_path: {path}')
                cmd= ["7z", "a", "-mx=0", path, m_path]
            self.suproc = await create_subprocess_exec(*cmd)
            await self.suproc.wait()
            if self.suproc.returncode == -9:
                return
            elif not self.seed:
                await clean_target(m_path)
        elif self.extract:
            try:
                if ospath.isfile(m_path):
                    path = get_base_name(m_path)
                if not config_dict['NO_TASKS_LOGS']:    
                    LOGGER.info(f"Extracting: {name}")
                async with status_dict_lock:
                    status_dict[self.uid] = ExtractStatus(name, size, gid, self)
                if ospath.isdir(m_path):
                    if self.seed:
                        self.newDir = f"{self.dir}10000"
                        path = f"{self.newDir}/{name}"
                    else:
                        path = m_path 
                    for dirpath, _, files in walk(m_path, topdown=False):
                        for file in files:
                            if is_first_archive_split(file) or is_archive(file) and not file.endswith('.rar'):
                                f_path = ospath.join(dirpath, file)
                                if self.seed:
                                    t_path = dirpath.replace(self.dir, self.newDir) 
                                else:
                                    t_path = dirpath
                                if self.__pswd is not None:
                                    cmd= ["7z", "x", f"-p{self.__pswd}", f_path, f"-o{t_path}", "-aot", "-xr!@PaxHeader"]
                                else:
                                    cmd= ["7z", "x", f_path, f"-o{t_path}", "-aot", "-xr!@PaxHeader"]
                                self.suproc = await create_subprocess_exec(*cmd)
                                await self.suproc.wait()
                                if self.suproc.returncode == -9:
                                    return
                                elif self.suproc.returncode != 0:
                                    LOGGER.error('Unable to extract archive splits!')
                        if not self.seed and self.suproc is not None and self.suproc.returncode == 0:
                            for file_ in files:
                                if is_archive_split(file_) or is_archive(file_):
                                    del_path = ospath.join(dirpath, file_)
                                    try:
                                        osremove(del_path)
                                    except:
                                        return
                else:
                    if self.seed and self.isLeech:
                        self.newDir = f"{self.dir}10000"
                        path = path.replace(self.dir, self.newDir)
                    if self.__pswd is not None:
                        cmd= ["7z", "x", f"-p{self.__pswd}", m_path, f"-o{path}", "-aot", "-xr!@PaxHeader"]
                    else:
                        cmd= ["7z", "x", m_path, f"-o{path}", "-aot", "-xr!@PaxHeader"]
                    self.suproc = await create_subprocess_exec(*cmd)
                    await self.suproc.wait()
                    if self.suproc.returncode == -9:
                        return
                    elif self.suproc.returncode == 0:
                        LOGGER.info(f"Extracted Path: {path}")
                        if not self.seed:
                            try:
                                osremove(m_path)
                            except:
                                return
                    else:
                        LOGGER.error('Unable to extract archive! Uploading anyway')
                        path = m_path
            except NotSupportedExtractionArchive:
                LOGGER.info("Not any valid archive, uploading file as it is.")
                path = m_path
        else:
            path = m_path
        up_dir, up_name = path.rsplit('/', 1)
        size = get_path_size(up_dir)
        if self.isLeech:
            m_size = []
            o_files = []
            if not self.__isZip:
                checked = False
                LEECH_SPLIT_SIZE = user_dict.get('split_size', False) or config_dict['LEECH_SPLIT_SIZE']   
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
                            elif not self.seed or self.newDir:
                                try:
                                    osremove(f_path)
                                except:
                                    return
                            else:
                                m_size.append(f_size)
                                o_files.append(file_)
            size = get_path_size(up_dir)
            for s in m_size:
                size = size - s
            if not config_dict['NO_TASKS_LOGS']:
                LOGGER.info(f"Leech Name: {up_name}")
            tg_up= TelegramUploader(up_dir, up_name, size, self)
            async with status_dict_lock:
                status_dict[self.uid] = TgUploadStatus(tg_up, size, gid, self)
            await update_all_messages()
            await tg_up.upload()    
        else:
            if config_dict['LOCAL_MIRROR']:
                size = get_readable_file_size(size)
                msg = f"<b>Name: </b><code>{escape(name)}</code>\n\n"
                msg += f"<b>Size: </b>{size}\n"
                msg += f'<b>cc: </b>{self.tag}\n\n'
                await sendMessage(msg, self.message)
                async with status_dict_lock:
                    if self.uid in status_dict.keys():
                        del status_dict[self.uid]
                    count = len(status_dict)
                if count == 0:
                    await self.clean()
                else:
                    await update_all_messages()
            else:
                size = get_path_size(path)
                if not config_dict['NO_TASKS_LOGS']:
                    LOGGER.info(f"Upload Name: {up_name}")
                await RcloneMirror(up_dir, up_name, size, self.user_id, self).mirror()

    async def onRcloneCopyComplete(self, conf, origin_dir, dest_remote, dest_dir):
        async with status_dict_lock:
            if self.uid in status_dict.keys():
                del status_dict[self.uid]
            count = len(status_dict)
        
        cmd = ["rclone", "size", f'--config={conf}', "--json", f"{dest_remote}:{dest_dir}{origin_dir}"]
        process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        out, err = await process.communicate()
        output = out.decode().strip()
        rc = await process.wait()
        if rc != 0:
            await sendMessage(err.decode().strip(), self.message)
            return
        else:
            data = loads(output)   
            files = data["count"]
            size = human_readable_bytes(data["bytes"])
        
        format_out = f"**Total Files** {files}" 
        format_out += f"\n**Total Size**: {size}"
        format_out += f"\n<b>cc: </b>{self.tag}"
        
        cmd = ["rclone", "link", f'--config={conf}', f"{dest_remote}:{dest_dir}{origin_dir}"]
        process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        out, err = await process.communicate()
        url = out.decode().strip()
        rc = await process.wait()
        if rc == 0:
            button= ButtonMaker()
            button.url_buildbutton("Cloud Link 🔗", url)
            await sendMarkup(format_out, self.message, reply_markup= button.build_menu(1))
        else:
            LOGGER.info(err.decode().strip())
            await sendMessage(format_out, self.message)
       
        await clean_download(self.dir)
        
        if count == 0:
            await self.clean()
        else:
            await update_all_messages()

    async def onRcloneSyncComplete(self, msg):
        async with status_dict_lock:
            if self.uid in status_dict.keys():
                del status_dict[self.uid]
            count = len(status_dict)

        await sendMessage(msg, self.message)
        
        await clean_download(self.dir)
        
        if count == 0:
            await self.clean()
        else:
            await update_all_messages()

    async def onRcloneUploadComplete(self, name, size, conf, remote, base, mime_type, isGdrive):      
        msg = f"<b>Name: </b><code>{escape(name)}</code>\n\n<b>Size: </b>{size}"
        msg += f'\n<b>cc: </b>{self.tag}\n\n'
        buttons= ButtonMaker()
        
        cmd = ["rclone", "link", f'--config={conf}', f"{remote}:{base}/{name}"]
        process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        out, _ = await process.communicate()
        url = out.decode().strip()
        rc = await process.wait()
        if rc == 0:
            GD_INDEX_URL = config_dict['GD_INDEX_URL']
            if isGdrive and GD_INDEX_URL:
                await add_index_link(name, mime_type, GD_INDEX_URL, buttons)
            buttons.url_buildbutton("Cloud Link 🔗", url)
            await sendMarkup(msg, self.message, buttons.build_menu(2))
        else:
            if isGdrive:
                await get_drive_link(remote, base, name, conf, mime_type, buttons)
                if GD_INDEX_URL := config_dict['GD_INDEX_URL']:
                    await add_index_link(name, mime_type, GD_INDEX_URL, buttons)
                await sendMarkup(msg, self.message, buttons.build_menu(2))   
            else:
                await sendMessage(msg, self.message)  

        if self.seed:
            if self.__isZip:
                await clean_target(f"{self.dir}/{name}")
            elif self.newDir:
                await clean_target(self.newDir)
            return 
        
        if self.isMultiZip:
            await clean_download(self.multiZipDir)
        elif not config_dict['MULTI_REMOTE_UP']:
            await clean_download(self.dir)

        async with status_dict_lock:
            if self.uid in status_dict.keys():
                del status_dict[self.uid]
            count = len(status_dict)

        if count == 0:
            await self.clean()
        else:
            await update_all_messages()

    async def onUploadComplete(self, link, size, files, folders, mime_type, name):
        msg = f"<b>Name: </b><code>{escape(name)}</code>\n\n<b>Size: </b>{size}"
        msg += f'\n<b>Total Files: </b>{folders}'
        if mime_type != 0:
            msg += f'\n<b>Corrupted Files: </b>{mime_type}'
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
        
        if self.seed:
            if self.__isZip:
                await clean_target(f"{self.dir}/{name}")
            elif self.newDir:
                await clean_target(self.newDir)
            return
        
        if self.isMultiZip:
            await clean_download(self.multiZipDir)
        else:
            await clean_download(self.dir)

        async with status_dict_lock:
            if self.uid in status_dict.keys():
                del status_dict[self.uid]
            count = len(status_dict)
        
        if count == 0:
            await self.clean()
        else:
            await update_all_messages()

    async def onDownloadError(self, error):
        async with status_dict_lock:
            if self.uid in status_dict.keys():
                del status_dict[self.uid]
            count = len(status_dict)

        msg = f"{self.tag} Download stopped due to: {escape(error)}"    
        await sendMessage(msg, self.message)

        if count == 0:
            await self.clean()
        else:
            await update_all_messages()

        if self.isMultiZip:
            await clean_download(self.multiZipDir)
        else:
            await clean_download(self.dir)

        if self.newDir:
            await clean_download(self.newDir)
        
    async def onUploadError(self, error):
        async with status_dict_lock:
            if self.uid in status_dict.keys():
                del status_dict[self.uid]
            count = len(status_dict)

        await sendMessage(f"{self.tag} {escape(error)}", self.message)
        
        if count == 0:
            await self.clean()
        else:
            await update_all_messages()

        await clean_download(self.dir)
        
        if self.newDir:
            await clean_download(self.newDir)

       
        

