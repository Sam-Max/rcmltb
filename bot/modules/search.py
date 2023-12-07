from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex
from aiohttp import ClientSession
from html import escape
from urllib.parse import quote
from bot import bot, LOGGER, config_dict, tmdb_titles, get_client
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import editMessage, sendMessage
from bot.helper.ext_utils.telegraph_helper import telegraph
from bot.helper.ext_utils.bot_utils import get_readable_file_size, run_sync


SITES = None
TELEGRAPH_LIMIT = 300
PLUGINS = []


async def initiate_search_tools():
    qbclient = await run_sync(get_client)
    qb_plugins = await run_sync(qbclient.search_plugins)
    if SEARCH_PLUGINS := config_dict["SEARCH_PLUGINS"]:
        globals()["PLUGINS"] = []
        src_plugins = eval(SEARCH_PLUGINS)
        if qb_plugins:
            names = [plugin["name"] for plugin in qb_plugins]
            await run_sync(qbclient.search_uninstall_plugin, names=names)
        await run_sync(qbclient.search_install_plugin, src_plugins)
    elif qb_plugins:
        for plugin in qb_plugins:
            await run_sync(qbclient.search_uninstall_plugin, names=plugin["name"])
        globals()["PLUGINS"] = []
    await run_sync(qbclient.auth_log_out)

    if SEARCH_API_LINK := config_dict["SEARCH_API_LINK"]:
        global SITES
        try:
            async with ClientSession(trust_env=True) as c:
                async with c.get(f"{SEARCH_API_LINK}/api/v1/sites") as res:
                    data = await res.json()
            SITES = {
                str(site): str(site).capitalize() for site in data["supported_sites"]
            }
            SITES["all"] = "All"
        except Exception as e:
            LOGGER.error(
                f"{e} Can't fetching sites from SEARCH_API_LINK make sure use latest version of API"
            )
            SITES = None


async def _search(key, site, message, method):
    if method.startswith("api"):
        SEARCH_API_LINK = config_dict["SEARCH_API_LINK"]
        SEARCH_LIMIT = config_dict["SEARCH_LIMIT"]
        if method == "apisearch":
            LOGGER.info(f"API Searching: {key} from {site}")
            if site == "all":
                api = f"{SEARCH_API_LINK}/api/v1/all/search?query={key}&limit={SEARCH_LIMIT}"
            else:
                api = f"{SEARCH_API_LINK}/api/v1/search?site={site}&query={key}&limit={SEARCH_LIMIT}"
        elif method == "apitrend":
            LOGGER.info(f"API Trending from {site}")
            if site == "all":
                api = f"{SEARCH_API_LINK}/api/v1/all/trending?limit={SEARCH_LIMIT}"
            else:
                api = f"{SEARCH_API_LINK}/api/v1/trending?site={site}&limit={SEARCH_LIMIT}"
        elif method == "apirecent":
            LOGGER.info(f"API Recent from {site}")
            if site == "all":
                api = f"{SEARCH_API_LINK}/api/v1/all/recent?limit={SEARCH_LIMIT}"
            else:
                api = (
                    f"{SEARCH_API_LINK}/api/v1/recent?site={site}&limit={SEARCH_LIMIT}"
                )
        try:
            async with ClientSession(trust_env=True) as c:
                async with c.get(api) as res:
                    search_results = await res.json()
            if "error" in search_results or search_results["total"] == 0:
                await editMessage(
                    f"No result found for <i>{key}</i>\nTorrent Site:- <i>{SITES.get(site)}</i>",
                    message,
                )
                return
            msg = f"<b>Found {min(search_results['total'], TELEGRAPH_LIMIT)}</b>"
            if method == "apitrend":
                msg += f" <b>trending result(s)\nTorrent Site:- <i>{SITES.get(site)}</i></b>"
            elif method == "apirecent":
                msg += (
                    f" <b>recent result(s)\nTorrent Site:- <i>{SITES.get(site)}</i></b>"
                )
            else:
                msg += f" <b>result(s) for <i>{key}</i>\nTorrent Site:- <i>{SITES.get(site)}</i></b>"
            search_results = search_results["data"]
        except Exception as e:
            await editMessage(str(e), message)
            return
    else:
        LOGGER.info(f"PLUGINS Searching: {key} from {site}")
        client = await run_sync(get_client)
        search = await run_sync(
            client.search_start, pattern=key, plugins=site, category="all"
        )
        search_id = search.id
        while True:
            result_status = await run_sync(client.search_status, search_id=search_id)
            status = result_status[0].status
            if status != "Running":
                break
        dict_search_results = await run_sync(
            client.search_results, search_id=search_id, limit=TELEGRAPH_LIMIT
        )
        search_results = dict_search_results.results
        total_results = dict_search_results.total
        if total_results == 0:
            await editMessage(
                f"No result found for <i>{key}</i>\nTorrent Site:- <i>{site.capitalize()}</i>",
                message,
            )
            return
        msg = f"<b>Found {min(total_results, TELEGRAPH_LIMIT)}</b>"
        msg += f" <b>result(s) for <i>{key}</i>\nTorrent Site:- <i>{site.capitalize()}</i></b>"
        await run_sync(client.search_delete, search_id=search_id)
        await run_sync(client.auth_log_out)

    link = await __getResult(search_results, key, message, method)
    buttons = ButtonMaker()
    buttons.url_buildbutton("🔎 VIEW", link)
    button = buttons.build_menu(1)
    await editMessage(msg, message, button)


