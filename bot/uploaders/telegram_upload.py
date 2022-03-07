#Adapted from:
#Github.com/Vasusen-code

import logging
import os
import time
from bot.downloaders.progress_for_pyrogram import progress_for_pyrogram
from bot.utils.g_vid_res import get_video_resolution
from bot.utils.screenshot import screenshot
from ethon.pyfunc import video_metadata

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)


async def upload_media_pyro(client, message, sender, file):
        LOGGER.info("Uploading...")
        c_time = time.time()
        try:
            if str(file).split(".")[-1] in ['mkv', 'mp4', 'webm']:
                    if str(file).split(".")[-1] in ['webm', 'mkv']:
                        path = str(file).split(".")[0] + ".mp4"
                        os.rename(file, path) 
                        file = str(file).split(".")[0] + ".mp4"
                        caption= str(file).split("/")[-1]   
                    data = video_metadata(file)
                    duration = data["duration"]
                    thumb_path = await screenshot(file, duration, sender)
                    width, height = get_video_resolution(thumb_path)
                    await client.send_video(
                        chat_id=sender,
                        video=file,
                        width=width,
                        height=height,
                        caption= f'`{caption}`',
                        parse_mode= "md" ,
                        thumb= thumb_path,
                        supports_streaming=True,
                        duration= duration,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            '**Uploading:**',
                            message,
                            c_time
                        )
                    )
            # elif str(file).split(".")[-1] in ['jpg', 'jpeg', 'png', 'webp']:
            #         await edit.edit("Uploading photo.")
            #         await bot.send_file(sender, file, caption=caption)  
            # elif str(file).split(".")[-1] in ['docx', 'doc', 'png', 'webp']:
            #         await edit.edit("Uploading document.")
            #         await bot.send_file(sender, file, caption=caption)        
            else:
                await client.send_document(
                    chat_id= sender,
                    document= file, 
                    progress=progress_for_pyrogram,
                    progress_args=(
                        '**Uploading:**',
                        message,
                        c_time
                    )
                )
            await message.delete()    
        except Exception as e:
            LOGGER.info(e)
            await client.send_message(sender, f'Failed to save')
            return