# Source: https://github.com/anasty17/mirror-leech-telegram-bot/blob/master/bot/modules/search.py
# Adapted for asyncio framework and pyrogram library

from asyncio import get_running_loop
from functools import partial
from html import escape
from urllib.parse import quote
from bot import LOGGER, SEARCH_API_LINK, SEARCH_LIMIT, SEARCH_PLUGINS, Bot, get_client
from requests import get as rget
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.message_utils import deleteMessage, editMessage, sendFile, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker
from bot.helper.ext_utils.html_helper import html_template



if SEARCH_PLUGINS is not None:
    PLUGINS = []
    qbclient = get_client()
    qb_plugins = qbclient.search_plugins()
    if qb_plugins:
        for plugin in qb_plugins:
            qbclient.search_uninstall_plugin(names=plugin['name'])
    qbclient.search_install_plugin(SEARCH_PLUGINS)
    qbclient.auth_log_out()

if SEARCH_API_LINK:
    try:
        res = rget(f'{SEARCH_API_LINK}/api/v1/sites').json()
        SITES = {str(site): str(site).capitalize() for site in res['supported_sites']}
        SITES['all'] = 'All'
    except Exception as e:
        LOGGER.error("Can't fetching sites from SEARCH_API_LINK make sure use latest version of API")
        SITES = None
else:
    SITES = None

def _api_buttons(user_id, method):
    buttons = ButtonMaker()
    for data, name in SITES.items():
        buttons.cb_buildbutton(name, f"torser {user_id} {data} {method}")
    buttons.cb_buildbutton("Cancel", f"torser {user_id} cancl")
    return buttons.build_menu(2)

def _plugin_buttons(user_id):
    buttons = ButtonMaker()
    if not PLUGINS:
        qbclient = get_client()
        pl = qbclient.search_plugins()
        for name in pl:
            PLUGINS.append(name['name'])
        qbclient.auth_log_out()
    for siteName in PLUGINS:
        buttons.cb_buildbutton(siteName.capitalize(), f"torser {user_id} {siteName} plugin")
    buttons.cb_buildbutton('All', f"torser {user_id} all plugin")
    buttons.cb_buildbutton("Cancel", f"torser {user_id} cancl")
    return buttons.build_menu(2)

async def handle_torrent_search(client, message):
    user_id = message.from_user.id
    buttons = ButtonMaker()
    args = message.text.split(maxsplit=1)
    if SITES is None and SEARCH_PLUGINS is None:
        await sendMessage("No API link or search PLUGINS added for this function", message)
    elif len(args) == 1 and SITES is None:
        await sendMessage("Send a search key along with command", message)
    elif len(args) == 1:
        buttons.cb_buildbutton('Trending', f"torser {user_id} apitrend")
        buttons.cb_buildbutton('Recent', f"torser {user_id} apirecent")
        buttons.cb_buildbutton("Cancel", f"torser {user_id} cancl")
        button = buttons.build_menu(2)
        await sendMarkup("Send a search key along with command", message, button)
    elif SITES is not None and SEARCH_PLUGINS is not None:
        buttons.cb_buildbutton('Api', f"torser {user_id} apisearch")
        buttons.cb_buildbutton('Plugins', f"torser {user_id} plugin")
        buttons.cb_buildbutton("Cancel", f"torser {user_id} cancl")
        button = buttons.build_menu(2)
        await sendMarkup('Choose tool to search:', message, button)
    elif SITES is not None:
        button = _api_buttons(user_id, "apisearch")
        await sendMarkup('Choose site to search:', message, button)
    else:
        button = _plugin_buttons(user_id)
        await sendMarkup('Choose site to search:', message, button)

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
        button = _plugin_buttons(user_id)
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
            resp = rget(api)
            search_results = resp.json()
            if "error" in search_results.keys():
                return await sendMessage("No result found for <i>{key}</i>\nTorrent Site:- <i>{SITES.get(site)}</i>", message)
            cap = f"<b>Found {search_results['total']}</b>"
            if method == 'apitrend':
                cap += f" <b>trending results\nTorrent Site:- <i>{SITES.get(site)}</i></b>"
            elif method == 'apirecent':
                cap += f" <b>recent results\nTorrent Site:- <i>{SITES.get(site)}</i></b>"
            else:
                cap += f" <b>results for <i>{key}</i>\nTorrent Site:- <i>{SITES.get(site)}</i></b>"
            search_results = search_results['data']
        except Exception as e:
            LOGGER.info(str(e)) 
    else:
        LOGGER.info(f"PLUGINS Searching: {key} from {site}")
        client = get_client()
        loop= get_running_loop()
        search = await loop.run_in_executor(None, partial(client.search_start, pattern=key, plugins=site, category='all'))
        search_id = search.id
        while True:
            result_status = await loop.run_in_executor(None, partial(client.search_status, search_id=search_id))
            status = result_status[0].status
            if status != 'Running':
                break
        dict_search_results = await loop.run_in_executor(None, partial(client.search_results, search_id=search_id))
        search_results = dict_search_results.results
        total_results = dict_search_results.total
        if total_results == 0:
            return await sendMessage(f"No result found for <i>{key}</i>\nTorrent Site:- <i>{site.capitalize()}</i>", message)
        cap = f"<b>Found {total_results}</b>"
        cap += f" <b>results for <i>{key}</i>\nTorrent Site:- <i>{site.capitalize()}</i></b>"
    hmsg = _getResult(search_results, key, method)
    name = f"{method}_{key}_{site}_{message.id}.html"
    with open(name, "w", encoding='utf-8') as f:
        f.write(html_template.replace('{msg}', hmsg).replace('{title}', f'{method}_{key}_{site}'))
    await deleteMessage(message)
    await sendFile(message.reply_to_message, name, cap)
    if not method.startswith('api'):
        await loop.run_in_executor(None, partial(client.search_delete, search_id=search_id))

