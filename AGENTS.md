# AGENTS.md

This file provides guidance for AI coding agents working in this repository.

## Project Overview

rcmltb is an async Telegram transfer bot for mirror, leech, clone, copy,
sync, and media workflows across Telegram, Google Drive, rclone remotes, MEGA,
Direct Links, torrents, and TMDB.

The current codebase assumes Python 3.10+ even though the README badge still
mentions 3.9+. Several files use `|` union typing syntax, so do not target 3.9.

The runtime is built around Pyrogram-compatible clients, asyncio/uvloop,
aria2c, qBittorrent, rclone, yt-dlp, JDownloader, and MongoDB-backed state.

## Repository Map

- `bot/__init__.py` sets up logging, `uvloop`, the global event loop, config
  loading, state containers, and the `bot` / `app` proxies.
- `bot/__main__.py` orchestrates startup, registers commands, and keeps the
  process alive.
- `bot/core/` contains config loading, client bootstrap, startup wiring,
  torrent manager integration, and JDownloader boot logic.
- `bot/helper/ext_utils/` contains most shared helpers: parsing, paths,
  rclone menus, DB persistence, help menus, task limits, templates, and link
  validation.
- `bot/helper/telegram_helper/` contains the command names, filters, button
  builder, and message helpers.
- `bot/helper/listeners/` contains the canonical `TaskListener` and backend
  listeners for aria2, qBittorrent, and JDownloader.
- `bot/modules/` contains the command handlers and callback routers.
- `bot/modules/tasks_listener.py` is a compatibility shim that re-exports
  `TaskListener` from `bot/helper/listeners/task_listener.py`.
- `bot/helper/mirror_leech_utils/` contains download backends, upload backends,
  status objects, and Google Drive helpers.
- `qbitweb/` provides the torrent selection web UI that is served by gunicorn
  when qBittorrent selection is enabled.
- Root scripts: `start.sh`, `update.py`, `session_generator.py`,
  `generate_drive_token.py`, `gen_sa_accounts.py`, and `add_to_team_drive.py`.
- Deployment files: `Dockerfile`, `docker-compose.yml`, and
  `.github/workflows/deploy.yml`.

## Runtime Artifacts and Secrets

Do not edit these unless the user explicitly asks:

- `config.env` and `config.py`
- `pyrogram.session*`
- `.netrc`
- `tokens/`, `rclone/`, `Thumbnails/`, `downloads/`
- `qBittorrent/`
- `botlog.txt` and other generated logs

`sample_config.env` is the template for local configuration.

## Build, Run & Deploy

```bash
pip3 install -r requirements.txt
pip3 install -r requirements-cli.txt
cp sample_config.env config.env
bash start.sh
```

- `start.sh` runs `update.py` and then `python3 -m bot`.
- Be careful with uncommitted changes before using `start.sh`; `update.py` can
  rewrite the checkout if `UPSTREAM_REPO` is configured.
- `Dockerfile` builds on `sammax23/rcmltb`, installs `requirements.txt`, and
  launches `bash start.sh`.
- `docker-compose.yml` mounts `./downloads` and `./config` and exposes ports 80
  and 8080.
- The runtime assumes external binaries such as `aria2c`, `qbittorrent-nox`,
  `rclone`, `7z`, `ffmpeg`, and `curl` are available in the image or host.
- The Heroku deployment is the manual workflow in `.github/workflows/deploy.yml`.
- There is no test suite, no formatter config, and no lint config in the repo.

## Config Model

- `Config.load()` first tries to import `config.py`; if that fails it reads
  environment variables from `config.env` / the process environment.
- Runtime config names must match `Config` attributes.
- `config_dict` is the canonical runtime snapshot. Prefer `config_dict["KEY"]`
  or `Config` over legacy module-level aliases.
- `bot/__init__.py` still exposes many legacy names via `__getattr__`, but that
  is compatibility-only.
- `Config._process_config_value()` trims whitespace, strips trailing slashes
  from URL-like values, forces `DOWNLOAD_DIR` to end in `/`, and parses `list`
  and `dict` values with `literal_eval`.
