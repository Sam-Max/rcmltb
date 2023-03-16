# Adapted for asyncio framework and pyrogram library and some extra modifications

from asyncio import Lock
from bot.helper.ext_utils.db_handler import DbManager
from feedparser import parse as feedparse
from asyncio import sleep
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram.filters import regex, command
from pyrogram import filters as pfilters
from datetime import datetime, timedelta
from apscheduler.triggers.interval import IntervalTrigger
from bot import LOGGER, RSS_DELAY, bot, rss_dict, config_dict, scheduler
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import editMarkup, editMessage, sendMarkup, sendMessage, sendRss
from bot.helper.ext_utils.button_build import ButtonMaker

rss_dict_lock = Lock()



async def rss(client, message):
   button= ButtonMaker() 
   button.cb_buildbutton("Subscriptions", "rss ls")
   button.cb_buildbutton("Get RSS", "rss get")
   button.cb_buildbutton("Subscribe", "rss sub")
   button.cb_buildbutton("Unsubscribe", "rss unsub")
   button.cb_buildbutton("Settings", "rss settings")
   button.cb_buildbutton("✘ Close Menu", f"rss close")
   await sendMarkup("Rss Menu", message, button.build_menu(2)) 

async def rss_list(message):
    if len(rss_dict) > 0:
        list_feed = "<b>Your subscriptions: </b>\n\n"
        for title, data in rss_dict.items():
            list_feed += f"<b>Title:</b> <code>{title}</code>\n<b>Feed Url: </b><code>{data['link']}</code>\n\n"
        await sendMessage(list_feed, message)
    else:
        await sendMessage("No subscriptions.", message)

async def rss_get(client, message):
    user_id= message.reply_to_message.from_user.id
    msg = "Send a Title Value, /ignore to cancel "
    question= await client.send_message(message.chat.id, text=msg)
    try:
        response = await client.listen.Message(pfilters.text, id=pfilters.user(user_id), timeout=60)
    except TimeoutError:
        await client.send_message(message.chat.id, text="Too late 60s gone, try again!")
    else:
        try:
            if response.text:
                if "/ignore" in response.text:
                    await client.listen.Cancel(pfilters.user(user_id))
                else:
                    msg= response.text.split(maxsplit=1)
                    if len(msg) > 1:
                        title = msg[0]
                        count = int(msg[1])
                        data = rss_dict.get(title)
                        if data is not None and count > 0:
                            try:
                                msg = await sendMessage(f"Getting the last <b>{count}</b> item(s) from {title}", message)
                                rss_d = feedparse(data['link'])
                                item_info = ""
                                for item_num in range(count):
                                    try:
                                        link = rss_d.entries[item_num]['links'][1]['href']
                                    except IndexError:
                                        link = rss_d.entries[item_num]['link']
                                    item_info += f"<b>Name: </b><code>{rss_d.entries[item_num]['title'].replace('>', '').replace('<', '')}</code>\n"
                                    item_info += f"<b>Link: </b><code>{link}</code>\n\n"
                                await editMessage(item_info, msg)
                            except IndexError as e:
                                LOGGER.error(str(e))
                                await editMessage("Parse depth exceeded. Try again with a lower value.", msg)
                            except Exception as e:
                                LOGGER.error(str(e))
                                await editMessage(str(e), msg)
                        else:
                            await sendMessage("Send a valid title/value.", message)
                    else:
                        await sendMessage("Send a title/value.", message)
        except Exception as ex:
            await sendMessage(str(ex), message) 
    finally:
        await question.delete()


