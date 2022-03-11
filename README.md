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
- speedtest - test speed of server
- cleardata- clear downloads
- restart - restart and update bot

## Deploying on Heroku
<p><a href="https://github.com/Sam009-max/RcloneTgBot/tree/heroku"> <img src="https://img.shields.io/badge/Deploy%20Guide-blueviolet?style=for-the-badge&logo=heroku" width="170""/></a></p>


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
        - `BOT_TOKEN`: The Telegram Bot Token (get from @BotFather) 
        - `RCLONE_CONFIG`: content of the rclone.conf file generated with rclone command-line program.

   - Non mandatory variables:
        - `UPSTREAM_REPO`: if your repo is private add your github repo link with format: `https://username:{githubtoken}@github.com/{username}/{reponame}`, so you can update your app from private repository on each restart. Get token from [Github settings](https://github.com/settings/tokens)
        - `UPSTREAM_BRANCH`: Upstream branch for update. 

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

4. **Deploying on VPS without Docker**
- sudo apt update 
- sudo apt install -y python3.8 
- sudo apt install -y python3-venv 
- python3 -m venv venv 
- source venv/bin/activate 
- pip install -r requirements.txt 
- sudo apt -qq install -y git wget curl python3 python3-pip locales ffmpeg
- curl https://rclone.org/install.sh | bash
- chmod 777 start.sh 
- ./start.sh


## Repositories used to develop this bot and credits:

1- [TorToolkit-Telegram](https://github.com/yash-dk/TorToolkit-Telegram) 

2- [Conversation-Pyrogram](https://github.com/Ripeey/Conversation-Pyrogram/archive/refs/heads/main.zip)

3- [Rclone](https://github.com/rclone/rclone)

4- [Telethon]() and [Pyrogram]()



