from asyncio import create_subprocess_exec
from shutil import rmtree
from sys import exit 
from bot.helper.ext_utils.bot_utils import cmd_exec, run_sync
from bot.helper.ext_utils.button_build import ButtonMaker
from bot.helper.ext_utils.zip_utils import get_path_size
from aioshutil import rmtree as aiormtree
from aiofiles.os import remove as aioremove, path as aiopath, mkdir
from os import path as ospath
from re import search as re_search
from bot import config_dict, DOWNLOAD_DIR, LOGGER, TG_MAX_FILE_SIZE, aria2, get_client, status_dict, status_dict_lock
from json import loads as jsnloads
from magic import Magic
from math import ceil
from subprocess import check_output

ARCH_EXT = [".tar.bz2", ".tar.gz", ".bz2", ".gz", ".tar.xz", ".tar", ".tbz2", ".tgz", ".lzma2",
                ".zip", ".7z", ".z", ".rar", ".iso", ".wim", ".cab", ".apm", ".arj", ".chm",
                ".cpio", ".cramfs", ".deb", ".dmg", ".fat", ".hfs", ".lzh", ".lzma", ".mbr",
                ".msi", ".mslz", ".nsis", ".ntfs", ".rpm", ".squashfs", ".udf", ".vhd", ".xar"]

ZIP_EXT = (".zip", ".7z", ".gzip2", ".iso", ".wim", ".rar")



async def clean_download(path):
    LOGGER.info(f"Cleaning Download")
    if await aiopath.isdir(path):
        try:
            await aiormtree(path)
        except:
            pass
    elif await aiopath.isfile(path):
        try:
            await aioremove(path)
        except:
            pass

async def clean_target(path: str):
    if await aiopath.exists(path):
        LOGGER.info(f"Cleaning Target")
        if await aiopath.isdir(path):
            try:
                 await aiormtree(path)
            except:
                pass
        elif await aiopath.isfile(path):
            try:
                await aioremove(path)
            except:
                pass

def clean_all():
    aria2.remove_all(True)
    get_client().torrents_delete(torrent_hashes="all")
    if not config_dict['LOCAL_MIRROR']:
        try:
            rmtree(DOWNLOAD_DIR)
        except:
            pass

async def start_cleanup():
    get_client().torrents_delete(torrent_hashes="all")

def exit_clean_up(signal, frame):
    try:
        LOGGER.info("Please wait, while we clean up the downloads and stop running downloads")
        clean_all()
        exit(0)
    except KeyboardInterrupt:
        LOGGER.warning("Force Exiting before the cleanup finishes!")
        exit(1)

def get_readable_size(size):
    """Get size in readable format"""

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i]) 

async def split_file(path, size, file_, dirpath, split_size, listener, start_time=0, i=1, inLoop=False, noMap=False):
    dirpath = f"{dirpath}/splited_files"
    if not await aiopath.exists(dirpath):
        await mkdir(dirpath)
    parts = ceil(size/config_dict['LEECH_SPLIT_SIZE'])
    if config_dict['EQUAL_SPLITS'] and not inLoop:
        split_size = ceil(size/parts) + 1000
    if (await get_document_type(path))[0]:
        duration = (await get_media_info(path))[0]
        base_name, extension = ospath.splitext(file_)
        split_size = split_size - 5000000
        while i <= parts or start_time < duration - 4:
            parted_name = "{}.part{}{}".format(str(base_name), str(i).zfill(3), str(extension))
            out_path = ospath.join(dirpath, parted_name)
            if not noMap:
                cmd= ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(start_time),
                                         "-i", path, "-fs", str(split_size), "-map", "0", "-map_chapters", "-1",
                                         "-async", "1", "-strict", "-2", "-c", "copy", out_path]
                listener.suproc = await create_subprocess_exec(*cmd)
            else:
                cmd= ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(start_time),
                                          "-i", path, "-fs", str(split_size), "-map_chapters", "-1", "-async", "1",
                                          "-strict", "-2","-c", "copy", out_path]
                listener.suproc = await create_subprocess_exec(*cmd)
            await listener.suproc.wait()
            if listener.suproc.returncode == -9:
                return False
            elif listener.suproc.returncode != 0 and not noMap:
                LOGGER.warning(f"Retrying without map, -map 0 not working in all situations. Path: {path}")
                try:
                    await aioremove(out_path)
                except:
                    pass
                return await split_file(path, size, file_, dirpath, split_size, listener, start_time, i, True, True)
            elif listener.suproc.returncode != 0:
                LOGGER.warning(f"Unable to split this video, if it's size less than {TG_MAX_FILE_SIZE} will be uploaded as it is. Path: {path}")
                try:
                    await aioremove(out_path)
                except:
                    pass
                return "errored"
            out_size = get_path_size(out_path)
            if out_size > TG_MAX_FILE_SIZE:
                dif = out_size - TG_MAX_FILE_SIZE
                split_size = split_size - dif + 5000000
                await aioremove(out_path)
                return await split_file(path, size, file_, dirpath, split_size, listener, start_time, i, True, noMap)
            lpd = (await get_media_info(out_path))[0]
            if lpd == 0:
                LOGGER.error(f'Something went wrong while splitting, mostly file is corrupted. Path: {path}')
                break
            elif duration == lpd:
                if not noMap:
                    LOGGER.warning(f"Retrying without map. -map 0 not working in all situations. Path: {path}")
                    try:
                        await aioremove(out_path)
                    except:
                        pass
                    return await split_file(path, size, file_, dirpath, split_size, listener, start_time, i, True, True)
                else:
                    LOGGER.warning(f"This file has been splitted with default stream and audio, so you will only see one part with less size from orginal one because it doesn't have all streams and audios. This happens mostly with MKV videos. noMap={noMap}. Path: {path}")
                    break
            elif lpd <= 3:
                await aioremove(out_path)
                break
            start_time += lpd - 3
            i = i + 1
    else:
        out_path = ospath.join(dirpath, file_ + ".")
        cmd= ["split", "--numeric-suffixes=1", "--suffix-length=3", f"--bytes={split_size}", path, out_path]
        listener.suproc = await create_subprocess_exec(*cmd)
        await listener.suproc.wait()
        if listener.suproc.returncode == -9:
            return False
    return True

