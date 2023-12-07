from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.rclone_data_holder import update_rclone_data


class Menus:
    LEECH = "leechmenu"
    COPY = "copymenu"
    MYFILES = "myfilesmenu"
    STORAGE = "storagemenu"
    CLEANUP = "cleanupmenu"
    SYNC = "syncmenu"
    REMOTE_SELECT = "remoteselectmenu"
    MIRROR_SELECT = "mirrorselectmenu"


def rcloneListNextPage(info, offset=0, max_results=10):
    start = offset
    end = max_results + start
    total = len(info)
    next_offset = offset + max_results

    if end > total:
        next_page = info[start:]
    elif start >= total:
        next_page = []
    else:
        next_page = info[start:end]

    return next_page, next_offset


def rcloneListButtonMaker(
    info, button, menu_type, dir_callback, file_callback, user_id
):
    for index, dir in enumerate(info):
        path = dir["Path"]
        update_rclone_data(str(index), path, user_id)

        if dir["MimeType"] == "inode/directory":
            button.cb_buildbutton(
                f"📁{path}", data=f"{menu_type}^{dir_callback}^{index}^{user_id}")
        else:
            size = get_readable_file_size(dir["Size"])
            button.cb_buildbutton(
                f"[{size}] {path}",
                data=f"{menu_type}^{file_callback}^{index}^True^{user_id}",
            )
