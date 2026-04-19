#!/usr/bin/env python3
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.db_handler import database
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (
    editMessage,
    sendFile,
    sendMessage,
    sendRss,
)
from bot.helper.ext_utils.bot_utils import get_size_bytes, new_thread
from bot.helper.ext_utils.misc_utils import arg_parser
from feedparser import parse as feedparse
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex, create
from pyrogram.types import Message
from asyncio import Lock, sleep
from datetime import datetime, timedelta
from time import time
from functools import partial
from aiohttp import ClientSession
from apscheduler.triggers.interval import IntervalTrigger
from re import split as re_split, compile, IGNORECASE
from io import BytesIO
from bot import scheduler, rss_dict, LOGGER, DATABASE_URL, config_dict, bot
from bot.helper.ext_utils.exceptions import RssShutdownException
from bot.helper.ext_utils.help_messages import RSS_HELP_MESSAGE

rss_dict_lock = Lock()
handler_dict = {}

# Regex for extracting size from feed summaries (e.g., "2.5 GB", "1.2 GiB")
size_regex = compile(r"(\d+(?:\.\d+)?\s?(?:GB|MB|KB|GiB|MiB|KiB|TB|TiB))", IGNORECASE)

# Browser headers to avoid feed blocking
RSS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Command mapping cache for direct handler invocation
_command_map = None


def _build_command_map():
    """Build a mapping from command name -> handler callback."""
    from bot.core.telegram_manager import TgClient
    mapping = {}
    if TgClient.bot is None:
        return mapping
    for group in TgClient.bot.dispatcher.groups.values():
        for handler in group:
            if isinstance(handler, MessageHandler) and handler.filters:
                # Try to extract commands from filters
                cmds = _extract_commands_from_filter(handler.filters)
                for cmd in cmds:
                    mapping[cmd] = handler.callback
    return mapping


def _extract_commands_from_filter(filter_obj):
    """Extract command names from a filter object."""
    commands = []
    # Handle command filter
    if hasattr(filter_obj, 'commands'):
        commands.extend(filter_obj.commands)
    # Handle AND/OR filters
    if hasattr(filter_obj, 'filters'):
        for f in filter_obj.filters:
            commands.extend(_extract_commands_from_filter(f))
    return commands


def _get_command_map():
    """Get cached command map, rebuild if needed."""
    global _command_map
    if _command_map is None:
        _command_map = _build_command_map()
    return _command_map


def _resolve_command(command_str):
    """Resolve a command string like 'ql -doc' into its handler function."""
    if not command_str:
        return None
    cmd_name = command_str.strip().lstrip("/").split(maxsplit=1)[0]
    mapping = _get_command_map()
    handler = mapping.get(cmd_name)
    # Try with CMD_SUFFIX if available
    if handler is None and config_dict.get("CMD_INDEX"):
        handler = mapping.get(cmd_name + config_dict["CMD_INDEX"])
    return handler


async def _start_rss_download(user_id, cmd, url, options, tag):
    """Execute handler directly instead of sending message to chat."""
    handler = _resolve_command(cmd)
    if handler is None:
        LOGGER.error(f"Could not resolve command handler for: {cmd}")
        return False
    
    try:
        # Create a fake message object for the handler
        fake_message = type('FakeMessage', (), {})()
        fake_message.from_user = type('User', (), {})()
        fake_message.from_user.id = user_id
        fake_message.from_user.username = tag.replace("@", "") if tag.startswith("@") else None
        fake_message.from_user.mention = tag
        fake_message.text = f"/{cmd} {url} {options or ''}".strip()
        fake_message.chat = type('Chat', (), {})()
        fake_message.chat.id = config_dict.get("RSS_CHAT_ID", 0)
        fake_message.chat.type = type('ChatType', (), {})()
        fake_message.chat.type.name = "CHANNEL"
        fake_message.id = 0
        fake_message.link = None
        
        # Call the handler directly
        await handler(None, fake_message)
        return True
    except Exception as e:
        LOGGER.error(f"Error executing handler for {cmd}: {e}")
        return False


def _parse_chat_id(chat_value):
    """Parse chat_id and optional topic_id from RSS_CHAT_ID.
    
    Supports formats:
    - chat_id (int or str)
    - chat_id|topic_id (forum topic)
    """
    if chat_value is None:
        return None, None
    
    if isinstance(chat_value, int):
        return chat_value, None
    
    chat_str = str(chat_value).strip()
    if "|" in chat_str:
        parts = chat_str.split("|", 1)
        chat_id = parts[0].strip()
        topic_id = parts[1].strip()
        # Convert to int if numeric
        if chat_id.lstrip("-").isdigit():
            chat_id = int(chat_id)
        if topic_id.lstrip("-").isdigit():
            topic_id = int(topic_id)
        return chat_id, topic_id
    
    # Simple chat_id
    if chat_str.lstrip("-").isdigit():
        return int(chat_str), None
    return chat_str, None


