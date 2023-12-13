from random import SystemRandom
from string import ascii_letters, digits
from os import makedirs
from threading import Event
from mega import MegaApi, MegaListener, MegaRequest, MegaTransfer, MegaError
from bot import LOGGER, config_dict, status_dict, status_dict_lock
from bot.helper.telegram_helper.message_utils import sendMessage, sendStatusMessage
from bot.helper.mirror_leech_utils.status_utils.mega_status import MegaDownloadStatus
from bot.helper.ext_utils.bot_utils import (
    get_mega_link_type,
    run_async_to_sync,
    run_sync_to_async,
)


class MegaAppListener(MegaListener):
    _NO_EVENT_ON = (MegaRequest.TYPE_LOGIN, MegaRequest.TYPE_FETCH_NODES)
    NO_ERROR = "no error"

    def __init__(self, continue_event: Event, listener):
        self.continue_event = continue_event
        self.node = None
        self.public_node = None
        self.listener = listener
        self.__bytes_transferred = 0
        self.is_cancelled = False
        self.completed = False
        self.isFile = False
        self.__speed = 0
        self.__name = ""
        self.error = None
        super().__init__()

    @property
    def speed(self):
        return self.__speed

    @property
    def downloaded_bytes(self):
        return self.__bytes_transferred

    def onRequestFinish(self, api, request, error):
        if str(error).lower() != "no error":
            self.error = error.copy()
            LOGGER.error(f"Mega onRequestFinishError: {self.error}")
            self.continue_event.set()
            return
        request_type = request.getType()
        if request_type == MegaRequest.TYPE_LOGIN:
            api.fetchNodes()
        elif request_type == MegaRequest.TYPE_GET_PUBLIC_NODE:
            self.public_node = request.getPublicMegaNode()
            self.__name = self.public_node.getName()
        elif request_type == MegaRequest.TYPE_FETCH_NODES:
            LOGGER.info("Fetching Root Node.")
            self.node = api.getRootNode()
            self.__name = self.node.getName()
            LOGGER.info(f"Node Name: {self.node.getName()}")
        if (
            request_type not in self._NO_EVENT_ON
            or self.node
            and "cloud drive" not in self.__name.lower()
        ):
            self.continue_event.set()

    def onRequestTemporaryError(self, api, request, error: MegaError):
        LOGGER.error(f"Mega Request error in {error}")
        if not self.is_cancelled:
            self.is_cancelled = True
            run_async_to_sync(
                self.listener.onDownloadError, f"RequestTempError: {error.toString()}"
            )
        self.error = error.toString()
        self.continue_event.set()

    def onTransferUpdate(self, api: MegaApi, transfer: MegaTransfer):
        if self.is_cancelled:
            api.cancelTransfer(transfer, None)
            self.continue_event.set()
            return
        self.__speed = transfer.getSpeed()
        self.__bytes_transferred = transfer.getTransferredBytes()

    def onTransferFinish(self, api: MegaApi, transfer: MegaTransfer, error):
        try:
            if self.is_cancelled:
                self.continue_event.set()
            elif transfer.isFinished() and (transfer.isFolderTransfer() or self.isFile):
                self.completed = True
                self.continue_event.set()
        except Exception as e:
            LOGGER.error(e)

    def onTransferTemporaryError(self, api, transfer, error):
        filen = transfer.getFileName()
        state = transfer.getState()
        errStr = error.toString()
        LOGGER.error(f"Mega download error in file {transfer} {filen}: {error}")
        if state in [1, 4]:
            # Sometimes MEGA (offical client) can't stream a node either and raises a temp failed error.
            # Don't break the transfer queue if transfer's in queued (1) or retrying (4) state [causes seg fault]
            return

        self.error = errStr
        if not self.is_cancelled:
            self.is_cancelled = True
            run_async_to_sync(
                self.listener.onDownloadError, f"TransferTempError: {errStr} ({filen})"
            )
            self.continue_event.set()

    async def cancel_task(self):
        self.is_cancelled = True
        await self.listener.onDownloadError("Download Canceled by user")


class AsyncExecutor:
    def __init__(self):
        self.continue_event = Event()

    def do(self, function, args):
        self.continue_event.clear()
        function(*args)
        self.continue_event.wait()


async def add_mega_download(mega_link, path: str, listener, name: str):
    MEGA_EMAIL = config_dict["MEGA_EMAIL"]
    MEGA_PASSWORD = config_dict["MEGA_PASSWORD"]

    api = MegaApi(None, None, None, "rcmltb")
    executor = AsyncExecutor()
    folder_api = None

    mega_listener = MegaAppListener(executor.continue_event, listener)
    api.addListener(mega_listener)

    if MEGA_EMAIL and MEGA_PASSWORD:
        await run_sync_to_async(executor.do, api.login, (MEGA_EMAIL, MEGA_PASSWORD))

    if get_mega_link_type(mega_link) == "file":
        await run_sync_to_async(executor.do, api.getPublicNode, (mega_link,))
        node = mega_listener.public_node
        mega_listener.isFile = True
    else:
        folder_api = MegaApi(None, None, None, "rcmltb")
        folder_api.addListener(mega_listener)
        await run_sync_to_async(executor.do, folder_api.loginToFolder, (mega_link,))
        node = await run_sync_to_async(folder_api.authorizeNode, mega_listener.node)
    if mega_listener.error is not None:
        await sendMessage(str(mega_listener.error), listener.message)
        await run_sync_to_async(executor.do, api.logout, ())
        if folder_api is not None:
            await run_sync_to_async(executor.do, folder_api.logout, ())
        return

    gid = "".join(SystemRandom().choices(ascii_letters + digits, k=8))
    name = name or node.getName()
    size = api.getSize(node)

    async with status_dict_lock:
        status_dict[listener.uid] = MegaDownloadStatus(
            name, size, gid, mega_listener, listener
        )

    await sendStatusMessage(listener.message)

    if not config_dict["NO_TASKS_LOGS"]:
        LOGGER.info(f"Download from Mega: {name}")

    makedirs(path, exist_ok=True)
    await run_sync_to_async(
        executor.do, api.startDownload, (node, path, name, None, False, None)
    )
    await run_sync_to_async(executor.do, api.logout, ())
    if folder_api is not None:
        await run_sync_to_async(executor.do, folder_api.logout, ())

    if mega_listener.completed:
        await listener.onDownloadComplete()
    elif (error := mega_listener.error) and mega_listener.is_cancelled:
        await listener.onDownloadError(error)