- `SEARCH_PLUGINS` and `YT_DLP_OPTIONS` are parsed from Python-literal strings,
  not JSON.
- The runtime uses `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`.

Required keys:

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `BOT_TOKEN`
- `OWNER_ID`

Important config groups:

- General: `DOWNLOAD_DIR`, `DATABASE_URL`, `CMD_INDEX`, `ALLOWED_CHATS`,
  `SUDO_USERS`, `AUTO_MIRROR`, `LOCAL_MIRROR`, `NO_TASKS_LOGS`, `BOT_PM`
- Queue/status: `PARALLEL_TASKS`, `QUEUE_ALL`, `QUEUE_DOWNLOAD`, `QUEUE_UPLOAD`,
  `STATUS_LIMIT`, `STATUS_UPDATE_INTERVAL`, `AUTO_DELETE_MESSAGE_DURATION`
- Rclone: `DEFAULT_OWNER_REMOTE`, `DEFAULT_GLOBAL_REMOTE`,
  `MULTI_RCLONE_CONFIG`, `REMOTE_SELECTION`, `MULTI_REMOTE_UP`,
  `USE_SERVICE_ACCOUNTS`, `SERVICE_ACCOUNTS_REMOTE`, `SERVER_SIDE`,
  `RC_INDEX_URL`, `RC_INDEX_PORT`, `RC_INDEX_USER`, `RC_INDEX_PASS`,
  `RCLONE_COPY_FLAGS`, `RCLONE_UPLOAD_FLAGS`, `RCLONE_DOWNLOAD_FLAGS`
- Google Drive: `GDRIVE_FOLDER_ID`, `IS_TEAM_DRIVE`, `GD_INDEX_URL`,
  `VIEW_LINK`, `EXTENSION_FILTER`
- Leech/upload: `AS_DOCUMENT`, `EQUAL_SPLITS`, `LEECH_SPLIT_SIZE`, `LEECH_LOG`,
  `NAME_SUBSTITUTE`, `UPLOAD_PATH_TEMPLATE`, `USER_SESSION_STRING`
- Search/media: `SEARCH_API_LINK`, `SEARCH_LIMIT`, `SEARCH_PLUGINS`,
  `TMDB_API_KEY`, `TMDB_LANGUAGE`
- External integrations: `QB_BASE_URL`, `QB_SERVER_PORT`, `UPSTREAM_REPO`,
  `UPSTREAM_BRANCH`, `JD_EMAIL`, `JD_PASSWORD`

## Runtime State and Proxies

- `bot` is a proxy that buffers `add_handler()` calls until the real Pyrogram
  bot client exists.
- `app` is a proxy for the optional userbot client started from
  `USER_SESSION_STRING`.
- `bot_loop` is the dedicated asyncio event loop created at import time.
- `scheduler` is an `AsyncIOScheduler` bound to `bot_loop`.
- `status_dict` / `status_dict_lock` track active tasks by message ID.
- `status_reply_dict` / `status_reply_dict_lock` track per-chat status messages.
- `queued_dl` and `queued_up` hold queued task events.
- `non_queued_dl` and `non_queued_up` track active task UIDs.
- `queue_dict_lock` and `same_directory_lock` guard queue and same-dir state.
- `Interval` and `QbInterval` hold periodic jobs.
- `QbTorrents` and `qb_listener_lock` support qBittorrent listener state.
- `user_data` stores auth users, sudo users, and per-user settings.
- `aria2_options`, `qbit_options`, `tmdb_titles`, `remotes_multi`,
  `leech_log`, and `GLOBAL_EXTENSION_FILTER` are live runtime caches.
- `TG_MAX_SPLIT_SIZE` is 2GB. `TgClient.MAX_SPLIT_SIZE` becomes 4GB when the
  user client is premium.
- If `LEECH_SPLIT_SIZE` is set to 0, the bot falls back to `TG_MAX_SPLIT_SIZE`.

## Startup Flow

1. `load_settings()` restores DB-backed config, private files, and user data
   if `DATABASE_URL` is set.
