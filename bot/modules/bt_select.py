from pyrogram.handlers import CallbackQueryHandler
from pyrogram import filters
from os import remove as osremove, path as ospath
from bot import bot, aria2, LOGGER
from bot.helper.ext_utils.bot_utils import run_sync
from bot.helper.telegram_helper.message_utils import sendStatusMessage
from bot.helper.ext_utils.misc_utils import getDownloadByGid


async def get_confirm(client, query):
    user_id = query.from_user.id
    data = query.data.split()
    message = query.message
    dl = await getDownloadByGid(data[2])
    if dl is None:
        await query.answer("This task has been cancelled!", show_alert=True)
        await message.delete()
        return
    if hasattr(dl, "listener"):
        listener = dl.listener()
    else:
        await query.answer(
            "Not in download state anymore! Keep this message to resume the seed if seed enabled!",
            show_alert=True,
        )
        return
    if user_id != listener.message.from_user.id:
        await query.answer("This task is not for you!", show_alert=True)
    elif data[1] == "pin":
        await query.answer(data[3], show_alert=True)
    elif data[1] == "done":
        await query.answer()
        id_ = data[3]
        if len(id_) > 20:
            client = dl.client()
            tor_info = (await run_sync(client.torrents_info, torrent_hash=id_))[0]
            path = tor_info.content_path.rsplit("/", 1)[0]
            res = await run_sync(client.torrents_files, torrent_hash=id_)
            for f in res:
                if f.priority == 0:
                    f_paths = [f"{path}/{f.name}", f"{path}/{f.name}.!qB"]
                    for f_path in f_paths:
                        if ospath.exists(f_path):
                            try:
                                osremove(f_path)
                            except:
                                pass
            await run_sync(client.torrents_resume, torrent_hashes=id_)
        else:
            res = await run_sync(aria2.client.get_files, id_)
            for f in res:
                if f["selected"] == "false" and ospath.exists(f["path"]):
                    try:
                        osremove(f["path"])
                    except:
                        pass
            try:
                await run_sync(aria2.client.unpause, id_)
            except Exception as e:
                LOGGER.error(
                    f"{e} Error in resume, this mostly happens after abuse aria2. Try to use select cmd again!"
                )
        await sendStatusMessage(message)
        await message.delete()
    elif data[1] == "rm":
        await query.answer()
        obj = dl.download()
        await obj.cancel_download()
        await message.delete()


confirm_handler = CallbackQueryHandler(get_confirm, filters=filters.regex("btsel"))
bot.add_handler(confirm_handler)
