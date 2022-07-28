import math
import time
from bot.utils.status_utils.bottom_status import get_bottom_status
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

FINISHED_PROGRESS_STR = "■"
UN_FINISHED_PROGRESS_STR = "□"


async def progress_for_pyrogram(
        current,
        total,
        file_name,
        ud_type,
        message,
        id, 
        start
):
    """ generic progress display for Telegram Upload / Download status """
    now = time.time()
    diff = now - start
    
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion
        elapsed_time = time_formatter(milliseconds=elapsed_time)
        estimated_total_time = time_formatter(milliseconds=estimated_total_time)

        progress = "{0}{1}\n**P:** {2}%\n".format(
            ''.join([FINISHED_PROGRESS_STR for i in range(math.floor(percentage / 10))]),
            ''.join([UN_FINISHED_PROGRESS_STR for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2))

        tmp = progress + "**Downloaded:** {0} of {1}\n**Speed**: {2} | **ETA:** {3}\n {4}".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time if estimated_total_time != '' else "0 s",
            get_bottom_status() 
        )
       
        try:
            await message.edit(
               "{}\n{}\n{}".format(
                    file_name,
                    ud_type,
                    tmp
                ),
                reply_markup=(InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data=(f"cancel_tgdown_{id}".encode('UTF-8')))]
                ]))
            )                           
        except:
            pass


def humanbytes(size: int) -> str:
    """ converts bytes into human readable format """
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2 ** 10
    number = 0
    dict_power_n = {
        0: " ",
        1: "Ki",
        2: "Mi",
        3: "Gi",
        4: "Ti"
    }
    while size > power:
        size /= power
        number += 1
    return str(round(size, 2)) + " " + dict_power_n[number] + 'B'

def time_formatter(milliseconds: int) -> str:
    """ converts seconds into human readable format """
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
          ((str(hours) + "h, ") if hours else "") + \
          ((str(minutes) + "m, ") if minutes else "") + \
          ((str(seconds) + "s, ") if seconds else "") + \
          ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]
