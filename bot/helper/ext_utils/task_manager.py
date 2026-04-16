from asyncio import Event, Lock

from bot import (
    queued_dl,
    queued_up,
    non_queued_dl,
    non_queued_up,
    queue_dict_lock,
    LOGGER,
    config_dict,
)
from bot.core.config_manager import Config


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
    async with queue_dict_lock:
        if state == "dl":
            if all_limit and len(non_queued_dl) + len(non_queued_up) >= all_limit:
                event = Event()
                queued_dl[listener.uid] = event
                is_over_limit = True
            elif dl_limit and len(non_queued_dl) >= dl_limit:
                event = Event()
                queued_dl[listener.uid] = event
                is_over_limit = True
            else:
                non_queued_dl.add(listener.uid)
        elif state == "up":
            if all_limit and len(non_queued_dl) + len(non_queued_up) >= all_limit:
                event = Event()
                queued_up[listener.uid] = event
                is_over_limit = True
            elif up_limit and len(non_queued_up) >= up_limit:
                event = Event()
                queued_up[listener.uid] = event
                is_over_limit = True
            else:
                non_queued_up.add(listener.uid)

    return is_over_limit, event


async def start_from_queued():
    """Start queued tasks when slots become available."""
    async with queue_dict_lock:
        all_limit = getattr(Config, "QUEUE_ALL", 0) or 0
        dl_limit = getattr(Config, "QUEUE_DOWNLOAD", 0) or 0
        up_limit = getattr(Config, "QUEUE_UPLOAD", 0) or 0

        if queued_dl and (
            (all_limit and len(non_queued_dl) + len(non_queued_up) < all_limit)
            or (dl_limit and len(non_queued_dl) < dl_limit)
            or (not all_limit and not dl_limit)
        ):
            for uid, event in list(queued_dl.items()):
                if all_limit and len(non_queued_dl) + len(non_queued_up) >= all_limit:
                    break
                if dl_limit and len(non_queued_dl) >= dl_limit:
                    break
                non_queued_dl.add(uid)
                del queued_dl[uid]
                event.set()
                break

        if queued_up and (
            (all_limit and len(non_queued_dl) + len(non_queued_up) < all_limit)
            or (up_limit and len(non_queued_up) < up_limit)
            or (not all_limit and not up_limit)
        ):
            for uid, event in list(queued_up.items()):
                if all_limit and len(non_queued_dl) + len(non_queued_up) >= all_limit:
                    break
                if up_limit and len(non_queued_up) >= up_limit:
                    break
                non_queued_up.add(uid)
                del queued_up[uid]
                event.set()
                break


async def stop_duplicate_check(listener):
    """Check if file already exists in destination."""
    # Placeholder for duplicate check logic
    pass
