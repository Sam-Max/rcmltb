"""JDownloader download helper."""

from base64 import b64encode
from asyncio import sleep
from os import path as ospath

from bot import LOGGER, status_dict, status_dict_lock
from bot.core.jdownloader_booter import jdownloader
from bot.helper.telegram_helper.message_utils import sendMessage, sendStatusMessage
from bot.helper.mirror_leech_utils.status_utils.jdownloader_status import (
    JDownloaderStatus,
)


async def add_jd_download(link, name, path, listener):
    """Add a download to JDownloader.

    Args:
        link: URL to download (HTTP link or DLC file path)
        name: Custom name for the download
        path: Download path
        listener: TaskListener instance
    """
    if not jdownloader.is_connected or not jdownloader.device:
        await sendMessage("JDownloader not connected. Please check configuration.", listener.message)
        return

    try:
        # Handle DLC files
        if link.endswith(".dlc") or "/dlc/" in link:
            if ospath.exists(link):
                # Read and encode DLC file
                with open(link, "rb") as f:
                    dlc_content = b64encode(f.read()).decode()
                await jdownloader.device.linkgrabber.add_container(
                    "DLC", f"data:;base64,{dlc_content}"
                )
            else:
                await sendMessage("DLC file not found.", listener.message)
                return
        else:
            # Add direct link
            await jdownloader.device.linkgrabber.add_links([
                {
                    "url": link,
                    "packageName": name or "",
                    "downloadFolder": path,
                }
            ])

        LOGGER.info(f"Added JDownloader link: {link}")
        
        # Wait for package to be added
        await sleep(5)
        
        # Query packages to get the new package ID
        packages = await jdownloader.device.linkgrabber.query_packages()
        if not packages:
            await sendMessage("Failed to add link to JDownloader.", listener.message)
            return
        
        # Get the most recent package
        package = packages[-1]
        gid = package.get("uuid")
        
        # Create status object
        async with status_dict_lock:
            status_dict[listener.uid] = JDownloaderStatus(listener, gid)
        
        await listener.onDownloadStart()
        await sendStatusMessage(listener.message)
        
        # Start downloading
        await jdownloader.device.downloads.start_downloads(package_ids=[gid])
        
    except Exception as e:
        LOGGER.error(f"Error adding JDownloader download: {e}")
        await sendMessage(f"Error: {str(e)}", listener.message)


async def handle_dlc_file(file_path, listener, path):
    """Handle DLC container file.

    Args:
        file_path: Path to DLC file
        listener: TaskListener instance
        path: Download path
    """
    if not jdownloader.is_connected or not jdownloader.device:
        await sendMessage("JDownloader not connected.", listener.message)
        return
    
    try:
        with open(file_path, "rb") as f:
            dlc_content = b64encode(f.read()).decode()
        
        await jdownloader.device.linkgrabber.add_container(
            "DLC", f"data:;base64,{dlc_content}"
        )
        
        LOGGER.info(f"Added DLC file: {file_path}")
        
        await sleep(5)
        
        packages = await jdownloader.device.linkgrabber.query_packages()
        if not packages:
            await sendMessage("Failed to add DLC file.", listener.message)
            return
        
        package = packages[-1]
        gid = package.get("uuid")
        
        async with status_dict_lock:
            status_dict[listener.uid] = JDownloaderStatus(listener, gid)
        
        await listener.onDownloadStart()
        await sendStatusMessage(listener.message)
        
        await jdownloader.device.downloads.start_downloads(package_ids=[gid])
        
    except Exception as e:
        LOGGER.error(f"Error handling DLC file: {e}")
        await sendMessage(f"Error: {str(e)}", listener.message)