async def rssMenu(event):
    user_id = event.from_user.id
    buttons = ButtonMaker()
    buttons.cb_buildbutton("➕ Subscribe", f"rss sub {user_id}")
    buttons.cb_buildbutton("📋 Subscriptions", f"rss list {user_id} 0")
    buttons.cb_buildbutton("📥 Get Items", f"rss get {user_id}")
    buttons.cb_buildbutton("✏️ Edit", f"rss edit {user_id}")
    buttons.cb_buildbutton("⏸️ Pause", f"rss pause {user_id}")
    buttons.cb_buildbutton("▶️ Resume", f"rss resume {user_id}")
    buttons.cb_buildbutton("❌ Unsubscribe", f"rss unsubscribe {user_id}")
    if await CustomFilters.sudo_filter("", event):
        buttons.cb_buildbutton("📚 All Subscriptions", f"rss listall {user_id} 0")
        buttons.cb_buildbutton("⏸️ Pause All", f"rss allpause {user_id}")
        buttons.cb_buildbutton("▶️ Resume All", f"rss allresume {user_id}")
        buttons.cb_buildbutton("❌ Unsubscribe All", f"rss allunsub {user_id}")
        buttons.cb_buildbutton("🗑️ Delete User", f"rss deluser {user_id}")
        # Add "Use This Chat" button for sudo users
        if hasattr(event, 'message') and event.message and hasattr(event.message, 'chat'):
            buttons.cb_buildbutton("📍 Use This Chat", f"rss usethis {user_id}")
        if scheduler.running:
            buttons.cb_buildbutton("⏹️ Shutdown Rss", f"rss shutdown {user_id}")
        else:
            buttons.cb_buildbutton("▶️ Start Rss", f"rss start {user_id}")
    buttons.cb_buildbutton("✘ Close", f"rss close {user_id}")
    button = buttons.build_menu(2)
    msg = f"📰 <b>Rss Menu</b> | Users: {len(rss_dict)} | Running: {scheduler.running}"
    return msg, button


async def updateRssMenu(query):
    msg, button = await rssMenu(query)
    await editMessage(msg, query.message, button)


async def getRssMenu(_, message):
    msg, button = await rssMenu(message)
    await sendMessage(msg, message, button)


def _parse_filter_args(item):
    """Parse RSS filter arguments using arg_parser style."""
    # Support both old format (c:, inf:, exf:, opt:) and new format (-c, -inf, -exf, -opt, -stv)
    arg_base = {
        "c": None,
        "inf": None,
        "exf": None,
        "opt": None,
        "stv": False,  # Case-sensitive flag
    }
    
    # Try new format first (-c, -inf, -exf, -opt, -stv)
    parts = item.split()
    i = 0
    while i < len(parts):
        part = parts[i]
        if part in ("-c", "c:"):
            if i + 1 < len(parts) and not parts[i + 1].startswith(("-", "c:", "inf:", "exf:", "opt:")):
                arg_base["c"] = parts[i + 1]
                i += 2
            else:
                arg_base["c"] = True
                i += 1
        elif part in ("-inf", "inf:"):
            if i + 1 < len(parts) and not parts[i + 1].startswith(("-", "c:", "inf:", "exf:", "opt:")):
                arg_base["inf"] = parts[i + 1]
                i += 2
            else:
                i += 1
        elif part in ("-exf", "exf:"):
            if i + 1 < len(parts) and not parts[i + 1].startswith(("-", "c:", "inf:", "exf:", "opt:")):
                arg_base["exf"] = parts[i + 1]
                i += 2
            else:
                i += 1
        elif part in ("-opt", "opt:"):
            if i + 1 < len(parts) and not parts[i + 1].startswith(("-", "c:", "inf:", "exf:", "opt:")):
                arg_base["opt"] = parts[i + 1]
                i += 2
            else:
                i += 1
        elif part in ("-stv", "stv"):
            arg_base["stv"] = True
            i += 1
        else:
            i += 1
    
    # Process filter lists
    inf_lists = []
    exf_lists = []
    
    if arg_base["inf"]:
        filters_list = arg_base["inf"].split("|")
        for x in filters_list:
            y = x.split(" or ")
            inf_lists.append(y)
    
    if arg_base["exf"]:
        filters_list = arg_base["exf"].split("|")
        for x in filters_list:
            y = x.split(" or ")
            exf_lists.append(y)
    
    return arg_base["c"], inf_lists, exf_lists, arg_base["opt"], arg_base["stv"]


