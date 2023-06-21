
An Rclone Mirror-Leech Telegram Bot to transfer to and from many clouds. Based on [mirror-leech-telegram-bot](https://github.com/anasty17/mirror-leech-telegram-bot) with rclone support added, and other features and changes from base code.


**NOTE**: Base repository added recently its own rclone implementation. 


## Features:

### Rclone
- Copy file/folder from cloud to cloud
- Leech file/folder from cloud to Telegram
- Mirror Link/Torrent/Magnets/Mega/Telegram-Files to cloud
- Mirror from Telegram to multiple clouds at the same time
- Telegram Navigation Button Menus to interact with cloud
- File Manager: size, mkdir, delete, dedupe and rename
- Service Accounts support with automatic switching
- Create cloud index as http or webdav webserver
- Sync between clouds (not folders)
- Search files on cloud
- Clean cloud trash
- View cloud storage info 

### Others
- Send rclone config file from bot
- Renaming menu for Telegram files
- Index support (rclone index for all remotes)
- Search tmdb titles
- Mirror and Leech files in batch from Telegram private/restricted channels
- Mirror and Leech links in batch from .txt file
- Extract and zip link/file from Telegram to cloud
- Extract and zip folder/file from cloud to Telegram
- Mirror to local host (no cloud upload)
- Queue system for Telegram downloads
- Refactor of the whole code to use only pyrogram with asyncio
- Docker based image based on ubuntu
- Compatible with linux `amd64, arm64/v8, arm/v7`
## Commands for bot(set through @BotFather)

```
mirror - or /m Mirror to selected cloud 
mirrorbatch - or /mb Mirror Telegram files/links in batch to cloud
mirrorselect - or /ms Select a fixed cloud/folder for mirror 
leech - or /l Leech from cloud/link to Telegram
leechbatch - or /lb Leech Telegram files/links in batch to Telegram 
ytdl - or /y Mirror ytdlp supported link
ytdlleech - or /yl Leech yt-dlp supported link
botfiles - or /bf Bot configuration files
myfiles - Rclone File Manager
copy - Copy from cloud to cloud
clone - Clone gdrive link file/folder 
count - count file/folder fom gdrive link
usetting - User settings
ownsetting - Owner settings
rss - Rss feed
tmdb - Search titles
cleanup - Clean cloud trash
cancelall - Cancel all tasks
storage - Cloud details
serve - Serve cloud as web index 
sync - Sync two clouds
search - Search for torrents
status - Status message of tasks
stats - Bot stats
shell - Run cmds in shell
log - Bot log
ip - show ip
ping - Ping bot
restart - Restart bot
```

## How to deploy?

1. **Installing requirements**

- Clone repo:

```
git clone https://github.com/Sam-Max/rcmltb rcmltb/ && cd rcmltb
```

- For Debian based distros
```
sudo apt install python3 python3-pip
```

Install Docker by following the [official Docker docs](https://docs.docker.com/engine/install/debian/)

- For Arch and it's derivatives:

```
sudo pacman -S docker python
```

- Install dependencies for running setup scripts:

```
pip3 install -r requirements-cli.txt
```

2. **Set up config file**

- cp config_sample.env config.env 

- Fill up the fields on the config.env: **NOTE**: All values must be filled between quotes, even if it's `Int`, `Bool` or `List`.

**1. Mandatory Fields**

  - `API_ID`: get this from https://my.telegram.org. `Int`
  - `API_HASH`: get this from https://my.telegram.org. `Str`
  - `BOT_TOKEN`: The Telegram Bot Token (get from @BotFather). `Str`
  - `OWNER_ID`: your Telegram User ID (not username) of the owner of the bot. `Int`

**2. Optional Fields**

  - `DOWNLOAD_DIR`: The path to the local folder where the downloads will go. `Str`
  - `SUDO_USERS`: Fill user_id of users whom you want to give sudo permission separated by spaces. `Str`
  - `ALLOWED_CHATS`: list of IDs of allowed chats who can use this bot separated by spaces `Str`
  - `AUTO_MIRROR`: For auto mirroring files sent to the bot. **NOTE**: If you add bot to group(not channel), you can also use this feature. Default is `False`. `Bool`
  - `DATABASE_URL`: Your Mongo Database URL (Connection string). Data will be saved in Database (auth and sudo users, owner and user setting, etc). **NOTE**: You can always edit all settings saved in database from mongodb site -> (browse collections). `Str`
  - `CMD_INDEX`: index number that will be added at the end of all commands. `Str`
  - `GD_INDEX_URL`: Refer to https://gitlab.com/ParveenBhadooOfficial/Google-Drive-Index. `Str`
  - `VIEW_LINK`: View Link button to open file Google Drive Index Link in browser instead of direct download link, you can figure out if it's compatible with your Index code or not, open any video from you Index and check if its URL ends with `?a=view`. Compatible with [BhadooIndex](https://gitlab.com/ParveenBhadooOfficial/Google-Drive-Index) Code. Default is `False`. `Bool`
  - `STATUS_LIMIT`: No. of tasks shown in status message with buttons.`Int`
  - `LOCAL_MIRROR`= set to `True` for enabling files to remain on host. Default to False.
  - `TORRENT_TIMEOUT`: Timeout of dead torrents downloading with qBittorrent
  - `AUTO_DELETE_MESSAGE_DURATION`: Interval of time (in seconds), after which the bot deletes it's message and command message. Set to `-1` to disable auto message deletion. `Int`
  - `TMDB_API_KEY`: your tmdb API key. [Click here](https://www.themoviedb.org/settings/api) 
  - `TMDB_LANGUAGE`: tmdb search language. Default `en`.
  - `PARALLEL_TASKS`: Number of parallel tasks for queue system. `Int`

  ### Update

  - `UPSTREAM_REPO`: Your github repository link. If your repo is private, add your github repo link with format: `https://username:{githubtoken}@github.com/{username}/{reponame}`: get token from [Github settings](https://github.com/settings/tokens). `Str`. With this field you can update your bot from public/private repository on each restart. 
  - `UPSTREAM_BRANCH`: Upstream branch for update. Default is `master`. `Str`
  **NOTE**: If any change in docker or requirements you will need to deploy/build again with updated repo for changes to apply. DON'T delete .gitignore file.

  ### Rclone
  
  - `DEFAULT_OWNER_REMOTE`: to set default remote from your rclone config for mirroring. (only for owner). `Str`
  - `DEFAULT_GLOBAL_REMOTE`: to set default remote from global rclone config for mirroring. Use this when `MULTI_RCLONE_CONFIG` is `False`. `Str`
  - `MULTI_RCLONE_CONFIG`: set to `True` for allowing each user to use their own rclone config. Default to False. `Bool` 
  - `REMOTE_SELECTION`: set to `True` to activate selection of cloud server each time using mirror command. Default to `False`. `Bool`
  - `MULTI_REMOTE_UP`= set to `True` for allowing upload to multiple clouds servers at the same time. `Bool`. (only for owner)
  - `USE_SERVICE_ACCOUNTS`: set to `True` for enabling SA for rclone copy. Default to False. `Bool`.
  - `SERVICE_ACCOUNTS_REMOTE`= name of the shared drive remote from your rclone config file. `Str`. **Note**: remote must have `team_drive` field with `id` in order to work. `Str`
  - `SERVER_SIDE`= set to `True` for enabling rclone server side copy. Default to False. **NOTE**: if you get errors while copy set this to `False`. `Bool`
  - `RCLONE_COPY_FLAGS` = key:value,key. All Flags: [RcloneFlags](https://rclone.org/flags/).`Str`
  - `RCLONE_UPLOAD_FLAGS` = key:value,key. `Str`
  - `RCLONE_DOWNLOAD_FLAGS` = key:value,key.`Str`
  - `RC_INDEX_URL`: Ip (public/domain) where bot is running for rclone index. Format of URL should be http://myip, where myip is the IP/Domain(public). `Str`
  - `RC_INDEX_PORT`: Port to use. Default to `8080`. `Str`
  - `RC_INDEX_USER`: Custom user. Default to `admin`. `Str`
  - `RC_INDEX_PASS`: Custom password. Default to `admin`. `Str`

  ### GDrive Tools

  - `GDRIVE_FOLDER_ID`: Folder/TeamDrive ID of the Google Drive Folder or `root` to which you want to clone. Required for `Google Drive`. `Int`
  - `IS_TEAM_DRIVE`: Set `True` if TeamDrive. Default is `False`. `Bool`
  - `EXTENSION_FILTER`: File extensions that won't clone. Separate them by space. `Str`
  **Notes**: Must add **token.pickle** file directly to root for cloning to work. You can use /botfiles command to add from bot.
   
  ### Leech

  - `LEECH_SPLIT_SIZE`: Telegram upload limit in bytes, to automatically slice the file bigger that this size into small parts to upload to Telegram. Default is `2GB` for non premium account or `4GB` if your account is premium. `Int`
  - `EQUAL_SPLITS`: Split files larger than **LEECH_SPLIT_SIZE** into equal parts size (not working with zip cmd). Default is `False`. `Bool`
  - `USER_SESSION_STRING`: Pyrogram session string for batch commands and for telegram premium upload. To generate string session use this command `python3 session_generator.py` on command line on your pc from repository folder. **NOTE**: When using string session, you have to use with `LEECH_LOG`. You can also use batch commands without string session, but you can't save messages from private/restricted telegram channels. `Str`
  - `LEECH_LOG`: Chat ID. Upload files to specific chat/chats. Add chats separated by spaces. `Str` **NOTE**: Only available for superGroup/channel. Add `-100` before channel/supergroup id. Add bot in that channel/group as admin if using without string session.
  - `BOT_PM`: set to `True` if you want to send leeched files in user's PM. Default to False. `Bool`

  ### MEGA

  - `MEGA_EMAIL`: E-Mail used to sign up on mega.nz for using premium account.`Str`
  - `MEGA_PASSWORD`: Password for mega.nz account.`Str`

  ### RSS

  - `RSS_DELAY`: Time in seconds for rss refresh interval. Default is `900` in sec. `Int`
  - `RSS_CHAT_ID`: Chat ID where rss links will be sent. If you want message to be sent to the channel then add channel id. Add `-100` before channel id. `Int`
  - **RSS NOTE**: `RSS_CHAT_ID` is required, otherwise monitor will not work. You must use `USER_STRING_SESSION` --OR-- *CHANNEL*. If using channel then bot should be added in both channel and group(linked to channel) and `RSS_CHAT_ID` is the channel id, so messages sent by the bot to channel will be forwarded to group. Otherwise with `USER_STRING_SESSION` add group id for `RSS_CHAT_ID`. If `DATABASE_URL` not added you will miss the feeds while bot offline.    

  ### qBittorrent/Aria2c

  - `QB_BASE_URL`: Valid BASE URL where the bot is deployed to use qbittorrent web selection and local mirror. Format of URL should be http://myip, where myip is the IP/Domain(public). If you have chosen port other than 80 so write it in this format http://myip:port (http and not https).`Str`
  - `QB_SERVER_PORT`: Port. Default to `80`. `Int`
  - `WEB_PINCODE`: If empty or False means no pincode required while torrent file web selection. Bool
  Qbittorrent NOTE: If your facing ram exceeded issue then set limit for MaxConnecs, decrease AsyncIOThreadsCount in qbittorrent config and set limit of DiskWriteCacheSize to 32.`Int`

  ### Torrent Search

  - `SEARCH_API_LINK`: Search api app link. Get your api from deploying this [repository](https://github.com/Ryuk-me/Torrent-Api-py). `Str`
  - `SEARCH_LIMIT`: Search limit for search api, limit for each site. Default is zero. `Int`
  - `SEARCH_PLUGINS`: List of qBittorrent search plugins (github raw links). Add/Delete plugins as you wish. Main Source: [qBittorrent Search Plugins (Official/Unofficial)](https://github.com/qbittorrent/search-plugins/wiki/Unofficial-search-plugins).`List`

3. **Deploying with Docker**

- Build Docker image:

```
sudo docker build . -t rcmltb 
```

- Run the image:

```
sudo docker run -p 80:80 -p 8080:8080 rcmltb
```

- To stop the container:

```
  sudo docker ps
```

```
  sudo docker stop id
```
- To clear the container:

```
  sudo docker container prune
```

- To delete the images:

```
  sudo docker image prune -a
```

4. **Deploying using docker-compose**

**NOTE**: If you want to use port other than 80 (torrent file selection) or 8080 (rclone serve), change it in docker-compose.yml

- Install docker-compose

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

1. Go to `https://mongodb.com/` and sign-up.
2. Create Shared Cluster (Free).
4. Add `username` and `password` for your db and click on `Add my current IP Address`.
6. Click on `Connect`, and then press on `Connect your application`.
7. Choose `Driver` **python** and `version` **3.6 or later**.
8. Copy your `connection string` and replace `<password>` with the password of your user, then press close.
9. Go to `Network Access` tab, click on edit button and finally click `Allow access from anywhere` and confirm.

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

## Bittorrent Seed

- Using `-d` argument alone will lead to use global options for aria2c or qbittorrent.

## Qbittorrent

- Global options: `GlobalMaxRatio` and `GlobalMaxSeedingMinutes` in qbittorrent.conf, `-1` means no limit, but you can cancel manually.
  - **NOTE**: Don't change `MaxRatioAction`.


## Using Service Accounts to avoid user rate limit [For Google Drive Remotes]

> For Service Account to work, you must set `USE_SERVICE_ACCOUNTS`= "True" in config file or environment variables.
>**NOTE**: Using Service Accounts is only recommended for Team Drive.

### 1. Generate Service Accounts. [What is Service Account?](https://cloud.google.com/iam/docs/service-accounts)

**Warning**: Abuse of this feature is not the aim of this project and we do **NOT** recommend that you make a lot of projects, just one project and 100 SAs allow you plenty of use, its also possible that over abuse might get your projects banned by Google.

>**NOTE**: If you have created SAs in past from this script, you can also just re download the keys by running:
```
python3 gen_sa_accounts.py --download-keys $PROJECTID
```
>**NOTE:** 1 Service Account can copy around 750 GB a day, 1 project can make 100 Service Accounts so you can copy 75 TB a day.

#### Two methods to create service accounts
Choose one of these methods

##### 1. Create Service Accounts in existed Project (Recommended Method)

- List your projects ids

```
python3 gen_sa_accounts.py --list-projects
```

- Enable services automatically by this command

```
python3 gen_sa_accounts.py --enable-services $PROJECTID
```

- Create Sevice Accounts to current project

```
python3 gen_sa_accounts.py --create-sas $PROJECTID
```

- Download Sevice Accounts as accounts folder

```
python3 gen_sa_accounts.py --download-keys $PROJECTID
```
##### 2. Create Service Accounts in New Project
```
python3 gen_sa_accounts.py --quick-setup 1 --new-only
```
A folder named accounts will be created which will contain keys for the Service Accounts.

### 2. Add Service Accounts

#### Two methods to add service accounts
Choose one of these methods

##### 1. Add Them To Google Group then to Team Drive (Recommended)
- Mount accounts folder

```
cd accounts
```

- Grab emails form all accounts to emails.txt file that would be created in accounts folder
- `For Windows using PowerShell`

```
$emails = Get-ChildItem .\**.json |Get-Content -Raw |ConvertFrom-Json |Select -ExpandProperty client_email >>emails.txt
```

- `For Linux`

```
grep -oPh '"client_email": "\K[^"]+' *.json > emails.txt
```

- Unmount acounts folder

```
cd ..
```
Then add emails from emails.txt to Google Group, after that add this Google Group to your Shared Drive and promote it to manager and delete email.txt file from accounts folder

##### 2. Add Them To Team Drive Directly
- Run:

```
python3 add_to_team_drive.py -d SharedTeamDriveSrcID
```
------

## Yt-dlp and Aria2c Authentication Using .netrc File
For using your premium accounts in yt-dlp or for protected Index Links, create .netrc and not netrc, this file will be hidden, so view hidden files to edit it after creation. Use following format on file: 

Format:

```
machine host login username password my_password
```

Example:

```
machine instagram login user.name password mypassword
```

**Instagram Note**: You must login even if you want to download public posts and after first try you must confirm that this was you logged in from different ip(you can confirm from phone app).

**Youtube Note**: For `youtube` authentication use [cookies.txt](https://github.com/ytdl-org/youtube-dl#how-do-i-pass-cookies-to-youtube-dl) file.

Using Aria2c you can also use built in feature from bot with or without username. Here example for index link without username.

```
machine example.workers.dev password index_password
```

Where host is the name of extractor (eg. instagram, Twitch). Multiple accounts of different hosts can be added each separated by a new line.

-----

## Donations

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/sammax09)

-----

## Bot Screenshot: 

<img src="./screenshot.png" alt="button menu example">

-----