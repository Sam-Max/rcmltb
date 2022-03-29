from bot.core.menus.menu_myfiles import settings_myfiles_menu


async def handle_myfiles(client, message):
     await settings_myfiles_menu(
                client= client, 
                message= message,
                msg= "Please select your drive to see files", 
                data_cb="list_drive_myfiles_menu"
            ) 