async def rssSub(_, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    if username := message.from_user.username:
        tag = f"@{username}"
    else:
        tag = message.from_user.mention
    msg = ""
    items = message.text.split("\n")
    for index, item in enumerate(items, start=1):
        args = item.split()
        if len(args) < 2:
            await sendMessage(
                f"{item}. Wrong Input format. Read help message before adding new subcription!",
                message,
            )
            continue
        title = args[0].strip()
        if (user_feeds := rss_dict.get(user_id, False)) and title in user_feeds:
            await sendMessage(
                f"This title {title} already subscribed! Choose another title!", message
            )
            continue
        feed_link = args[1].strip()
        if feed_link.startswith(("inf:", "exf:", "opt:", "c:", "-")):
            await sendMessage(
                message,
                f"Wrong input in line {index}! Re-add only the mentioned line correctly! Read the example!",
            )
            continue
        
        # Parse filters and options using the new parser
        cmd, inf_lists, exf_lists, opt, sensitive = _parse_filter_args(item)
        
        try:
            # Retry logic: try up to 3 times
            html = None
            tries = 0
            while tries < 3:
                try:
                    async with ClientSession(headers=RSS_HEADERS, trust_env=True) as session:
                        async with session.get(feed_link) as res:
                            html = await res.text()
                    break
                except Exception as e:
                    tries += 1
                    if tries >= 3:
                        raise
                    LOGGER.warning(f"Retry {tries}/3 for feed {title}: {e}")
                    await sleep(2)
            
            rss_d = feedparse(html)
            last_title = rss_d.entries[0]["title"]
            msg += "✅ <b>Subscribed!</b>"
            msg += f"\n<b>Title: </b><code>{title}</code>\n<b>Feed Url: </b>{feed_link}"
            msg += f"\n<b>latest record for </b>{rss_d.feed.title}:"
            msg += (
                f"\nName: <code>{last_title.replace('>', '').replace('<', '')}</code>"
            )
            try:
                last_link = rss_d.entries[0]["links"][1]["href"]
            except IndexError:
                last_link = rss_d.entries[0]["link"]
            msg += f"\nLink: <code>{last_link}</code>"
            msg += f"\n<b>Command: </b><code>{cmd}</code>"
            msg += (
                f"\n<b>Filters:-</b>\ninf: <code>{inf_lists}</code>\nexf: <code>{exf_lists}</code>"
            )
            msg += f"\nSensitive: <code>{sensitive}</code>"
            msg += f"\nOptions: {opt}\n\n"
            async with rss_dict_lock:
                feed_data = {
                    "link": feed_link,
                    "last_feed": last_link,
                    "last_title": last_title,
                    "inf": inf_lists,
                    "exf": exf_lists,
                    "paused": False,
                    "command": cmd,
                    "options": opt,
                    "tag": tag,
                    "sensitive": sensitive,
                }
                if rss_dict.get(user_id, False):
                    rss_dict[user_id][title] = feed_data
                else:
                    rss_dict[user_id] = {title: feed_data}
            LOGGER.info(
                f"Rss Feed Added: id: {user_id} - title: {title} - link: {feed_link} - c: {cmd} - inf: {inf_lists} - exf: {exf_lists} - stv: {sensitive} - opt: {opt}"
            )
        except (IndexError, AttributeError) as e:
            emsg = f"❌ The link: {feed_link} doesn't seem to be a RSS feed or it's region-blocked!"
            await sendMessage(emsg + "\nError: " + str(e), message)
        except Exception as e:
            await sendMessage(str(e), message)
    if DATABASE_URL:
        await database.rss_update(user_id)
    if msg:
        await sendMessage(msg, message)
    await updateRssMenu(pre_event)


async def getUserId(title):
    async with rss_dict_lock:
        return next(
            (
                (True, user_id)
                for user_id, feed in list(rss_dict.items())
                if feed.get("title") == title
            ),
            (False, False),
        )


async def rssUpdate(client, message, pre_event, state):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    titles = message.text.split()
    is_sudo = await CustomFilters.sudo_filter("", message)
    updated = []
    for title in titles:
        title = title.strip()
        if not (res := rss_dict[user_id].get(title, False)):
            if is_sudo:
                res, user_id = await getUserId(title)
            if not res:
                user_id = message.from_user.id
                await sendMessage(f"{title} not found!", message)
                continue
        istate = rss_dict[user_id][title].get("paused", False)
        if istate and state == "pause" or not istate and state == "resume":
            await sendMessage(f"{title} already {state}d!", message)
            continue
        async with rss_dict_lock:
            updated.append(title)
            if state == "unsubscribe":
                del rss_dict[user_id][title]
            elif state == "pause":
                rss_dict[user_id][title]["paused"] = True
            elif state == "resume":
                rss_dict[user_id][title]["paused"] = False
        if state == "resume":
            if scheduler.state == 2:
                scheduler.resume()
            elif is_sudo and not scheduler.running:
                addJob(config_dict["RSS_DELAY"])
                scheduler.start()
        if is_sudo and DATABASE_URL and user_id != message.from_user.id:
            await database.rss_update(user_id)
        if not rss_dict[user_id]:
            async with rss_dict_lock:
                del rss_dict[user_id]
            if DATABASE_URL:
                await database.rss_delete(user_id)
                if not rss_dict:
                    await database.trunc_table("rss")
    LOGGER.info(f"Rss link with Title(s): {updated} has been {state}d!")
    await sendMessage(
        f"Rss links with Title(s): <code>{updated}</code> has been {state}d!", message
    )
    if DATABASE_URL and rss_dict.get(user_id):
        await database.rss_update(user_id)
    await updateRssMenu(pre_event)


async def rssList(query, start, all_users=False):
    user_id = query.from_user.id
    buttons = ButtonMaker()
    if all_users:
        list_feed = f"<b>All subscriptions | Page: {int(start/5)} </b>"
        async with rss_dict_lock:
            keysCount = sum(len(v.keys()) for v in list(rss_dict.values()))
            index = 0
            for titles in list(rss_dict.values()):
                for index, (title, data) in enumerate(
                    list(titles.items())[start : 5 + start]
                ):
                    list_feed += f"\n\n<b>Title:</b> <code>{title}</code>\n"
                    list_feed += f"<b>Feed Url:</b> <code>{data['link']}</code>\n"
                    list_feed += f"<b>Command:</b> <code>{data.get('command')}</code>\n"
                    list_feed += f"<b>Inf:</b> <code>{data.get('inf')}</code>\n"
                    list_feed += f"<b>Exf:</b> <code>{data.get('exf')}</code>\n"
                    list_feed += f"<b>Paused:</b> <code>{data.get('paused')}</code>\n"
                    list_feed += f"<b>Sensitive:</b> <code>{data.get('sensitive', False)}</code>\n"
                    list_feed += f"<b>Options:</b> <code>{data.get('options')}</code>\n"
                    list_feed += f"<b>User:</b> {data.get('tag', '').replace('@', '', 1)}"
                    index += 1
                    if index == 5:
                        break
    else:
        list_feed = f"<b>Your subscriptions | Page: {int(start/5)} </b>"
        async with rss_dict_lock:
            keysCount = len(rss_dict.get(user_id, {}).keys())
            for title, data in list(rss_dict[user_id].items())[start : 5 + start]:
                list_feed += f"\n\n<b>Title:</b> <code>{title}</code>\n<b>Feed Url: </b><code>{data['link']}</code>\n"
                list_feed += f"<b>Command:</b> <code>{data.get('command')}</code>\n"
                list_feed += f"<b>Inf:</b> <code>{data.get('inf')}</code>\n"
                list_feed += f"<b>Exf:</b> <code>{data.get('exf')}</code>\n"
                list_feed += f"<b>Paused:</b> <code>{data.get('paused')}</code>\n"
                list_feed += f"<b>Sensitive:</b> <code>{data.get('sensitive', False)}</code>\n"
                list_feed += f"<b>Options:</b> <code>{data.get('options')}</code>"
    buttons.cb_buildbutton("Back", f"rss back {user_id}")
    buttons.cb_buildbutton("Close", f"rss close {user_id}")
    if keysCount > 5:
        for x in range(0, keysCount, 5):
            buttons.cb_buildbutton(
                f"{int(x/5)}", f"rss list {user_id} {x}", position="footer"
            )
    button = buttons.build_menu(2)
    if query.message.text.html == list_feed:
        return
    await editMessage(list_feed, query.message, button)


async def rssGet(client, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    args = message.text.split()
    if len(args) < 2:
        await sendMessage(
            f"{args}. Wrong Input format. You should add number of the items you want to get. Read help message before adding new subcription!",
            message,
        )
        await updateRssMenu(pre_event)
        return
    try:
        title = args[0]
        count = int(args[1])
        data = rss_dict[user_id].get(title, False)
        if data and count > 0:
            msg = await sendMessage(
                f"Getting the last <b>{count}</b> item(s) from {title}", message
            )
            try:
                # Retry logic for rssGet
                html = None
                tries = 0
                while tries < 3:
                    try:
                        async with ClientSession(headers=RSS_HEADERS, trust_env=True) as session:
                            async with session.get(data["link"]) as res:
                                html = await res.text()
                        break
                    except Exception as e:
                        tries += 1
                        if tries >= 3:
                            raise
                        LOGGER.warning(f"Retry {tries}/3 for rssGet {title}: {e}")
                        await sleep(2)
                
                rss_d = feedparse(html)
                item_info = ""
                for item_num in range(count):
                    try:
                        link = rss_d.entries[item_num]["links"][1]["href"]
                    except IndexError:
                        link = rss_d.entries[item_num]["link"]
                    item_info += f"<b>Name: </b><code>{rss_d.entries[item_num]['title'].replace('>', '').replace('<', '')}</code>\n"
                    item_info += f"<b>Link: </b><code>{link}</code>\n\n"
                item_info_ecd = item_info.encode()
                if len(item_info_ecd) > 4000:
                    with BytesIO(item_info_ecd) as out_file:
                        out_file.name = f"rssGet {title} items_no. {count}.txt"
                        await sendFile(message, out_file)
                    await msg.delete()
                else:
                    await editMessage(item_info, msg)
            except IndexError as e:
                LOGGER.error(str(e))
                await editMessage(
                    "Parse depth exceeded. Try again with a lower value.", msg
                )
            except Exception as e:
                LOGGER.error(str(e))
                await editMessage(str(e), msg)
    except Exception as e:
        LOGGER.error(str(e))
        await sendMessage(f"Enter a valid value!. {e}", message)
    await updateRssMenu(pre_event)


async def rssEdit(client, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    items = message.text.split("\n")
    for item in items:
        args = item.split()
        if len(args) < 1:
            continue
        title = args[0].strip()
        if len(args) < 2:
            await sendMessage(
                f"{item}. Wrong Input format. Read help message before editing!",
                message,
            )
            continue
        elif not rss_dict[user_id].get(title, False):
            await sendMessage("Enter a valid title. Title not found!", message)
            continue
        
        # Parse new values
        cmd, inf_lists, exf_lists, opt, sensitive = _parse_filter_args(item)
        
        async with rss_dict_lock:
            if opt is not None:
                if isinstance(opt, str) and opt.lower() == "none":
                    opt = None
                rss_dict[user_id][title]["options"] = opt
            if cmd is not None:
                if isinstance(cmd, str) and cmd.lower() == "none":
                    cmd = None
                rss_dict[user_id][title]["command"] = cmd
            if inf_lists is not None:
                rss_dict[user_id][title]["inf"] = inf_lists
            if exf_lists is not None:
                rss_dict[user_id][title]["exf"] = exf_lists
            # Update sensitive flag
            if "stv" in item or "-stv" in item:
                rss_dict[user_id][title]["sensitive"] = sensitive
    if DATABASE_URL:
        await database.rss_update(user_id)
    await updateRssMenu(pre_event)


async def rssDelete(client, message, pre_event):
    handler_dict[message.from_user.id] = False
    users = message.text.split()
    for user in users:
        user = int(user)
        async with rss_dict_lock:
            del rss_dict[user]
        if DATABASE_URL:
            await database.rss_delete(user)
    await updateRssMenu(pre_event)


async def setRssChat(_, message, pre_event):
    """Set the current chat as RSS_CHAT_ID."""
    user_id = message.from_user.id
    handler_dict[user_id] = False
    
    chat_id = message.chat.id
    topic_id = None
    
    # Check if this is a forum topic
    if hasattr(message, 'message_thread_id') and message.message_thread_id:
        topic_id = message.message_thread_id
        chat_value = f"{chat_id}|{topic_id}"
    else:
        chat_value = str(chat_id)
    
    # Update config
    from bot.core.config_manager import Config
    Config.set("RSS_CHAT_ID", chat_value)
    config_dict["RSS_CHAT_ID"] = chat_value
    
    await sendMessage(
        f"✅ RSS_CHAT_ID set to: <code>{chat_value}</code>\n\n"
        f"The RSS monitor will now send notifications to this chat.",
        message
    )
    await updateRssMenu(pre_event)
    
    LOGGER.info(f"RSS_CHAT_ID updated to {chat_value} by user {user_id}")


async def event_handler(client, query, pfunc):
    user_id = query.from_user.id
    handler_dict[user_id] = True
    start_time = time()

    async def event_filter(_, __, event):
        user = event.from_user or event.sender_chat
        return bool(
            user.id == user_id and event.chat.id == query.message.chat.id and event.text
        )

    handler = client.add_handler(MessageHandler(pfunc, create(event_filter)), group=-1)

    while handler_dict[user_id]:
        await sleep(0.5)
        if time() - start_time > 60:
            handler_dict[user_id] = False
            await updateRssMenu(query)
    client.remove_handler(*handler)


@new_thread
async def rssListener(client, query):
    user_id = query.from_user.id
    message = query.message
    data = query.data.split()
    if int(data[2]) != user_id and not await CustomFilters.sudo_filter("", query):
        await query.answer(
            text="You don't have permission to use these buttons!", show_alert=True
        )
    elif data[1] == "close":
        await query.answer()
        handler_dict[user_id] = False
        await message.reply_to_message.delete()
        await message.delete()
    elif data[1] == "back":
        await query.answer()
        handler_dict[user_id] = False
        await updateRssMenu(query)
    elif data[1] == "sub":
        await query.answer()
        handler_dict[user_id] = False
        buttons = ButtonMaker()
        buttons.cb_buildbutton("Back", f"rss back {user_id}")
        buttons.cb_buildbutton("Close", f"rss close {user_id}")
        button = buttons.build_menu(2)
        await editMessage(RSS_HELP_MESSAGE, message, button)
        pfunc = partial(rssSub, pre_event=query)
        await event_handler(client, query, pfunc)
    elif data[1] == "list":
        handler_dict[user_id] = False
        if len(rss_dict.get(int(data[2]), {})) == 0:
            await query.answer(text="📭 No subscriptions!", show_alert=True)
        else:
            await query.answer()
            start = int(data[3])
            await rssList(query, start)
    elif data[1] == "get":
        handler_dict[user_id] = False
        if len(rss_dict.get(int(data[2]), {})) == 0:
            await query.answer(text="No subscriptions!", show_alert=True)
        else:
            await query.answer()
            buttons = ButtonMaker()
            buttons.cb_buildbutton("Back", f"rss back {user_id}")
            buttons.cb_buildbutton("Close", f"rss close {user_id}")
            button = buttons.build_menu(2)
            await editMessage(
                "Send one title with value separated by space get last X items.\nTitle Value\nTimeout: 60 sec.",
                message,
                button,
            )
            pfunc = partial(rssGet, pre_event=query)
            await event_handler(client, query, pfunc)
    elif data[1] in ["unsubscribe", "pause", "resume"]:
        handler_dict[user_id] = False
        if len(rss_dict.get(int(data[2]), {})) == 0:
            await query.answer(text="No subscriptions!", show_alert=True)
        else:
            await query.answer()
            buttons = ButtonMaker()
            buttons.cb_buildbutton("Back", f"rss back {user_id}")
            if data[1] == "pause":
                buttons.cb_buildbutton("Pause AllMyFeeds", f"rss uallpause {user_id}")
            elif data[1] == "resume":
                buttons.cb_buildbutton("Resume AllMyFeeds", f"rss uallresume {user_id}")
            elif data[1] == "unsubscribe":
                buttons.cb_buildbutton("Unsub AllMyFeeds", f"rss uallunsub {user_id}")
            buttons.cb_buildbutton("Close", f"rss close {user_id}")
            button = buttons.build_menu(2)
            await editMessage(
                f"Send one or more rss titles separated by space to {data[1]}.\nTimeout: 60 sec.",
                message,
                button,
            )
            pfunc = partial(rssUpdate, pre_event=query, state=data[1])
            await event_handler(client, query, pfunc)
    elif data[1] == "edit":
        handler_dict[user_id] = False
        if len(rss_dict.get(int(data[2]), {})) == 0:
            await query.answer(text="No subscriptions!", show_alert=True)
        else:
            await query.answer()
            buttons = ButtonMaker()
            buttons.cb_buildbutton("Back", f"rss back {user_id}")
            buttons.cb_buildbutton("Close", f"rss close {user_id}")
            button = buttons.build_menu(2)
            msg = """Send one or more rss titles with new filters or command separated by new line.
Examples:
Title1 c: mirror exf: none inf: 1080 or 720 opt: up: remote:path/subdir
Title2 c: none inf: none opt: none stv
Title3 -c mirror -inf "1080 or 720" -stv
Note: Only what you provide will be edited, the rest will be the same like example 2: exf will stay same as it is.
Use <code>stv</code> or <code>-stv</code> for case-sensitive filtering.
Timeout: 60 sec.
            """
            await editMessage(msg, message, button)
            pfunc = partial(rssEdit, pre_event=query)
            await event_handler(client, query, pfunc)
    elif data[1] == "usethis":
        # Use This Chat button handler
        handler_dict[user_id] = False
        await query.answer()
        buttons = ButtonMaker()
        buttons.cb_buildbutton("Back", f"rss back {user_id}")
        buttons.cb_buildbutton("Close", f"rss close {user_id}")
        button = buttons.build_menu(2)
        
        chat_id = query.message.chat.id
        thread_id = query.message.message_thread_id if hasattr(query.message, 'message_thread_id') else None
        
        if thread_id:
            msg = f"Current chat detected: <code>{chat_id}|{thread_id}</code>\n\nSend <code>/confirm</code> to set this as RSS chat, or any other text to cancel.\nTimeout: 60 sec."
        else:
            msg = f"Current chat detected: <code>{chat_id}</code>\n\nSend <code>/confirm</code> to set this as RSS chat, or any other text to cancel.\nTimeout: 60 sec."
        
        await editMessage(msg, message, button)
        pfunc = partial(setRssChat, pre_event=query)
        await event_handler(client, query, pfunc)
    elif data[1].startswith("uall"):
        handler_dict[user_id] = False
        if len(rss_dict.get(int(data[2]), {})) == 0:
            await query.answer(text="No subscriptions!", show_alert=True)
            return
        await query.answer()
        if data[1].endswith("unsub"):
            async with rss_dict_lock:
                del rss_dict[int(data[2])]
            if DATABASE_URL:
                await database.rss_delete(int(data[2]))
            await updateRssMenu(query)
        elif data[1].endswith("pause"):
            async with rss_dict_lock:
                for title in list(rss_dict[int(data[2])].keys()):
                    rss_dict[int(data[2])][title]["paused"] = True
            if DATABASE_URL:
                await database.rss_update(int(data[2]))
        elif data[1].endswith("resume"):
            async with rss_dict_lock:
                for title in list(rss_dict[int(data[2])].keys()):
                    rss_dict[int(data[2])][title]["paused"] = False
            if scheduler.state == 2:
                scheduler.resume()
            if DATABASE_URL:
                await database.rss_update(int(data[2]))
        await updateRssMenu(query)
    elif data[1].startswith("all"):
        if len(rss_dict) == 0:
            await query.answer(text="No subscriptions!", show_alert=True)
            return
        await query.answer()
        if data[1].endswith("unsub"):
            async with rss_dict_lock:
                rss_dict.clear()
            if DATABASE_URL:
                await database.trunc_table("rss")
            await updateRssMenu(query)
        elif data[1].endswith("pause"):
            async with rss_dict_lock:
                for user in list(rss_dict.keys()):
                    for title in list(rss_dict[user].keys()):
                        rss_dict[int(data[2])][title]["paused"] = True
            if scheduler.running:
                scheduler.pause()
            if DATABASE_URL:
                await database.rss_update_all()
        elif data[1].endswith("resume"):
            async with rss_dict_lock:
                for user in list(rss_dict.keys()):
                    for title in list(rss_dict[user].keys()):
                        rss_dict[int(data[2])][title]["paused"] = False
            if scheduler.state == 2:
                scheduler.resume()
            elif not scheduler.running:
                addJob(config_dict["RSS_DELAY"])
                scheduler.start()
            if DATABASE_URL:
                await database.rss_update_all()
    elif data[1] == "deluser":
        if len(rss_dict) == 0:
            await query.answer(text="No subscriptions!", show_alert=True)
        else:
            await query.answer()
            buttons = ButtonMaker()
            buttons.cb_buildbutton("Back", f"rss back {user_id}")
            buttons.cb_buildbutton("Close", f"rss close {user_id}")
            button = buttons.build_menu(2)
            msg = "Send one or more user_id separated by space to delete their resources.\nTimeout: 60 sec."
            await editMessage(msg, message, button)
            pfunc = partial(rssDelete, pre_event=query)
            await event_handler(client, query, pfunc)
    elif data[1] == "listall":
        if not rss_dict:
            await query.answer(text="No subscriptions!", show_alert=True)
        else:
            await query.answer()
            start = int(data[3])
            await rssList(query, start, all_users=True)
    elif data[1] == "shutdown":
        if scheduler.running:
            await query.answer()
            scheduler.shutdown(wait=False)
            await sleep(0.5)
            await updateRssMenu(query)
        else:
            await query.answer(text="ℹ️ Already Stopped!", show_alert=True)
    elif data[1] == "start":
        if not scheduler.running:
            await query.answer()
            addJob(config_dict["RSS_DELAY"])
            scheduler.start()
            await updateRssMenu(query)
        else:
            await query.answer(text="ℹ️ Already Running!", show_alert=True)


async def rssMonitor():
    if not config_dict.get("RSS_CHAT_ID"):
        LOGGER.warning("RSS_CHAT_ID not added! Shutting down rss scheduler...")
        scheduler.shutdown(wait=False)
        return
    
    # Parse chat_id and topic_id
    rss_chat_id, rss_topic_id = _parse_chat_id(config_dict.get("RSS_CHAT_ID"))
    if not rss_chat_id:
        LOGGER.warning("Invalid RSS_CHAT_ID! Shutting down rss scheduler...")
        scheduler.shutdown(wait=False)
        return
    
    if len(rss_dict) == 0:
        scheduler.pause()
        return
    
    all_paused = True
    rss_size_limit = config_dict.get("RSS_SIZE_LIMIT", 0)
    
    for user, items in list(rss_dict.items()):
        for title, data in list(items.items()):
            await sleep(0)
            try:
                if data.get("paused", False):
                    continue
                
                # Retry logic: try up to 3 times
                html = None
                tries = 0
                last_error = None
                while tries < 3:
                    try:
                        async with ClientSession(headers=RSS_HEADERS, trust_env=True) as session:
                            async with session.get(data["link"]) as res:
                                html = await res.text()
                        break
                    except Exception as e:
                        tries += 1
                        last_error = e
                        if tries >= 3:
                            raise
                        LOGGER.warning(f"Retry {tries}/3 for feed {title}: {e}")
                        await sleep(2 ** tries)  # Exponential backoff
                
                rss_d = feedparse(html)
                try:
                    last_link = rss_d.entries[0]["links"][1]["href"]
                except IndexError:
                    last_link = rss_d.entries[0]["link"]
                last_title = rss_d.entries[0]["title"]
                
                if data.get("last_feed") == last_link or data.get("last_title") == last_title:
                    all_paused = False
                    continue
                
                all_paused = False
                feed_count = 0
                
                while True:
                    try:
                        await sleep(10)
                    except Exception:
                        raise RssShutdownException("Rss Monitor Stopped!")
                    
                    try:
                        item_title = rss_d.entries[feed_count]["title"]
                        try:
                            url = rss_d.entries[feed_count]["links"][1]["href"]
                        except IndexError:
                            url = rss_d.entries[feed_count]["link"]
                        
                        if data.get("last_feed") == url or data.get("last_title") == item_title:
                            break
                    except IndexError:
                        LOGGER.warning(
                            f"Reached Max index no. {feed_count} for this feed: {title}. Maybe you need to use less RSS_DELAY to not miss some torrents"
                        )
                        break
                    
                    # Check size limit if configured
                    if rss_size_limit > 0:
                        size = 0
                        # Try to get size from feed entry
                        entry = rss_d.entries[feed_count]
                        if entry.get("size"):
                            try:
                                size = int(entry["size"])
                            except (ValueError, TypeError):
                                size = 0
                        elif entry.get("summary"):
                            # Try to extract size from summary
                            summary = entry["summary"]
                            matches = size_regex.findall(summary)
                            if matches:
                                size = get_size_bytes(matches[0])
                        
                        if size > rss_size_limit:
                            LOGGER.info(f"Skipping {item_title}: size {size} bytes exceeds limit {rss_size_limit}")
                            feed_count += 1
                            continue
                    
                    # Apply filters with case sensitivity support
                    parse = True
                    sensitive = data.get("sensitive", False)
                    
                    for flist in data.get("inf", []):
                        if sensitive:
                            # Case-sensitive check
                            if all(x not in item_title for x in flist):
                                parse = False
                                feed_count += 1
                                break
                        else:
                            # Case-insensitive check (original behavior)
                            if all(x.lower() not in item_title.lower() for x in flist):
                                parse = False
                                feed_count += 1
                                break
                    
                    if not parse:
                        continue
                    
                    for flist in data.get("exf", []):
                        if sensitive:
                            # Case-sensitive check
                            if any(x in item_title for x in flist):
                                parse = False
                                feed_count += 1
                                break
                        else:
                            # Case-insensitive check (original behavior)
                            if any(x.lower() in item_title.lower() for x in flist):
                                parse = False
                                feed_count += 1
                                break
                    
                    if not parse:
                        continue
                    
                    # Execute command
                    cmd = data.get("command")
                    options = data.get("options") or ""
                    tag = data.get("tag", "")
                    
                    if cmd:
                        # Use direct handler invocation
                        success = await _start_rss_download(user, cmd, url, options, tag)
                        if not success:
                            # Fallback to sending message if handler invocation fails
                            feed_msg = f"/{cmd.replace('/', '')} {url} {options}".strip()
                            feed_msg += f"\n<b>Tag: </b><code>{tag}</code> <code>{user}</code>"
                            await sendRss(feed_msg, rss_chat_id, rss_topic_id)
                    else:
                        feed_msg = f"<b>Name: </b><code>{item_title.replace('>', '').replace('<', '')}</code>\n\n"
                        feed_msg += f"<b>Link: </b><code>{url}</code>"
                        feed_msg += f"\n<b>Tag: </b><code>{tag}</code> <code>{user}</code>"
                        await sendRss(feed_msg, rss_chat_id, rss_topic_id)
                    
                    feed_count += 1
                
                async with rss_dict_lock:
                    if user not in rss_dict or not rss_dict[user].get(title, False):
                        continue
                    rss_dict[user][title].update(
                        {"last_feed": last_link, "last_title": last_title}
                    )
                await database.rss_update(user)
                LOGGER.info(f"Feed Name: {title}")
                LOGGER.info(f"Last item: {last_link}")
                
            except RssShutdownException as ex:
                LOGGER.info(ex)
                break
            except Exception as e:
                LOGGER.error(f"{e} Feed Name: {title} - Feed Link: {data.get('link', 'N/A')}")
                continue
    
    if all_paused:
        scheduler.pause()


def addJob(delay):
    scheduler.add_job(
        rssMonitor,
        trigger=IntervalTrigger(seconds=delay),
        id="0",
        name="RSS",
        misfire_grace_time=15,
        max_instances=1,
        next_run_time=datetime.now() + timedelta(seconds=20),
        replace_existing=True,
    )


addJob(config_dict["RSS_DELAY"])
scheduler.start()

bot.add_handler(
    MessageHandler(
        getRssMenu, filters=command(BotCommands.RssCommand) & CustomFilters.user_filter
    )
)
bot.add_handler(CallbackQueryHandler(rssListener, filters=regex("^rss")))
