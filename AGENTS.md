# AGENTS.md

This file provides guidance for AI coding agents working in this repository.

## Project Overview

**rcmltb** is an async Python Telegram bot (Rclone Mirror-Leech Telegram Bot) for
transferring files to/from cloud storage (Google Drive, MEGA, local, etc.) and
Telegram. Built on Pyrogram + asyncio. Version 4.6 by Sam-Max.

## Repository Layout

```
bot/
  __init__.py          # Global config, state, DB init, Pyrogram client bootstrap, proxy classes
  __main__.py          # Entry point, main() startup orchestration, bot commands
  conv_pyrogram.py     # Conversation helper for Pyrogram (interactive user input)
  core/
    config_manager.py  # Config class with type conversion, validation, loading
    handlers.py        # Central handler registration (add_handlers())
    telegram_manager.py# TgClient class (bot/user Pyrogram clients)
    startup.py         # load_settings(), load_configurations(), save_settings(), update_variables()
    torrent_manager.py # TorrentManager (Aria2 + qBittorrent management)
    jdownloader_booter.py # JDownloader process management
  modules/             # Bot command handlers (35+ modules)
  helper/
    common.py          # TaskConfig base class
    ext_utils/
      bot_utils.py     # Core utils: setInterval, new_task, run_sync_to_async, get_readable_message, cmd_exec
      batch_helper.py  # Batch processing helpers
      bulk_links.py    # Bulk link extraction from text files
      db_handler.py    # DbManager class (MongoDB CRUD operations)
      exceptions.py    # Custom exceptions (DirectDownloadLinkException, etc.)
      files_utils.py   # File ops: clean_download, split_file, get_document_type, get_mime_type
      help_messages.py # Help text dicts, help_callback, help_command, create_*_help_buttons
      human_format.py  # get_readable_file_size, human_readable_bytes
      links_utils.py   # Link validation: is_url, is_gdrive_link, is_mega_link, is_magnet, etc.
      media_utils.py   # get_detailed_media_info, format_media_info
      menu_utils.py    # Menus enum, rcloneListButtonMaker, rcloneListNextPage
      misc_utils.py    # Mixed utils: arg_parser, bt_selection_buttons, getTaskByGid, apply_name_substitute
      rclone_data_holder.py # get_rclone_data, update_rclone_data (per-task rclone state)
      rclone_utils.py  # Rclone helpers: list_remotes, list_folder, is_gdrive_remote, get_id
      task_manager.py  # check_running_tasks, start_from_queued, stop_duplicate_check
      telegraph_helper.py # Telegraph integration
      template_utils.py   # apply_upload_template (path templating)
    telegram_helper/
      bot_commands.py  # _BotCommands class (all command definitions with aliases)
      button_build.py  # ButtonMaker class (inline keyboard builder)
      filters.py       # CustomFilters: owner_filter, user_filter, chat_filter, sudo_filter
      message_utils.py # sendMessage, sendMarkup, editMessage, sendFile, deleteMessage, etc.
    listeners/
      aria2_listener.py     # Aria2 WebSocket event callbacks
      jdownloader_listener.py # JDownloader event callbacks
      qbit_listener.py      # qBittorrent polling callbacks
      task_listener.py      # TaskListener class (lifecycle hooks for downloads/uploads)
    mirror_leech_utils/
      download_utils/
        aria2_download.py     # add_aria2c_download
        direct_link_generator.py # Direct link extraction (1472 lines, dispatch/router)
        gd_downloader.py      # add_gd_download
        jd_download.py        # add_jd_download
        mega_download.py      # MEGA downloader
        qbit_downloader.py    # add_qb_torrent
        rclone_copy.py        # RcloneCopy class
        rclone_leech.py       # RcloneLeech class
        telegram_downloader.py# TelegramDownloader class
        yt_dlp_helper.py      # YoutubeDLHelper class
      upload_utils/
        rclone_mirror.py      # RcloneMirror class
        telegram_uploader.py  # TelegramUploader class
      status_utils/
        aria_status.py        # Aria2 download/upload status
        clone_status.py       # GDrive clone status
        extract_status.py     # 7z extraction status
        gdrive_status.py      # GDrive upload/download status
        jdownloader_status.py # JDownloader status
        mega_status.py        # MEGA status
        qbit_status.py        # qBittorrent status
        rclone_status.py      # Rclone status
        split_status.py       # File split status
        status_utils.py       # MirrorStatus enum, TaskType enum, progress bar helpers
        sync_status.py        # Rclone sync status
        tg_download_status.py # Telegram download status
        tg_upload_status.py   # Telegram upload status
        yt_dlp_status.py      # YT-DLP status
      gd_utils/
        clone.py              # gdClone class
        count.py              # gdCount class
        download.py           # GDrive downloader
        helper.py             # GDrive helper functions
      debrid_utils/
        debrid_helper.py      # RealDebrid class
qbitweb/
  __init__.py           # qBittorrent web UI server
  nodes.py              # Node definitions
  wserver.py            # Web server for torrent selection
Root scripts:
  add_to_team_drive.py  # Add service accounts to Team Drive
  generate_drive_token.py # Generate Google Drive OAuth token
  gen_sa_accounts.py    # Generate Google service accounts
  session_generator.py  # Generate Pyrogram session strings
  update.py             # Git pull updater
```