2. `TgClient.start_bot()` and `TgClient.start_user()` start the Pyrogram clients
   concurrently.
3. `load_configurations()` starts qbitweb when `QB_BASE_URL` is set, ensures
   qBittorrent-nox is running, prepares `.netrc`, runs `aria.sh`, and extracts
   `accounts.zip` if present.
4. `TorrentManager.initiate()` connects to aria2 and qBittorrent.
5. `start_cleanup()` clears old qBittorrent state and recreates `DOWNLOAD_DIR`
   unless `LOCAL_MIRROR` is enabled.
6. `update_variables()` populates auth users, sudo users, extension filters, and
   leech log destinations.
7. `update_aria2_options()` and `update_qbit_options()` apply saved engine
   settings.
8. `TorrentManager.aria2_init()` performs a lightweight aria2 health check.
9. Help buttons and Telegraph are initialized.
10. Torrent search tools are loaded.
11. aria2 callbacks are registered.
12. `add_handlers()` imports the command modules and registers the handlers.
13. JDownloader is booted if `JD_EMAIL` and `JD_PASSWORD` are configured.
14. Restart status is updated if `.restartmsg` exists.
15. Bot commands are published via `set_bot_commands()`.
16. `save_settings()` persists the runtime config snapshot back to MongoDB.

## Command Surface

Use `BotCommands` instead of raw strings. All commands are suffixed with
`CMD_INDEX` automatically.

| Area | Commands | Main files |
| --- | --- | --- |
| Mirror and leech | `mirror/m`, `leech/l`, `mirror_batch/mb`, `leech_batch/lb`, `mirror_select/ms`, `ytdl/y`, `ytdl_leech/yl`, `pmirror`, `pleech`, `jdmirror/jm`, `jdleech/jl` | `mirror_leech.py`, `leech.py`, `batch.py`, `mirror_select.py`, `ytdlp.py`, `pmirror.py` |
| Cloud transfer | `clone`, `copy`, `sync`, `bisync`, `rcfm`, `storage`, `cleanup`, `serve`, `count` | `clone.py`, `copy.py`, `sync.py`, `bisync.py`, `rcfm.py`, `storage.py`, `cleanup.py`, `serve.py`, `gd_count.py` |
| Task control | `status`, `cancel`, `cancel_all`, `force_start/fs` | `status.py`, `cancel.py`, `force_start.py` |
| Search and metadata | `torrsch`, `tmdb`, `mediainfo`, `sel` | `torr_search.py`, `tmdb.py`, `mediainfo.py`, `torr_select.py` |
| Settings and admin | `files/bf`, `user_setting`, `own_setting`, `shell`, `exec`, `restart`, `ping`, `ip`, `log` | `botfiles.py`, `user_settings.py`, `owner_settings.py`, `shell.py`, `exec.py`, `core/handlers.py` |
| Help | `help` | `help_messages.py` |

Access control and filters:

- `owner_filter` allows only `OWNER_ID`.
- `sudo_filter` allows `OWNER_ID` and IDs in `SUDO_USERS`.
- `user_filter` allows owner, auth users, sudo users, and auth chats.
- `chat_filter` allows auth chats and forum topic IDs stored on `user_data`.
- Most handlers use `filters.command(...) & (CustomFilters.user_filter |
  CustomFilters.chat_filter)`.

Callback prefixes worth preserving:

- `mirrormenu`, `remoteselectmenu`, `leechmenu`, `leechselect`
- `copymenu`, `next_copy`, `myfilesmenu`, `next_myfiles`
- `servemenu`, `syncmenu`, `bisyncmenu`, `storagemenu`, `cleanupmenu`
- `ownersetmenu`, `userset`, `status`, `canall`, `ytq`
- `tmdbsubcat`, `tmdbdetails`, `tmdbnext`, `tdmbsearch`, `help`

## Core Workflows

- Mirror/leech: `mirror_leech.py` dispatches direct links, GDrive links, MEGA,
  magnet links, Telegram files, and JDownloader sources. It supports `-s`,
  `-d`, `-i`, `-m`, `-n`, `-au`, `-ap`, `-e`, `-z`, and `-ss`.
