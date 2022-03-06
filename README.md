# An rclone telegram bot to upload and transfer to many clouds

Contact: [Telegram](https://t.me/SamMax009)

    - Mirror Telegram files to cloud.
    - Leech cloud files and folders to Telegram.
    - Transfer from cloud to cloud.
    - Renaming of files.
    - Menu to list clouds from rclone.conf and selection of folders, subfolders, and files.
    - Progress bar when downloading and uploading.


## Commands for bot(set through @BotFather) 
- mirror - mirror to selected cloud 
- leech - leech from cloud to telegram
- copy - copy from cloud to cloud
- config - config rclone and set folder where to mirror 
- logs - get logs from server
- speed_test - test speed of server
- cleardata- clear downloads


## Steps: 

1. **Setting up config file:**
- cr config_sample.env config.env
- Fill up mandatory variables:
    - `API_ID`: get this from https://my.telegram.org. Don't put this in quotes.
    - `API_HASH`: get this from https://my.telegram.org
    - `OWNER_ID`: your Telegram User ID (not username) of the owner of the bot.
    - `BOT_TOKEN`: The Telegram Bot Token (get from @BotFather) 
    - `RCLONE_CONFIG`: content of the rclone.conf file generated with rclone command-line program.

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

1- [TorToolkit-Telegram](https://github.com/yash-dk/TorToolkit-Telegram) 

2- [Conversation-Pyrogram](https://github.com/Ripeey/Conversation-Pyrogram/archive/refs/heads/main.zip)

3- [Rclone](https://github.com/rclone/rclone)

4- Telethon and Pyrogram API libraries.



