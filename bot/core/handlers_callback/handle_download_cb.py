from bot.core.get_vars import get_val
from pyrogram import filters
from bot.downloaders.telegram_download import down_load_media_pyro


async def handle_download_cb(client, query):
        data= query.data
        list = data.split(" ")
        message= query.message

        message_type= get_val("MESSAGE_TYPE")

        if "default" in list[1]:
            await down_load_media_pyro(client, message, message_type)

        if "rename" in list[1]: 
            question= await message.reply(
                 text= "Envíe el nuevo nombre para el archivo /ignorar para cancelar", 
                 #reply_to_message_id= messageid, 
                 #reply_markup= ForceReply()
             )
            reply_message = await client.listen.Message(filters.text, id='1', timeout= 30)

            if "/ignorar" in reply_message.text:
                await question.delete()
                await message.delete()
                await client.listen.Cancel("1")
            else:
                await question.delete()
                await down_load_media_pyro(client, message, message_type, reply_message.text, True)
