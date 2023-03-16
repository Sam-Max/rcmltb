from random import SystemRandom
from string import ascii_letters, digits
from os import makedirs
from asyncio import Event
from mega import (MegaApi, MegaListener, MegaRequest, MegaTransfer, MegaError)
from bot import LOGGER, config_dict, status_dict, status_dict_lock
from bot.helper.ext_utils.message_utils import sendMessage, sendStatusMessage
from bot.helper.mirror_leech_utils.status_utils.mega_status import MegaDownloadStatus
from bot.helper.ext_utils.bot_utils import get_mega_link_type, run_async, run_sync



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
        self.__speed = 0
        self.__name = ''
        self.__size = 0
        self.error = None
        self.gid = ""
        super().__init__()

    @property
    def speed(self):
        """Returns speed of the download in bytes/second"""
        return self.__speed

    @property
    def name(self):
        """Returns name of the download"""
        return self.__name

    def setValues(self, name, size, gid):
        self.__name = name
        self.__size = size
        self.gid = gid

    @property
    def size(self):
        """Size of download in bytes"""
        return self.__size

    @property
    def downloaded_bytes(self):
        return self.__bytes_transferred

    def onRequestFinish(self, api, request, error):
        if str(error).lower() != "no error":
            self.error = error.copy()
            LOGGER.error(f'Mega onRequestFinishError: {self.error}')
            run_async(self.event_setter)
            return
        request_type = request.getType()
        if request_type == MegaRequest.TYPE_LOGIN:
            api.fetchNodes()
        elif request_type == MegaRequest.TYPE_GET_PUBLIC_NODE:
            self.public_node = request.getPublicMegaNode()
        elif request_type == MegaRequest.TYPE_FETCH_NODES:
            LOGGER.info("Fetching Root Node.")
            self.node = api.getRootNode()
            LOGGER.info(f"Node Name: {self.node.getName()}")
        if request_type not in self._NO_EVENT_ON or self.node and "cloud drive" not in self.node.getName().lower():
            run_async(self.event_setter)

    def onRequestTemporaryError(self, api, request, error: MegaError):
        LOGGER.error(f'Mega Request error in {error}')
        if not self.is_cancelled:
            self.is_cancelled = True
            run_async(self.listener.onDownloadError, f"RequestTempError: {error.toString()}")
        self.error = error.toString()
        run_async(self.event_setter)

    def onTransferUpdate(self, api: MegaApi, transfer: MegaTransfer):
        if self.is_cancelled:
            api.cancelTransfer(transfer, None)
            run_async(self.event_setter)
            return
        self.__speed = transfer.getSpeed()
        self.__bytes_transferred = transfer.getTransferredBytes()

    def onTransferFinish(self, api: MegaApi, transfer: MegaTransfer, error):
        try:
            if self.is_cancelled:
                run_async(self.event_setter)
                return
            elif transfer.isFinished() and (transfer.isFolderTransfer() or transfer.getFileName() == self.name):
                run_async(self.listener.onDownloadComplete)
                run_async(self.event_setter)
        except Exception as e:
            LOGGER.error(e)

    def onTransferTemporaryError(self, api, transfer, error):
        filen = transfer.getFileName()
        state = transfer.getState()
        errStr = error.toString()
        LOGGER.error(f'Mega download error in file {transfer} {filen}: {error}')
        if state in [1, 4]:
            # Sometimes MEGA (offical client) can't stream a node either and raises a temp failed error.
            # Don't break the transfer queue if transfer's in queued (1) or retrying (4) state [causes seg fault]
            return
        self.error = errStr
        if not self.is_cancelled:
            self.is_cancelled = True
            run_async(self.listener.onDownloadError, f"TransferTempError: {errStr} ({filen})")
            run_async(self.event_setter)

    async def event_setter(self):
        self.continue_event.set()

    async def cancel_download(self):
        self.is_cancelled = True
        await self.listener.onDownloadError("Download Canceled by user")

class AsyncExecutor:
    def __init__(self):
        self.continue_event = Event()

    async def do(self, function, args):
        self.continue_event.clear()
        await run_sync(function,*args)
        await self.continue_event.wait()
        
async def add_mega_download(mega_link: str, path: str, listener, name: str):
    MEGA_API_KEY = config_dict['MEGA_API_KEY']
    MEGA_EMAIL_ID = config_dict['MEGA_EMAIL_ID']
    MEGA_PASSWORD = config_dict['MEGA_PASSWORD']
    api = MegaApi(MEGA_API_KEY, None, None, 'rclone-mirror-telegram-bot')
    executor = AsyncExecutor()
    folder_api = None
    mega_listener = MegaAppListener(executor.continue_event, listener)
    await run_sync(api.addListener, mega_listener)
    if MEGA_EMAIL_ID and MEGA_PASSWORD:
        await executor.do(api.login, (MEGA_EMAIL_ID, MEGA_PASSWORD))
    if get_mega_link_type(mega_link) == "file":
        await executor.do(api.getPublicNode, (mega_link,))
        node = mega_listener.public_node
    else:
        folder_api = MegaApi(MEGA_API_KEY, None, None, 'rcmltb')
        await run_sync(folder_api.addListener, mega_listener)
        await executor.do(folder_api.loginToFolder, (mega_link,))
        node = await run_sync(folder_api.authorizeNode, mega_listener.node)
    if mega_listener.error is not None:
        await sendMessage(str(mega_listener.error), listener.message)
        await run_sync(api.removeListener, mega_listener)
        if folder_api is not None:
            await run_sync(folder_api.removeListener, mega_listener)
        return
    gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=8))
    mname = name or await run_sync(node.getName) 
    size = await run_sync(api.getSize, node)
    async with status_dict_lock:
        status_dict[listener.uid] = MegaDownloadStatus(mega_listener, listener)
    makedirs(path, exist_ok=True)
    mega_listener.setValues(mname, size, gid)
    await sendStatusMessage(listener.message)
    await executor.do(api.startDownload, (node, path, name, None, False, None))
    await run_sync(api.removeListener, mega_listener)
    if folder_api is not None:
        await run_sync(folder_api.removeListener, mega_listener)
        