## Build, Run & Deploy

### Run the bot

```bash
# Install dependencies
pip3 install -r requirements.txt

# Copy and edit config
cp sample_config.env config.env
# Fill in TELEGRAM_API_ID, TELEGRAM_API_HASH, BOT_TOKEN, OWNER_ID

# Start (runs update.py then starts the bot)
bash start.sh
# Or directly:
python3 -m bot
```

### Docker

```bash
docker-compose up --build -d
# Exposes port 80 (qBittorrent web) and 8080 (rclone serve index)
```

### Heroku

Deploy via the GitHub Actions workflow `.github/workflows/deploy.yml` (manual dispatch).

### No test or lint tooling

This project has **no automated tests, no linter configuration, and no formatter
configuration**. There is no test suite, no pytest/unittest integration, no
flake8/ruff/black/isort/mypy config, and no Makefile. If you add tooling, use
`pip install` and keep it compatible with the existing Dockerfile.

## Code Style Guidelines

### Imports

Group imports in this order, separated by blank lines:

1. **stdlib** (`from asyncio import ...`, `from os import path as ospath`)
2. **third-party** (`from pyrogram import ...`, `from aiohttp import ...`)
3. **local project** (`from bot import ...`, `from bot.modules.xxx import ...`)

Within each group, prefer `from x import y` over `import x`. When the module
name conflicts with a built-in or common name, use an alias:
```python
from os import path as ospath, remove as osremove
from re import match as re_match, search
```

Avoid wildcard imports (`from x import *`).

### Naming

| Element            | Convention       | Example                          |
|--------------------|------------------|----------------------------------|
| Functions/methods  | `snake_case`     | `get_readable_message()`         |
| Variables          | `snake_case`     | `user_id`, `status_dict`         |
| Constants          | `UPPER_SNAKE`    | `DOWNLOAD_DIR`, `TG_MAX_SPLIT_SIZE` |
| Classes            | `PascalCase`     | `TaskListener`, `ButtonMaker`    |
| Exceptions         | PascalCase + `Exception` | `DirectDownloadLinkException` |
| Module-level       | lowercase        | `bot_utils.py`, `message_utils.py` |

### Async Patterns

- All Telegram handlers and I/O-bound functions are `async def`.
- Use `await` for all async calls; never block the event loop.
- Bridge sync code to async with `run_sync_to_async(func, *args)` (from `bot_utils`).
- Bridge async code to sync with `run_async_to_sync(func, *args)` when needed.
- Use `@new_task` decorator to fire-and-forget coroutines.
- Use `setInterval` class for periodic async tasks.
- Use `asyncio.Lock` for shared mutable state (`status_dict_lock`, etc.).

### Error Handling

- Use `try/except Exception as e` with `LOGGER.error(str(e))` for non-fatal errors.
- Pyrogram `FloodWait` errors are handled by sleeping `fw.value * 1.2` then retrying.
- `MessageNotModified` is caught and silently ignored (sleep 1s).
- Custom exceptions live in `bot/helper/ext_utils/exceptions.py` -- extend `Exception`
  with a docstring. `DirectDownloadLinkException` is the most common.
