
import os

class ExecConfig:

        API_HASH = ""
        API_ID = 0
        BOT_TOKEN = ""

        OWNER_ID = 0

        # Chracter to use as a completed progress 
        COMPLETED_STR = "▰"

        # Chracter to use as a incomplete progress
        REMAINING_STR = "▱"

        BASE_DIR= "/"

        # Set this value to show all the remotes while leeching
        SHOW_REMOTE_LIST = False

        # to determine if upload process is canceled        
        UP_CANCEL= False

        # For vps set path here or you can use runtime too
        #RCLONE_CONFIG= os.path.join(os.getcwd(), 'rclone.conf')

        #rclone config text from conf file
        RCLONE_CONFIG = ""
        
        # Name of the RCLONE drive from the config
        DEF_RCLONE_DRIVE = ""

        # Time to wait before edit message
        EDIT_SLEEP_SECS = 10

        # Set this to your bot username if you want to add the username of your bot at the end of the commands like
        # /leech@Bot so the value will be @Bot
        BOT_CMD_POSTFIX = "" 

        





