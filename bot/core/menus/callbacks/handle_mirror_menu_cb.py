import asyncio
from bot.core.get_vars import get_val
from bot.downloaders.telegram_download import down_load_media_pyro
from pyrogram import filters

async def handle_mirror_menu_callback(client, query):
        list = query.data.split("_")
        message= query.message
        tag = f"@{message.reply_to_message.from_user.username}"
        media= get_val("MEDIA")
        isZip = get_val("IS_ZIP")
        extract = get_val("EXTRACT")
        pswd = get_val("PSWD") 

        if "default" in list[1]:
            await down_load_media_pyro(client, message, media, tag, pswd, isZip, extract)

        if "rename" in list[1]: 
            question= await client.send_message(message.chat.id, text= "Send the new name /ignore to cancel")
            try:
                response = await client.listen.Message(filters.text, id= tag, timeout = 30)
            except asyncio.TimeoutError:
                await question.reply("Cannot wait more longer for your response!")
            else:
                if response:
                    if "/ignore" in response.text:
                        await question.reply("Okay cancelled question!")
                        await client.listen.Cancel(tag)
                    else:
                        await down_load_media_pyro(client, message, media, tag, pswd, isZip, extract, response.text, True)
            finally:
                await question.delete()