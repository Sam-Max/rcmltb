from asyncio import sleep
import os
import re
import time
from bot import bot
from bot.helper.ext_utils.bot_utils import HASH_REGEX, is_magnet, run_sync_to_async
from bot.helper.ext_utils.exceptions import ProviderException
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.mirror_leech_utils.debrid_utils.debrid_helper import RealDebrid
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import deleteMessage, sendMessage
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters


debrid_data = {}


async def load_debrid_token():
    if os.path.exists("debrid/debrid_token.txt"):
        with open("debrid/debrid_token.txt", "r") as f:
            debrid_data["token"] = f.read().strip()


async def authorize(_, query):
    message = query.message
    rd_client = RealDebrid()
    try:
        response = rd_client.get_device_code()
        text = (
            f"🔐 <b>Real-Debrid Authorization</b>\n\n"
            f"Visit the URL below and enter the code:\n"
            f"<a href='{response['verification_url']}'>{response['verification_url']}</a>\n\n"
            f"<b>Code:</b> <code>{response['user_code']}</code>\n"
            f"<b>Timeout:</b> <code>120s</code>"
        )
        await sendMessage(text, message)

        device_code = response["device_code"]
        interval = int(response["interval"])
        expires_in = int(response["expires_in"])
        start_time = time.time()

        while time.time() - start_time < expires_in:
            res = rd_client.authorize(device_code)
            if "token" in res:
                debrid_data["token"] = res["token"]
                path = f"{os.getcwd()}/debrid/debrid_token.txt"
                os.makedirs(path, exist_ok=True)
                with open(f"{path}", "w") as f:
                    f.write(res["token"])
                await sendMessage("✅ <b>Authorized</b>", message)
                break
            await sleep(1000 * interval)
    except ProviderException as e:
        await sendMessage(e.message, message)


async def get_user_torrents(_, query):
    message = query.message
    rd_client = RealDebrid(debrid_data.get("token", None))
    try:
        response = await run_sync_to_async(rd_client.get_user_torrent_list, 1, 50)
        result = ""
        msg = await sendMessage("📥 <b>Fetching torrent list...</b>", message)
        for index, res in enumerate(response, start=1):
            if res["links"]:
                res = await run_sync_to_async(
                    rd_client.create_download_link, res["links"][0]
                )
                if res:
                    result += (
                        f"{index}. <a href='{res['download']}'>{res['filename']}</a>\n"
                    )
            await sleep(0.1)
        await deleteMessage(msg)
        await sendMessage(result, msg)
    except ProviderException as e:
        await sendMessage(e.message, message)


async def get_user_downloads(_, query):
    message = query.message
    rd_client = RealDebrid(debrid_data.get("token", None))
    try:
        response = await run_sync_to_async(rd_client.get_user_downloads_list, 1, 50)
        result = ""
        for index, res in enumerate(response, start=1):
            if res["download"]:
                result += (
                    f"{index}. <a href='{res['download']}'>{res['filename']}</a>\n"
                )
        await sendMessage(result, message)
    except ProviderException as e:
        await sendMessage(e.message, message)


async def add_magnet(client, query):
    message = query.message
    rd_client = RealDebrid(debrid_data.get("token", None))
    question = await sendMessage(
        "🧲 <b>Send a magnet link</b> to add to Debrid.\n/ignore to cancel",
        message,
    )
    try:
        if response := await client.listen.Message(filters.text, timeout=60):
            if response.text:
                if "/ignore" in response.text:
                    pass
                else:
                    magnet = response.text.strip()
                    response = await run_sync_to_async(
                        rd_client.add_magent_link, magnet
                    )
                    tor_info = await run_sync_to_async(
                        rd_client.get_torrent_info, response["id"]
                    )
                    if tor_info["status"] == "waiting_files_selection":
                        await run_sync_to_async(rd_client.select_files, tor_info["id"])
                    msg = "✅ <b>Magnet link added to Debrid</b>\n\n"
                    msg += f"<b>Status:</b> <code>/info {response['id']}</code>"
                    await sendMessage(msg, query.message)
    except TimeoutError:
        await sendMessage("<b>Timed out.</b> No response in 60s, try again.", message)
    except ProviderException as e:
        await sendMessage(e.message, message)
    finally:
        await question.delete()


