# AGENTS.md

This file provides guidance for AI coding agents working in this repository.

## Project Overview

**rcmltb** is an async Python Telegram bot (Rclone Mirror-Leech Telegram Bot) for
transferring files to/from cloud storage (Google Drive, MEGA, local, etc.) and
Telegram. Built on Pyrogram + asyncio. Version 4.6 by Sam-Max.

## Repository Layout

```
bot/
  __init__.py          # Global config, state, DB init, Pyrogram client bootstrap
  __main__.py          # Entry point, command registration, main loop
  conv_pyrogram.py     # Conversation helper for Pyrogram
  modules/             # Bot command handlers (cancel, copy, clone, leech, mirror, rss, etc.)
  helper/
    ext_utils/         # Utilities: bot_utils, db_handler, exceptions, human_format, misc_utils, rclone_utils
    telegram_helper/   # Telegram helpers: bot_commands, button_build, filters, message_utils
    mirror_leech_utils/
      download_utils/  # aria2, gdrive, mega, qbittorrent, telegram, rclone, yt-dlp downloaders
      upload_utils/    # rclone_mirror, telegram_uploader
      status_utils/    # Status classes for each task type
      gd_utils/        # Google Drive helpers
      debrid_utils/    # Debrid service helpers
qbitweb/               # qBittorrent web UI server
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

### Configuration & Global State

- Environment variables are loaded in `bot/__init__.py` via `python-dotenv`.
- All config values are stored in the module-level `config_dict` dict.
- User data is stored in `user_data` dict keyed by user/chat ID.
- Status tracking uses `status_dict` with `status_dict_lock`.
- Access config via `config_dict["KEY"]`, not the module-level variables directly
  (module vars are set at import time and not updated when DB config changes).

### Telegram Handler Registration

Handlers are registered at module level or in `__main__.py`:
```python
bot.add_handler(
    MessageHandler(
        handle_mirror,
        filters=filters.command(BotCommands.MirrorCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
```
Use `CustomFilters.owner_filter`, `sudo_filter`, `user_filter`, or `chat_filter`
to restrict access.

### File Naming Conventions

- Utility modules: `*_utils.py` (e.g., `bot_utils.py`, `misc_utils.py`)
- Status classes: `*_status.py` in `status_utils/`
- Downloaders: `*_downloader.py` or `*_download.py` in `download_utils/`
- Uploaders: `*_uploader.py` or `*_mirror.py` in `upload_utils/`

### General Guidelines

- Keep functions focused; large modules like `direct_link_generator.py` (1472 lines)
  are acceptable for dispatch/router functions but extract helpers when possible.
- Use `LOGGER.info()` / `LOGGER.error()` for operational logging (not `print()`).
- The bot uses `uvloop` for performance -- do not introduce blocking I/O.
- External processes are spawned via `asyncio.create_subprocess_exec` (never
  `os.system` or `subprocess.call` in async code).
- The `config.env` file is gitignored; use `sample_config.env` as the template.
