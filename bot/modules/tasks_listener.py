from html import escape
from json import loads as jsloads
from aioshutil import move
from os import path as ospath, remove as osremove, walk
from aiofiles.os import listdir, makedirs
from asyncio import create_subprocess_exec, sleep
from requests import utils as rutils
from bot import (
    DOWNLOAD_DIR,
    LOGGER,
    TG_MAX_FILE_SIZE,
    Interval,
    status_dict,
    status_dict_lock,
    user_data,
    aria2,
    config_dict,
)
from bot.helper.ext_utils.bot_utils import (
    cmd_exec,
    is_archive,
    is_archive_split,
    is_first_archive_split,
    run_sync,
)
from bot.helper.ext_utils.exceptions import NotSupportedExtractionArchive
from bot.helper.ext_utils.human_format import (
    get_readable_file_size,
    human_readable_bytes,
)
from bot.helper.telegram_helper.message_utils import (
    delete_all_messages,
    sendMarkup,
    sendMessage,
    update_all_messages,
)
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.misc_utils import (
    clean_download,
    clean_target,
    get_base_name,
    get_path_size,
    split_file,
)
from bot.helper.ext_utils.rclone_utils import get_drive_link
from bot.helper.mirror_leech_utils.status_utils.tg_upload_status import TgUploadStatus
from bot.helper.mirror_leech_utils.upload_utils.rclone_upload import RcloneMirror
from bot.helper.mirror_leech_utils.status_utils.extract_status import ExtractStatus
from bot.helper.mirror_leech_utils.status_utils.split_status import SplitStatus
from bot.helper.mirror_leech_utils.status_utils.zip_status import ZipStatus
from bot.helper.mirror_leech_utils.upload_utils.telegram_uploader import (
    TelegramUploader,
)