- Bare `except:` (without exception type) appears in legacy code -- prefer
  `except Exception:` when writing new code.

### String Formatting

Use f-strings exclusively:
```python
msg += f"\n<b>Speed:</b> {download.speed()} | <b>ETA:</b> {download.eta()}"
```

For HTML in Telegram messages, use `<b>`, `<code>`, `<a href='...'>` tags. Use
`html.escape()` when embedding user-provided text.

### Type Hints

Type hints are used sparingly. Add them to new function signatures where clarity
helps, but do not add them retroactively to existing code unless asked:
```python
async def sendMessage(text: str, message, reply_markup=None):
def speed_string_to_bytes(size_text: str):
```

## Architecture

### Startup Flow (`bot/__main__.py` -> `main()`)

1. `load_settings()` -- Load config from MongoDB (`db.settings.config`, `db.settings.aria2c`, `db.settings.qbittorrent`, `db.settings.files`)
2. `TgClient.start_bot()` + `TgClient.start_user()` -- Start Pyrogram clients concurrently
3. `load_configurations()` -- Start qbitweb gunicorn, qbittorrent-nox, aria2c, extract accounts.zip
4. `TorrentManager.initiate()` -- Connect to Aria2 (port 6800) and qBittorrent (port 8090)
5. `start_cleanup()` -- Delete old qbit torrents, recreate DOWNLOAD_DIR
6. `update_variables()` -- Populate `user_data` from ALLOWED_CHATS/SUDO_USERS/EXTENSION_FILTER/LEECH_LOG
7. `update_aria2_options()` / `update_qbit_options()` -- Apply saved settings
8. `TorrentManager.aria2_init()` -- Test aria2 connection
9. Create help buttons + init telegraph (concurrent via `gather()`)
10. Initiate search tools + load debrid token
11. Add aria2 callbacks
12. `add_handlers()` -- Register all module handlers
13. Boot JDownloader if configured
14. Handle restart message
15. Set bot commands via `set_bot_commands()`
16. `save_settings()` -- Persist config to MongoDB

### Bot Proxy Pattern (`bot/__init__.py`)

- `_BotProxy` buffers `add_handler()` calls before bot is initialized, then flushes them after `TgClient.start_bot()`
- `_AppProxy` delegates to `TgClient.user` (userbot client)
- This allows modules to register handlers at import time, before the bot client exists

### Global State (`bot/__init__.py`)

| Variable | Purpose |
|----------|---------|
| `status_dict` / `status_dict_lock` | Active tasks keyed by message ID |
| `status_reply_dict` / `status_reply_dict_lock` | Status messages per chat |
| `queued_dl` / `queued_up` | Queued task events |
| `non_queued_dl` / `non_queued_up` | Sets of actively running task UIDs |
| `user_data` | Per-user settings dict (keyed by user_id) |
| `config_dict` | Runtime config (from `Config.get_all()`) |
| `rss_dict` | RSS subscriptions per user |
| `aria2_options` / `qbit_options` | Download engine settings |
| `leech_log` | List of leech log chat IDs |
| `tmdb_titles` | TMDB title cache |
| `remotes_multi` | Multi-remote upload list |

### Handler Registration

Two patterns exist:

**1. Central registration** in `bot/core/handlers.py`:
```python
def add_handlers():
    bot = TgClient.bot
    bot.add_handler(MessageHandler(start, filters=command(BotCommands.StartCommand)))
    # ... imports all modules to trigger their add_handler() calls
```

**2. Module-level registration** at the bottom of each module file:
```python
bot.add_handler(
    MessageHandler(
        handle_mirror,
        filters=command(BotCommands.MirrorCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
bot.add_handler(CallbackQueryHandler(callback_func, filters=regex("^pattern")))
```

Use `CustomFilters.owner_filter`, `sudo_filter`, `user_filter`, or `chat_filter`
to restrict access.

### Filter Chain

```python
filters.command(BotCommands.XXX) & (CustomFilters.user_filter | CustomFilters.chat_filter)
```

| Filter | Description |
|--------|-------------|
| `owner_filter` | Only OWNER_ID |
| `sudo_filter` | OWNER_ID or users in SUDO_USERS |
| `user_filter` | OWNER_ID, auth users, or sudo users (includes chat-level auth) |
| `chat_filter` | Authenticated chats (with optional thread_id filtering) |

