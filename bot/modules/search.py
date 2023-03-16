# Source: https://github.com/anasty17/mirror-leech-telegram-bot/blob/master/bot/modules/search.py
# Adapted for asyncio framework and pyrogram library

from html import escape
from urllib.parse import quote
from aiohttp import ClientSession
from bot import LOGGER, bot, get_client, config_dict
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import run_sync
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.message_utils import editMessage,sendMarkup, sendMessage
from bot.helper.ext_utils.button_build import ButtonMaker
from bot.helper.ext_utils.telegraph_helper import telegraph

PLUGINS = []
SITES = None
TELEGRAPH_LIMIT = 300



async def initiate_search_tools():
    qbclient = await run_sync(get_client)
    qb_plugins = await run_sync(qbclient.search_plugins)
    if SEARCH_PLUGINS := config_dict['SEARCH_PLUGINS']:
        globals()['PLUGINS'] = []
        src_plugins = eval(SEARCH_PLUGINS)
        if qb_plugins:
            for plugin in qb_plugins:
                 await run_sync(qbclient.search_uninstall_plugin, names=plugin['name'])
        await run_sync(qbclient.search_install_plugin, src_plugins)
        await run_sync(qbclient.auth_log_out)
    elif qb_plugins:
        for plugin in qb_plugins:
            await run_sync(qbclient.search_uninstall_plugin, names=plugin['name'])
        globals()['PLUGINS'] = []
    await run_sync(qbclient.auth_log_out)

    if SEARCH_API_LINK := config_dict['SEARCH_API_LINK']:
        global SITES
        try:
            async with ClientSession(trust_env=True) as c:
                async with c.get(f'{SEARCH_API_LINK}/api/v1/sites') as res:
                    data = await res.json()
            SITES = {str(site): str(site).capitalize() for site in data['supported_sites']}
            SITES['all'] = 'All'
        except Exception:
            LOGGER.error("Can't fetching sites from SEARCH_API_LINK make sure use latest version of API")
            SITES = None

def _api_buttons(user_id, method):
    buttons = ButtonMaker()
    for data, name in SITES.items():
        buttons.cb_buildbutton(name, f"torser {user_id} {data} {method}")
    buttons.cb_buildbutton("Cancel", f"torser {user_id} cancl")
    return buttons.build_menu(2)

async  def _plugin_buttons(user_id):
    buttons = ButtonMaker()
    if not PLUGINS:
        qbclient = await run_sync(get_client)
        pl = await run_sync(qbclient.search_plugins)
        for name in pl:
            PLUGINS.append(name['name'])
        await run_sync(qbclient.auth_log_out)
    for siteName in PLUGINS:
        buttons.cb_buildbutton(siteName.capitalize(), f"torser {user_id} {siteName} plugin")
    buttons.cb_buildbutton('All', f"torser {user_id} all plugin")
    buttons.cb_buildbutton("Cancel", f"torser {user_id} cancl")
    return buttons.build_menu(2)

async def handle_torrent_search(client, message):
    user_id = message.from_user.id
    buttons = ButtonMaker()
    args = message.text.split(maxsplit=1)
    SEARCH_PLUGINS = config_dict['SEARCH_PLUGINS']
    if SITES is None and not SEARCH_PLUGINS:
        await sendMessage("No API link or search PLUGINS added for this function", message)
    elif len(args) == 1 and SITES is None:
        await sendMessage("Send a search key along with command", message)
    elif len(args) == 1:
        buttons.cb_buildbutton('Trending', f"torser {user_id} apitrend")
        buttons.cb_buildbutton('Recent', f"torser {user_id} apirecent")
        buttons.cb_buildbutton("Cancel", f"torser {user_id} cancl")
        button = buttons.build_menu(2)
        await sendMarkup("Send a search key along with command", message, button)
    elif SITES is not None and SEARCH_PLUGINS:
        buttons.cb_buildbutton('Api', f"torser {user_id} apisearch")
        buttons.cb_buildbutton('Plugins', f"torser {user_id} plugin")
        buttons.cb_buildbutton("Cancel", f"torser {user_id} cancl")
        button = buttons.build_menu(2)
        await sendMarkup('Choose tool to search:', message, button)
    elif SITES is not None:
        button = _api_buttons(user_id, "apisearch")
        await sendMarkup('Choose site to search | API:', message, button)
    else:
        button = await _plugin_buttons(user_id)
        await sendMarkup('Choose site to search | Plugins:', message, button)

