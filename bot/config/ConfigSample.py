
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

        # Gdrive Config
        GDRIVE_BASE_DIR = "/"

        # The base direcory to which the files will be upload if using RCLONE for other engine than GDRIVE/ONEDRIVE
        RCLONE_BASE_DIR = "/"
        
        # Set this value to show all the remotes while leeching
        SHOW_REMOTE_LIST = False

        # if upload process is canceled        
        UPCANCEL= False
        
        # For vps set path here or you can use runtime too
        RCLONE_CONFIG= os.path.join(os.getcwd(), 'rclone.conf')
        
        # Name of the RCLONE drive from the config
        DEF_RCLONE_DRIVE = "teamdrive"

        # if upload process is canceled        
        UPCANCEL= False

        # Time to wait before edit message
        EDIT_SLEEP_SECS = 10

        # Set this to your bot username if you want to add the username of your bot at the end of the commands like
        # /leech@Bot so the value will be @Bot
        BOT_CMD_POSTFIX = "" 

        