### Callback Query Patterns

All callback data uses `^` as delimiter. Common patterns:
- `menu_type^action^user_id` -- e.g., `userset^12345^doc`
- `menu_type^action^param^user_id` -- e.g., `copymenu^remote_origin^gdrive^12345`
- `menu_type^action^param^param^user_id` -- e.g., `torser^12345^1337x^apisearch`
- `menu_type^pages^user_id` -- Pagination placeholder
- `next_type offset is_second_menu back_callback` -- Next page data (space-separated)

For help callbacks, space-separated: `help m Rename`, `help close`, `help_cat download`, `help_cmd download mirror`

### Conversation Pattern

Uses `client.listen.Message(filters, id=filters.user(user_id), timeout=60)` from
`conv_pyrogram.py` for interactive user input with 60-second timeout. Cancel with `/ignore`.

### Queue System (`modules/queue.py`)

- `QueueManager` -- Priority queue with configurable workers
- `QueueItem` -- Dataclass with task, callbacks, priority
- `conditional_queue_add(message, func, *args)` -- If `PARALLEL_TASKS > 0`, queue the task; else run directly
- `add_to_queue(message, task, *args)` -- Add to queue with full/empty handling

### Task Manager (`ext_utils/task_manager.py`)

- `check_running_tasks(listener, state)` -- Check QUEUE_ALL/QUEUE_DOWNLOAD/QUEUE_UPLOAD limits
- `start_dl_from_queued(mid)` / `start_up_from_queued(mid)` -- Release queued tasks
- `start_from_queued()` -- Auto-start queued tasks when slots free up
- `stop_duplicate_check(listener)` -- Check GDrive for existing files

### TaskListener Lifecycle (`listeners/task_listener.py`)

`TaskListener` extends `TaskConfig` and provides lifecycle hooks:
- `onDownloadStart()` -- Called when download begins
- `onDownloadComplete()` -- Post-download: compression, extraction, name substitution, routes to uploader
- `onUploadComplete(link, size, files, folders, mime_type, name, ...)` -- Build result message
- `onDownloadError(error)` -- Clean up, remove from status_dict
- `onUploadError(error)` -- Clean up, remove from status_dict
- `onRcloneCopyComplete(...)` -- Handle rclone copy completion
- `onRcloneSyncComplete(msg)` -- Handle rclone sync completion

## All Modules and Commands

| Module | Commands | Callback Regex | Description |
|--------|----------|----------------|-------------|
| `core/handlers.py` | `start`, `restart`, `ping`, `ip`, `log` | -- | Core handlers (owner/sudo restricted) |
| `mirror_leech.py` | `mirror`/`m`, `leech`/`l`, `jdmirror`/`jm`, `jdleech`/`jl` | `mirrormenu`, `remoteselectmenu` | Core mirror/leech with arg parser |
| `clone.py` | `clone` | -- | Google Drive clone (`-i` for multi) |
| `copy.py` | `copy` | `copymenu`, `next_copy` | Rclone copy (origin -> destination menus) |
| `ytdlp.py` | `ytdl`/`y`, `ytdl_leech`/`yl` | `^ytq` | YT-DLP mirror/leech |
| `status.py` | `status` | `status` | Task status display (per-chat pagination) |
| `cancel.py` | `cancel`, `cancel_all` | `canall` | Cancel single/all tasks |
| `rss.py` | `rss` | `^rss` | RSS feed monitor with scheduler |
| `torr_search.py` | `torrsch` | `^torser` | Torrent search (API + plugins) |
| `owner_settings.py` | `own_setting` | `ownersetmenu` | Owner config settings UI |
| `user_settings.py` | `user_setting` | `userset` | User settings (thumb, yt_opt, split, etc.) |
| `force_start.py` | `force_start`/`fs` | -- | Force start queued tasks (`fd`/`fu` flags) |
| `debrid.py` | `debrid`, `info` | `rd` | Real-Debrid integration |
| `tmdb.py` | `tmdb` | `tmdbsubcat`, `tmdbdetails`, `tmdbnext`, `tdmbsearch` | TMDB movie/TV browse + search |
| `batch.py` | `mirror_batch`/`mb`, `leech_batch`/`lb` | -- | Batch from links or .txt files |
| `sync.py` | `sync` | `syncmenu` | Rclone sync (source -> destination) |
| `bisync.py` | `bisync` | `bisyncmenu` | Rclone bidirectional sync |
| `rcfm.py` | `rcfm` | `myfilesmenu`, `next_myfiles` | Rclone cloud file manager |
| `myfilesset.py` | (internal) | -- | Cloud file ops: delete, rename, mkdir, dedupe, search |
| `mirror_select.py` | `mirror_select`/`ms` | `mirrorselectmenu`, `next_ms` | Destination folder picker |
| `botfiles.py` | `files`/`bf` | `configmenu` | Upload/delete config files |
| `stats.py` | `stats` | -- | Bot/system statistics |
| `serve.py` | `serve` | `servemenu` | Rclone HTTP/WebDAV server |
| `shell.py` | `shell` | -- | Owner-only shell execution |
| `exec.py` | `exec` | -- | Owner-only Python exec |
| `storage.py` | `storage` | `storagemenu` | Rclone `about` storage info |
| `cleanup.py` | `cleanup` | `cleanupmenu` | Rclone trash cleanup |
| `gd_count.py` | `count` | -- | Google Drive file count |
| `pmirror.py` | `pmirror`, `pleech` | -- | Private channel mirror/leech via userbot |
| `mediainfo.py` | `mediainfo` | -- | Media file technical info |
| `torr_select.py` | `sel` | -- | Torrent file selection |
| `queue.py` | (internal) | -- | QueueManager with PARALLEL_TASKS workers |
| `help_messages.py` | `help` | `^help` | Help menu with categories and navigation |