async def rss_sub(client, message):
    user_id= message.reply_to_message.from_user.id
    msg = f"Use this format to add feed url: Title https://www.rss-url.com"
    msg += " f: 1080 or 720 or 144p|mkv or mp4|hevc (optional)\n\nThis filter will parse links that it's titles"
    msg += " contains `(1080 or 720 or 144p) and (mkv or mp4) and hevc` words. You can add whatever you want.\n\n"
    msg += "Another example: f:  1080  or 720p|.web. or .webrip.|hvec or x264. This will parse titles that contains"
    msg += " ( 1080  or 720p) and (.web. or .webrip.) and (hvec or x264). I have added space before and after 1080"
    msg += " to avoid wrong matching. If this `10805695` number in title it will match 1080 if added 1080 without"
    msg += " spaces after it."
    msg += "\n\nFilters Notes:\n\n1. | means and.\n\n2. Add `or` between similar keys, you can add it"
    msg += " between qualities or between extensions, so don't add filter like this f: 1080|mp4 or 720|web"
    msg += " because this will parse 1080 and (mp4 or 720) and web ... not (1080 and mp4) or (720 and web)."
    msg += "\n\n3. You can add `or` and `|` as much as you want."
    msg += "\n\n4. Take look on title if it has static special character after or before the qualities or extensions"
    msg += " or whatever and use them in filter to avoid wrong match"
    await sendMessage(msg, message)
    question= await client.send_message(message.chat.id, text="Send feed url, /ignore to cancel")
    try:
        response = await client.listen.Message(pfilters.text, id=pfilters.user(user_id), timeout=60)
    except TimeoutError:
        await client.send_message(message.chat.id, text="Too late 60s gone, try again!")
    else:
        try:
            if response.text:
                if "/ignore" in response.text:
                    await client.listen.Cancel(pfilters.user(user_id))
                else:
                    args = response.text.split(maxsplit=2)
                    title = args[0].strip()
                    feed_link = args[1].strip()
                    f_lists = []
                    filters = None

                    if len(args) == 3:
                        filters = args[2].lstrip().lower()
                        if filters.startswith('f: '):
                            filters = filters.split('f: ', 1)[1]
                            filters_list = filters.split('|')
                            for x in filters_list:
                                y = x.split(' or ')
                                f_lists.append(y)
                        else:
                            filters = None

                    exists = rss_dict.get(title)
                    if exists:
                        return await sendMessage("This title already subscribed! Choose another title!", message)
                    try:
                        rss_d = feedparse(feed_link)
                        sub_msg = "<b>Subscribed!</b>"
                        sub_msg += f"\n\n<b>Title: </b><code>{title}</code>\n<b>Feed Url: </b>{feed_link}"
                        sub_msg += f"\n\n<b>latest record for </b>{rss_d.feed.title}:"
                        sub_msg += f"\n\n<b>Name: </b><code>{rss_d.entries[0]['title'].replace('>', '').replace('<', '')}</code>"
                        try:
                            link = rss_d.entries[0]['links'][1]['href']
                        except IndexError:
                            link = rss_d.entries[0]['link']
                        sub_msg += f"\n\n<b>Link: </b><code>{link}</code>"
                        sub_msg += f"\n\n<b>Filters: </b><code>{filters}</code>"
                        last_link = rss_d.entries[0]['link']
                        last_title = rss_d.entries[0]['title']
                        async with rss_dict_lock:
                            if len(rss_dict) == 0:
                                scheduler.resume()
                            rss_dict[title] = {'link': feed_link, 'last_feed': last_link, 'last_title': last_title, 'filters': f_lists}
                        await DbManager().rss_update(title)
                        await sendMessage(sub_msg, message)
                        LOGGER.info(f"Rss Feed Added: {title} - {feed_link} - {filters}")
                    except (IndexError, AttributeError) as e:
                        msg = "The link doesn't seem to be a RSS feed or it's region-blocked!"
                        await sendMessage(msg + '\nError: ' + str(e), message)
                    except Exception as e:
                        await sendMessage(str(e), message)
        except Exception as ex:
            await sendMessage(str(ex), message) 
    finally:
        await question.delete()

async def rss_unsub(client, message):
    user_id= message.reply_to_message.from_user.id
    msg = "Send feed url title to remove, /ignore to cancel "
    question= await client.send_message(message.chat.id, text=msg)
    try:
        response = await client.listen.Message(pfilters.text, id=pfilters.user(user_id), timeout=60)
    except TimeoutError:
        await client.send_message(message.chat.id, text="Too late 60s gone, try again!")
    else:
        try:
            if response.text:
                if "/ignore" in response.text:
                    await client.listen.Cancel(pfilters.user(user_id))
                else:
                    title = response.text
                    exists = rss_dict.get(title)
                    if not exists:
                        msg = "Rss link not exists! Nothing removed!"
                        await sendMessage(msg, message)
                    else:
                        await DbManager().rss_delete(title)
                        async with rss_dict_lock:
                            del rss_dict[title]
                        await sendMessage(f"Rss link with Title: <code>{title}</code> has been removed!", message)
                        LOGGER.info(f"Rss link with Title: {title} has been removed!")
        except Exception as ex:
            await sendMessage(str(ex), message) 
    finally:
        await question.delete()

async def rss_settings(message):
    buttons = ButtonMaker()
    buttons.cb_buildbutton("Unsubscribe All", "rss unsuball")
    if scheduler.running :
        buttons.cb_buildbutton("Shutdown", "rss shutdown")
    else:
        buttons.cb_buildbutton("Start", "rss start")
    buttons.cb_buildbutton("Close", "rss close")
    button = buttons.build_menu(1)
    await editMarkup('Rss Settings', message, button)

