from pyrogram.handlers import CallbackQueryHandler
from pyrogram import filters
from os import remove, path as ospath
from bot import bot, aria2, LOGGER
from bot.helper.ext_utils.bot_utils import run_sync
from bot.helper.ext_utils.message_utils import sendStatusMessage
from bot.helper.ext_utils.misc_utils import getDownloadByGid



async def get_confirm(client, callback_query):
    query = callback_query
    user_id = query.from_user.id
    data = query.data
    data = data.split()
    dl = await getDownloadByGid(data[2])
    if not dl:
        await query.answer(text="This task has been cancelled!", show_alert=True)
        await query.message.delete()
        return
    if hasattr(dl, 'listener'):
        listener = dl.listener()
    else:
        await query.answer(text="Not in download state anymore! Keep this message to resume the seed if seed enabled!", show_alert=True)
        return
    if user_id != listener.message.from_user.id:
        await query.answer(text="This task is not for you!", show_alert=True)
    elif data[1] == "pin":
        await query.answer(text=data[3], show_alert=True)
    elif data[1] == "done":
        await query.answer()
        id_ = data[3]
        if len(id_) > 20:
            client = dl.client()
            tor_info = (await run_sync(client.torrents_info, torrent_hash=id_))[0]
            path = tor_info.content_path.rsplit('/', 1)[0]
            res = await run_sync(client.torrents_files, torrent_hash=id_)
            for f in res:
                if f.priority == 0:
                    f_paths = [f"{path}/{f.name}", f"{path}/{f.name}.!qB"]
                    for f_path in f_paths:
                       if ospath.exists(f_path):
                           try:
                               remove(f_path)
                           except:
                               pass
            await run_sync(client.torrents_resume, torrent_hashes=id_)
        else:
            res = await run_sync(aria2.client.get_files, id_)
            for f in res:
                if f['selected'] == 'false' and ospath.exists(f['path']):
                    try:
                        remove(f['path'])
                    except:
                        pass
            try:
                await run_sync(aria2.client.unpause, id_)
            except Exception as e:
                LOGGER.error(f"{e} Error in resume, this mostly happens after abuse aria2. Try to use select cmd again!")
        await sendStatusMessage(listener.message)


confirm_handler = CallbackQueryHandler(get_confirm, filters= filters.regex("btsel"))
bot.add_handler(confirm_handler)
