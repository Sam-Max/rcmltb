from asyncio import Event

from bot import (
    queued_dl,
    queued_up,
    non_queued_dl,
    non_queued_up,
    queue_dict_lock,
    LOGGER,
)
from bot.core.config_manager import Config
from bot.helper.ext_utils.links_utils import is_gdrive_id
from bot.helper.ext_utils.bot_utils import run_sync_to_async


async def stop_duplicate_check(listener):
    """Check if file already exists in GDrive destination."""
    if (
        listener.isLeech
        or not getattr(listener, "stop_duplicate", False)
        or listener.sameDir
        or listener.select
        or not is_gdrive_id(getattr(listener, "up_dest", ""))
    ):
        return False, None

    name = listener.name
    LOGGER.info(f"Checking File/Folder if already in Drive: {name}")

    if listener.compress:
        name = f"{name}.zip"
    elif listener.extract:
        try:
            from bot.helper.ext_utils.files_utils import get_base_name

            name = get_base_name(name)
        except Exception:
            name = None

    if name is not None:
        from bot.helper.mirror_leech_utils.gd_utils.helper import GoogleDriveHelper

        gd = GoogleDriveHelper()
        gd.use_sa = False
        dest_id = listener.up_dest
        if dest_id.startswith("sa:"):
            gd.use_sa = True
            dest_id = dest_id.replace("sa:", "", 1)
        elif dest_id.startswith("tp:"):
            dest_id = dest_id.replace("tp:", "", 1)
        try:
            escaped_name = gd.escapes(name)
            gd.service = gd.authorize()
            query = f"'{dest_id}' in parents and name = '{escaped_name}' and trashed = false"
            response = (
                gd.service.files()
                .list(
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                    q=query,
                    spaces="drive",
                    pageSize=5,
                    fields="files(id, name)",
                )
                .execute()
            )
            if response.get("files"):
                msg = f"File/Folder already exists in Drive:\n<code>{name}</code>"
                return msg, None
        except Exception as e:
            LOGGER.error(f"stop_duplicate_check error: {e}")

    return False, None


async def check_running_tasks(listener, state="dl"):
    """Check if task limits are exceeded and queue if needed.

    Args:
        listener: The task listener
        state: "dl" for download, "up" for upload

    Returns:
        tuple: (is_over_limit, event or None)
    """
    all_limit = getattr(Config, "QUEUE_ALL", 0) or 0
    dl_limit = getattr(Config, "QUEUE_DOWNLOAD", 0) or 0
    up_limit = getattr(Config, "QUEUE_UPLOAD", 0) or 0

    event = None
    is_over_limit = False
    force_run = getattr(listener, "force_run", False)
    force_upload = getattr(listener, "force_upload", False)
    force_download = getattr(listener, "force_download", False)

    async with queue_dict_lock:
        if state == "up" and listener.uid in non_queued_dl:
            non_queued_dl.discard(listener.uid)

        state_limit = dl_limit if state == "dl" else up_limit
        if (
            (all_limit or state_limit)
            and not force_run
            and not (force_upload and state == "up")
            and not (force_download and state == "dl")
        ):
            dl_count = len(non_queued_dl)
            up_count = len(non_queued_up)
            t_count = dl_count if state == "dl" else up_count
            is_over_limit = (
                all_limit
                and dl_count + up_count >= all_limit
                and (not state_limit or t_count >= state_limit)
            ) or (state_limit and t_count >= state_limit)
            if is_over_limit:
                event = Event()
                if state == "dl":
                    queued_dl[listener.uid] = event
                else:
                    queued_up[listener.uid] = event

        if not is_over_limit:
            if state == "up":
                non_queued_up.add(listener.uid)
            else:
                non_queued_dl.add(listener.uid)

    return is_over_limit, event


async def start_dl_from_queued(mid):
    """Start a specific queued download task by message ID."""
    if mid in queued_dl:
        queued_dl[mid].set()
        del queued_dl[mid]
        non_queued_dl.add(mid)


async def start_up_from_queued(mid):
    """Start a specific queued upload task by message ID."""
    if mid in queued_up:
        queued_up[mid].set()
        del queued_up[mid]
        non_queued_up.add(mid)


async def start_from_queued():
    """Start queued tasks when slots become available."""
    all_limit = getattr(Config, "QUEUE_ALL", 0) or 0
    dl_limit = getattr(Config, "QUEUE_DOWNLOAD", 0) or 0
    up_limit = getattr(Config, "QUEUE_UPLOAD", 0) or 0

    if all_limit:
        async with queue_dict_lock:
            dl = len(non_queued_dl)
            up = len(non_queued_up)
            all_ = dl + up
            if all_ < all_limit:
                f_tasks = all_limit - all_
                if queued_up and (not up_limit or up < up_limit):
                    for index, mid in enumerate(list(queued_up.keys()), start=1):
                        await start_up_from_queued(mid)
                        f_tasks -= 1
                        if f_tasks == 0 or (up_limit and index >= up_limit - up):
                            break
                if queued_dl and (not dl_limit or dl < dl_limit) and f_tasks != 0:
                    for index, mid in enumerate(list(queued_dl.keys()), start=1):
                        await start_dl_from_queued(mid)
                        if (dl_limit and index >= dl_limit - dl) or index == f_tasks:
                            break
        return

    if up_limit:
        async with queue_dict_lock:
            up = len(non_queued_up)
            if queued_up and up < up_limit:
                f_tasks = up_limit - up
                for index, mid in enumerate(list(queued_up.keys()), start=1):
                    await start_up_from_queued(mid)
                    if index == f_tasks:
                        break
    else:
        async with queue_dict_lock:
            if queued_up:
                for mid in list(queued_up.keys()):
                    await start_up_from_queued(mid)

    if dl_limit:
        async with queue_dict_lock:
            dl = len(non_queued_dl)
            if queued_dl and dl < dl_limit:
                f_tasks = dl_limit - dl
                for index, mid in enumerate(list(queued_dl.keys()), start=1):
                    await start_dl_from_queued(mid)
                    if index == f_tasks:
                        break
    else:
        async with queue_dict_lock:
            if queued_dl:
                for mid in list(queued_dl.keys()):
                    await start_dl_from_queued(mid)
