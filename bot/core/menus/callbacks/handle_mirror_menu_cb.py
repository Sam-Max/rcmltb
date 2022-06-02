import asyncio
from bot.core.get_vars import get_val
from bot.downloaders.mirror_download import handle_mirror_download
from pyrogram import filters

async def handle_mirror_menu_callback(client, query):
        list = query.data.split("_")
        message= query.message
        tag = f"@{message.reply_to_message.from_user.username}"
        
        file= get_val("FILE")
        isZip = get_val("IS_ZIP")
        extract = get_val("EXTRACT")
        pswd = get_val("PSWD") 

        if "default" in list[1]:
            await handle_mirror_download(client, message, file, tag, pswd, isZip=isZip, extract=extract)

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
                        await handle_mirror_download(client, message, file, tag, pswd, isZip=isZip, extract=extract, new_name=response.text, is_rename=True)
            finally:
                await question.delete()