async def add_torrent(client, query):
    message = query.message
    rd_client = RealDebrid(debrid_data.get("token", None))
    question = await sendMessage(
        "📁 <b>Send a torrent file</b> to add to Debrid.\n/ignore to cancel",
        message,
    )
    try:
        if response := await client.listen.Message(
            filters.document | filters.text,
            timeout=60,
        ):
            if response.text and "/ignore" in response.text:
                pass
            elif (
                response.document.mime_type == "application/x-bittorrent"
                or response.document.file_name.endswith(".torrent")
            ):
                path = f"{os.getcwd()}/torrents/"
                os.makedirs(path, exist_ok=True)
                file_path = f"{path}{response.document.file_name}.torrent"
                await client.download_media(response, file_name=file_path)
                with open(file_path, "rb") as file:
                    response = await run_sync_to_async(rd_client.add_torrent_file, file)
                    if response:
                        tor_info = await run_sync_to_async(
                            rd_client.get_torrent_info, response["id"]
                        )
                        if tor_info["status"] == "waiting_files_selection":
                            await run_sync_to_async(
                                rd_client.select_files, tor_info["id"]
                            )
                        msg = "✅ <b>Torrent file added to Debrid</b>\n\n"
                        msg += f"<b>Status:</b> <code>/info {response['id']}</code>"
                        await sendMessage(msg, query.message)
    except TimeoutError:
        await sendMessage("<b>Timed out.</b> No response in 60s, try again.", message)
    except ProviderException as e:
        await sendMessage(e.message, message)
    finally:
        await question.delete()


async def delete_torrent(client, query):
    message = query.message
    rd_client = RealDebrid(debrid_data.get("token", None))
    question = await sendMessage(
        "🔢 <b>Send a torrent ID</b> to delete from Debrid.\n/ignore to cancel", message
    )
    try:
        if response := await client.listen.Message(filters.text, timeout=60):
            if "/ignore" in response.text:
                pass
            else:
                id = response.text.strip()
                await run_sync_to_async(rd_client.delete_torrent, id)
                await sendMessage("✅ <b>Torrent deleted</b>", query.message)
    except TimeoutError:
        await sendMessage("<b>Timed out.</b> No response in 60s, try again.", message)
    except ProviderException as e:
        await sendMessage(e.message, message)
    finally:
        await question.delete()


async def get_user(_, query):
    message = query.message
    rd_client = RealDebrid(debrid_data.get("token", None))
    try:
        response = await run_sync_to_async(rd_client.get_user)
        user_info = f"👤 <b>User Info</b>\n\n"
        user_info += f"<b>User:</b> <code>{response['username']}</code>\n"
        user_info += f"<b>Email:</b> <code>{response['email']}</code>\n"
        user_info += f"<b>Points:</b> <code>{response['points']}</code>\n"
        user_info += f"<b>Type:</b> <code>{response['type']}</code>\n"
        user_info += f"<b>Expiration:</b> <code>{response['expiration']}</code>"
        await sendMessage(user_info, message)
    except ProviderException as e:
        await sendMessage(e.message, message)


async def get_availabilty(client, query):
    message = query.message
    rd_client = RealDebrid(debrid_data.get("token", None))
    question = await sendMessage(
        "🔍 <b>Send a magnet link</b> to check cache availability and extract download link.\n/ignore to cancel",
        message,
    )
    try:
        if response := await client.listen.Message(filters.text, timeout=60):
            if "/ignore" in response.text:
                pass
            else:
                magnet_link = response.text.strip()
                if is_magnet(magnet_link):
                    hash = re.search(HASH_REGEX, magnet_link).group(1)
                    if hash:
                        response = await run_sync_to_async(
                            rd_client.get_torrent_instant_availability, hash
                        )
                        if hash in response:
                            response = await run_sync_to_async(
                                rd_client.add_magent_link, magnet_link
                            )
                            await run_sync_to_async(
                                rd_client.select_files, response["id"], "all"
                            )
                            torr_info = await run_sync_to_async(
                                rd_client.get_torrent_info, response["id"]
                            )
                            result = ""
                            for index, link in enumerate(torr_info["links"], start=1):
                                res = await run_sync_to_async(
                                    rd_client.create_download_link, link
                                )
                                if res:
                                    result += f"{index}. <a href='{res['download']}'>{res['filename']}</a>\n\n"
                            await sendMessage(result, message)
                        else:
                            await sendMessage("❌ <b>Torrent not cached</b>", message)
                    else:
                        await sendMessage(
                            "❌ <b>Error:</b> Failed to extract hash from magnet link.", message
                        )
    except TimeoutError:
        await sendMessage("<b>Timed out.</b> No response in 60s, try again.", message)
    except ProviderException as e:
        await sendMessage(e.message, message)
    finally:
        await question.delete()


