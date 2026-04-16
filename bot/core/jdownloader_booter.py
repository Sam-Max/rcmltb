"""JDownloader booter module for handling JDownloader connection and management."""

from asyncio import sleep
from os import path as ospath

from bot import LOGGER, bot_loop
from bot.core.config_manager import Config
from bot.helper.ext_utils.bot_utils import new_task

try:
    from myjd import MyJdApi
    from myjd.exception import (
        MYJDApiException,
        MYJDConnectionException,
        MYJDDecodeException,
    )
    MYJD_AVAILABLE = True
except ImportError:
    MYJD_AVAILABLE = False
    MyJdApi = None
    MYJDApiException = Exception
    MYJDConnectionException = Exception
    MYJDDecodeException = Exception


class JDownloader:
    """Extended MyJdApi class with boot and connection management."""

    def __init__(self):
        if MYJD_AVAILABLE and MyJdApi:
            self._api = MyJdApi()
        else:
            self._api = None
        self._is_connected = False
        self._boot_attempted = False

    @property
    def is_connected(self):
        """Check if JDownloader is connected."""
        return self._is_connected

    async def boot(self):
        """Boot JDownloader and establish connection.

        Writes config files and starts JDownloader.jar if email/password are provided.
        """
        if self._boot_attempted:
            return
        self._boot_attempted = True

        if not MYJD_AVAILABLE:
            LOGGER.warning("myjd package not installed, JDownloader support disabled")
            return

        jd_email = getattr(Config, "JD_EMAIL", "")
        jd_password = getattr(Config, "JD_PASSWORD", "")

        if not jd_email or not jd_password:
            LOGGER.info("JDownloader credentials not set, skipping boot")
            return

        try:
            # Check if JDownloader directory exists
            jd_dir = "/JDownloader"
            if not ospath.exists(jd_dir):
                LOGGER.warning(f"JDownloader directory not found: {jd_dir}")
                return

            # Write myJDownloader settings
            jd_settings = f"""{{"devicename": "rcmltb", "autoconnectenabledv2": true, "email": "{jd_email}", "password": "{jd_password}", "storage": "{jd_dir}/cfg"}}"""

            settings_path = f"{jd_dir}/cfg/org.jdownloader.api.myjdownloader.MyJDownloaderSettings.json"
            if ospath.exists(jd_dir):
                from aiofiles import open as aiopen
                from aiofiles.os import makedirs

                await makedirs(f"{jd_dir}/cfg", exist_ok=True)
                async with aiopen(settings_path, "w") as f:
                    await f.write(jd_settings)

            # Start JDownloader.jar in background
            LOGGER.info("Starting JDownloader...")
            from asyncio import create_subprocess_exec
            from asyncio.subprocess import DEVNULL

            proc = await create_subprocess_exec(
                "java",
                "-jar",
                f"{jd_dir}/JDownloader.jar",
                cwd=jd_dir,
                stdout=DEVNULL,
                stderr=DEVNULL,
            )

            # Wait for JDownloader to start
            await sleep(30)

            # Try to connect
            await self.connect()

        except Exception as e:
            LOGGER.error(f"Error booting JDownloader: {e}")

    async def connect(self):
        """Connect to JDownloader using email/password."""
        if not self._api:
            return False

        jd_email = getattr(Config, "JD_EMAIL", "")
        jd_password = getattr(Config, "JD_PASSWORD", "")

        if not jd_email or not jd_password:
            return False

        try:
            self._is_connected = False
            await self._api.connect_api(jd_email, jd_password)
            self._is_connected = True
            LOGGER.info("JDownloader connected successfully")
            return True
        except MYJDConnectionException as e:
            LOGGER.error(f"JDownloader connection failed: {e}")
        except MYJDApiException as e:
            LOGGER.error(f"JDownloader API error: {e}")
        except Exception as e:
            LOGGER.error(f"JDownloader connect error: {e}")
        return False

    async def reconnect(self):
        """Reconnect to JDownloader."""
        if not self._api:
            return False
        try:
            await self._api.reconnect_api()
            self._is_connected = True
            return True
        except Exception as e:
            LOGGER.error(f"JDownloader reconnect error: {e}")
            self._is_connected = False
            return False

    async def disconnect(self):
        """Disconnect from JDownloader."""
        if not self._api:
            return
        try:
            await self._api.disconnect_api()
        except Exception:
            pass
        self._is_connected = False

    @property
    def device(self):
        """Access the JDownloader device API."""
        if self._api:
            return self._api.device
        return None


# Global JDownloader instance
jdownloader = JDownloader()


@new_task
async def jdownloader_boot():
    """Boot JDownloader in background."""
    await jdownloader.boot()
