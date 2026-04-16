"""JDownloader status utility."""

from bot import LOGGER
from bot.core.jdownloader_booter import jdownloader
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


class JDownloaderStatus:
    """Status class for JDownloader downloads."""

    def __init__(self, listener, gid):
        self._listener = listener
        self._gid = gid
        self._info = {}

    async def _update_info(self):
        """Update download info from JDownloader."""
        device = jdownloader.get_device()
        if not jdownloader.is_connected or not device:
            return
        try:
            packages = await device.linkgrabber.query_packages()
            for package in packages:
                if package.get("uuid") == self._gid:
                    self._info = package
                    break
        except Exception as e:
            LOGGER.error(f"Error updating JDownloader info: {e}")

    def gid(self):
        """Return download GID."""
        return self._gid

    def name(self):
        """Return download name."""
        return self._info.get("name", "Unknown")

    def progress(self):
        """Return download progress percentage."""
        bytes_loaded = self._info.get("bytesLoaded", 0)
        bytes_total = self._info.get("bytesTotal", 0)
        if bytes_total == 0:
            return "0%"
        return f"{round(bytes_loaded / bytes_total * 100, 2)}%"

    def speed(self):
        """Return download speed."""
        speed = self._info.get("speed", 0)
        from bot.helper.ext_utils.human_format import human_readable_bytes
        return f"{human_readable_bytes(speed)}/s"

    def eta(self):
        """Return estimated time of arrival."""
        bytes_loaded = self._info.get("bytesLoaded", 0)
        bytes_total = self._info.get("bytesTotal", 0)
        speed = self._info.get("speed", 0)
        if speed == 0:
            return "-"
        eta_seconds = (bytes_total - bytes_loaded) / speed
        from bot.helper.ext_utils.bot_utils import get_readable_time
        return get_readable_time(eta_seconds)

    def status(self):
        """Return download status."""
        return MirrorStatus.STATUS_DOWNLOADING

    def type(self):
        """Return task type."""
        from bot.helper.mirror_leech_utils.status_utils.status_utils import TaskType
        return TaskType.TELEGRAM

    def processed_bytes(self):
        """Return processed bytes."""
        from bot.helper.ext_utils.human_format import human_readable_bytes
        return human_readable_bytes(self._info.get("bytesLoaded", 0))

    def size(self):
        """Return total size."""
        from bot.helper.ext_utils.human_format import human_readable_bytes
        return human_readable_bytes(self._info.get("bytesTotal", 0))

    async def cancel_task(self):
        """Cancel the download task."""
        device = jdownloader.get_device()
        if jdownloader.is_connected and device:
            try:
                await device.linkgrabber.remove_links(
                    package_ids=[self._gid]
                )
            except Exception as e:
                LOGGER.error(f"Error canceling JDownloader task: {e}")
        await self._listener.onDownloadError("Download cancelled by user")
