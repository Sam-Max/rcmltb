# An rclone bot to upload and transfer to many clouds

Contact: [Telegram](https://t.me/SamMax009)

    - Upload telegram files to cloud.
    - Transfer from cloud to cloud.
    - Renaming of files.
    - Menu to list clouds from rclone.conf and selection of folders and files.
    - Progress bar when downloading and uploading.


## Commands for bot(set through @BotFather) 
- upload - upload to selected cloud 
- copy - copy from cloud to cloud
- config - configurate rclone and set upload folder 
- logs - get logs from server
- clean- clean downloads
- restart - restart bot

## Steps: 

1. **Setting up config file:**
- cr config_sample.env config.env
- Fill up mandatory variables:
    - `API_ID`
    - `API_HASH`
    - `OWNER_ID`
    - `BOT_TOKEN`
    - `RCLONE_CONFIG`

2. **Deploy vps**
- sudo apt update 
- sudo apt install -y python3.8 
- sudo apt install -y python3-venv 
- python3 -m venv venv 
- source venv/bin/activate 
- pip install -r requirements.txt 
- curl https://rclone.org/install.sh | bash
- chmod 777 start.sh 
- ./start.sh

## Deploying on Heroku
<p><a href="https://github.com/Sam009-max/RcloneTgBot/tree/heroku"> <img src="https://img.shields.io/badge/Deploy%20Guide-blueviolet?style=for-the-badge&logo=heroku" width="170""/></a></p>

## Repositories used to develop this bot and credits:

1- Telethon and Pyrogram.

2- [Conversation-Pyrogram](https://github.com/Ripeey/Conversation-Pyrogram/archive/refs/heads/main.zip)

3- [TorToolkit-Telegram](https://github.com/yash-dk/TorToolkit-Telegram)

4- [EvamariaTG](https://github.com/EvamariaTG/EvaMaria)

