from pyrogram.types import InlineKeyboardMarkup
import asyncio
from json import loads as jsonloads
from bot.utils.bot_utils.message_utils import editMessage, sendMessage
from bot.utils.bot_utils.misc_utils import ButtonMaker, get_rclone_config, get_readable_size


async def settings_myfiles_menu(
    client,
    message, 
    msg="", 
    drive_base="", 
    drive_name="", 
    submenu="", 
    edit=False,
    is_folder= True,
    ):
    
     buttons= ButtonMaker()

     if submenu == "myfiles_menu_setting":
          if drive_base == "":
               buttons.cbl_buildbutton("📁 Calculate Size", "myfilesmenu^size_action")
          else:
               if is_folder:
                    buttons.dbuildbutton("📁 Calculate Size", "myfilesmenu^size_action",
                                         "🗑 Delete", "myfilesmenu^delete_action^folder")
               else:
                    buttons.cbl_buildbutton ("🗑 Delete", "myfilesmenu^delete_action^file")
          
          buttons.cbl_buildbutton("✘ Close Menu", f"myfilesmenu^close")

          if edit:
               await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
          else:
               await sendMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

     elif submenu == "rclone_size":
        path = get_rclone_config()
        files_count, total_size = await rclone_size(message, drive_base,drive_name, path)
        total_size = get_readable_size(total_size)
        msg= f"Total Files: {files_count}\nFolder Size: {total_size}"
        
        buttons.cbl_buildbutton("✘ Close Menu", f"myfilesmenu^close")

        if edit:
            await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
        else:
            await sendMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

     elif submenu == "rclone_delete":
          if is_folder:
               buttons.dbuildbutton("Yes", "myfilesmenu^yes^folder",
                                    "No", "myfilesmenu^no^folder")
               msg= f"Are you sure you want to delete this folder permanently?"
          else:
               buttons.dbuildbutton("Yes", "myfilesmenu^yes^file",
                                    "No", "myfilesmenu^no^file")
               msg= f"Are you sure you want to delete this file permanently?"

          await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

     elif submenu == "yes":
          conf_path = get_rclone_config()
          if is_folder:
               await rclone_purge(message, drive_base, drive_name, conf_path)    
               msg= f"The folder has been deleted successfully!!"
          else:
               await rclone_delete(message, drive_base, drive_name, conf_path)  
               msg= f"The file has been deleted successfully!!"
     
          buttons.cbl_buildbutton("✘ Close Menu", f"myfilesmenu^close")
          
          if edit:
               await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
          else:
               await sendMessage.reply(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button)) 

async def rclone_size(message, drive_base, drive_name, conf_path):
     await editMessage("**Calculating Folder Size...**\n\nPlease wait, it will take some time depending on number of files", message)
    
     cmd = ["rclone", "size", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--json"] 
     process = await asyncio.create_subprocess_exec(*cmd,
                stdout=asyncio.subprocess.PIPE, 
                stderr=asyncio.subprocess.PIPE)
     stdout, stderr = await process.communicate()
     stdout = stdout.decode().strip()
     return_code = await process.wait()

     if return_code != 0:
          err = stderr.decode().strip()
          return await sendMessage(f'Error: {err}', message)

     data = jsonloads(stdout)
     files = data["count"]
     size = data["bytes"]

     return files, size

async def rclone_purge(message,drive_base, drive_name, conf_path):
     cmd = ["rclone", "purge", f'--config={conf_path}', f"{drive_name}:{drive_base}"] 
     process = await asyncio.create_subprocess_exec(*cmd,
                stdout=asyncio.subprocess.PIPE, 
                stderr=asyncio.subprocess.PIPE)
     stdout, stderr = await process.communicate()
     stdout = stdout.decode().strip()
     return_code = await process.wait()

     if return_code != 0:
          err = stderr.decode().strip()
          return await sendMessage(f'Error: {err}', message)

async def rclone_delete(message, drive_base, drive_name, conf_path):
     cmd = ["rclone", "delete", f'--config={conf_path}', f"{drive_name}:{drive_base}"] 
     process = await asyncio.create_subprocess_exec(*cmd,
                stdout=asyncio.subprocess.PIPE, 
                stderr=asyncio.subprocess.PIPE)
     stdout, stderr = await process.communicate()
     stdout = stdout.decode().strip()
     return_code = await process.wait()

     if return_code != 0:
          err = stderr.decode().strip()
          return await sendMessage(f'Error: {err}', message)