- `TaskListener` handles the post-download pipeline: zip, extract, name
  substitution, queue gating, split handling, and upload routing.
- Telegram private mirror/leech: `pmirror` and `pleech` use the optional
  `app` userbot to access private channels when `USER_SESSION_STRING` is set.
- Rclone navigation: `leech`, `copy`, `rcfm`, `storage`, `cleanup`, and `serve`
  all build inline menus through `menu_utils`, `rclone_utils`, and
  `rclone_data_holder`.
- Search: `torr_search.py` can use either the API backend or qBittorrent search
  plugins. It can publish large result sets through Telegraph pages.
- TMDB: `tmdb.py` needs `TMDB_API_KEY` and search plugins, stores titles in
  `tmdb_titles`, and can hand off to torrent search.
- Status and queue: `PARALLEL_TASKS` enables the async queue manager; otherwise
  tasks run immediately. `QUEUE_ALL`, `QUEUE_DOWNLOAD`, and `QUEUE_UPLOAD` are
  enforced by `task_manager.py`. Status pages use `status_pages` plus `turn()`.
- Settings: owner settings edit config, aria2, and qBittorrent state; user
  settings store per-user thumbs, split sizes, yt-dlp options, categories, name
  substitution, and upload templates.

## Helper Modules

- `bot/helper/ext_utils/bot_utils.py`: task helpers, async bridges, status
  pagination, `cmd_exec`, `new_task`, `run_sync_to_async`, `run_async_to_sync`,
  `update_user_ldata`, `clean_unwanted`.
- `bot/helper/ext_utils/misc_utils.py`: legacy/general helpers for file and
  media handling, `arg_parser`, `apply_name_substitute`, `getTaskByGid`,
  `getAllTasks`, and image helpers.
- `bot/helper/ext_utils/batch_helper.py`: batch-link extraction and parsing for
  `mirror_batch` / `leech_batch` flows.
- `bot/helper/ext_utils/files_utils.py`: cleanup, archive detection, MIME and
  media inspection, recursive sizing, and `split_file()`.
- `bot/helper/ext_utils/rclone_utils.py`: rclone config lookup, path checks,
  remote listing, pagination, and flag injection.
- `bot/helper/ext_utils/rclone_data_holder.py`: per-user ephemeral state for
  rclone menus and selections.
- `bot/helper/ext_utils/links_utils.py`: URL, GDrive, MEGA, magnet, Telegram,
  share-link, and rclone-path detection.
- `bot/helper/ext_utils/menu_utils.py`: menu namespaces plus list pagination and
  button population helpers.
- `bot/helper/ext_utils/telegraph_helper.py`: Telegraph bootstrap and page
  creation/editing for search and help flows.
- `bot/helper/ext_utils/template_utils.py`: upload path templating.
- `bot/helper/ext_utils/db_handler.py`: Mongo persistence for config, files,
  user data, and thumbs.
- `bot/helper/ext_utils/task_manager.py`: queue-limit enforcement and duplicate
  GDrive detection.
- `bot/helper/ext_utils/help_messages.py`: help text and help menu callbacks.

## Code Style and Editing Rules

- Keep imports grouped as stdlib, third-party, then local project imports.
- Prefer `from x import y` over `import x` when practical.
- Use f-strings and HTML tags for Telegram messages.
- Keep new Telegram handlers and I/O-bound functions async.
- Use `run_sync_to_async()` for blocking code and `asyncio.create_subprocess_*`
  for external commands.
- Use `LOGGER.info()` / `LOGGER.error()` for operational logging.
- Prefer `config_dict` and `Config` for runtime config reads.
- When adding or renaming a command, update `BotCommands`, the handler module,
  and `set_bot_commands()` in `bot/__main__.py`.
- When adding a config key, update `Config`, `sample_config.env`, and any UI or
  persistence code that exposes it.
- Use `apply_patch` for manual file edits.
- Avoid editing generated artifacts or secrets unless the user explicitly asks.
