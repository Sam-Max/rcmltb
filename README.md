# An rclone bot to upload and transfer to many cloud servers, made by @SamMax009

Contact: [Telegram](https://t.me/SamMax009)

    - Upload telegram files to cloud.
    - Transfer from cloud to cloud.
    - Renaming of files.
    - Menu to list clouds from rclone.conf and selection of folders and files.
    - Progress bar when downloading and uploading.

## Variables

    - API_ID
    - API_HASH
    - OWNER_ID
    - BOT_TOKEN
    - RCLONE_CONFIG

## Commands for bot(set through @BotFather) 
- upload - upload to selected cloud 
- copy - copy from cloud to cloud
- conf - config rclone and set upload folder 
- logs - get logs from server
- clean- clean downloads

## Secrets for github

    HEROKU_API_KEY
    HEROKU_APP_NAME
    HEROKU_EMAIL
    
    
## Deploy to heroku
- Fork the repo.
- Create app in heroku
- Go to settings of app / config vars / add all variables
- connect to github and deploy
- turn on dynos

## Deploy Manual. 
- sudo apt update 
- sudo apt install -y python3.8 
- sudo apt install -y python3-venv 
- python3 -m venv venv 
- source venv/bin/activate 
- pip install -r requirements.txt 
- curl https://rclone.org/install.sh | bash
- chmod 777 start.sh 
- ./start.sh

## Repositories used to develop this bot and credits:

1- Telethon and Pyrogram.

2- [Conversation-Pyrogram](https://github.com/Ripeey/Conversation-Pyrogram/archive/refs/heads/main.zip)

3- [TorToolkit-Telegram](https://github.com/yash-dk/TorToolkit-Telegram)

4- [EvamariaTG] (https://github.com/EvamariaTG/EvaMaria)

