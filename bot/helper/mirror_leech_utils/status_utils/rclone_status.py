from asyncio import sleep
from bot import botloop
from re import findall
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


class RcloneStatus:
    def __init__(self, obj, gid):
        self.__obj = obj
        self.__gid = gid
        self.__percent= 0
        self.__speed= 0 
        self.__transfered_bytes = 0 
        self.__eta= "-"
        self.is_rclone= True
        botloop.create_task(self.read_stdout())
    
    async def read_stdout(self):
        blank = 0
        while True:
            if self.__obj.process is not None:
                data = await self.__obj.process.stdout.readline()
                data = data.decode().strip()
                mat = findall('Transferred:.*ETA.*', data)
                if len(mat) > 0:
                    nstr = mat[0].replace('Transferred:', '')
                    nstr = nstr.strip()
                    nstr = nstr.split(',')
                    percent = nstr[1].strip('% ')
                    try:
                        self.__percent = int(percent)
                    except:
                        pass
                    self.__transfered_bytes = nstr[0]
                    self.__speed = nstr[2]
                    self.__eta = nstr[3].replace('ETA', '')

                if data == '':
                    blank += 1
                    if blank == 20:
                        break
                else:
                    blank = 0
            await sleep(0.5)

    def gid(self):
        return self.__gid

    def processed_bytes(self):
        return self.__transfered_bytes

    def size_raw(self):
        return self.__obj.size

    def size(self):
        return get_readable_file_size(self.size_raw())

    def status(self):
        if self.__obj.status_type == MirrorStatus.STATUS_UPLOADING:
            return MirrorStatus.STATUS_UPLOADING
        elif self.__obj.status_type== MirrorStatus.STATUS_COPYING:
            return MirrorStatus.STATUS_COPYING
        else:
            return MirrorStatus.STATUS_DOWNLOADING

    def name(self):
        return self.__obj.name

    def progress(self):
        return self.__percent   

    def speed(self):
        return f'{self.__speed}'

    def eta(self):
        return self.__eta

    def download(self):
        return self.__obj
    
    def type(self):
        return "Rclone"
        