async def __getResult(search_results, key, message, method):
    telegraph_content = []
    if method == "apirecent":
        msg = "<h4>API Recent Results</h4>"
    elif method == "apisearch":
        msg = f"<h4>API Search Result(s) For {key}</h4>"
    elif method == "apitrend":
        msg = "<h4>API Trending Results</h4>"
    else:
        msg = f"<h4>PLUGINS Search Result(s) For {key}</h4>"
    for index, result in enumerate(search_results, start=1):
        if method.startswith("api"):
            try:
                if "name" in result.keys():
                    msg += f"<code><a href='{result['url']}'>{escape(result['name'])}</a></code><br>"
                if "torrents" in result.keys():
                    for subres in result["torrents"]:
                        msg += f"<b>Quality: </b>{subres['quality']} | <b>Type: </b>{subres['type']} | "
                        msg += f"<b>Size: </b>{subres['size']}<br>"
                        if "torrent" in subres.keys():
                            msg += f"<a href='{subres['torrent']}'>Direct Link</a><br>"
                        elif "magnet" in subres.keys():
                            msg += "<b>Share Magnet to</b> "
                            msg += f"<a href='http://t.me/share/url?url={subres['magnet']}'>Telegram</a><br>"
                    msg += "<br>"
                else:
                    msg += f"<b>Size: </b>{result['size']}<br>"
                    try:
                        msg += f"<b>Seeders: </b>{result['seeders']} | <b>Leechers: </b>{result['leechers']}<br>"
                    except:
                        pass
                    if "torrent" in result.keys():
                        msg += f"<a href='{result['torrent']}'>Direct Link</a><br><br>"
                    elif "magnet" in result.keys():
                        msg += "<b>Share Magnet to</b> "
                        msg += f"<a href='http://t.me/share/url?url={quote(result['magnet'])}'>Telegram</a><br><br>"
                    else:
                        msg += "<br>"
            except:
                continue
        else:
            msg += f"<a href='{result.descrLink}'>{escape(result.fileName)}</a><br>"
            msg += f"<b>Size: </b>{get_readable_file_size(result.fileSize)}<br>"
            msg += f"<b>Seeders: </b>{result.nbSeeders} | <b>Leechers: </b>{result.nbLeechers}<br>"
            link = result.fileUrl
            if link.startswith("magnet:"):
                msg += f"<b>Share Magnet to</b> <a href='http://t.me/share/url?url={quote(link)}'>Telegram</a><br><br>"
            else:
                msg += f"<a href='{link}'>Direct Link</a><br><br>"

        if len(msg.encode("utf-8")) > 39000:
            telegraph_content.append(msg)
            msg = ""

        if index == TELEGRAPH_LIMIT:
            break

    if msg != "":
        telegraph_content.append(msg)

    await editMessage(
        f"<b>Creating</b> {len(telegraph_content)} <b>Telegraph pages.</b>", message
    )
    path = [
        (
            await telegraph.create_page(
                title="Mirror-leech-bot Torrent Search", content=content
            )
        )["path"]
        for content in telegraph_content
    ]
    if len(path) > 1:
        await editMessage(
            f"<b>Editing</b> {len(telegraph_content)} <b>Telegraph pages.</b>", message
        )
        await telegraph.edit_telegraph(path, telegraph_content)
    return f"https://telegra.ph/{path[0]}"


async def tmdbSearch(message, id):
    buttons = ButtonMaker()
    user_id = message.from_user.id
    SEARCH_PLUGINS = config_dict["SEARCH_PLUGINS"]
    if SITES is None and not SEARCH_PLUGINS:
        await editMessage(
            "No API link or search PLUGINS added for this function", message
        )
    elif SITES is not None and SEARCH_PLUGINS:
        buttons.cb_buildbutton("Api", f"torser^{user_id}^apisearch^_^{id}")
        buttons.cb_buildbutton("Plugins", f"torser^{user_id}^plugin^_^{id}")
        buttons.cb_buildbutton("Cancel", f"torser^{user_id}^cancel")
        button = buttons.build_menu(2)
        await editMessage("Choose tool to search:", message, button)
    elif SITES is not None:
        button = __api_buttons(user_id, "apisearch", id, True)
        await editMessage("Choose site to search | API:", message, button)
    else:
        button = await _plugin_buttons(user_id, id, True)
        await editMessage("Choose site to search | Plugins:", message, button)


