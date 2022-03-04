#Adapted from:
#Github.com/Vasusen-code

import logging
import os
import time
from bot.downloaders.progress_for_pyrogram import progress_for_pyrogram
from bot.utils.screenshot import screenshot
from ethon.pyfunc import video_metadata

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)


async def upload_media_pyro(client, message, sender, file):
        LOGGER.info("Leeching...")
        c_time = time.time()
        try:
            if str(file).split(".")[-1] in ['mkv', 'mp4', 'webm']:
                    if str(file).split(".")[-1] in ['webm', 'mkv']:
                        path = str(file).split(".")[0] + ".mp4"
                        os.rename(file, path) 
                        file = str(file).split(".")[0] + ".mp4"
                    data = video_metadata(file)
                    duration = data["duration"]
                    thumb_path = await screenshot(file, duration, sender)
                    await client.send_video(
                        chat_id=sender,
                        video=file,
                        caption= str(file),
                        thumb= thumb_path,
                        supports_streaming=True,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            '**Uploading:**\n',
                            message,
                            c_time
                        )
                    )
            else:
                await client.send_document(
                    chat_id= sender,
                    document= str(file), 
                    progress=progress_for_pyrogram,
                    progress_args=(
                        '**Uploading:**\n',
                        message,
                        c_time
                    )
                )
            await message.delete()           
        except Exception as e:
            LOGGER.info(e)
            await client.send_message(sender, f'Failed to save')
            return 