class TaskListener:
    def __init__(
        self,
        message,
        tag,
        user_id,
        compress=None,
        extract=None,
        select=False,
        seed=False,
        isLeech=False,
        screenshots=False,
        sameDir={},
    ):
        self.message = message
        self.tag = tag
        self.uid = message.id
        self.user_id = user_id
        self.compress = compress
        self.extract = extract
        self.sameDir = sameDir
        self.isLeech = isLeech
        self.seed = seed
        self.select = select
        self.screenshots = screenshots
        self.dir = f"{DOWNLOAD_DIR}{self.uid}"
        self.newDir = ""
        self.isSuperGroup = message.chat.type.name in ["SUPERGROUP", "CHANNEL"]
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

    async def onDownloadComplete(self):
        multi_links = False
        while True:
            if self.sameDir:
                if (
                    self.sameDir["total"] in [1, 0]
                    or self.sameDir["total"] > 1
                    and len(self.sameDir["tasks"]) > 1
                ):
                    break
            else:
                break
            await sleep(0.2)

        async with status_dict_lock:
            if self.sameDir and self.sameDir["total"] > 1:
                self.sameDir["tasks"].remove(self.uid)
                self.sameDir["total"] -= 1
                folder_name = self.sameDir["name"]
                spath = f"{self.dir}/{folder_name}"
                des_path = (
                    f"{DOWNLOAD_DIR}{list(self.sameDir['tasks'])[0]}/{folder_name}"
                )
                await makedirs(des_path, exist_ok=True)
                for item in await listdir(spath):
                    if item.endswith((".aria2", ".!qB")):
                        continue
                    item_path = f"{self.dir}/{folder_name}/{item}"
                    if item in await listdir(des_path):
                        await move(item_path, f"{des_path}/{self.uid}-{item}")
                    else:
                        await move(item_path, f"{des_path}/{item}")
                multi_links = True
            download = status_dict[self.uid]
            name = str(download.name()).replace("/", "")
            gid = download.gid()

        if not config_dict["NO_TASKS_LOGS"]:
            LOGGER.info(f"Download completed: {name}")

        if multi_links:
            await self.onUploadError("Downloaded! Waiting for other tasks...")
            return

        if name == "None" or not ospath.exists(f"{self.dir}/{name}"):
            try:
                files = await listdir(self.dir)
            except Exception as e:
                await self.onUploadError(str(e))
                return
            name = files[-1]
            if name == "yt-dlp-thumb":
                name = files[0]

        path = ""
        m_path = f"{self.dir}/{name}"
        size = await get_path_size(m_path)
        user_dict = user_data.get(self.message.from_user.id, {})

        if self.compress is not None:
            pswd = self.compress
            if self.seed and self.isLeech:
                self.newDir = f"{self.dir}10000"
                path = f"{self.newDir}/{name}.zip"
            else:
                path = f"{m_path}.zip"
            async with status_dict_lock:
                status_dict[self.uid] = ZipStatus(name, size, gid, self)
            LEECH_SPLIT_SIZE = (
                user_dict.get("split_size", False) or config_dict["LEECH_SPLIT_SIZE"]
            )
            if pswd:
                if self.isLeech and int(size) > LEECH_SPLIT_SIZE:
                    cmd = [
                        "7z",
                        f"-v{LEECH_SPLIT_SIZE}b",
                        "a",
                        "-mx=0",
                        f"-p{pswd}",
                        path,
                        m_path,
                    ]
                else:
                    cmd = ["7z", "a", "-mx=0", f"-p{pswd}", path, m_path]
            elif self.isLeech and int(size) > LEECH_SPLIT_SIZE:
                cmd = ["7z", f"-v{LEECH_SPLIT_SIZE}b", "a", "-mx=0", path, m_path]
            else:
                cmd = ["7z", "a", "-mx=0", path, m_path]
            self.suproc = await create_subprocess_exec(*cmd)
            await self.suproc.wait()
            if self.suproc.returncode == -9:
                return
            elif not self.seed:
                await clean_target(m_path)

        if self.extract is not None:
            pswd = self.extract
            try:
                if ospath.isfile(m_path):
                    path = get_base_name(m_path)
                if not config_dict["NO_TASKS_LOGS"]:
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
                            if (
                                is_first_archive_split(file)
                                or is_archive(file)
                                and not file.endswith(".rar")
                            ):
                                f_path = ospath.join(dirpath, file)
                                if self.seed:
                                    t_path = dirpath.replace(self.dir, self.newDir)
                                else:
                                    t_path = dirpath
                                if pswd:
                                    cmd = [
                                        "7z",
                                        "x",
                                        f"-p{pswd}",
                                        f_path,
                                        f"-o{t_path}",
                                        "-aot",
                                        "-xr!@PaxHeader",
                                    ]
                                else:
                                    cmd = [
                                        "7z",
                                        "x",
                                        f_path,
                                        f"-o{t_path}",
                                        "-aot",
                                        "-xr!@PaxHeader",
                                    ]
                                self.suproc = await create_subprocess_exec(*cmd)
                                await self.suproc.wait()
                                if self.suproc.returncode == -9:
                                    return
                                elif self.suproc.returncode != 0:
                                    LOGGER.error("Unable to extract archive splits!")
                        if (
                            not self.seed
                            and self.suproc is not None
                            and self.suproc.returncode == 0
                        ):
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
                    if pswd:
                        cmd = [
                            "7z",
                            "x",
                            f"-p{pswd}",
                            m_path,
                            f"-o{path}",
                            "-aot",
                            "-xr!@PaxHeader",
                        ]
                    else:
                        cmd = ["7z", "x", m_path, f"-o{path}", "-aot", "-xr!@PaxHeader"]
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
                        LOGGER.error("Unable to extract archive! Uploading anyway")
                        self.newDir = ""
                        path = m_path
            except NotSupportedExtractionArchive:
                LOGGER.info("Not any valid archive, uploading file as it is.")
                self.newDir = ""
                path = m_path

        if self.compress is None and self.extract is None:
            path = m_path

        up_dir, up_name = path.rsplit("/", 1)
        size = await get_path_size(up_dir)
        if self.isLeech:
            m_size = []
            o_files = []
            if self.compress is None:
                checked = False
                LEECH_SPLIT_SIZE = (
                    user_dict.get("split_size", False)
                    or config_dict["LEECH_SPLIT_SIZE"]
                )
                for dirpath, _, files in walk(up_dir, topdown=False):
                    for file_ in files:
                        f_path = ospath.join(dirpath, file_)
                        f_size = ospath.getsize(f_path)
                        if f_size > LEECH_SPLIT_SIZE:
                            if not checked:
                                checked = True
                                async with status_dict_lock:
                                    status_dict[self.uid] = SplitStatus(
                                        up_name, f_size, gid, self
                                    )
                                LOGGER.info(f"Splitting: {up_name}")
                            res = await split_file(
                                f_path, f_size, file_, dirpath, LEECH_SPLIT_SIZE, self
                            )
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
            size = await get_path_size(up_dir)
            for s in m_size:
                size = size - s
            if not config_dict["NO_TASKS_LOGS"]:
                LOGGER.info(f"Leech Name: {up_name}")
            tg_up = TelegramUploader(up_dir, up_name, size, self)
            async with status_dict_lock:
                status_dict[self.uid] = TgUploadStatus(tg_up, size, gid, self)
            await update_all_messages()
            await tg_up.upload()
        else:
            if config_dict["LOCAL_MIRROR"]:
                size = get_readable_file_size(size)
                msg = f"<b>Name: </b><code>{escape(name)}</code>\n\n"
                msg += f"<b>Size: </b>{size}\n"
                msg += f"<b>cc: </b>{self.tag}\n\n"
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
                size = await get_path_size(path)
                if not config_dict["NO_TASKS_LOGS"]:
                    LOGGER.info(f"Upload Name: {up_name}")
                await RcloneMirror(up_dir, up_name, size, self.user_id, self).mirror()

    async def onRcloneCopyComplete(
        self, config_path, name, dest_remote, dest_dir, isGdrive
    ):
        async with status_dict_lock:
            if self.uid in status_dict.keys():
                del status_dict[self.uid]
            count = len(status_dict)

        button = ButtonMaker()
        path = f"{dest_remote}:{dest_dir}/{name}"

        if name.endswith("/"):
            mime_type = "Folder"
        else:
            mime_type = "File"

        cmd = [
            "rclone",
            "size",
            f"--config={config_path}",
            "--json",
            f"{dest_remote}:{dest_dir}{name}",
        ]
        out, err, rc = await cmd_exec(cmd)
        if rc != 0:
            await sendMessage(f"Error: {err}", self.message)
            return
        data = jsloads(out)
        msg = f"<b>Total Files</b>: {data['count']}"
        msg += f"\n<b>Total Size</b>: {human_readable_bytes(data['bytes'])}"
        msg += f"\n\n<b>cc: </b>{self.tag}"

        if isGdrive:
            link = await get_drive_link(path, config_path, mime_type)
            if link:
                button.url_buildbutton("Cloud Link 🔗", link)
            else:
                button.url_buildbutton(
                    "Cloud Link 🚫", "https://drive.google.com/uc?id=err"
                )
        else:
            cmd = [
                "rclone",
                "link",
                f"--config={config_path}",
                f"{dest_remote}:{dest_dir}{name}",
            ]
            out, err, rc = await cmd_exec(cmd)
            url = out.strip()
            if rc == 0:
                button.url_buildbutton("Cloud Link 🔗", url)
            else:
                LOGGER.error(f"Error while getting link. Error: {err}")
                button.url_buildbutton("Cloud Link 🚫", "http://www.example.com")

        await sendMarkup(msg, self.message, reply_markup=button.build_menu(1))

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

    async def onRcloneUploadComplete(
        self, name, size, config_path, remote, base, mime_type, isGdrive
    ):
        msg = f"<b>Name: </b><code>{escape(name)}</code>\n"
        msg += f"<b>Size: </b>{size}\n"
        msg += f"<b>Type: </b>{mime_type}\n\n"

        button = ButtonMaker()
        path = f"{remote}:{base}/{name}"

        if isGdrive:
            link = await get_drive_link(path, config_path, mime_type)
            if link:
                button.url_buildbutton("Cloud Link 🔗", link)
            else:
                button.url_buildbutton(
                    "Cloud Link 🚫", "https://drive.google.com/uc?id=err"
                )
        else:
            cmd = ["rclone", "link", f"--config={config_path}", path]
            res, err, code = await cmd_exec(cmd)
            if code == 0:
                button.url_buildbutton("Cloud Link 🔗", res)
            else:
                LOGGER.error(f"Error while getting link. Error: {err}")
                button.url_buildbutton("Cloud Link 🚫", "http://www.example.com")
        if isGdrive and (GD_INDEX_URL := config_dict["GD_INDEX_URL"]):
            encoded_path = rutils.quote(f"{base}{name}")
            share_url = f"{GD_INDEX_URL}/{encoded_path}"
            if type == "Folder":
                share_url += "/"
                button.url_buildbutton("⚡ Index Link", share_url)
            else:
                button.url_buildbutton("⚡ Index Link", share_url)
                if config_dict["VIEW_LINK"]:
                    share_urls = f"{GD_INDEX_URL}/{encoded_path}?a=view"
                    button.url_buildbutton("🌐 View Link", share_urls)
        elif RC_INDEX_URL := config_dict["RC_INDEX_URL"]:
            RC_INDEX_PORT = config_dict["RC_INDEX_PORT"]
            encoded_path = rutils.quote(f"{base}{name}")
            share_url = f"{RC_INDEX_URL}:{RC_INDEX_PORT}/[{remote}:]/{encoded_path}"
            if mime_type == "Folder":
                share_url += "/"
            button.url_buildbutton("Rclone Link 🔗", share_url)

        msg += f"<b>cc: </b>{self.tag}"
        await sendMessage(msg, self.message, button.build_menu(2))

        if self.seed:
            if self.newDir:
                await clean_target(self.newDir)
            elif self.compress is not None:
                await clean_target(f"{self.dir}/{name}")
            return

        if not config_dict["MULTI_REMOTE_UP"]:
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
        msg = f"<b>Name: </b><code>{escape(name)}</code>\n\n"
        msg += f"<b>Size: </b>{size}"

        if self.isLeech:
            msg += f"\n<b>Total Files: </b>{folders}"
            if mime_type != 0:
                msg += f"\n<b>Corrupted Files: </b>{mime_type}"
            msg += f"\n<b>cc: </b>{self.tag}\n\n"
            if not files:
                await sendMessage(msg, self.message)
            else:
                fmsg = ""
                for index, (link, name) in enumerate(files.items(), start=1):
                    fmsg += f"{index}. <a href='{link}'>{name}</a>\n"
                    if len(fmsg.encode() + msg.encode()) > 4000:
                        await sendMessage(msg + fmsg, self.message)
                        await sleep(1)
                        fmsg = ""
                if fmsg != "":
                    await sendMessage(msg + fmsg, self.message)
            if self.seed:
                if self.newDir:
                    await clean_target(self.newDir)
                return
        else:
            msg += f"\n\n<b>Type: </b>{mime_type}"
            if mime_type == "Folder":
                msg += f"\n<b>SubFolders: </b>{folders}"
                msg += f"\n<b>Files: </b>{files}"

            buttons = ButtonMaker()
            buttons.url_buildbutton("Cloud Link", link)

            msg += f"\n\n<b>cc: </b>{self.tag}"
            await sendMessage(msg, self.message, buttons.build_menu(1))

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

        if self.sameDir and self.uid in self.sameDir["tasks"]:
            self.sameDir["tasks"].remove(self.uid)
            self.sameDir["total"] -= 1

        msg = f"{self.tag} Download stopped due to: {escape(error)}"
        await sendMessage(msg, self.message)

        if count == 0:
            await self.clean()
        else:
            await update_all_messages()

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
