import subprocess
import logging

from bot.core.get_vars import get_val
from .progress_for_rclone import rclone_process_update_tele

log = logging.getLogger(__name__)

async def rclone_copy_transfer(e, conf_path):

    origin_drive = get_val("ORIGIN_DRIVE")
    origin_dir = get_val("ORIGIN_DIR")
    dest_drive = get_val("DEST_DRIVE")
    dest_dir = get_val("DEST_DIR")

    log.info(f'{origin_drive}:{origin_dir}-{dest_drive}:{dest_dir}')

    rclone_copy_cmd = ['rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{origin_dir}',
                       f'{dest_drive}:{dest_dir}', '-P']

    message = await e.edit("Preparing to copy...")

    rclone_pr = subprocess.Popen(
        rclone_copy_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    rcres = await rclone_process_update_tele(rclone_pr, message)

    if rcres:
        rclone_pr.kill()
        await message.edit("Copy cancelled")
        return

    await message.edit("Copied Successfully ✅")


