import asyncio
import json
import logging
import re


async def get_glink(drive_name, drive_base, ent_name, conf_path, isdir=True):
        ent_name = re.escape(ent_name)

        if isdir:
            get_id_cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only",
                            "-f", f"+ {ent_name}/", "-f", "- *"]
        else:
            get_id_cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--files-only",
                            "-f", f"+ {ent_name}", "-f", "- *"]

        process = await asyncio.create_subprocess_exec(
            *get_id_cmd,
            stdout=asyncio.subprocess.PIPE
        )

        stdout, _ = await process.communicate()
        stdout = stdout.decode().strip()

        try:
            data = json.loads(stdout)
            id = data[0]["ID"]
            name = data[0]["Name"]
            return (id, name)
        except Exception:
            logging.exception("Error Occured while getting id ::- {}".format(stdout))