## Configuration & Global State

### Required Config
- `TELEGRAM_API_ID` (int)
- `TELEGRAM_API_HASH` (str)
- `BOT_TOKEN` (str)
- `OWNER_ID` (int)

### All Config Options (`bot/core/config_manager.py`)

| Config Key | Type | Default | Description |
|-----------|------|---------|-------------|
| `AS_DOCUMENT` | bool | False | Leech files as document |
| `ALLOWED_CHATS` | str | "" | Space-separated chat IDs |
| `AUTO_DELETE_MESSAGE_DURATION` | int | 30 | Auto-delete message seconds |
| `AUTO_MIRROR` | bool | False | Auto-mirror all media |
| `BOT_PM` | bool | False | Send results in PM |
| `CMD_INDEX` | str | "" | Command suffix |
| `DATABASE_URL` | str | "" | MongoDB connection string |
| `DEFAULT_OWNER_REMOTE` | str | "" | Default rclone remote for owner |
| `DEFAULT_GLOBAL_REMOTE` | str | "" | Default global remote |
| `DOWNLOAD_DIR` | str | "/usr/src/app/downloads/" | Download directory |
| `EQUAL_SPLITS` | bool | False | Equal-sized leech splits |
| `EXTENSION_FILTER` | str | "" | Space-separated extensions to exclude |
| `GDRIVE_FOLDER_ID` | str | "" | Default GD folder |
| `GD_INDEX_URL` | str | "" | GD index URL |
| `IS_TEAM_DRIVE` | bool | False | Use Team Drive |
| `LEECH_LOG` | str | "" | Space-separated leech log chat IDs |
| `LEECH_SPLIT_SIZE` | int | 2097152000 | Max leech split size |
| `LOCAL_MIRROR` | bool | False | Skip upload, show local path |
| `MEGA_EMAIL` | str | "" | MEGA account email |
| `MEGA_PASSWORD` | str | "" | MEGA account password |
| `MULTI_RCLONE_CONFIG` | bool | False | Per-user rclone configs |
| `MULTI_REMOTE_UP` | bool | False | Upload to multiple remotes |
| `NO_TASKS_LOGS` | bool | False | Disable task logging |
| `PARALLEL_TASKS` | int | 0 | Max parallel tasks (0=unlimited) |
| `QB_BASE_URL` | str | "" | qBittorrent web UI base URL |
| `QB_SERVER_PORT` | int | 80 | qBittorrent web UI port |
| `RC_INDEX_PASS` | str | "admin" | Rclone index password |
| `RC_INDEX_PORT` | int | 8080 | Rclone index port |
| `RC_INDEX_URL` | str | "" | Rclone index URL |
| `RC_INDEX_USER` | str | "admin" | Rclone index user |
| `RCLONE_COPY_FLAGS` | str | "" | Global rclone copy flags |
| `RCLONE_DOWNLOAD_FLAGS` | str | "" | Global rclone download flags |
| `RCLONE_UPLOAD_FLAGS` | str | "" | Global rclone upload flags |
| `REMOTE_SELECTION` | bool | False | Force remote selection |
| `RSS_CHAT_ID` | int | 0 | RSS feed chat ID |
| `RSS_DELAY` | int | 900 | RSS check interval (seconds) |
| `RSS_SIZE_LIMIT` | int | 0 | Max RSS item size (bytes) |
| `SEARCH_API_LINK` | str | "" | Torrent search API URL |
| `SEARCH_LIMIT` | int | 0 | Search result limit |
| `SEARCH_PLUGINS` | list | [] | qBittorrent search plugins |
| `SERVER_SIDE` | bool | False | Server-side rclone operations |
| `SERVICE_ACCOUNTS_REMOTE` | str | "" | Service accounts remote |
| `STATUS_LIMIT` | int | 10 | Tasks per status page |
| `STATUS_UPDATE_INTERVAL` | int | 10 | Status refresh interval |
| `SUDO_USERS` | str | "" | Space-separated sudo user IDs |
| `TMDB_API_KEY` | str | "" | TMDB API key |
| `TMDB_LANGUAGE` | str | "en" | TMDB language |
| `TORRENT_TIMEOUT` | int | 0 | Torrent stop timeout |
| `UPSTREAM_BRANCH` | str | "master" | Git branch for updates |
| `UPSTREAM_REPO` | str | "" | Git repo for updates |
| `USE_SERVICE_ACCOUNTS` | bool | False | Use GD service accounts |
| `USER_SESSION_STRING` | str | "" | Userbot session string |
| `VIEW_LINK` | bool | False | Show view link for GD |
| `WEB_PINCODE` | bool | False | Require pincode for web selection |
| `YT_DLP_OPTIONS` | dict | {} | Default yt-dlp options |
| `JD_EMAIL` | str | "" | JDownloader email |
| `JD_PASSWORD` | str | "" | JDownloader password |
| `QUEUE_ALL` | int | 0 | Max total queued tasks |
| `QUEUE_DOWNLOAD` | int | 0 | Max queued downloads |
| `QUEUE_UPLOAD` | int | 0 | Max queued uploads |
| `NAME_SUBSTITUTE` | str | "" | Global name substitution pattern |
| `UPLOAD_PATH_TEMPLATE` | str | "" | Global upload path template |

