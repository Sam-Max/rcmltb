#https://github.com/yash-dk/TorToolkit-Telegram/blob/master/tortoolkit/functions/zip7_utils.py

import asyncio, shlex, os, time
from typing import Union,List,Tuple
from bot import DOWNLOAD_DIR, LOGGER, TG_SPLIT_SIZE
from subprocess import Popen

async def cli_call(cmd: Union[str,List[str]]) -> Tuple[str,str]:
    if isinstance(cmd,str):
        cmd = shlex.split(cmd)
    elif isinstance(cmd,(list,tuple)):
        pass
    else:
        return None,None

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stderr=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    
    stdout = stdout.decode().strip()
    stderr = stderr.decode().strip()
    
    return stdout, stderr, process.returncode

async def split_in_zip(path, size=None):
    if os.path.exists(path):
        if os.path.isfile(path):
            LOGGER.info("Starting the split for {}".format(path))
            fname = os.path.basename(path)
            bdir = os.path.dirname(path)
            bdir = os.path.join(bdir, str(time.time()).replace(".",""))
            if not os.path.exists(bdir):
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

async def extract_archive(path, password=""):
    if os.path.exists(path):
        if os.path.isfile(path):
            valid_exts = (".zip", ".7z", ".tar", ".gzip2", ".iso", ".wim", ".rar", ".tar.gz",".tar.bz2")
            
            if str(path).endswith(valid_exts):
                time_s= str(time.time()).replace(".","") 
                userpath = f'{DOWNLOAD_DIR}{time_s}'
                if not os.path.exists(userpath):
                    os.mkdir(userpath)
                    
                extpath = os.path.join(userpath, os.path.basename(path))
                for i in valid_exts:
                    li = extpath.rsplit(i, maxsplit=1)
                    extpath = "".join(li)

                if not os.path.exists(extpath):
                    os.mkdir(extpath)
                    
                if str(path).endswith(("tar","tar.gz","tar.bz2")):
                    cmd = f'tar -xvf "{path}" -C "{extpath}" --warning=none'
                else:
                    cmd = f'7z x -y "{path}" "-o{extpath}" "-p{password}"'
                
                out, err, _ = await cli_call(cmd)
                
                if err:
                    if "Wrong password" in err:
                        msg= "Wrong Password"
                    else:
                        LOGGER.error(err)
                        LOGGER.error(out)
                    return False, msg
                else:
                    return extpath, ""
        else:
            msg= "Wrong file extension, can't extract"
            return False, msg
    else:
        msg= "Fatal Error"
        return False, msg

def get_path_size(path: str):
    if os.path.isfile(path):
        return os.path.getsize(path)
    total_size = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            abs_path = os.path.join(root, f)
            total_size += os.path.getsize(abs_path)
    return total_size