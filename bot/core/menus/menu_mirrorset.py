from bot import LOGGER
from bot.core.varholderwrap import get_val, set_val
from bot.utils.bot_utils.menu_utils import Menus, rcloneListButtonMaker
from bot.utils.bot_utils.misc_utils import TelethonButtonMaker, get_rclone_config, pairwise
import os, configparser
import asyncio
from json import loads as jsonloads

yes = "✅"
folder_icon= "📁"

async def mirrorset_menu(
    query, 
    message, 
    msg="", 
    submenu="", 
    drive_base="", 
    drive_name="", 
    edit=False, 
    data_cb="", 
    data_back_cb= ""
    ):
    
    buttons = TelethonButtonMaker()

    if submenu == "list_drive":
        path= os.path.join(os.getcwd(), "rclone.conf")
        conf = configparser.ConfigParser()
        conf.read(path)

        for j in conf.sections():
            prev = ""
            if j == get_val("RCLONE_MIRRORSET_DRIVE"):
                prev = yes
            if "team_drive" in list(conf[j]):
                buttons.cb_buildsecbutton(f"{prev} {folder_icon} {j}", f"mirrorsetmenu^list_drive_mirrorset_menu^{j}")
            else:
                buttons.cb_buildsecbutton(f"{prev} {folder_icon} {j}", f"mirrorsetmenu^list_drive_mirrorset_menu^{j}")
        
        for a, b in pairwise(buttons.second_button):
            row= [] 
            if b == None:
                row.append(a)  
                buttons.ap_buildbutton(row)
                break
            row.append(a)
            row.append(b)
            buttons.ap_buildbutton(row)

        buttons.cbl_buildbutton("✘ Close Menu", f"mirrorsetmenu^close")

        if edit:
            await message.edit(msg, buttons=buttons.first_button)
        else:
            await message.reply(msg, buttons=buttons.first_button)


    elif submenu == "list_dir":
        conf_path = get_rclone_config()

        buttons.cbl_buildbutton(f"✅ Select this folder", f"mirrorsetmenu^close")

        cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only"] 

        process = await asyncio.create_subprocess_exec(*cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
        )

        out, err = await process.communicate()
        out = out.decode().strip()
        return_code = await process.wait()
        
        if return_code != 0:
           err = err.decode().strip()
           return await message.reply(f'Error: {err}')  

        list_info = jsonloads(out)
        list_info.sort(key=lambda x: x["Name"])  
        set_val("list_info", list_info)

        if len(list_info) == 0:
            buttons.cbl_buildbutton("❌Nothing to show❌", "mirrorsetmenu^pages")
        else:    
            total = len(list_info)
            max_results= 10
            offset= 0
            start = offset
            end = max_results + start
            next_offset = offset + max_results

            if end > total:
                list_info= list_info[offset:]    
            elif offset >= total:
                list_info= []    
            else:
                list_info= list_info[start:end] 
  

            rcloneListButtonMaker(result_list=list_info, 
                buttons= buttons, 
                menu_type= Menus.MIRRORSET,
                callback= data_cb   
             )

            if offset == 0 and total <= 10:
                buttons.cbl_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="mirrorsetmenu^pages") 
            else: 
                buttons.dbuildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", "mirrorsetmenu^pages",
                                    "NEXT ⏩", f"n_mirrorset {next_offset} {data_back_cb}")

        buttons.cbl_buildbutton("⬅️ Back", f"mirrorsetmenu^{data_back_cb}")
        buttons.cbl_buildbutton("✘ Close Menu", f"mirrorsetmenu^close")

        if edit:
            await message.edit(msg, buttons=buttons.first_button)
        else:
            await message.reply(msg, buttons=buttons.first_button)