async def rss_set_update(client, callback_query):
    query = callback_query
    user_id = query.from_user.id
    msg = query.message
    data = query.data
    data = data.split()
    if not CustomFilters._owner_query(user_id):
        await query.answer(text="You don't have permission to use these buttons!", show_alert=True)
    elif data[1] == 'ls':
        await query.answer()
        await rss_list(msg) 
    elif data[1] == 'get':
        await query.answer()
        await rss_get(client, msg)
    elif data[1] == 'sub':
        await query.answer()
        await rss_sub(client, msg)
    elif data[1] == 'unsub':
        await query.answer()
        await rss_unsub(client, msg)
    elif data[1] == 'settings':
        await query.answer()    
        await rss_settings(msg)
    elif data[1] == 'unsuball':
        await query.answer()
        if len(rss_dict) > 0:
            await DbManager().trunc_table('rss')
            async with rss_dict_lock:
                rss_dict.clear()
            scheduler.pause()
            await editMessage("All Rss Subscriptions have been removed.", msg)
        else:
            await editMessage("No subscriptions to remove!", msg)
    elif data[1] == 'shutdown':
        await query.answer()
        scheduler.shutdown(wait=False)
        await editMessage("Rss Down", msg)
    elif data[1] == 'start':
        await query.answer()
        await editMessage("Rss Started", msg)
        if scheduler.state == 2:
            scheduler.resume()
        elif not scheduler.running:
            scheduler.add_job(rss_monitor, trigger=IntervalTrigger(seconds=config_dict['RSS_DELAY']), id='0', name='RSS', misfire_grace_time=15,
                      max_instances=1, next_run_time=datetime.now()+timedelta(seconds=20), replace_existing=True)
            scheduler.start()
    else:
        await query.answer()
        await query.message.delete()
        await query.message.reply_to_message.delete()

async def rss_monitor():
    if not config_dict['RSS_CHAT_ID']:
        LOGGER.warning('RSS_CHAT_ID not added! Shutting down rss scheduler...')
        scheduler.shutdown(wait=False)
        return
    if len(rss_dict) == 0:
        scheduler.pause()
        return
    for title, data in list(rss_dict.items()):
        try:
            rss_d = feedparse(data['link'])
            last_link = rss_d.entries[0]['link']
            last_title = rss_d.entries[0]['title']
            if data['last_feed'] == last_link or data['last_title'] == last_title:
                continue
            feed_count = 0
            while True:
                try:
                    if data['last_feed'] == rss_d.entries[feed_count]['link'] or \
                       data['last_title'] == rss_d.entries[feed_count]['title']:
                       break
                except IndexError:
                    LOGGER.warning(f"Reached Max index no. {feed_count} for this feed: {title}. Maybe you need to use less RSS_DELAY to not miss some torrents")
                    break
                parse = True
                for flist in data['filters']:
                    if all(x not in str(rss_d.entries[feed_count]['title']).lower() for x in flist):
                        parse = False
                        feed_count += 1
                        break
                if not parse:
                    continue
                try:
                    url = rss_d.entries[feed_count]['links'][1]['href']
                except IndexError:
                    url = rss_d.entries[feed_count]['link']
                if RSS_COMMAND := config_dict['RSS_COMMAND']:
                    feed_msg = f"/{RSS_COMMAND.replace('/', '')} {url}"
                else:
                    feed_msg = f"<b>Name: </b><code>{rss_d.entries[feed_count]['title'].replace('>', '').replace('<', '')}</code>\n\n"
                    feed_msg += f"<b>Link: </b><code>{url}</code>"
                await sendRss(feed_msg)
                feed_count += 1
                await sleep(5)
            async with rss_dict_lock:
                if title not in rss_dict:
                    continue
                rss_dict[title].update({'last_feed': last_link, 'last_title': last_title})
            await DbManager().rss_update(title)
            LOGGER.info(f"Feed Name: {title}")
            LOGGER.info(f"Last item: {last_link}")
        except Exception as e:
            LOGGER.error(f"{e} Feed Name: {title} - Feed Link: {data['link']}")
            continue

rss_handler = MessageHandler(rss, filters= command(BotCommands.RssCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
rss_buttons_handler = CallbackQueryHandler(rss_set_update, filters= regex("rss"))

bot.add_handler(rss_handler)
bot.add_handler(rss_buttons_handler)


scheduler.add_job(rss_monitor, trigger=IntervalTrigger(seconds=RSS_DELAY), id='0', name='RSS', misfire_grace_time=15,
                      max_instances=1, next_run_time=datetime.now()+timedelta(seconds=20), replace_existing=True)
scheduler.start()
