import shlex, os, time
from os import path as ospath
from asyncio.subprocess import PIPE, create_subprocess_exec
from typing import Union,List,Tuple
from bot import LOGGER
from re import I, split as re_split
from bot.helper.ext_utils.exceptions import NotSupportedExtractionArchive

ARCH_EXT = [".tar.bz2", ".tar.gz", ".bz2", ".gz", ".tar.xz", ".tar", ".tbz2", ".tgz", ".lzma2",
            ".zip", ".7z", ".z", ".rar", ".iso", ".wim", ".cab", ".apm", ".arj", ".chm",
            ".cpio", ".cramfs", ".deb", ".dmg", ".fat", ".hfs", ".lzh", ".lzma", ".mbr",
            ".msi", ".mslz", ".nsis", ".ntfs", ".rpm", ".squashfs", ".udf", ".vhd", ".xar"]


#https://github.com/yash-dk/TorToolkit-Telegram/blob/master/tortoolkit/functions/  -- zip7_utils.py

async def cli_call(cmd: Union[str,List[str]]) -> Tuple[str,str]:
    if isinstance(cmd,str):
        cmd = shlex.split(cmd)
    elif isinstance(cmd,(list,tuple)):
        pass
    else:
        return None,None

    process = await create_subprocess_exec(*cmd,
        stderr=PIPE,
        stdout=PIPE)

    stdout, stderr = await process.communicate()
    
    stdout = stdout.decode().strip()
    stderr = stderr.decode().strip()
    
    return stdout, stderr, process.returncode

async def split_in_zip(path, size=None):
    if ospath.exists(path):
        if os.path.isfile(path):
            LOGGER.info("Starting the split for {}".format(path))
            fname = ospath.basename(path)
            bdir = ospath.dirname(path)
            bdir = ospath.join(bdir, str(time.time()).replace(".",""))
            if not ospath.exists(bdir):
                os.mkdir(bdir)

            if size is None:
                size = 1900
            else:
                size = int(size)
                size = int(size/(1024*1024))
            cmd = f'7z a -tzip -mx=0 "{bdir}/{fname}.zip" "{path}" -v{size}m '

            _, err, _ = await cli_call(cmd)
            
            if err:
                LOGGER.error(f"Error in zip split {err}")
                return None
            else:
                return bdir
        else:
            return None
    else:
        return None

#https://github.com/anasty17/mirror-leech-telegram-bot/ -- fs_utils.py 

def get_base_name(orig_path: str):
    extension = next(
        (ext for ext in ARCH_EXT if orig_path.lower().endswith(ext)), ''
    )
    if extension != '':
        return re_split(f'{extension}$', orig_path, maxsplit=1, flags=I)[0]
    else:
        raise NotSupportedExtractionArchive('File format not supported for extraction')
    
def get_path_size(path: str):
    if os.path.isfile(path):
        return os.path.getsize(path)
    total_size = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            abs_path = os.path.join(root, f)
            total_size += os.path.getsize(abs_path)
    return total_size