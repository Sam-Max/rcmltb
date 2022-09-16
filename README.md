# An Rclone Telegram bot to transfer to and from many clouds

## Features:

### qBittorrent
- Qbittorrent support for torrent and magnets

### Aria2c
- Aria support for direct download links

### Mirror
- From Telegram to cloud
- Torrent/magnets to cloud using qBittorrent
- Directs links to cloud using Aria2
- Mega.nz links to cloud
- Files in batch from Telegram to cloud

### Leech
- File/folder from cloud to Telegram
- Directs links to Telegram using Aria2
- Mega.nz links to Telegram
- Torrent/magnets to Telegram using qBittorrent
- 4gb file with premium account

### Copy
- Copy file/folder from cloud to cloud

### Status
- Progress bar for download and upload
- Status for tasks

### Archives
- Extract and Zip link/file from Telegram to cloud
- Extract and Zip folder/file from cloud to Telegram
- Using 7-zip tool to extract all supported files
- Extract rar, zip and 7z with or without password

### Others
- Telegram Navigation Bottom Menus to interact with cloud
- Renaming of Telegram files
- Load and change rclone config file from bot.
- File Manager (size, mkdir, delete, dedupe, rename)

### From Other Repositories
- Search on torrents with Torrent Search API or with variable plugins using qBittorrent search engine
- Select files from Torrent before downloading 
- Get restricted messages from private channels.
- Clone Google Drive files/folders from link to cloud using gclone
- Thumbnail support
- Set upload as document or as media 
- Update bot at startup and with restart command using UPSTREAM_REPO
- Own users settings when using bot or added to supergroup (thumbnail, as document/as media, rclone.conf)
- Direct links Supported:
  > letsupload.io, hxfile.co, anonfiles.com, bayfiles.com, antfiles, fembed.com, fembed.net, femax20.com, layarkacaxxi.icu, fcdn.stream, sbplay.org, naniplay.com, naniplay.nanime.in, naniplay.nanime.biz, sbembed.com, streamtape.com, streamsb.net, feurl.com, pixeldrain.com, racaty.net, 1fichier.com, 1drv.ms (Only works for file not folder or business account), uptobox.com (Uptobox account must be premium) and solidfiles.com

## Commands for bot(set through @BotFather)

