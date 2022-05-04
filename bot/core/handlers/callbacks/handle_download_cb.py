import asyncio
from bot.core.get_vars import get_val
from pyrogram import filters
from bot.downloaders.telegram_download import down_load_media_pyro


async def handle_download_cb(client, query):
        list = query.data.split(" ")
        message= query.message
        tag = f"@{message.reply_to_message.from_user.username}"
        media= get_val("MEDIA")

        if "default" in list[1]:
            await down_load_media_pyro(client, message, media, tag)

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
                        await down_load_media_pyro(client, message, media, tag, response.text, True)
            finally:
                await question.delete()