#Adapted from:
#Github.com/Vasusen-code

import logging
import os
import time
from bot.downloaders.progress_for_pyrogram import progress_for_pyrogram
from bot.utils.g_vid_res import get_video_resolution
from bot.utils.get_media_info import get_m_info
from bot.utils.screenshot import screenshot

log= logging.getLogger(__name__)

VIDEO_SUFFIXES = ["mkv", "mp4", "mov", "wmv", "3gp", "mpg", "webm", "avi", "flv", "m4v", "gif"]

async def upload_media_pyro(client, message, sender, file):
        log.info("Uploading...")
        c_time = time.time()
        try:
            if str(file).split(".")[-1] in VIDEO_SUFFIXES:
                    if not str(file).split(".")[-1] in ['mp4', 'mkv']:
                        path = str(file).split(".")[0] + ".mp4"
                        os.rename(file, path) 
                        file = str(file).split(".")[0] + ".mp4"
                    caption= str(file).split("/")[-1]  
                    duration= get_m_info(file)[0]
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
            else:
                caption= str(file).split("/")[-1]  
                await client.send_document(
                    chat_id= sender,
                    document= file, 
                    caption= f'`{caption}`',
                    parse_mode= "md",
                    progress=progress_for_pyrogram,
                    progress_args=(
                        '**Uploading:**',
                        message,
                        c_time
                    )
                )
            await message.delete()    
        except Exception as e:
            log.info(e)
            await client.send_message(sender, f"Failed to save: {file} - cause: {e}")
            return