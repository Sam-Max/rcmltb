from bot.helper.ext_utils.bot_utils import MirrorStatus


class QueueStatus:
    def __init__(self, listener, gid, status):
        self.__listener = listener
        self.__gid = gid
        self.__status = status
        self.message = listener.message

    def gid(self):
        return self.__gid

    def name(self):
        if self.__status == "dl":
            return f"Waiting for download: {self.__listener.name}"
        return f"Waiting for upload: {self.__listener.name}"

    def size(self):
        return ""

    def progress(self):
        return ""

    def speed(self):
        return ""

    def eta(self):
        return ""

    def status(self):
        if self.__status == "dl":
            return MirrorStatus.STATUS_QUEUEDL
        return MirrorStatus.STATUS_QUEUEUP

    def processed_bytes(self):
        return ""

    def processed_raw(self):
        return 0

    def task(self):
        return self

    async def cancel_task(self):
        await self.__listener.onDownloadError("Task cancelled from queue!")