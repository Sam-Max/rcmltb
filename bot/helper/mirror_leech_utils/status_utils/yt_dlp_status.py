from bot.helper.ext_utils.bot_utils import (
    MirrorStatus,
    get_readable_file_size,
    get_readable_time,
)


class YtDlpDownloadStatus:
    def __init__(self, obj, listener, gid):
        self.__obj = obj
        self.__listener = listener
        self.__gid = gid
        self.message = listener.message

    def gid(self):
        return self.__gid

    def processed_bytes(self):
        return get_readable_file_size(self.processed_raw())

    def processed_raw(self):
        return self.__obj.downloaded_bytes or 0

    def size(self):
        return get_readable_file_size(self.__obj.size)

    def status(self):
        return MirrorStatus.STATUS_DOWNLOADING

    def name(self):
        return self.__obj.name or self.__listener.name or "Unknown"

    def progress(self):
        return f"{round(self.__obj.progress, 2)}%"

    def speed(self):
        return f"{get_readable_file_size(self.__obj.download_speed)}/s"

    def eta(self):
        if self.__obj.eta != "-":
            return get_readable_time(self.__obj.eta)
        speed = self.__obj.download_speed
        remaining = self.__obj.size - self.processed_raw()
        if speed > 0 and remaining > 0:
            return get_readable_time(remaining / speed)
        return "-"

    def task(self):
        return self.__obj

    def type(self):
        return "Ytdl"
