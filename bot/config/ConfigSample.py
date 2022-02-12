
import os

class ExecConfig:

        API_HASH = "***REMOVED***"
        API_ID = ***REMOVED***
        BOT_TOKEN = "5282894676:AAEM-a7V8YmxHWhWGtkSYDUGAyZTddeH5gM"

        ALD_USR = [***REMOVED***]
        OWNER_ID = ***REMOVED***

        # Chracter to use as a completed progress 
        COMPLETED_STR = "▰"

        # Chracter to use as a incomplete progress
        REMAINING_STR = "▱"

        # Set this value to show all the remotes while leeching
        SHOW_REMOTE_LIST = False

        # value to determine if upload process is canceled        
        UPCANCEL= False

        BASE_DIR= "/"
        
        # For vps set path here or you can use runtime too
        #RCLONE_CONFIG= os.path.join(os.getcwd(), 'rclone.conf')

        #rclone config text from conf file
        RCLONE_CONFIG = '''[teamtvadictos]
type = drive
scope = drive
token = {"access_token":"ya29.A0ARrdaM8RE7EzZLqSA6UkYfU7o1jrBUoArQKt3knvaccL9Bi31ROFkdR55aj94cr4UbCLqk2kefl_Aia9VbaO7W_QhkmiYitOvUb2K4SdayIDhFLEkN_cBXOWBzSYdVThQnTzy9nMfy2_qOeu_NXMM6MU2Lh5","token_type":"Bearer","refresh_token":"1//03zfVK07qdQT2CgYIARAAGAMSNwF-L9IrWMWzxvXxQu1oHjss2O6HBSic65HpUlPUBQ3q5Wj-PMa7KkN6F63aI5gfc4W-JOqecZg","expiry":"2022-01-24T22:26:44.6996005+01:00"}
team_drive = 0ALRlYPnR4WI3Uk9PVA
root_folder_id =

[teampstuffs]
type = drive
scope = drive
token = {"access_token":"ya29.a0ARrdaM9prHcY2y7vVDeE7L4QWlx0__YnH2T82gAW37CmQVGfn9KUvY0OxuUm7FRYsWnASfc8m1sgCTSFegLiRk4KuOM8bQEorZt8HdVrQAAE2OhzD1e98BH_PpvmVBtKT5fXwEDru1O9KdpnZsfh21AGWCpwMQ","token_type":"Bearer","refresh_token":"1//03oqFkYnGr8wMCgYIARAAGAMSNwF-L9IrTGrImKkQQXyP3SwQtaLS_erpfo6-yUax4HxTZA2PqcVyXggDByASUuiVkxdpL1rNctY","expiry":"2021-10-26T14:22:43.068920551Z"}
team_drive = 0ANEjugbpAMqaUk9PVA
root_folder_id =

[owncloud]
type = webdav
url = https://nube.uclv.cu/remote.php/dav/files/F710225B-7C3E-47B5-8916-A24DEA970549/
user = ecnunez
pass = vWdGKR_Q1uPc4E6WENK7ayfH-9ONx4xJTY8
vendor = nextcloud

[cryptowncloud]
type = crypt
remote = owncloud:/share
password = 9tGSmc1x0YpyCoUKYjnM0xR80IcuJ26EsP6sfGi7A-EX4_fdRqA

'''
        
        # Name of the RCLONE drive from the config
        DEF_RCLONE_DRIVE = ""

        # Time to wait before edit message
        EDIT_SLEEP_SECS = 10

        # Set this to your bot username if you want to add the username of your bot at the end of the commands like
        # /leech@Bot so the value will be @Bot
        BOT_CMD_POSTFIX = "" 

        





