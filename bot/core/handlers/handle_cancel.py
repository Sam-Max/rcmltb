
from bot import GLOBAL_RC_INST


async def handle_cancel(e):
   data = e.data.decode("UTF-8").split("_")
   id= data[1]
   for rc_up in GLOBAL_RC_INST:
        if rc_up.id == id:
            rc_up.cancel = True
            break  