async def torrent_search_but(client, callback_query):
    query = callback_query
    user_id = query.from_user.id
    message = query.message
    key = message.reply_to_message.text.split(maxsplit=1)
    key = key[1].strip() if len(key) > 1 else None
    data = query.data
    data = data.split()
    if user_id != int(data[1]):
        await query.answer(text="This menu is not for you!", show_alert=True)
    elif data[2].startswith('api'):
        await query.answer()
        button = _api_buttons(user_id, data[2])
        await editMessage('Choose site:', message, button)
    elif data[2] == 'plugin':
        await query.answer()
        button = await _plugin_buttons(user_id)
        await editMessage('Choose site:', message, button)
    elif data[2] != "cancl":
        await query.answer()
        site = data[2]
        method = data[3]
        if method.startswith('api'):
            if key is None:
                if method == 'apirecent':
                    endpoint = 'Recent'
                elif method == 'apitrend':
                    endpoint = 'Trending'
                await editMessage(f"<b>Listing {endpoint} Items...\nTorrent Site:- <i>{SITES.get(site)}</i></b>", message)
            else:
                await editMessage(f"<b>Searching for <i>{key}</i>\nTorrent Site:- <i>{SITES.get(site)}</i></b>", message)
        else:
            await editMessage(f"<b>Searching for <i>{key}</i>\nTorrent Site:- <i>{site.capitalize()}</i></b>", message)
        await _search(key, site, message, method)
    else:
        await query.answer()
        await editMessage("Search has been canceled!", message)

async def _search(key, site, message, method):
    if method.startswith('api'):
        SEARCH_API_LINK = config_dict['SEARCH_API_LINK']
        SEARCH_LIMIT = config_dict['SEARCH_LIMIT']
        if method == 'apisearch':
            LOGGER.info(f"API Searching: {key} from {site}")
            if site == 'all':
                api = f"{SEARCH_API_LINK}/api/v1/all/search?query={key}&limit={SEARCH_LIMIT}"
            else:
                api = f"{SEARCH_API_LINK}/api/v1/search?site={site}&query={key}&limit={SEARCH_LIMIT}"
        elif method == 'apitrend':
            LOGGER.info(f"API Trending from {site}")
            if site == 'all':
                api = f"{SEARCH_API_LINK}/api/v1/all/trending?limit={SEARCH_LIMIT}"
            else:
                api = f"{SEARCH_API_LINK}/api/v1/trending?site={site}&limit={SEARCH_LIMIT}"
        elif method == 'apirecent':
            LOGGER.info(f"API Recent from {site}")
            if site == 'all':
                api = f"{SEARCH_API_LINK}/api/v1/all/recent?limit={SEARCH_LIMIT}"
            else:
                api = f"{SEARCH_API_LINK}/api/v1/recent?site={site}&limit={SEARCH_LIMIT}"
        try:
            async with ClientSession(trust_env=True) as c:
                async with c.get(api) as res:
                    search_results = await res.json()
            if 'error' in search_results or search_results['total'] == 0:
                await editMessage(message, f"No result found for <i>{key}</i>\nTorrent Site:- <i>{SITES.get(site)}</i>")
                return
            msg = f"<b>Found {min(search_results['total'], TELEGRAPH_LIMIT)}</b>"
            if method == 'apitrend':
                msg += f" <b>trending result(s)\nTorrent Site:- <i>{SITES.get(site)}</i></b>"
            elif method == 'apirecent':
                msg += f" <b>recent result(s)\nTorrent Site:- <i>{SITES.get(site)}</i></b>"
            else:
                msg += f" <b>result(s) for <i>{key}</i>\nTorrent Site:- <i>{SITES.get(site)}</i></b>"
            search_results = search_results['data']
        except Exception as e:
            await editMessage(message, str(e))
            LOGGER.info(str(e)) 
    else:
        LOGGER.info(f"PLUGINS Searching: {key} from {site}")
        client = await run_sync(get_client)
        search = await run_sync(client.search_start, pattern=key, plugins=site, category='all')
        search_id = search.id
        while True:
            result_status = await run_sync(client.search_status, search_id=search_id)
            status = result_status[0].status
            if status != 'Running':
                break
        dict_search_results = await run_sync(client.search_results, search_id=search_id)
        search_results = dict_search_results.results
        total_results = dict_search_results.total
        if total_results == 0:
            return await sendMessage(f"No result found for <i>{key}</i>\nTorrent Site:- <i>{site.capitalize()}</i>", message)
        msg = f"<b>Found {min(total_results, TELEGRAPH_LIMIT)}</b>"
        msg += f" <b>result(s) for <i>{key}</i>\nTorrent Site:- <i>{site.capitalize()}</i></b>"
    link = await _getResult(search_results, key, message, method)
    buttons = ButtonMaker()
    buttons.url_buildbutton("🔎 VIEW", link)
    button = buttons.build_menu(1)
    await editMessage(msg, message, button)
    if not method.startswith('api'):
        await run_sync(client.search_delete, search_id=search_id)


