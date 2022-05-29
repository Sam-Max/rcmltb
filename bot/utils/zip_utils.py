#https://github.com/yash-dk/TorToolkit-Telegram/blob/master/tortoolkit/functions/zip7_utils.py

import logging
import asyncio,shlex,os,logging,time
from typing import Union,List,Tuple

from bot import LOGGER

log= logging.getLogger(__name__)

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
            log.info("Starting the split for {}".format(path))
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
                log.error(f"Error in zip split {err}")
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
                userpath = os.path.join(os.getcwd(), "Downloads", "userdata")
                if not os.path.exists(userpath):
                    os.mkdir(userpath)

                extpath = os.path.join(userpath,os.path.basename(path))
                for i in valid_exts:
                    li = extpath.rsplit(i, 1)
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
                        LOGGER.error("Wrong Password")
                        return False
                    else:
                        LOGGER.error(err)
                        LOGGER.error(out)
                        return False
                else:
                    return extpath
        else:
            # False means that the stuff can be upload but cant be extracted as its a dir
            return False
    else:
        # None means fetal error and cant be ignored
        return None 