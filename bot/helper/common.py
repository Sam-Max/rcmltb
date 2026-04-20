from asyncio import create_subprocess_exec
from html import escape
from os import path as ospath, remove as osremove, walk

from aiofiles.os import listdir, makedirs
from aioshutil import move

from bot import (
    config_dict,
    LOGGER,
    status_dict,
    status_dict_lock,
    user_data,
)
from bot.core.torrent_manager import TorrentManager
from bot.helper.ext_utils.bot_utils import (
    is_archive,
    is_archive_split,
    is_first_archive_split,
    run_sync_to_async,
)
from bot.helper.ext_utils.exceptions import NotSupportedExtractionArchive
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.telegram_helper.message_utils import (
    delete_all_messages,
    sendMessage,
    update_all_messages,
)
from bot.helper.mirror_leech_utils.status_utils.extract_status import ExtractStatus
from bot.helper.mirror_leech_utils.status_utils.split_status import SplitStatus
from bot.helper.mirror_leech_utils.status_utils.zip_status import ZipStatus
from bot.core.telegram_manager import TgClient
from bot.helper.ext_utils.links_utils import is_gdrive_id, is_rclone_path


class TaskConfig:
    def __init__(self):
        self.mid = ""
        self.user_id = 0
        self.dir = ""
        self.up_dir = ""
        self.link = ""
        self.tag = ""
        self.name = ""
        self.size = 0
        self.is_leech = False
        self.is_qbit = False
        self.is_file = False
        self.extract = False
        self.compress = False
        self.select = False
        self.seed = False
        self.same_dir = {}
        self.folder_name = ""
        self.is_cancelled = False
        self.subproc = None
        self.new_dir = ""
        self.force_upload = False
        self.force_download = False
        self.force_run = False
        self.stop_duplicate = False
        self.up_dest = ""
        self.user_transmission = False
        self.bot_transmission = False
        self.is_ytdlp = False
        self.is_super_chat = False
        self.split_size = 0
        self.max_split_size = 0
        self.as_doc = False
        self.as_med = False
        self.thumb = None
        self.name_sub = ""
        self.thumbnail_layout = ""
        self.rc_flags = ""
        self.hybrid_leech = False

    async def before_start(self):
        if not self.is_leech:
            self.stop_duplicate = (
                self.user_dict.get("STOP_DUPLICATE")
                or "STOP_DUPLICATE" not in self.user_dict
                and config_dict.get("STOP_DUPLICATE", False)
            )
            default_upload = (
                self.user_dict.get("DEFAULT_UPLOAD", "") or config_dict.get("DEFAULT_UPLOAD", "")
            )
            if (not self.up_dest and default_upload == "rc") or self.up_dest == "rc":
                self.up_dest = self.user_dict.get("RCLONE_PATH") or config_dict.get("RCLONE_PATH", "")
            elif (not self.up_dest and default_upload == "gd") or self.up_dest == "gd":
                self.up_dest = self.user_dict.get("GDRIVE_ID") or config_dict.get("GDRIVE_ID", "")
            if not self.up_dest:
                raise ValueError("No Upload Destination!")
            if self.up_dest.startswith("rcl"):
                from bot.helper.ext_utils.rclone_utils import is_rclone_config
                if not await is_rclone_config(self.user_id, self.message):
                    raise ValueError("Rclone config not found!")
            elif self.up_dest.startswith("gdl"):
                raise ValueError("Google Drive interactive selection not yet supported for yt-dlp.")
            elif is_rclone_path(self.up_dest):
                self.up_dest = self.up_dest.rstrip("/")
            elif not is_gdrive_id(self.up_dest):
                raise ValueError("Wrong Upload Destination!")
        else:
            self.up_dest = (
                self.up_dest
                or self.user_dict.get("LEECH_DUMP_CHAT")
                or config_dict.get("LEECH_DUMP_CHAT", "")
            )

            if self.user_transmission or self.bot_transmission:
                if self.bot_transmission:
                    self.user_transmission = False
                    self.hybrid_leech = False
                elif self.user_transmission:
                    self.user_transmission = TgClient.IS_PREMIUM_USER

            if self.hybrid_leech and not self.user_transmission:
                self.hybrid_leech = TgClient.IS_PREMIUM_USER

            if self.split_size:
                if str(self.split_size).isdigit():
                    self.split_size = int(self.split_size)
                else:
                    from bot.helper.ext_utils.bot_utils import get_size_bytes
                    self.split_size = get_size_bytes(self.split_size)

            self.split_size = (
                self.split_size
                or self.user_dict.get("split_size")
                or config_dict.get("LEECH_SPLIT_SIZE", 0)
            )
            self.max_split_size = (
                TgClient.MAX_SPLIT_SIZE if self.user_transmission else 2097152000
            )
            if self.split_size:
                self.split_size = min(self.split_size, self.max_split_size)
            else:
                self.split_size = self.max_split_size

            if not self.as_doc:
                self.as_doc = (
                    not self.as_med
                    if self.as_med
                    else (
                        self.user_dict.get("AS_DOCUMENT", False)
                        or config_dict.get("AS_DOCUMENT", False)
                        and "AS_DOCUMENT" not in self.user_dict
                    )
                )

            self.thumbnail_layout = (
                self.thumbnail_layout
                or self.user_dict.get("THUMBNAIL_LAYOUT", False)
                or (
                    config_dict.get("THUMBNAIL_LAYOUT", "")
                    if "THUMBNAIL_LAYOUT" not in self.user_dict
                    else ""
                )
            )

    async def proceed_extract(self, path, gid):
        """Extract archive files."""
        from bot.helper.ext_utils.files_utils import (
            get_base_name,
            get_path_size,
            clean_target,
        )

        m_path = path
        name = ospath.basename(path)
        size = await get_path_size(m_path)

        try:
            if ospath.isfile(m_path):
                path = get_base_name(m_path)
            if not config_dict["NO_TASKS_LOGS"]:
                LOGGER.info(f"Extracting: {name}")
            async with status_dict_lock:
                status_dict[self.uid] = ExtractStatus(name, size, gid, self)

            if ospath.isdir(m_path):
                if self.seed:
                    self.new_dir = f"{self.dir}10000"
                    path = f"{self.new_dir}/{name}"
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
                                t_path = dirpath.replace(self.dir, self.new_dir)
                            else:
                                t_path = dirpath
                            if self.compress:
                                pswd = self.extract
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
                                except Exception:
                                    return
            else:
                if self.seed and self.is_leech:
                    self.new_dir = f"{self.dir}10000"
                    path = path.replace(self.dir, self.new_dir)
                pswd = self.extract
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
                        except Exception:
                            return
                else:
                    LOGGER.error("Unable to extract archive! Uploading anyway")
                    self.new_dir = ""
                    path = m_path
        except NotSupportedExtractionArchive:
            LOGGER.info("Not any valid archive, uploading file as it is.")
            self.new_dir = ""
            path = m_path

        return path

    async def proceed_compress(self, path, gid):
        """Compress files using 7z."""
        from bot.helper.ext_utils.files_utils import get_path_size, clean_target

        m_path = path
        name = ospath.basename(path)
        size = await get_path_size(m_path)
        pswd = self.compress

        if self.seed and self.is_leech:
            self.new_dir = f"{self.dir}10000"
            path = f"{self.new_dir}/{name}.zip"
        else:
            path = f"{m_path}.zip"

        async with status_dict_lock:
            status_dict[self.uid] = ZipStatus(name, size, gid, self)

        LEECH_SPLIT_SIZE = config_dict["LEECH_SPLIT_SIZE"]
        if pswd:
            if self.is_leech and int(size) > LEECH_SPLIT_SIZE:
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
        elif self.is_leech and int(size) > LEECH_SPLIT_SIZE:
            cmd = ["7z", f"-v{LEECH_SPLIT_SIZE}b", "a", "-mx=0", path, m_path]
        else:
            cmd = ["7z", "a", "-mx=0", path, m_path]

        self.suproc = await create_subprocess_exec(*cmd)
        await self.suproc.wait()
        if self.suproc.returncode == -9:
            return None
        elif not self.seed:
            await clean_target(m_path)

        return path

    async def proceed_split(self, path, gid):
        """Split large files for leech uploads."""
        from bot.helper.ext_utils.files_utils import get_path_size, split_file

        up_dir, up_name = path.rsplit("/", 1)
        size = await get_path_size(up_dir)

        user_dict = user_data.get(self.user_id, {})
        LEECH_SPLIT_SIZE = user_dict.get("split_size", False) or config_dict[
            "LEECH_SPLIT_SIZE"
        ]

        for dirpath, _, files in walk(up_dir, topdown=False):
            for file_ in files:
                f_path = ospath.join(dirpath, file_)
                f_size = ospath.getsize(f_path)
                if f_size > LEECH_SPLIT_SIZE:
                    async with status_dict_lock:
                        status_dict[self.uid] = SplitStatus(up_name, f_size, gid, self)
                    LOGGER.info(f"Splitting: {up_name}")
                    res = await split_file(
                        f_path, f_size, file_, dirpath, LEECH_SPLIT_SIZE, self
                    )
                    if not res:
                        return False
                    if res == "errored":
                        from bot import TG_MAX_SPLIT_SIZE

                        if f_size <= TG_MAX_SPLIT_SIZE:
                            continue
                        else:
                            try:
                                osremove(f_path)
                            except Exception:
                                return False
                    elif not self.seed or self.new_dir:
                        try:
                            osremove(f_path)
                        except Exception:
                            return False

        return True