async def _getResult(search_results, key, message, method):
    telegraph_content = []
    if method == 'apirecent':
        msg = "<h4>API Recent Results</h4>"
    elif method == 'apisearch':
        msg = f"<h4>API Search Result(s) For {key}</h4>"
    elif method == 'apitrend':
        msg = "<h4>API Trending Results</h4>"
    else:
        msg = f"<h4>PLUGINS Search Result(s) For {key}</h4>"
    for index, result in enumerate(search_results, start=1):
        if method.startswith('api'):
            if 'name' in result.keys():
                msg += f"<code><a href='{result['url']}'>{escape(result['name'])}</a></code><br>"
            if 'torrents' in result.keys():
                for subres in result['torrents']:
                    msg += f"<b>Quality: </b>{subres['quality']} | <b>Type: </b>{subres['type']} | "
                    msg += f"<b>Size: </b>{subres['size']}<br>"
                    if 'torrent' in subres.keys():
                        msg += f"<a href='{subres['torrent']}'>Direct Link</a><br>"
                    elif 'magnet' in subres.keys():
                        msg += f"<b>Share Magnet to</b> "
                        msg += f"<a href='http://t.me/share/url?url={subres['magnet']}'>Telegram</a><br>"
                msg += '<br>'
            else:
                msg += f"<b>Size: </b>{result['size']}<br>"
                try:
                    msg += f"<b>Seeders: </b>{result['seeders']} | <b>Leechers: </b>{result['leechers']}<br>"
                except:
                    pass
                if 'torrent' in result.keys():
                    msg += f"<a href='{result['torrent']}'>Direct Link</a><br><br>"
                elif 'magnet' in result.keys():
                    msg += f"<b>Share Magnet to</b> "
                    msg += f"<a href='http://t.me/share/url?url={quote(result['magnet'])}'>Telegram</a><br><br>"
                else:
                    msg += '<br>'
        else:
            msg += f"<a href='{result.descrLink}'>{escape(result.fileName)}</a><br>"
            msg += f"<b>Size: </b>{get_readable_file_size(result.fileSize)}<br>"
            msg += f"<b>Seeders: </b>{result.nbSeeders} | <b>Leechers: </b>{result.nbLeechers}<br>"
            link = result.fileUrl
            if link.startswith('magnet:'):
                msg += f"<b>Share Magnet to</b> <a href='http://t.me/share/url?url={quote(link)}'>Telegram</a><br><br>"
            else:
                msg += f"<a href='{link}'>Direct Link</a><br><br>"
       
        if len(msg.encode('utf-8')) > 39000:
           telegraph_content.append(msg)
           msg = ""

        if index == TELEGRAPH_LIMIT:
            break

    if msg != "":
        telegraph_content.append(msg)

    await editMessage(f"<b>Creating</b> {len(telegraph_content)} <b>Telegraph pages.</b>", message)
    path = []
    for content in telegraph_content:   
        page= await telegraph.create_page(title='Torrent Search', content=content)
        path.append(page["path"])
    if len(path) > 1:
        await editMessage(f"<b>Editing</b> {len(telegraph_content)} <b>Telegraph pages.</b>", message)
        await telegraph.edit_telegraph(path, telegraph_content)
    LOGGER.info(path)
    return f"https://telegra.ph/{path[0]}"


torrent_search_handler = MessageHandler(handle_torrent_search, filters= filters.command(BotCommands.SearchCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
torrent_search_but_handler = CallbackQueryHandler(torrent_search_but, filters= filters.regex("torser"))


bot.add_handler(torrent_search_handler)
bot.add_handler(torrent_search_but_handler)
        