Access config via `config_dict["KEY"]`, not the module-level variables directly
(module vars are set at import time and not updated when DB config changes).

### Database (MongoDB: `rcmltb`)

| Collection | Key | Data |
|-----------|-----|------|
| `settings.config` | `bot_id` | Full `config_dict` |
| `settings.deployConfig` | `bot_id` | Original `config.env` values |
| `settings.aria2c` | `bot_id` | Aria2 global options |
| `settings.qbittorrent` | `bot_id` | qBittorrent preferences |
| `settings.files` | `bot_id` | Binary file data (keys use `__` for `.`) |
| `users` | `user_id` | User settings: thumb, rclone, yt_opt, split_size, etc. |
| `rss.{bot_id}` | `user_id` | RSS subscriptions per user |

### `DbManager` Methods

| Method | Purpose |
|--------|---------|
| `db_load()` | Import all data from DB on startup |
| `update_config(dict_)` | Update bot config |
| `update_aria2(key, value)` | Update aria2 option |
| `update_qbittorrent(key, value)` | Update qbit option |
| `update_private_file(path)` | Save binary file (config.env, .netrc, etc.) |
| `update_user_doc(user_id, key, path)` | Save user document (rclone, token) |
| `update_user_data(user_id)` | Save user settings dict |
| `update_thumb(user_id, path)` | Save user thumbnail |
| `rss_update(user_id)` | Save user RSS data |
| `rss_update_all()` | Save all RSS data |
| `rss_delete(user_id)` | Delete user RSS data |
| `trunc_table(name)` | Drop collection |

