
from os import listdir, remove, path as ospath
from bot import DOWNLOAD_DIR, aria2
from ....uploaders.rclone.rclone_mirror import RcloneMirror
from bot.utils.bot_utils.misc_utils import getDownloadByGid


async def get_confirm(update, callback_query):
    query = callback_query
    message= query.message
    data = query.data.split()
    tag= f"@{message.reply_to_message.from_user.username}"
    dl = await getDownloadByGid(data[2])
    if data[1] == "pin":
        await query.answer(text=data[3], show_alert=True)
    elif data[1] == "done":
        id_ = data[3]     
        await query.answer()
        if len(id_) > 20:
            client = dl.client()
            tor_info = client.torrents_info(torrent_hash=id_)[0]
            path = tor_info.content_path.rsplit('/', 1)[0]
            res = client.torrents_files(torrent_hash=id_)
            for f in res:
                if f.priority == 0:
                    f_paths = [f"{path}/{f.name}", f"{path}/{f.name}.!qB"]
                    for f_path in f_paths:
                       if ospath.exists(f_path):
                           try:
                               remove(f_path)
                           except:
                               pass
            client.torrents_resume(torrent_hashes=id_)
        else:
            res = aria2.client.get_files(id_)
            for f in res:
                if f['selected'] == 'false' and ospath.exists(f['path']):
                    try:
                        remove(f['path'])
                    except:
                        pass
            aria2.client.unpause(id_)
        status, rmsg = await dl.create_status()
        name= dl.name()
        path= f'{DOWNLOAD_DIR}{dl.id}'
        if status:
            if name == "None" or not ospath.exists(f'{path}/{name}'):
                name = listdir(path)[-1]
                path = f'{path}/{name}'
            else:
                path= f'{path}/{name}'     
            rclone_mirror = RcloneMirror(path, rmsg, tag)
            await rclone_mirror.mirror()
        else:
            await query.message.delete()    