async def torrent_info(_, message):
    _, id = message.text.split()
    rd_client = RealDebrid(debrid_data.get("token", None))
    try:
        response = await run_sync_to_async(rd_client.get_torrent_info, id)
        msg = f"<b>Torrent Info</b>\n\n"
        msg += f"<b>Name:</b> <code>{response['filename']}</code>\n"
        msg += f"<b>Total Size:</b> <code>{get_readable_file_size(response['original_bytes'])}</code>\n"
        msg += f"<b>Status:</b> <code>{response['status'].capitalize()}</code>\n"
        msg += f"<b>Progress:</b> <code>{response['progress']}%</code>"
        await sendMessage(msg, message)
    except ProviderException as e:
        await sendMessage(e.message, message)


async def generate_link(client, query):
    message = query.message
    rd_client = RealDebrid(debrid_data.get("token", None))
    try:
        res = await run_sync_to_async(rd_client.get_hosts)
        hosts = ""
        for host in res:
            hosts += f"{host}, "
    question = await sendMessage(
        f"🌐 <b>Supported Hosts:</b> <code>{hosts}</code>\n\n<b>Send a link</b> from the above hosters to generate a direct download link.\n/ignore to cancel",
        message,
    )
        if response := await client.listen.Message(filters.text, timeout=60):
            if "/ignore" in response.text:
                pass
            else:
                link = response.text.strip()
                res = await run_sync_to_async(rd_client.create_download_link, link)
                await sendMessage(f"🔗 <b>Download Link:</b>\n{res['download']}", query.message)
    except TimeoutError:
        await sendMessage("<b>Timed out.</b> No response in 60s, try again.", message)
    except ProviderException as e:
        await sendMessage(e.message, message)
    finally:
        await question.delete()


async def rd_callback(client, query):
    message = query.message
    data = query.data.split("^")
    if data[1] == "ut":
        await get_user_torrents(client, query)
        await query.answer()
    elif data[1] == "ud":
        await get_user_downloads(client, query)
        await query.answer()
    elif data[1] == "gl":
        await generate_link(client, query)
        await query.answer()
    elif data[1] == "auth":
        await authorize(client, query)
        await query.answer()
    elif data[1] == "cha":
        await get_availabilty(client, query)
        await query.answer()
    elif data[1] == "addm":
        await add_magnet(client, query)
        await query.answer()
    elif data[1] == "addt":
        await add_torrent(client, query)
        await query.answer()
    elif data[1] == "delt":
        await delete_torrent(client, query)
        await query.answer()
    elif data[1] == "uinf":
        await get_user(client, query)
        await query.answer()
    else:
        await query.answer()
        await deleteMessage(message)


async def real_debrid(_, message):
    buttons = ButtonMaker()
    buttons.cb_buildbutton("🔐 Authorize", f"rd^auth")
    buttons.cb_buildbutton("👤 User Info", f"rd^uinf")
    buttons.cb_buildbutton("🧲 User Torrents", f"rd^ut")
    buttons.cb_buildbutton("📥 User Downloads", f"rd^ud")
    buttons.cb_buildbutton("🔍 Check Available", f"rd^cha")
    buttons.cb_buildbutton("🔗 Generate Link", f"rd^gl")
    buttons.cb_buildbutton("🧲 Add Magnet", f"rd^addm")
    buttons.cb_buildbutton("📁 Add Torrent", f"rd^addt")
    buttons.cb_buildbutton("🗑️ Delete Torrent", f"rd^delt")
    buttons.cb_buildbutton("✘ Close Menu", "rd^close", position="footer")
    msg = "⚡ <b>Debrid Menu</b>\n\n"
    msg += "<b>Note:</b> Currently supports Real-Debrid only."
    await sendMessage(msg, message, buttons.build_menu(2))


bot.add_handler(
    MessageHandler(
        real_debrid,
        filters=filters.command(BotCommands.Debrid) & (CustomFilters.user_filter),
    )
)

bot.add_handler(
    MessageHandler(
        torrent_info,
        filters=filters.command(BotCommands.DebridInfo) & (CustomFilters.user_filter),
    )
)


bot.add_handler(
    CallbackQueryHandler(rd_callback, filters=filters.regex("rd")),
)