### User Data Paths

| Type | Path Pattern |
|------|-------------|
| Multi-user rclone | `rclone/{user_id}/rclone.conf` |
| Global rclone | `rclone/rclone_global/rclone.conf` |
| User token | `tokens/{user_id}.pickle` |
| User thumbnail | `Thumbnails/{user_id}.jpg` |

### User Settings (`user_data` per user_id)

| Key | Type | Description |
|-----|------|-------------|
| `thumb` | path | Custom thumbnail image |
| `rclone` | path | User-specific rclone.conf |
| `rclone_global` | bool | Use global rclone config |
| `token_pickle` | path | Google Drive token |
| `as_doc` | bool | Leech as document |
| `yt_opt` | str | Default yt-dlp options |
| `equal_splits` | bool | Equal-sized splits |
| `split_size` | int | Custom split size |
| `name_sub` | str | Name substitution pattern |
| `screenshots_count` | int | Number of screenshots |
| `screenshots_as_album` | bool | Send screenshots as album |
| `category` | str | Default upload category |
| `upload_template` | str | Upload path template |

## Utility Functions

### `bot_utils.py`

| Function | Purpose |
|----------|---------|
| `is_first_archive_split(file)` | Check if file is first split of archive |
| `is_archive(file)` | Check if file is an archive |
| `is_archive_split(file)` | Check if file is a split archive |
| `get_content_type(link)` | HTTP Content-Type check |
| `is_share_link(url)` | gdtot/filepress/etc detection |
| `get_readable_time(seconds)` | Human-readable duration |
| `speed_string_to_bytes(size_text)` | Parse speed string to bytes |
| `get_size_bytes(size_text)` | Parse size string to bytes |
| `get_readable_message(chat_id, status_filter)` | Build status message with pagination |
| `text_size_to_bytes(size_text)` | Parse size text |
| `turn(data, chat_id)` | Handle status page navigation |
| `run_sync_to_async(func, *args)` | Thread pool executor bridge |
| `run_async_to_sync(func, *args)` | Run async from sync context |
| `create_task(func, *args)` | Create asyncio task |
| `cmd_exec(cmd, shell)` | Execute command, return (stdout, stderr, returncode) |
| `update_user_ldata(id_, key, value)` | Update user data dict |
| `clean_unwanted(path)` | Remove .!qB and .unwanted files |

### `misc_utils.py`

| Function | Purpose |
|----------|---------|
| `clean_download(path)` / `clean_target(path)` | Delete files/dirs |
| `start_cleanup()` / `clean_all()` | Startup/cleanup routines |
| `exit_clean_up(signal, frame)` | SIGINT handler |
| `get_readable_size(size)` | Human-readable size |
| `get_base_name(orig_path)` | Extract archive base name |
| `get_path_size(path)` | Recursive size calculation |
| `split_file(...)` | Video/file splitting with ffmpeg |
| `get_document_type(path)` | Detect video/audio/image |
| `get_mime_type(file_path)` | MIME type detection via python-magic |
| `get_media_info(path)` | Duration, artist, title via ffprobe |
| `get_video_resolution(path)` | Width/height via ffprobe |
| `bt_selection_buttons(id_)` | qBittorrent selection buttons |
| `getTaskByGid(gid)` | Find task by GID |
| `getAllTasks(status)` | Filter tasks by status |
| `get_image_from_url(url, filename)` | Download image from URL |
| `apply_name_substitute(name, substitutes)` | Regex-based filename substitution |
| `arg_parser(args, arg_base)` | Parse flag-based arguments |

### `rclone_utils.py`

| Function | Purpose |
|----------|---------|
| `is_rclone_config(user_id, message, isLeech)` | Check if rclone.conf exists |
| `is_remote_selected(user_id, message)` | Check if destination remote selected |
| `get_rclone_path(user_id, message)` | Get path to rclone.conf |
| `setRcloneFlags(cmd, type)` | Add global rclone flags |
| `is_gdrive_remote(remote, config_file)` | Check if remote is Google Drive |
| `list_remotes(message, menu_type, ...)` | List rclone remotes with buttons |
| `is_valid_path(remote, path, message)` | Validate remote path exists |
| `list_folder(message, rclone_remote, base_dir, menu_type, ...)` | List remote contents |
| `create_next_buttons(...)` | Build pagination buttons |
| `get_id(rclone_path, config_path, name, mime_type)` | Get Google Drive file ID |