async def get_document_type(path):
    is_video = False
    is_audio = False
    is_image = False
    if path.endswith(tuple(ARCH_EXT)) or re_search(r'.+(\.|_)(rar|7z|zip|bin)(\.0*\d+)?$', path):
        return is_video, is_audio, is_image
    mime_type = await run_sync(get_mime_type, path)
    if mime_type.startswith('audio'):
        is_audio = True
        return is_video, is_audio, is_image
    if mime_type.startswith('image'):
        is_image = True
        return is_video, is_audio, is_image
    if not mime_type.startswith('video') and not mime_type.endswith('octet-stream'):
        return is_video, is_audio, is_image
    try:
        result = await cmd_exec(["ffprobe", "-hide_banner", "-loglevel", "error", "-print_format",
                                 "json", "-show_streams", path])
        if res := result[1]:
            LOGGER.warning(f'Get Document Type: {res}')
    except Exception as e:
        LOGGER.error(f'Get Document Type: {e}. Mostly File not found!')
        return is_video, is_audio, is_image
    fields = eval(result[0]).get('streams')
    if fields is None:
        LOGGER.error(f"get_document_type: {result}")
        return is_video, is_audio, is_image
    for stream in fields:
        if stream.get('codec_type') == 'video':
            is_video = True
        elif stream.get('codec_type') == 'audio':
            is_audio = True
    return is_video, is_audio, is_image

def get_mime_type(file_path):
    mime = Magic(mime=True)
    mime_type = mime.from_file(file_path)
    mime_type = mime_type or "text/plain"
    return mime_type

async def get_media_info(path):
    try:
        result = await cmd_exec(["ffprobe", "-hide_banner", "-loglevel", "error", "-print_format", "json", "-show_format", "-show_streams", path])
        if res := result[1]:
            LOGGER.warning(f'Get Media Info: {res}')
    except Exception as e:
        LOGGER.error(f'Get Media Info: {e}. Mostly File not found!')
        return 0, None, None
    fields = eval(result[0]).get('format')
    if fields is None:
        LOGGER.error(f"get_media_info: {result}")
        return 0, None, None
    duration = round(float(fields.get('duration', 0)))
    if fields := fields.get('tags'):
        artist = fields.get('artist')
        if artist is None:
            artist = fields.get('ARTIST')
        title = fields.get('title')
        if title is None:
            title = fields.get('TITLE')
    else:
        title = None
        artist = None
    return duration, artist, title

def get_video_resolution(path):
    try:
        result = check_output(["ffprobe", "-hide_banner", "-loglevel", "error", "-select_streams", "v:0",
                                          "-show_entries", "stream=width,height", "-of", "json", path]).decode('utf-8')
        fields = jsnloads(result)['streams'][0]

        width = int(fields['width'])
        height = int(fields['height'])
        return width, height
    except Exception as e:
        LOGGER.error(f"get_video_resolution: {e}")
        return 480, 320

def bt_selection_buttons(id_):
    if len(id_) > 20:
        gid = id_[:12]
    else:
        gid = id_

    pincode = ""
    for n in id_:
        if n.isdigit():
            pincode += str(n)
        if len(pincode) == 4:
            break

    buttons = ButtonMaker()
    QB_BASE_URL = config_dict['QB_BASE_URL']
    if config_dict['WEB_PINCODE']:
        buttons.url_buildbutton("Select Files", f"{QB_BASE_URL}/app/files/{id_}")
        buttons.cb_buildbutton("Pincode", f"btsel pin {gid} {pincode}")
    else:
        buttons.url_buildbutton("Select Files", f"{QB_BASE_URL}/app/files/{id_}?pin_code={pincode}")
    buttons.cb_buildbutton("Done Selecting", f"btsel done {gid} {id_}")
    return buttons.build_menu(2)

async def getDownloadByGid(gid):
    async with status_dict_lock:
        for dl in list(status_dict.values()):
            if dl.gid() == gid:
                return dl
    return None

async def getAllDownload(req_status: str):
    async with status_dict_lock:
        for dl in list(status_dict.values()):
            status = dl.status()
            if req_status in ['all', status]:
                return dl
    return None



