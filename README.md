# An Rclone Telegram bot to transfer to and from many clouds

## Features:

- Mirror from Telegram to cloud.
- Mirror-batch up to 100 files at once from Telegram to cloud (private or public channel)
- Leech files and folders from cloud to Telegram.
- Copy from one cloud to another.
- Button panels to interact with clouds.
- Renaming of Telegram files.
- Progress bar when downloading and uploading.

## Commands for bot(set through @BotFather)

```
mirror - mirror to selected cloud 
mirrorbatch - mirror batch files to selected cloud 
leech - leech from cloud to telegram
copy - copy from cloud to cloud
myfiles - file manager
config - select cloud and folder for mirror
logs - get logs from server
server - get server info
speedtest - test speed of server
cleardata- clear downloads
restart - restart bot
```

## Deploy on VPS: 

1. **Installing requirements**

 - Clone repo:

        git clone https://github.com/Sam-Max/Rclone-Tg-Bot rclonetgbot/ && cd rclonetgbot

 - Install Docker(skip this if deploying without docker).

        sudo apt install snapd
        sudo snap install docker

2. **Set up config file**

- cp config_sample.env config.env 

- Fill up variables:

   - Mandatory variables:
        - `API_ID`: get this from https://my.telegram.org. Don't put this in quotes.
        - `API_HASH`: get this from https://my.telegram.org
        - `OWNER_ID`: your Telegram User ID (not username) of the owner of the bot.
        - `ALLOWED_USERS`: list of IDs of allowed users who can use this bot separated by spaces
        - `ALLOWED_CHATS`: list of IDs of allowed chats who can use this bot separated by spaces
        - `BOT_TOKEN`: The Telegram Bot Token (get from @BotFather) 
        - `RCLONE_CONFIG`: content of the rclone.conf file generated with rclone command-line program.

   - Non mandatory variables:
        - `UPSTREAM_REPO`: if your repo is private add your github repo link with format: `https://username:{githubtoken}@github.com/{username}/{reponame}`, so you can update your app from private repository on each restart. Get token from [Github settings](https://github.com/settings/tokens)
        - `SESSION`: Pyrogram Session: [![Run on Repl.it](https://replit.com/badge/github/vasusen-code/saverestrictedcontentbot)](https://replit.com/@SpEcHiDe/GenerateStringSession) 
        - `UPSTREAM_BRANCH`: Upstream branch for update. 
        - `TG_SPLIT_SIZE`: Telegram upload limit in bytes (max `2097151000` which is ~2GB), to automatically slice the file bigger that this size into small parts to upload to Telegram.
        - `EDIT_SLEEP_SECS`: Seconds for update the progress message regulary. Default to 10. 

3. **Deploying on VPS Using Docker**

- Start Docker daemon (skip if already running), if installed by snap then use 2nd command:
    
        sudo dockerd
        sudo snap start docker

     Note: If not started or not starting, run the command below then try to start.

        sudo apt install docker.io

- Build Docker image:

        sudo docker build . -t rclonetg-bot 

- Run the image:

        sudo docker run rclonetg-bot 

- To stop the image:

        sudo docker ps
        sudo docker stop id

- To clear the container:

        sudo docker container prune

- To delete the images:

        sudo docker image prune -a

4. **Deploying on VPS without Docker**
- sudo apt update 
- sudo apt install -y python3.8 
- sudo apt install -y python3-venv 
- python3 -m venv venv 
- source venv/bin/activate 
- pip install -r requirements.txt 
- sudo apt -qq install -y git wget curl python3 python3-pip locales ffmpeg p7zip-full
- curl https://rclone.org/install.sh | bash
- chmod 777 start.sh 
- ./start.sh


## Repositories used to develop this bot:

1- [TorToolkit-Telegram](https://github.com/yash-dk/TorToolkit-Telegram) 

2- [Conversation-Pyrogram](https://github.com/Ripeey/Conversation-Pyrogram/archive/refs/heads/main.zip)

3- [Rclone](https://github.com/rclone/rclone)

4- [Telethon]() and [Pyrogram]()

5- Others mentioned in the bot code...



