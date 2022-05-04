from pyrogram.types import InlineKeyboardMarkup
from pyrogram.types import InlineKeyboardButton
import asyncio
import json
import logging
from bot.utils.get_rclone_conf import get_config
from bot.utils.get_size_p import get_size

header= ""

async def settings_myfiles_menu(
    client,
    message, 
    drive_base="", 
    msg="", 
    drive_name="", 
    submenu=None, 
    edit=False,
    is_folder= True,
    ):
    
     menu = []

     if submenu is None:
          if drive_base == "":
               menu = [[InlineKeyboardButton(text= "📁 Calculate Size", callback_data= "myfilesmenu^size_action")]]
          else:
               if is_folder:
                    menu = [[InlineKeyboardButton(text= "📁 Calculate Size", callback_data= "myfilesmenu^size_action"),
                         InlineKeyboardButton(text= "🗑 Delete", callback_data= "myfilesmenu^delete_action^folder")],
                         ]
               else:
                    menu = [[InlineKeyboardButton(text= "🗑 Delete", callback_data= "myfilesmenu^delete_action^file")]]
          
          menu.append(
               [InlineKeyboardButton("✘ Close Menu", f"myfilesmenu^selfdest")]
          )

          if edit:
               await message.edit(msg, reply_markup= InlineKeyboardMarkup(menu))
          else:
               await message.reply_text(msg, quote= True, reply_markup= InlineKeyboardMarkup(menu))

     elif submenu == "rclone_size":
        conf_path = await get_config()
        logging.info(f"{drive_name}:{drive_base}")

        files_count, total_size = await rclone_size(
            message,
            drive_base, 
            drive_name, 
            conf_path, 
        )

        total_size = get_size(total_size)
        msg= f"Total Files: {files_count}\nFolder Size: {total_size}"

        menu.append(
               [InlineKeyboardButton("✘ Close Menu", f"myfilesmenu^selfdest")]
          )

        if edit:
            await message.edit(msg, reply_markup= InlineKeyboardMarkup(menu))
        else:
            await message.reply(header, reply_markup= InlineKeyboardMarkup(menu))  

     elif submenu == "rclone_delete":
          if is_folder:
               buttons = [[InlineKeyboardButton(text= "Yes", callback_data= "myfilesmenu^yes^folder"),
               InlineKeyboardButton(text= "No", callback_data= "myfilesmenu^no^folder")]]

               msg= f"Are you sure you want to delete this folder permanently?"
          else:
               buttons = [[InlineKeyboardButton(text= "Yes", callback_data= "myfilesmenu^yes^file"),
               InlineKeyboardButton(text= "No", callback_data= "myfilesmenu^no^file")]]

               msg= f"Are you sure you want to delete this file permanently?"

          await message.edit(msg, reply_markup= InlineKeyboardMarkup(buttons))

     elif submenu == "yes":
          conf_path = await get_config()
          
          menu.append(
               [InlineKeyboardButton("✘ Close Menu", f"myfilesmenu^selfdest")]
          )

          if is_folder:
               await rclone_purge(
                    drive_base, 
                    drive_name, 
                    conf_path
               )    
               msg= f"The folder has been deleted successfully!!"

          else:
               await rclone_delete(
                    drive_base, 
                    drive_name, 
                    conf_path
               )  
               msg= f"The file has been deleted successfully!!"

          if edit:
               await message.edit(msg, reply_markup= InlineKeyboardMarkup(menu))
          else:
               await message.reply(header, reply_markup= InlineKeyboardMarkup(menu)) 

async def rclone_size(
     message,
     drive_base, 
     drive_name, 
     conf_path
     ):

     await message.edit("**Calculating Folder Size...**\n\nPlease wait, it will take some time depending on number of files.")

     cmd = ["rclone", "size", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--json"] 

     process = await asyncio.create_subprocess_exec(
     *cmd,
     stdout=asyncio.subprocess.PIPE
     )

     stdout, stderr = await process.communicate()
     stdout = stdout.decode().strip()

     if process.returncode != 0:
          logging.info(stderr)

     try:
          data = json.loads(stdout)
          files = data["count"]
          size = data["bytes"]
     except Exception as exc:
          logging.info(exc)

     return files, size

async def rclone_purge (
     drive_base, 
     drive_name, 
     conf_path
     ):

     cmd = ["rclone", "purge", f'--config={conf_path}', f"{drive_name}:{drive_base}"] 

     process = await asyncio.create_subprocess_exec(
     *cmd,
     stdout=asyncio.subprocess.PIPE
     )

     stdout, stderr = await process.communicate()
     stdout = stdout.decode().strip()

     if process.returncode != 0:
          logging.info(stderr)


async def rclone_delete (
     drive_base, 
     drive_name, 
     conf_path, 
     ):

     cmd = ["rclone", "delete", f'--config={conf_path}', f"{drive_name}:{drive_base}"] 

     process = await asyncio.create_subprocess_exec(
     *cmd,
     stdout=asyncio.subprocess.PIPE
     )

     stdout, stderr = await process.communicate()
     stdout = stdout.decode().strip()

     if process.returncode != 0:
          logging.info(stderr)

