# An Rclone Telegram bot to transfer to and from many clouds

## Features:

### qBittorrent
- Qbittorrent support for torrent and magnets
- Select files from Torrent before downloading 
- Zip and unzip

### Aria2c
- Aria support for direct download links

### Mirror
- From Telegram to cloud
- Torrent/magnets to cloud using qBittorrent
- Mega.nz and directs links to cloud
- Files in batch from Telegram to cloud

### Leech
- File/folder from cloud to Telegram
- Link/magnets to Telegram using qBittorrent
- Mega.nz and directs links to Telegram
- Files in batch from Telegram to Telegram
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

### Database
- SQL Database
- Save rclone.conf and token.pickle files on db
- Save user leech settings(thumbnails, sudo and allowed users, etc) on db

### RSS
- Rss feed with filter.

### Others
- Telegram Navigation Bottom Menus to interact with Cloud
- Renaming of Telegram files
- Load/change rclone.conf file from bot
- Load/change token.pickle from bot
- Change all config variables from bot
- File Manager (size, mkdir, delete, dedupe, rename)

### From Other Repositories
- Search on torrents with Torrent Search API or with variable plugins using qBittorrent search engine
- SQL Database support
- Ytdl support
- Select files from Torrent before downloading 
- Get restricted messages from private channels.
- Upload files to supergroup/channel.
- Clone Google Drive files/folders from link
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
ytdlmirror - mirror ytdlp supported link
ytdlzipmirror- mirror and zip ytdlp supported link
leech - leech from cloud to Telegram
unzipleech - leech and extract to Telegram 
zipleech - leech and zip to Telegram 
leechbatch - leech files in batch to Telegram 
ytdlleech - leech yt-dlp supported link
ytdlzipleech - leech and zip yt-dlp supported link
myfiles - file manager
clone - clone gdrive file/folder from link
copy - copy from cloud to cloud
config - rclone config
usetting - user settings
ownsetting - owner settings
rsslist - list all subscribed rss feed 
rssget - get specific No. of links from specific rss feed
rsssub - subscribe new rss feed
rssunsub - unsubscribe rss feed by title
rssset - rss settings
cleanup - clean drive trash
cancelall - cancel all tasks
storage - drive details
search - search for torrents
status - status message of tasks
stats - bot stats
shell - run cmds in shell
speedtest - test server speed
log - bot log
ping - ping bot
restart - restart bot
```

## Deploy on VPS: 

1. **Installing requirements**

 - Clone repo:

        git clone https://github.com/Sam-Max/rclone-mirror-leech-telegram-bot rclonetgbot/ && cd rclonetgbot

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

   - Non mandatory variables:
        - `DOWNLOAD_DIR`: The path to the local folder where the downloads will go
        - `SUDO_USERS`: Fill user_id of users whom you want to give sudo permission separated by spaces. `Str`
        - `DEFAULT_DRIVE`: To set a default drive from your rclone.conf. `Str`
        - `AUTO_MIRROR`: For auto mirroring files sent to the bot. Default is `False`. `Bool`
        - `ALLOWED_CHATS`: list of IDs of allowed chats who can use this bot separated by spaces `Str`
        - `UPSTREAM_REPO`: if your repo is private add your github repo link with format: `https://username:{githubtoken}@github.com/{username}/{reponame}`, so you can update your app from private repository on each restart. Get token from [Github settings](https://github.com/settings/tokens)
        - `UPSTREAM_BRANCH`: Upstream branch for update
        - `DATABASE_URL`: Your SQL Database URL. Follow this [Generate Database](https://github.com/anasty17/mirror-leech-telegram-bot/tree/master#generate-database) to generate database. Data that will be saved in Database: auth and sudo users, leech settings including thumbnails for each user. `Str`
        - `CMD_INDEX`: index number that will be added at the end of all commands. `Str`
        - `EDIT_SLEEP_SECS`: Seconds for update regulary rclone progress message. Default to 10
        - `TORRENT_TIMEOUT`: Timeout of dead torrents downloading with qBittorrent

   - CLONE
     - `GDRIVE_FOLDER_ID`: Folder/TeamDrive ID of the Google Drive Folder or `root` to which you want to clone. Required for `Google Drive`. `Str`
     - `IS_TEAM_DRIVE`: Set `True` if TeamDrive. Default is `False`. `Bool`
     - `EXTENSION_FILTER`: File extensions that won't clone. Separate them by space. `Str`
     **Notes**: Must add **token.pickle** file directly to root for cloning to work. You can use /config command to add from bot.
   
   - LEECH
        - `LEECH_SPLIT_SIZE`: Telegram upload limit in bytes, to automatically slice the file bigger that this size into small parts to upload to Telegram. Default is `2GB` for non premium account or `4GB` if your account is premium
        - `DUMP_CHAT`: Chat ID. Upload files to specific chat. `str`. **NOTE**: Only available for superGroup/channel. Add `-100` before channel/supergroup id.
        - `USER_SESSION_STRING`: Pyrogram session string for batch commands and to download/upload using your telegram account (needed for telegram premium upload). To generate string session use this command `python3 session_generator.py` on command line on your pc from repository folder. **NOTE**: when using string session, you have to use with supergroup not bot.
        - `AS_DOCUMENT`: Default type of Telegram file upload. Default is `False` mean as media. `Bool`

   - MEGA
        - `MEGA_API_KEY`: Mega.nz API key to mirror mega.nz links. Get it from Mega SDK Page
        - `MEGA_EMAIL_ID`: E-Mail ID used to sign up on mega.nz for using premium account
        - `MEGA_PASSWORD`: Password for mega.nz account

   - RSS
        - `RSS_DELAY`: Time in seconds for rss refresh interval. Default is `900` in sec. `Str`
        - `RSS_COMMAND`: Choose command for the desired action. `Str`
        - `RSS_CHAT_ID`: Chat ID where rss links will be sent. Add `-100` before channel id. `Str`
        - `RSS_USER_SESSION_STRING`: To send rss links from your telegram account. To generate session string use this command `python3 generate_string_session.py`. `Str`. **NOTE**: Don't use same session string as `USER_SESSION_STRING`.
        - **RSS NOTE**: `DATABASE_URL` and `RSS_CHAT_ID` are required, otherwise rss commands will not work. You must use bot in group. You can also add the bot to a channel and link this channel to group so messages sent by bot to channel will be forwarded to group without using `RSS_USER_STRING_SESSION`.    

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

   - Private Files
        - `YT_COOKIES_URL`: Youtube authentication cookies. Check setup [Here](https://github.com/ytdl-org/youtube-dl#how-do-i-pass-cookies-to-youtube-dl). Use gist raw link and remove commit id from the link, so you can edit it from gists only. `Str`
 
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
## Generate Database

**1. Using Railway**
- Go to [railway](https://railway.app) and create account
- Start new project
- Press on `Provision PostgreSQL`
- After creating database press on `PostgresSQL`
- Go to `Connect` column
- Copy `Postgres Connection URL` and fill `DATABASE_URL` variable with it

**2. Using ElephantSQL**
- Go to [elephantsql](https://elephantsql.com) and create account
- Hit `Create New Instance`
- Follow the further instructions in the screen
- Hit `Select Region`
- Hit `Review`
- Hit `Create instance`
- Select your database name
- Copy your database url, and fill `DATABASE_URL` variable with it

------

## How to create rclone config file

**Check this youtube video (not mine, credits to author):** 
<p><a href="https://www.youtube.com/watch?v=Sp9lG_BYlSg"> <img src="https://img.shields.io/badge/See%20Video-black?style=for-the-badge&logo=YouTube" width="160""/></a></p>

**Notes**:
- When you create rclone.conf file add at least two accounts if you want to copy from cloud to cloud. 
- For those on android phone, you can use [RCX app](https://play.google.com/store/apps/details?id=io.github.x0b.rcx&hl=en_IN&gl=US) app to create rclone.conf file. Use "Export rclone config" option in app menu to get config file.
- Rclone supported providers:
  > 1Fichier, Amazon Drive, Amazon S3, Backblaze B2, Box, Ceph, DigitalOcean Spaces, Dreamhost, **Dropbox**,   Enterprise File Fabric, FTP, GetSky, Google Cloud Storage, **Google Drive**, Google Photos, HDFS, HTTP, Hubic, IBM COS S3, Koofr, Mail.ru Cloud, **Mega**, Microsoft Azure Blob Storage, **Microsoft OneDrive**, **Nextcloud**, OVH, OpenDrive, Oracle Cloud Storage, ownCloud, pCloud, premiumize.me, put.io, Scaleway, Seafile, SFTP, **WebDAV**, Yandex Disk, etc. **Check all providers on official site**: [Click here](https://rclone.org/#providers).

## Getting Google OAuth API credential file and token.pickle

**NOTES**
- You need OS with a browser.
- Windows users should install python3 and pip. You can find how to install and use them from google.
- You can ONLY open the generated link from `generate_drive_token.py` in local browser.

1. Visit the [Google Cloud Console](https://console.developers.google.com/apis/credentials)
2. Go to the OAuth Consent tab, fill it, and save.
3. Go to the Credentials tab and click Create Credentials -> OAuth Client ID
4. Choose Desktop and Create.
5. Publish your OAuth consent screen App to prevent **token.pickle** from expire
6. Use the download button to download your credentials.
7. Move that file to the root of rclone-tg-bot, and rename it to **credentials.json**
8. Visit [Google API page](https://console.developers.google.com/apis/library)
9. Search for Google Drive Api and enable it
10. Finally, run the script to generate **token.pickle** file for Google Drive:
```
pip3 install google-api-python-client google-auth-httplib2 google-auth-oauthlib
python3 generate_drive_token.py
```
------

## Bot Screenshot: 

<img src="./screenshot.png" alt="button menu example">

-----