"""JDownloader listener for handling download events."""

from asyncio import sleep
from bot import LOGGER, status_dict, status_dict_lock
from bot.core.jdownloader_booter import jdownloader


class JDownloaderListener:
    """Listener for JDownloader download events."""

    def __init__(self, listener, gid):
        self._listener = listener
        self._gid = gid
        self._finished = False

    async def on_download_start(self):
        """Called when download starts."""
        LOGGER.info(f"JDownloader download started: {self._gid}")

    async def on_download_complete(self):
        """Called when download completes."""
        if self._finished:
            return
        self._finished = True
        
        LOGGER.info(f"JDownloader download complete: {self._gid}")
        
        async with status_dict_lock:
            if self._listener.uid in status_dict:
                del status_dict[self._listener.uid]
        
        await self._listener.onDownloadComplete()

    async def on_download_error(self, error):
        """Called when download errors."""
        if self._finished:
            return
        self._finished = True
        
        LOGGER.error(f"JDownloader download error: {error}")
        
        async with status_dict_lock:
            if self._listener.uid in status_dict:
                del status_dict[self._listener.uid]
        
        await self._listener.onDownloadError(str(error))


async def jdownloader_monitor(listener, gid):
    """Monitor JDownloader download progress.
    
    Args:
        listener: TaskListener instance
        gid: Package UUID
    """
    jd_listener = JDownloaderListener(listener, gid)
    await jd_listener.on_download_start()
    
    while not jd_listener._finished:
        try:
            if not jdownloader.is_connected:
                await sleep(5)
                continue
            
            # Query download status
            packages = await jdownloader.device.downloads.query_packages()
            package = None
            
            for pkg in packages:
                if pkg.get("uuid") == gid:
                    package = pkg
                    break
            
            if package:
                status = package.get("status")
                
                if status == "FINISHED":
                    await jd_listener.on_download_complete()
                    break
                elif status in ["FAILED", "SKIPPED"]:
                    await jd_listener.on_download_error(f"Download {status}")
                    break
            else:
                # Package not in downloads anymore, check if finished
                await sleep(2)
                packages = await jdownloader.device.downloads.query_packages()
                if not any(pkg.get("uuid") == gid for pkg in packages):
                    await jd_listener.on_download_complete()
                    break
            
            await sleep(3)
            
        except Exception as e:
            LOGGER.error(f"Error in JDownloader monitor: {e}")
            await sleep(5)
