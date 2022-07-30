from asyncio import sleep
from random import randrange
from bot import Bot
from bot.utils.status_utils.pyrogram_progress import progress_for_pyrogram

class TelegramStatus:
     def __init__(self, user_message):
        self.id = self.__create_id(8)
        self._user_message = user_message
        self.cancelled = False

     def __create_id(self, count):
        map = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        id = ''
        i = 0
        while i < count:
            rnd = randrange(len(map))
            id += map[rnd]
            i += 1
        return id

     async def progress(self, current, total, name, status, current_time):
        if self.cancelled:
               await sleep(1.5)  
               await self._user_message.edit('Process cancelled!.')
               Bot.stop_transmission()
        await progress_for_pyrogram(current, total, name, status, self._user_message, self.id, current_time) 
             

