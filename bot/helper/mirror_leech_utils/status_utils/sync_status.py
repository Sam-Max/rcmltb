from asyncio import sleep
from re import findall
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


class SyncStatus:
    def __init__(self, process, gid, source, destination):
        self.__source = source
        self.__destination= destination
        self.__process = process
        self.__gid = gid
        self.__percent= 0
        self.__speed= 0 
        self.__transfered_bytes = 0 
        self.__eta= "-"
        self.is_rclone= True

    async def read_stdout(self):
        blank= 0
        while True:
            data = await self.__process.stdout.readline()
            match = findall('Transferred:.*ETA.*', data.decode().strip())
            if len(match) > 0:
                nstr = match[0].replace('Transferred:', '')
                self.info = nstr.strip().split(',')
                self.__transfered_bytes = self.info[0]
                try:
                    self.__percent = int(self.info[1].strip('% '))
                except:
                    pass
                self.__speed = self.info[2]
                self.__eta = self.info[3].replace('ETA', '') 
            if len(match) == 0:
                blank += 1
                if blank == 15:
                    break
            else:
                blank = 0
            await sleep(0)
    
    def gid(self):
        return self.__gid

    def processed_bytes(self):
        return self.__transfered_bytes

    def status(self):
        return MirrorStatus.STATUS_SYNCING

    def name(self):
        return f'{self.__source} 🔄 {self.__destination}' 
    
    def size_raw(self):
        return 0

    def progress(self):
        return self.__percent

    def speed(self):
        return f'{self.__speed}'

    def eta(self):
        return self.__eta

    def download(self):
        return self.__process

    def type(self):
        return "RcloneSync"
        