async def torrentSearch(_, message):
    user_id = message.from_user.id
    buttons = ButtonMaker()
    key = message.text.split()
    SEARCH_PLUGINS = config_dict["SEARCH_PLUGINS"]
    if SITES is None and not SEARCH_PLUGINS:
        await sendMessage(
            "No API link or search PLUGINS added for this function", message
        )
    elif len(key) == 1 and SITES is None:
        await sendMessage("Send a search key along with command", message)
    elif len(key) == 1:
        buttons.cb_buildbutton("Trending", f"torser^{user_id}^apitrend")
        buttons.cb_buildbutton("Recent", f"torser^{user_id}^apirecent")
        buttons.cb_buildbutton("Cancel", f"torser^{user_id}^cancel")
        button = buttons.build_menu(2)
        await sendMessage("Send a search key along with command", message, button)
    elif SITES is not None and SEARCH_PLUGINS:
        buttons.cb_buildbutton("Api", f"torser^{user_id}^apisearch")
        buttons.cb_buildbutton("Plugins", f"torser^{user_id}^plugin")
        buttons.cb_buildbutton("Cancel", f"torser^{user_id}^cancel")
        button = buttons.build_menu(2)
        await sendMessage("Choose tool to search:", message, button)
    elif SITES is not None:
        button = __api_buttons(user_id, "apisearch")
        await sendMessage("Choose site to search | API:", message, button)
    else:
        button = await _plugin_buttons(user_id)
        await sendMessage("Choose site to search | Plugins:", message, button)


def __api_buttons(user_id, method, id=None, is_tdmb=False):
    buttons = ButtonMaker()
    for data, name in SITES.items():
        if is_tdmb:
            buttons.cb_buildbutton(name, f"torser^{user_id}^{data}^{method}^{id}")
        else:
            buttons.cb_buildbutton(name, f"torser^{user_id}^{data}^{method}")
    buttons.cb_buildbutton("Cancel", f"torser^{user_id}^cancel")
    return buttons.build_menu(2)


async def _plugin_buttons(user_id, id=None, is_tdmb=False):
    buttons = ButtonMaker()
    if not PLUGINS:
        qbclient = await run_sync(get_client)
        pl = await run_sync(qbclient.search_plugins)
        for name in pl:
            PLUGINS.append(name["name"])
        await run_sync(qbclient.auth_log_out)
    for siteName in PLUGINS:
        if is_tdmb:
            buttons.cb_buildbutton(
                siteName.capitalize(), f"torser^{user_id}^{siteName}^plugin^{id}"
            )
        else:
            buttons.cb_buildbutton(
                siteName.capitalize(), f"torser^{user_id}^{siteName}^plugin"
            )
    if is_tdmb:
        buttons.cb_buildbutton("All", f"torser^{user_id}^all^plugin^{id}")
    else:
        buttons.cb_buildbutton("All", f"torser^{user_id}^all^plugin")
    buttons.cb_buildbutton("Cancel", f"torser^{user_id}^cancel")
    return buttons.build_menu(2)


async def torrentSearchUpdate(_, query):
    message = query.message
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        user_id = message.from_user.id
    data = query.data.split("^")
    if len(data) > 4:
        title = tmdb_titles.get(int(data[4]), "")
        key = title
    else:
        key = message.reply_to_message.text.split(maxsplit=1)
        if len(key) > 1:
            key = key[1].strip()
        else:
            key = None
    if user_id != int(data[1]):
        await query.answer("Not Yours!", show_alert=True)
    if data[2].startswith("api"):
        await query.answer()
        if len(data) > 4:
            button = __api_buttons(user_id, data[2], data[4], True)
        else:
            button = __api_buttons(user_id, data[2])
        await editMessage("Choose site:", message, button)
    elif data[2] == "plugin":
        await query.answer()
        if len(data) > 4:
            button = await _plugin_buttons(user_id, data[4], True)
        else:
            button = await _plugin_buttons(user_id)
        await editMessage("Choose site:", message, button)
    elif data[2] != "cancel":
        await query.answer()
        site = data[2]
        method = data[3]
        if method.startswith("api"):
            if key is None:
                if method == "apirecent":
                    endpoint = "Recent"
                elif method == "apitrend":
                    endpoint = "Trending"
                await editMessage(
                    f"<b>Listing {endpoint} Items...\nTorrent Site:- <i>{SITES.get(site)}</i></b>",
                    message,
                )
            else:
                await editMessage(
                    f"<b>⏳ Searching for <i>{key}</i>\nTorrent Site:- <i>{SITES.get(site)}</i></b>",
                    message,
                )
        else:
            await editMessage(
                f"<b>⏳ Searching for <i>{key}</i>\nTorrent Site:- <i>{site.capitalize()}</i></b>",
                message,
            )
        await _search(key, site, message, method)
    else:
        await query.answer()
        await editMessage("Search has been canceled!", message)


bot.add_handler(
    MessageHandler(torrentSearch, filters=command(BotCommands.SearchCommand))
)
bot.add_handler(CallbackQueryHandler(torrentSearchUpdate, filters=regex("^torser")))
