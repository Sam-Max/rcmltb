from math import ceil
from os import makedirs, mkdir, path as ospath, remove as osremove
from shutil import rmtree
from bot.helper.ext_utils.zip_utils import get_path_size
from magic import Magic
from bot import config_dict, DOWNLOAD_DIR, LOGGER, TG_MAX_FILE_SIZE, aria2, get_client, status_dict, status_dict_lock
from json import loads as jsnloads
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from subprocess import Popen, check_output
from subprocess import check_output

ARCH_EXT = [".tar.bz2", ".tar.gz", ".bz2", ".gz", ".tar.xz", ".tar", ".tbz2", ".tgz", ".lzma2",
                ".zip", ".7z", ".z", ".rar", ".iso", ".wim", ".cab", ".apm", ".arj", ".chm",
                ".cpio", ".cramfs", ".deb", ".dmg", ".fat", ".hfs", ".lzh", ".lzma", ".mbr",
                ".msi", ".mslz", ".nsis", ".ntfs", ".rpm", ".squashfs", ".udf", ".vhd", ".xar"]

ZIP_EXT = (".zip", ".7z", ".gzip2", ".iso", ".wim", ".rar")

def clean_download(path):
    LOGGER.info(f"Cleaning Download")
    if ospath.isdir(path):
        try:
            rmtree(path)
        except:
            pass
    elif ospath.isfile(path):
        try:
            osremove(path)
        except:
            pass

def clean_target(path: str):
    if ospath.exists(path):
        LOGGER.info(f"Cleaning Target")
        if ospath.isdir(path):
            try:
                rmtree(path)
            except:
                pass
        elif ospath.isfile(path):
            try:
                osremove(path)
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

def start_cleanup():
    if not config_dict['LOCAL_MIRROR']:
        try:
            rmtree(DOWNLOAD_DIR)
        except:
            pass
        try:
            makedirs(DOWNLOAD_DIR)  
        except:
            pass

def get_readable_size(size):
    """Get size in readable format"""

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i]) 

def split_file(path, size, file_, dirpath, split_size, listener, start_time=0, i=1, inLoop=False, noMap=False):
    dirpath = f"{dirpath}/splited_files"
    if not ospath.exists(dirpath):
        mkdir(dirpath)
    parts = ceil(size/config_dict['LEECH_SPLIT_SIZE'])
    if config_dict['EQUAL_SPLITS'] and not inLoop:
        split_size = ceil(size/parts) + 1000
    if get_media_streams(path)[0]:
        duration = get_media_info(path)[0]
        base_name, extension = ospath.splitext(file_)
        split_size = split_size - 5000000
        while i <= parts or start_time < duration - 4:
            parted_name = "{}.part{}{}".format(str(base_name), str(i).zfill(3), str(extension))
            out_path = ospath.join(dirpath, parted_name)
            if not noMap:
                listener.suproc = Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(start_time),
                                         "-i", path, "-fs", str(split_size), "-map", "0", "-map_chapters", "-1",
                                         "-async", "1", "-strict", "-2", "-c", "copy", out_path])
            else:
                listener.suproc = Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(start_time),
                                          "-i", path, "-fs", str(split_size), "-map_chapters", "-1", "-async", "1",
                                          "-strict", "-2","-c", "copy", out_path])
            listener.suproc.wait()
            if listener.suproc.returncode == -9:
                return False
            elif listener.suproc.returncode != 0 and not noMap:
                LOGGER.warning(f"Retrying without map, -map 0 not working in all situations. Path: {path}")
                try:
                    osremove(out_path)
                except:
                    pass
                return split_file(path, size, file_, dirpath, split_size, listener, start_time, i, True, True)
            elif listener.suproc.returncode != 0:
                LOGGER.warning(f"Unable to split this video, if it's size less than {TG_MAX_FILE_SIZE} will be uploaded as it is. Path: {path}")
                try:
                    osremove(out_path)
                except:
                    pass
                return "errored"
            out_size = get_path_size(out_path)
            if out_size > TG_MAX_FILE_SIZE:
                dif = out_size - TG_MAX_FILE_SIZE
                split_size = split_size - dif + 5000000
                osremove(out_path)
                return split_file(path, size, file_, dirpath, split_size, listener, start_time, i, True, noMap)
            lpd = get_media_info(out_path)[0]
            if lpd == 0:
                LOGGER.error(f'Something went wrong while splitting, mostly file is corrupted. Path: {path}')
                break
            elif duration == lpd:
                if not noMap:
                    LOGGER.warning(f"Retrying without map. -map 0 not working in all situations. Path: {path}")
                    try:
                        osremove(out_path)
                    except:
                        pass
                    return split_file(path, size, file_, dirpath, split_size, listener, start_time, i, True, True)
                else:
                    LOGGER.warning(f"This file has been splitted with default stream and audio, so you will only see one part with less size from orginal one because it doesn't have all streams and audios. This happens mostly with MKV videos. noMap={noMap}. Path: {path}")
                    break
            elif lpd <= 3:
                osremove(out_path)
                break
            start_time += lpd - 3
            i = i + 1
    else:
        out_path = ospath.join(dirpath, file_ + ".")
        listener.suproc = Popen(["split", "--numeric-suffixes=1", "--suffix-length=3",
                                f"--bytes={split_size}", path, out_path])
        listener.suproc.wait()
        if listener.suproc.returncode == -9:
            return False
    return True