### `links_utils.py`

| Function | Purpose |
|----------|---------|
| `is_url` | Check if string is a URL |
| `is_gdrive_link` | Check if GDrive link |
| `is_gdrive_id` | Check if GDrive ID |
| `is_mega_link` | Check if MEGA link |
| `is_magnet` | Check if magnet link |
| `is_share_link` | Check if share link (gdtot, etc.) |
| `is_telegram_link` | Check if Telegram link |
| `is_rclone_path` | Check if rclone path |

### `button_build.py`

`ButtonMaker` class:
- `url_buildbutton(key, link)` -- External URL button
- `cb_buildbutton(key, data, position)` -- Callback button (positions: `header`, `footer`, `footer_second`, `footer_third`)
- `build_menu(n_cols)` -- Build InlineKeyboardMarkup

### `message_utils.py`

| Function | Purpose |
|----------|---------|
| `sendMessage(text, message, reply_markup)` | Send text reply |
| `sendMarkup(text, message, reply_markup)` | Send text with markup |
| `sendPhoto(text, message, path, reply_markup)` | Send photo with caption |
| `editMessage(text, message, reply_markup)` | Edit existing message |
| `editMarkup(text, message, reply_markup)` | Edit with markup |
| `sendFile(message, file, caption)` | Send document |
| `sendRss(text, chat_id, thread_id)` | Send RSS message (bot or userbot) |
| `deleteMessage(message)` | Delete message |
| `delete_all_messages()` | Delete all status messages |
| `update_all_messages(force)` | Refresh all status displays |
| `sendStatusMessage(msg)` | Show status for a chat |
| `auto_delete_message(cmd_message, bot_message)` | Auto-delete after duration |

## Important Patterns

### Name Substitution

Format: `old::new|old2::new2`
- `\|` for literal pipe, `\::` for literal double-colon
- Applied via `apply_name_substitute(name, pattern)` using `re.sub` with escaped patterns

### Upload Path Templates

Variables: `{username}`, `{user_id}`, `{date}`, `{year}`, `{month}`, `{day}`, `{category}`, `{task_type}`
- Per-user via `upload_template` in user_data
- Global via `UPLOAD_PATH_TEMPLATE` config
- Applied via `apply_upload_template(template, user_id, username, category, task_type)`

### Multi-Task Pattern (`-i` flag)

Commands support `-i N` for batch processing: sends next message with decremented counter

### SameDir Pattern (`-m` flag)

Groups multiple downloads into a single folder for combined upload

### Mirror/Leech Args (`mirror_leech.py`)

Common flags parsed by `arg_parser`:
- `-s` -- Select files (torrent)
- `-d` -- Seed ratio/time (e.g., `-d 0.7:10`)
- `-i` -- Multi links count
- `-m` -- Same directory name
- `-n` -- New name
- `-au` / `-ap` -- Auth username/password
- `-e` -- Extract
- `-z` -- Zip (with optional password)
- `-ss` -- Screenshots count

### External Services

| Service | Connection | Purpose |
|---------|-----------|---------|
| Aria2 | WebSocket `localhost:6800` | Direct link / torrent downloads |
| qBittorrent | API `localhost:8090` | Torrent downloads |
| qbitweb | Gunicorn server | Torrent selection UI |
| Rclone Index | HTTP on configured port | File browsing via rclone serve |
| JDownloader | Java process `/JDownloader/JDownloader.jar` | Hosted downloads |

### General Guidelines

- Keep functions focused; large modules like `direct_link_generator.py` (1472 lines)
  are acceptable for dispatch/router functions but extract helpers when possible.
- Use `LOGGER.info()` / `LOGGER.error()` for operational logging (not `print()`).
- The bot uses `uvloop` for performance -- do not introduce blocking I/O.
- External processes are spawned via `asyncio.create_subprocess_exec` (never
  `os.system` or `subprocess.call` in async code).
- The `config.env` file is gitignored; use `sample_config.env` as the template.