def _getResult(search_results, key, method):
    if method == 'apirecent':
        msg = '<span class="container center rfontsize"><h4>API Recent Results</h4></span>'
    elif method == 'apisearch':
        msg = f'<span class="container center rfontsize"><h4>API Search Results For {key}</h4></span>'
    elif method == 'apitrend':
        msg = '<span class="container center rfontsize"><h4>API Trending Results</h4></span>'
    else:
        msg = f'<span class="container center rfontsize"><h4>PLUGINS Search Results For {key}</h4></span>'
    for result in search_results:
        msg += '<span class="container start rfontsize">'
        if method.startswith('api'):
            if 'name' in result.keys():
                msg += f"<div> <a class='withhover' href='{result['url']}'>{escape(result['name'])}</a></div>"
            if 'torrents' in result.keys():
                for subres in result['torrents']:
                    msg += f"<span class='topmarginsm'><b>Quality: </b>{subres['quality']} | "
                    msg += f"<b>Type: </b>{subres['type']} | <b>Size: </b>{subres['size']}</span>"
                    if 'torrent' in subres.keys():
                        msg += "<span class='topmarginxl'><a class='withhover' "
                        msg += f"href='{subres['torrent']}'>Direct Link</a></span>"
                    elif 'magnet' in subres.keys():
                        msg += "<span><b>Share Magnet to</b> <a class='withhover' "
                        msg += f"href='http://t.me/share/url?url={subres['magnet']}'>Telegram</a></span>"
                msg += '<br>'
            else:
                msg += f"<span class='topmarginsm'><b>Size: </b>{result['size']}</span>"
                try:
                    msg += f"<span class='topmarginsm'><b>Seeders: </b>{result['seeders']} | "
                    msg += f"<b>Leechers: </b>{result['leechers']}</span>"
                except:
                    pass
                if 'torrent' in result.keys():
                    msg += "<span class='topmarginxl'><a class='withhover' "
                    msg += f"href='{result['torrent']}'>Direct Link</a></span>"
                elif 'magnet' in result.keys():
                    msg += "<span class='topmarginxl'><b>Share Magnet to</b> <a class='withhover' "
                    msg += f"href='http://t.me/share/url?url={quote(result['magnet'])}'>Telegram</a></span>"
        else:
            msg += f"<div> <a class='withhover' href='{result.descrLink}'>{escape(result.fileName)}</a></div>"
            msg += f"<span class='topmarginsm'><b>Size: </b>{get_readable_file_size(result.fileSize)}</span>"
            msg += f"<span class='topmarginsm'><b>Seeders: </b>{result.nbSeeders} | "
            msg += f"<b>Leechers: </b>{result.nbLeechers}</span>"
            link = result.fileUrl
            if link.startswith('magnet:'):
                msg += "<span class='topmarginxl'><b>Share Magnet to</b> <a class='withhover' "
                msg += f"href='http://t.me/share/url?url={quote(link)}'>Telegram</a></span>"
            else:
                msg += f"<span class='topmarginxl'><a class='withhover' href='{link}'>Direct Link</a></span>"
        msg += '</span>'
    return msg

torrent_search_handler = MessageHandler(handle_torrent_search, filters= filters.command(BotCommands.SearchCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
torrent_search_but_handler = CallbackQueryHandler(torrent_search_but, filters= filters.regex("torser"))

Bot.add_handler(torrent_search_handler)
Bot.add_handler(torrent_search_but_handler)
        