def get_media_streams(path):
    is_video = False
    is_audio = False

    mime_type = get_mime_type(path)
    if mime_type.startswith('audio'):
        is_audio = True
        return is_video, is_audio

    if path.endswith('.bin') or not mime_type.startswith('video') and not mime_type.endswith('octet-stream'):
        return is_video, is_audio

    try:
        result = check_output(["ffprobe", "-hide_banner", "-loglevel", "error", "-print_format",
                               "json", "-show_streams", path]).decode('utf-8')
    except Exception as e:
        if not mime_type.endswith('octet-stream'):
            LOGGER.error(f'{e}. Mostly file not found!')
        return is_video, is_audio

    fields = eval(result).get('streams')
    if fields is None:
        LOGGER.error(f"get_media_streams: {result}")
        return is_video, is_audio

    for stream in fields:
        if stream.get('codec_type') == 'video':
            is_video = True
        elif stream.get('codec_type') == 'audio':
            is_audio = True

    return is_video, is_audio

def get_mime_type(file_path):
    mime = Magic(mime=True)
    mime_type = mime.from_file(file_path)
    mime_type = mime_type or "text/plain"
    return mime_type

def get_media_info(path):
    try:
        result = check_output(["ffprobe", "-hide_banner", "-loglevel", "error", "-print_format",
                                            "json", "-show_format", path]).decode('utf-8')
        fields = eval(result)['format']
    except Exception as e:
        LOGGER.error(f"get_media_info: {e}")
        return 0, None, None
    try:
        duration = round(float(fields['duration']))
    except:
        duration = 0
    try:
        artist = str(fields['tags']['artist'])
    except:
        artist = None
    try:
        title = str(fields['tags']['title'])
    except:
        title = None
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

def bt_selection_buttons(id_: str):
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

def getDownloadByGid(gid):
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

class ButtonMaker:
    def __init__(self):
        self.first_button = []
        self.__header_button = []
        self.__footer_button = []
        self.__footer_second_button = []
        self.__footer_third_button = []

    def url_buildbutton(self, key, link):
        self.first_button.append(InlineKeyboardButton(text = key, url = link))

    def cb_buildbutton(self, key, data, position= None):
        if not position:
            self.first_button.append(InlineKeyboardButton(text = key, callback_data = data))
        elif position == 'header':
            self.__header_button.append(InlineKeyboardButton(text = key, callback_data = data))
        elif position == 'footer':
            self.__footer_button.append(InlineKeyboardButton(text = key, callback_data = data))
        elif position == 'footer_second':
            self.__footer_second_button.append(InlineKeyboardButton(text = key, callback_data = data))  
        elif position == 'footer_third':
            self.__footer_third_button.append(InlineKeyboardButton(text = key, callback_data = data))  

    def build_menu(self, n_cols):
        menu = [self.first_button[i: i + n_cols] for i in range(0, len(self.first_button), n_cols)]
        if self.__header_button:
            menu.insert(0, self.__header_button)
        if self.__footer_button:
            if len(self.__footer_button) > 8:
                [menu.append(self.__footer_button[i:i + 8]) for i in range(0, len(self.__footer_button), 8)]
            else:
                menu.append(self.__footer_button)
        if self.__footer_second_button:
            menu.append(self.__footer_second_button)
        if self.__footer_third_button:
            menu.append(self.__footer_third_button)
        return InlineKeyboardMarkup(menu)