```
mirror - mirror to selected cloud 
unzipmirror - mirror and extract to cloud 
zipmirror - mirror and zip to cloud 
mirrorset - select cloud/folder where to mirror
mirrorbatch - mirror files in batch to cloud 
leech - leech from cloud to Telegram
unzipleech - leech and extract to Telegram 
zipleech - leech and zip to Telegram 
leechset - leech settings
leechbatch - leech files in batch to Telegram 
myfiles - file manager
clone - clone gdrive files/folder to cloud
copy - copy from cloud to cloud
config - rclone config
cleanup - clean drive trash
storage - drive details
search - search for torrents
status - status message of tasks
server - server stats
speedtest - test server speed
log - bot log
ping - ping bot
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
        - `API_ID`: get this from https://my.telegram.org. Don't put this in quotes
        - `API_HASH`: get this from https://my.telegram.org
        - `BOT_TOKEN`: The Telegram Bot Token (get from @BotFather)
        - `OWNER_ID`: your Telegram User ID (not username) of the owner of the bot
        - `DOWNLOAD_DIR`: The path to the local folder where the downloads will go

   - Non mandatory variables:
        - `ALLOWED_USERS`: list of IDs of allowed users who can use this bot separated by spaces
        - `ALLOWED_CHATS`: list of IDs of allowed chats who can use this bot separated by spaces
        - `UPSTREAM_REPO`: if your repo is private add your github repo link with format: `https://username:{githubtoken}@github.com/{username}/{reponame}`, so you can update your app from private repository on each restart. Get token from [Github settings](https://github.com/settings/tokens)
        - `CMD_INDEX`: index number that will be added at the end of all commands. `Str`
        - `UPSTREAM_BRANCH`: Upstream branch for update
        - `EDIT_SLEEP_SECS`: Seconds for update regulary rclone progress message. Default to 10
        - `TORRENT_TIMEOUT`: Timeout of dead torrents downloading with qBittorrent
   
   - LEECH
        - `TG_SPLIT_SIZE`: Telegram upload limit in bytes, to automatically slice the file bigger that this size into small parts to upload to Telegram. Default is `2GB` for non premium account or `4GB` if your account is premium
        - `DUMP_CHAT`: Chat ID. Upload files to specific chat. `str`. **NOTE**: Only available for superGroup/channel. Add `-100` before channel/supergroup id.
        - `USER_SESSION_STRING`: Pyrogram session string for mirrorbatch command and to download/upload using your telegram account (needed for telegram premium upload). To generate string session use this command `python3 session_generator.py` on command line on your pc from repository folder. **NOTE**: when using string session, you have to use with supergroup or channel not bot.
        - `AS_DOCUMENT`: Default type of Telegram file upload. Default is `False` mean as media. `Bool`

   - MEGA
        - `MEGA_API_KEY`: Mega.nz API key to mirror mega.nz links. Get it from Mega SDK Page
        - `MEGA_EMAIL_ID`: E-Mail ID used to sign up on mega.nz for using premium account
        - `MEGA_PASSWORD`: Password for mega.nz account

   - qBittorrent
        - `BASE_URL_OF_BOT`: Valid BASE URL where the bot is deployed to use qbittorrent web selection. Format of URL should be http://myip, where myip is the IP/Domain(public). If you have chosen port other than 80 so write it in this format http://myip:port (http and not https). Str
        - `SERVER_PORT`: Port. Str
        - `WEB_PINCODE`: If empty or False means no more pincode required while qbit web selection. Bool
        Qbittorrent NOTE: If your facing ram exceeded issue then set limit for MaxConnecs, decrease AsyncIOThreadsCount in qbittorrent config and set limit of DiskWriteCacheSize to 32

   - Torrent Search
        - `SEARCH_API_LINK`: Search api app link. Get your api from deploying this [repository](https://github.com/Ryuk-me/Torrent-Api-py). `Str`
        - `SEARCH_LIMIT`: Search limit for search api, limit for each site. Default is zero. `Str`
        - `SEARCH_PLUGINS`: List of qBittorrent search plugins (github raw links). `Str`
        - Supported Sites:
        >1337x, Piratebay, Nyaasi, Torlock, Torrent Galaxy, Zooqle, Kickass, Bitsearch, MagnetDL, Libgen, YTS, Limetorrent, TorrentFunk, Glodls, TorrentProject and YourBittorrent
 
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

4. **Deploying on VPS Using docker-compose**

**NOTE**: If you want to use port other than 80, change it in docker-compose.yml

```
sudo apt install docker-compose
```
- Build and run Docker image:
```
sudo docker-compose up
```
- After editing files with nano for example (nano start.sh):
```
sudo docker-compose up --build
```
- To stop the image:
```
sudo docker-compose stop
```
- To run the image:
```
sudo docker-compose start

```

## How to create rclone config file

**Check this youtube video (not mine, credits to author):** 
<p><a href="https://www.youtube.com/watch?v=Sp9lG_BYlSg"> <img src="https://img.shields.io/badge/See%20Video-black?style=for-the-badge&logo=YouTube" width="160""/></a></p>

**Notes**:
- When you create rclone.conf file add at least two accounts if you want to copy from cloud to cloud. 
- For those on android phone, you can use [RCX app](https://play.google.com/store/apps/details?id=io.github.x0b.rcx&hl=en_IN&gl=US) app to create rclone.conf file. Use "Export rclone config" option in app menu to get config file.
- Rclone supported providers:
  > 1Fichier, Amazon Drive, Amazon S3, Backblaze B2, Box, Ceph, DigitalOcean Spaces, Dreamhost, **Dropbox**,   Enterprise File Fabric, FTP, GetSky, Google Cloud Storage, **Google Drive**, Google Photos, HDFS, HTTP, Hubic, IBM COS S3, Koofr, Mail.ru Cloud, **Mega**, Microsoft Azure Blob Storage, **Microsoft OneDrive**, **Nextcloud**, OVH, OpenDrive, Oracle Cloud Storage, ownCloud, pCloud, premiumize.me, put.io, Scaleway, Seafile, SFTP, **WebDAV**, Yandex Disk, etc. **Check all providers on official site**: [Click here](https://rclone.org/#providers).

## Bot Screenshot: 

<img src="./screenshot.png" alt="button menu example">

## Donations

<p> If you like this project you can help me, donating the amount you wish.</p>

[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](YOUR_EMAIL_CODE)

-----

## Repositories used to develop this bot:

1- [TorToolkit-Telegram](https://github.com/yash-dk/TorToolkit-Telegram). Base repository.

2- [Rclone](https://github.com/rclone/rclone)

4- [Pyrogram](https://github.com/pyrogram/pyrogram)

4- and many others mentioned in code.
