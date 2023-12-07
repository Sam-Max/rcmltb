from asyncio import sleep
from re import findall
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


class RcloneStatus:
    def __init__(self, obj, listener, gid):
        self.__obj = obj
        self.__gid = gid
        self.__percent = 0
        self.__speed = 0
        self.__transfered_bytes = 0
        self.__blank = 0
        self.__eta = "-"
        self.message = listener.message
        self.is_rclone = True

    async def start(self):
        while True:
            data = (await self.__obj.process.stdout.readline()).decode()
            if match := findall("Transferred:.*ETA.*", data):
                self.info = match[0].replace("Transferred:", "").strip().split(",")
                self.__transfered_bytes = self.info[0]
                try:
                    self.__percent = int(self.info[1].strip("% "))
                except:
                    pass
                self.__speed = self.info[2]
                self.__eta = self.info[3].replace("ETA", "")
                self.__blank = 0
            if not match:
                self.__blank += 1
                if self.__blank == 15:
                    break
            await sleep(0)

    def gid(self):
        return self.__gid

    def processed_bytes(self):
        return self.__transfered_bytes

    def size(self):
        return get_readable_file_size(self.__obj.size)

    def status(self):
        if self.__obj.status_type == MirrorStatus.STATUS_UPLOADING:
            return MirrorStatus.STATUS_UPLOADING
        elif self.__obj.status_type == MirrorStatus.STATUS_COPYING:
            return MirrorStatus.STATUS_COPYING
        else:
            return MirrorStatus.STATUS_DOWNLOADING

    def name(self):
        return self.__obj.name

    def progress(self):
        return self.__percent

    def speed(self):
        return f"{self.__speed}"

    def eta(self):
        return self.__eta

    def download(self):
        return self.__obj

    def type(self):
        return "Rclone"
