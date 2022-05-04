#Adapted from:
#Github.com/Vasusen-code

import logging
import os
import time
from bot.downloaders.progress_for_pyrogram import progress_for_pyrogram
from bot.utils.g_vid_res import get_video_resolution
from bot.utils.get_media_info import get_m_info
from bot.utils.screenshot import screenshot
from pyrogram import enums

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
                        parse_mode= enums.ParseMode.MARKDOWN ,
                        thumb= thumb_path,
                        supports_streaming=True,
                        duration= duration,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            "Name: `{}`".format(caption),
                            '**Uploading:**',
                            message,
                            c_time
                        )
                    )
            else:
                caption= str(file).split("/")[-1]  
                await client.send_document(
                    chat_id= sender,
                    document= file, 
                    caption= f'`{caption}`',
                    parse_mode= enums.ParseMode.MARKDOWN,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        "Name: `{}`".format(caption),
                        '**Uploading:**',
                        message,
                        c_time
                    )
                )
            await message.delete()    
        except Exception as e:
            log.info(e)
            await message.delete() 
            file_name= str(file).split("/")[-1]
            await client.send_message(sender, f"Failed to save: {file_name} - cause: {e}")  
            return