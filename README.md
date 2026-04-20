
<div align="center">

# 🤖 rcmltb

### **Rclone Mirror-Leech Telegram Bot**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Pyrogram](https://img.shields.io/badge/Pyrogram-Async-blue.svg)](https://docs.pyrogram.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-GPL--3.0-green.svg)](LICENSE)

An **asynchronous** Telegram bot for transferring files between cloud storage services and Telegram.

**Mirror** → Cloud | **Leech** → Telegram | **Clone** → Cloud to Cloud

[Features](#-features) • [Commands](#-bot-commands) • [Deployment](#-deployment) • [Configuration](#%EF%B8%8F-configuration)

</div>

---

> ⚠️ **Stability Notice**: The project is currently in a large refactor phase. During this period, behavior may be unstable and breaking changes can happen between updates until the refactor is completed.

---

> 💡 **Fork Notice**: Originally based on [mirror-leech-telegram-bot](https://github.com/anasty17/mirror-leech-telegram-bot) with enhanced **Rclone** support and additional features. The base repository has since added its own rclone implementation.

---

## 🌟 Features

### ☁️ Rclone
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

### 🔧 Core Features
| Feature | Description |
|---------|-------------|
| **Queue System** | Advanced queuing with `QUEUE_ALL`, `QUEUE_DOWNLOAD`, `QUEUE_UPLOAD` limits |
| **Private Channels** | Mirror/leech from private Telegram channels |
| **Upload Templates** | Dynamic paths with variables like `{username}`, `{date}`, `{category}` |
| **MediaInfo** | Detailed media file analysis with `/mediainfo` |
| **Screenshots** | User-configurable screenshot generation |
| **Name Substitution** | Pattern-based filename renaming (`old::new`) |
| **Force Start** | Bypass queue for urgent tasks |
| **JDownloader** | Integration with JDownloader |
| **Status Filters** | Per-chat pagination with DL/UL/Seed/Clone/Queue filters |

### 📦 Additional Features
- Send rclone config file from bot
- Renaming menu for Telegram files
- Index support (rclone index for all remotes)
- Search TMDB titles
- Mirror and Leech files in batch from Telegram private/restricted channels
- Mirror and Leech links in batch from `.txt` file
- Extract and zip link/file from Telegram to cloud
- Extract and zip folder/file from cloud to Telegram
- Mirror to local host (no cloud upload)
- Refactored to use Pyrogram with asyncio
- Docker-based image (Ubuntu)
- Compatible with Linux `amd64`, `arm64/v8`, `arm/v7`

---

## 🤖 Bot Commands

Set these commands through [@BotFather](https://t.me/BotFather).

### 📥 Mirror Commands
| Command | Description |
|---------|-------------|
| `mirror` or `/m` | Mirror to selected cloud |
| `mirror_batch` or `/mb` | Mirror Telegram files/links in batch |
| `mirror_select` or `/ms` | Select a fixed cloud/folder for mirror |
| `jdmirror` or `/jm` | Mirror via JDownloader |
| `ytdl` or `/y` | Mirror yt-dlp supported link |
| `ytdleech` or `/yl` | Leech yt-dlp supported link |
| `jdleech` or `/jl` | Leech via JDownloader |

### 📤 Leech Commands
| Command | Description |
|---------|-------------|
| `leech` or `/l` | Leech from cloud/link to Telegram |
| `leech_batch` or `/lb` | Leech Telegram files/links in batch |

### ☁️ Cloud Management
| Command | Description |
|---------|-------------|
| `copy` | Copy from cloud to cloud |
| `clone` | Clone Google Drive link file/folder |
| `count` | Count file/folder from Google Drive link |
| `rcfm` | Rclone File Manager |
| `sync` | Sync two clouds |
| `bisync` | Bidirectional cloud sync |
| `cleanup` | Clean cloud trash |
| `storage` | Cloud storage details |
| `serve` | Serve cloud as web index |

### ⚙️ System & Tools
| Command | Description |
|---------|-------------|
| `files` or `/bf` | Bot configuration files |
| `mediainfo` | Get detailed media file information |
| `cancel` | Cancel a task |
| `force_start` or `/fs` | Force start a queued task |
| `usetting` | User settings |
| `bsetting` | Owner settings |
| `tmdb` | Search titles |
| `torrsch` | Search for torrents |
| `cancel_all` | Cancel all tasks |

### 📊 Status & Info
| Command | Description |
|---------|-------------|
| `status` | Status message of tasks |
| `stats` | Bot statistics |
| `log` | Bot log |
| `ip` | Show IP address |
| `ping` | Ping bot |

### 🔧 Admin Commands
| Command | Description |
|---------|-------------|
| `shell` | Run commands in shell |
| `exec` | Run Python code |
| `restart` | Restart bot |

---

## 🚀 Deployment

### 1️⃣ Installing Requirements

**Clone the repository:**
```bash
git clone https://github.com/Sam-Max/rcmltb rcmltb/ && cd rcmltb
```

**For Debian-based distros:**
```bash
sudo apt install python3 python3-pip
```

Install Docker by following the [official Docker docs](https://docs.docker.com/engine/install/debian/)

**For Arch and derivatives:**
```bash
sudo pacman -S docker python
```

**Install dependencies for setup scripts:**
```bash
pip3 install -r requirements-cli.txt
```

---

### 2️⃣ Configuration

Copy the sample config file:
```bash
cp sample_config.env config.env
```

> **NOTE**: All values must be filled between quotes, even if it's `Int`, `Bool`, or `List`.

#### Required Configuration

| Variable | Description | Type |
|----------|-------------|------|
| `TELEGRAM_API_ID` | Get from https://my.telegram.org | `Int` |
| `TELEGRAM_API_HASH` | Get from https://my.telegram.org | `Str` |
| `BOT_TOKEN` | Telegram Bot Token from [@BotFather](https://t.me/BotFather) | `Str` |
| `OWNER_ID` | Your Telegram User ID (not username) | `Int` |

---

#### Optional Configuration

##### General Settings
| Variable | Description | Type |
|----------|-------------|------|
| `DOWNLOAD_DIR` | Path to local downloads folder | `Str` |
| `SUDO_USERS` | User IDs with sudo permission (space-separated) | `Str` |
| `ALLOWED_CHATS` | Allowed chat IDs (space-separated) | `Str` |
| `AUTO_MIRROR` | Auto mirror files sent to bot. Default: `False` | `Bool` |
| `DATABASE_URL` | MongoDB connection string | `Str` |
| `CMD_INDEX` | Index number added to commands | `Str` |
| `GD_INDEX_URL` | Google Drive Index URL | `Str` |
| `VIEW_LINK` | View link button instead of direct download. Default: `False` | `Bool` |
| `STATUS_LIMIT` | Number of tasks shown in status | `Int` |
| `LOCAL_MIRROR` | Keep files on host. Default: `False` | `Bool` |
| `TORRENT_TIMEOUT` | Timeout for dead torrents (qBittorrent) | `Int` |
| `AUTO_DELETE_MESSAGE_DURATION` | Auto-delete messages after X seconds. `-1` to disable | `Int` |
| `TMDB_API_KEY` | TMDB API key ([Get here](https://www.themoviedb.org/settings/api)) | `Str` |
| `TMDB_LANGUAGE` | TMDB search language. Default: `en` | `Str` |
| `PARALLEL_TASKS` | Number of parallel tasks for queue | `Int` |

##### Update Settings
| Variable | Description | Type |
|----------|-------------|------|
| `UPSTREAM_REPO` | GitHub repository link (supports private repos with token) | `Str` |
| `UPSTREAM_BRANCH` | Upstream branch. Default: `master` | `Str` |

> **NOTE**: If docker or requirements change, rebuild the image for changes to apply.

---

##### ☁️ Rclone Settings
| Variable | Description | Type |
|----------|-------------|------|
| `DEFAULT_OWNER_REMOTE` | Default remote for owner | `Str` |
| `DEFAULT_GLOBAL_REMOTE` | Default remote from global config | `Str` |
| `MULTI_RCLONE_CONFIG` | Allow each user their own config. Default: `False` | `Bool` |
| `REMOTE_SELECTION` | Select cloud each mirror. Default: `False` | `Bool` |
| `MULTI_REMOTE_UP` | Upload to multiple clouds. Default: `False` | `Bool` |
| `USE_SERVICE_ACCOUNTS` | Enable Service Accounts. Default: `False` | `Bool` |
| `SERVICE_ACCOUNTS_REMOTE` | Shared drive remote name | `Str` |
| `SERVER_SIDE` | Enable server-side copy. Default: `False` | `Bool` |
| `RCLONE_COPY_FLAGS` | Copy flags (key:value,key) | `Str` |
| `RCLONE_UPLOAD_FLAGS` | Upload flags | `Str` |
| `RCLONE_DOWNLOAD_FLAGS` | Download flags | `Str` |
| `RC_INDEX_URL` | Public IP/domain for index | `Str` |
| `RC_INDEX_PORT` | Index port. Default: `8080` | `Str` |
| `RC_INDEX_USER` | Index user. Default: `admin` | `Str` |
| `RC_INDEX_PASS` | Index password. Default: `admin` | `Str` |
| `UPLOAD_PATH_TEMPLATE` | Dynamic path template (e.g., `"remote:/{username}/{category}/{date}/"`) | `Str` |

**Template Variables:** `{username}`, `{user_id}`, `{date}`, `{year}`, `{month}`, `{day}`, `{category}`, `{task_type}`

---

##### 📁 Google Drive Settings
| Variable | Description | Type |
|----------|-------------|------|
| `GDRIVE_FOLDER_ID` | Folder/TeamDrive ID or `root` | `Str` |
| `IS_TEAM_DRIVE` | Set `True` if TeamDrive | `Bool` |
| `EXTENSION_FILTER` | Excluded file extensions (space-separated) | `Str` |

> **Note**: Add `token.pickle` to root for cloning. Use `/files` command to add via bot.

---

##### 📤 Leech Settings
| Variable | Description | Type |
|----------|-------------|------|
| `LEECH_SPLIT_SIZE` | Upload limit (2GB non-premium, 4GB premium) | `Int` |
| `EQUAL_SPLITS` | Split into equal parts. Default: `False` | `Bool` |
| `USER_SESSION_STRING` | Pyrogram session string ([Generate](#session-generation)) | `Str` |
| `LEECH_LOG` | Chat ID(s) for uploads (space-separated, add `-100` prefix) | `Str` |
| `BOT_PM` | Send files to user's PM. Default: `False` | `Bool` |
| `NAME_SUBSTITUTE` | Filename substitution pattern (`old::new\|old2::new2`) | `Str` |

---

##### ☁️ MEGA Settings
| Variable | Description | Type |
|----------|-------------|------|
| `MEGA_EMAIL` | MEGA account email | `Str` |
| `MEGA_PASSWORD` | MEGA account password | `Str` |

---

##### ⬇️ JDownloader Settings
| Variable | Description | Type |
|----------|-------------|------|
| `JD_EMAIL` | JDownloader account email | `Str` |
| `JD_PASSWORD` | JDownloader account password | `Str` |

---

##### 📊 Queue System Settings
| Variable | Description | Type |
|----------|-------------|------|
| `QUEUE_ALL` | Max total concurrent tasks (`0` = unlimited) | `Int` |
| `QUEUE_DOWNLOAD` | Max concurrent downloads (`0` = unlimited) | `Int` |
| `QUEUE_UPLOAD` | Max concurrent uploads (`0` = unlimited) | `Int` |

---

##### 🌐 qBittorrent/Aria2c Settings
| Variable | Description | Type |
|----------|-------------|------|
| `QB_BASE_URL` | Bot URL for qBittorrent web selection | `Str` |
| `QB_SERVER_PORT` | Port. Default: `80` | `Int` |
| `WEB_PINCODE` | Require pincode for torrent selection. Default: `False` | `Bool` |

> **qBittorrent Note**: For RAM issues, limit `MaxConnecs`, decrease `AsyncIOThreadsCount`, and set `DiskWriteCacheSize` to 32.

---

##### 🔍 Torrent Search Settings
| Variable | Description | Type |
|----------|-------------|------|
| `SEARCH_API_LINK` | Torrent search API ([Deploy](https://github.com/Ryuk-me/Torrent-Api-py)) | `Str` |
| `SEARCH_LIMIT` | Results per site. Default: `0` | `Int` |
| `SEARCH_PLUGINS` | qBittorrent search plugin URLs | `List` |

---

### 3️⃣ Deploying with Docker

**Build Docker image:**
```bash
sudo docker build . -t rcmltb
```

**Run the image:**
```bash
sudo docker run -p 80:80 -p 8080:8080 rcmltb
```

**Stop container:**
```bash
sudo docker ps
sudo docker stop <container_id>
```

**Clear container:**
```bash
sudo docker container prune
```

**Delete images:**
```bash
sudo docker image prune -a
```

---

### 4️⃣ Deploying with Docker Compose

> **NOTE**: Change ports in `docker-compose.yml` if not using 80 (torrents) or 8080 (rclone).

**Install docker-compose:**
```bash
sudo apt install docker-compose
```

**Build and run:**
```bash
sudo docker-compose up
```

**After editing files:**
```bash
sudo docker-compose up --build
```

**Stop/Start:**
```bash
sudo docker-compose stop
sudo docker-compose start
```

---

## 🔐 Session Generation

To generate `USER_SESSION_STRING`:

```bash
python3 session_generator.py
```

Run this on your PC from the repository folder.

---

## 🗄️ MongoDB Setup

### Local MongoDB with Docker Compose (No Auth)

`docker-compose.yml` includes a local `mongo` service with persistent storage.

1. Set `DATABASE_URL` in `config.env`:

```env
DATABASE_URL="mongodb://mongo:27017/rcmltb"
```

2. Start services:

```bash
docker compose up -d
```

3. Verify both containers:

```bash
docker compose ps
```

MongoDB data persists in the `mongo_data` volume.

### MongoDB Atlas (Cloud)

1. Go to [mongodb.com](https://mongodb.com/) and sign up
2. Create a Shared Cluster (Free)
3. Add `username` and `password`, click `Add my current IP Address`
4. Click `Connect` → `Connect your application`
5. Choose Driver: **Python**, Version: **3.6 or later**
6. Copy the connection string, replace `<password>` with your user's password
7. Go to `Network Access`, click Edit → `Allow access from anywhere` → Confirm

---

## ☁️ Rclone Configuration

**Video Tutorial:** [YouTube Guide](https://www.youtube.com/watch?v=Sp9lG_BYlSg)

### Quick Tips:
- Add at least two accounts in `rclone.conf` for cloud-to-cloud copy
- Android users: Use [RCX app](https://play.google.com/store/apps/details?id=io.github.x0b.rcx)

### Supported Providers:
1Fichier, Amazon Drive, Amazon S3, Backblaze B2, Box, Ceph, DigitalOcean Spaces, Dreamhost, **Dropbox**, Enterprise File Fabric, FTP, GetSky, Google Cloud Storage, **Google Drive**, Google Photos, HDFS, HTTP, Hubic, IBM COS S3, Koofr, Mail.ru Cloud, **Mega**, Microsoft Azure Blob Storage, **Microsoft OneDrive**, **Nextcloud**, OVH, OpenDrive, Oracle Cloud Storage, ownCloud, pCloud, premiumize.me, put.io, Scaleway, Seafile, SFTP, **WebDAV**, Yandex Disk, and more.

[View all providers](https://rclone.org/#providers)

---

## 🔑 Google OAuth Setup

> **Requirements**: OS with a browser. Windows users need Python3 and pip.

1. Visit [Google Cloud Console](https://console.developers.google.com/apis/credentials)
2. Go to OAuth Consent tab, fill it, save
3. Credentials tab → Create Credentials → OAuth Client ID
4. Choose **Desktop** and Create
5. Publish your OAuth consent to prevent token expiry
6. Download credentials, move to bot root, rename to `credentials.json`
7. Visit [Google API Library](https://console.developers.google.com/apis/library)
8. Search and enable **Google Drive API**
9. Generate token:

```bash
pip3 install google-api-python-client google-auth-httplib2 google-auth-oauthlib
python3 generate_drive_token.py
```

---

## 🌱 Bittorrent Seeding

Using `-d` alone uses global options for aria2c/qBittorrent.

### qBittorrent Global Options:
- `GlobalMaxRatio` and `GlobalMaxSeedingMinutes` in `qbittorrent.conf`
- `-1` = no limit
- **Don't change `MaxRatioAction`**

---

## 🔧 Service Accounts (Google Drive)

> Set `USE_SERVICE_ACCOUNTS="True"` to enable. Recommended for Team Drive only.

### Limits
- 1 Service Account = ~750 GB/day
- 1 Project = 100 Service Accounts = ~75 TB/day

### Generate Service Accounts

**List projects:**
```bash
python3 gen_sa_accounts.py --list-projects
```

**Enable services:**
```bash
python3 gen_sa_accounts.py --enable-services $PROJECTID
```

**Create Service Accounts:**
```bash
python3 gen_sa_accounts.py --create-sas $PROJECTID
```

**Download keys:**
```bash
python3 gen_sa_accounts.py --download-keys $PROJECTID
```

**Quick setup (new project):**
```bash
python3 gen_sa_accounts.py --quick-setup 1 --new-only
```

### Add to Team Drive

**Method 1: Via Google Group (Recommended)**
```bash
cd accounts
# Extract emails
grep -oPh '"client_email": "\K[^"]+' *.json > emails.txt
cd ..
# Add emails.txt to Google Group, then add Group to Team Drive as Manager
```

**Method 2: Direct add:**
```bash
python3 add_to_team_drive.py -d SharedTeamDriveSrcID
```

---

## 🔐 .netrc Authentication

For yt-dlp premium accounts or protected Index Links, create `.netrc`:

```
machine host login username password my_password
```

**Example:**
```
machine instagram login user.name password mypassword
```

**Notes:**
- **Instagram**: Must login even for public posts; confirm login from new IP
- **YouTube**: Use [cookies.txt](https://github.com/ytdl-org/youtube-dl#how-do-i-pass-cookies-to-youtube-dl) instead

**Aria2c index link example:**
```
machine example.workers.dev password index_password
```

---

## ☕ Support

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/sammax09)

---
