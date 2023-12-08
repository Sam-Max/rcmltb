from argparse import ArgumentParser
from bot import DOWNLOAD_DIR, OWNER_ID, PARALLEL_TASKS, bot, config_dict
from asyncio import TimeoutError, sleep
from bot import bot, DOWNLOAD_DIR, config_dict, m_queue
from pyrogram import filters
from base64 import b64encode
from os import path as ospath
from re import match as re_match
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import (
    get_content_type,
    is_gdrive_link,
    is_magnet,
    is_mega_link,
    is_url,
    new_task,
    run_sync,
)
from bot.helper.mirror_leech_utils.download_utils.direct_link_generator import (
    direct_link_generator,
)
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.help_messages import MIRROR_HELP_MESSAGE
from bot.helper.ext_utils.menu_utils import Menus
from bot.helper.telegram_helper.message_utils import (
    deleteMessage,
    sendMarkup,
    sendMessage,
)
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.misc_utils import get_readable_size
from bot.helper.ext_utils.rclone_data_holder import update_rclone_data
from bot.helper.ext_utils.rclone_utils import (
    is_rclone_config,
    is_remote_selected,
    list_remotes,
)
from bot.helper.mirror_leech_utils.download_utils.aria2_download import (
    add_aria2c_download,
)
from bot.helper.mirror_leech_utils.download_utils.gd_downloader import add_gd_download
from bot.helper.mirror_leech_utils.download_utils.mega_download import add_mega_download
from bot.helper.mirror_leech_utils.download_utils.qbit_downloader import add_qb_torrent
from bot.helper.mirror_leech_utils.download_utils.telegram_downloader import (
    TelegramDownloader,
)
from bot.modules.tasks_listener import TaskListener


listener_dict = {}


async def handle_mirror(client, message):
    await mirror_leech(client, message)


# Added some modifications from base repository
async def mirror_leech(client, message, isLeech=False, sameDir=None):
    user_id = message.from_user.id
    message_id = message.id

    if not isLeech:
        if await is_rclone_config(user_id, message):
            pass
        else:
            return
        if await is_remote_selected(user_id, message):
            pass
        else:
            return

    message_list = message.text.split("\n")
    message_args = message_list[0].split()

    try:
        args = parser.parse_args(message_args[1:])
    except Exception:
        await sendMessage(MIRROR_HELP_MESSAGE, message)
        return

    select = args.select
    multi = args.multi
    seed = args.seed
    folder_name = args.folderName
    compress = args.zipPswd
    extract = args.extractPswd
    name = args.newName
    screenshots = args.screenshots
    link = " ".join(args.link)
    file = None
    seed_time = None
    ratio = None

    if not isinstance(seed, bool):
        dargs = seed.split(":")
        ratio = dargs[0] or None
        if len(dargs) == 2:
            seed_time = dargs[1] or None
        seed = True

    if folder_name:
        seed = False
        ratio = None
        seed_time = None
        folder_name = f"/{folder_name}"
        if sameDir is None:
            sameDir = {"total": multi, "tasks": set(), "name": folder_name}
        sameDir["tasks"].add(message_id)

    @new_task
    async def _run_multi():
        if multi > 1:
            await sleep(5)
            msg = [s.strip() for s in message_args]
            index = msg.index("-i")
            msg[index + 1] = f"{multi - 1}"
            nextmsg = await client.get_messages(
                message.chat.id, message.reply_to_message.id + 1
            )
            nextmsg = await sendMessage(" ".join(msg), nextmsg)
            nextmsg = await client.get_messages(message.chat.id, nextmsg.id)
            if folder_name:
                sameDir["tasks"].add(nextmsg.id)
            nextmsg.from_user = message.from_user
            await sleep(5)
            await mirror_leech(client, nextmsg, isLeech, sameDir)

    _run_multi()

    path = f"{DOWNLOAD_DIR}{message_id}{folder_name}"

    if username := message.from_user.username:
        tag = f"@{username}"
    else:
        tag = message.from_user.mention

    if reply_message := message.reply_to_message:
        file = (
            reply_message.document
            or reply_message.video
            or reply_message.audio
            or reply_message.photo
            or reply_message.voice
            or reply_message.video_note
            or reply_message.sticker
            or reply_message.animation
            or None
        )
        if file is None:
            reply_text = reply_message.text.split("\n", 1)[0].strip()
            if is_url(reply_text) or is_magnet(reply_text):
                link = reply_text
        elif reply_message.document and (
            file.mime_type == "application/x-bittorrent"
            or file.file_name.endswith(".torrent")
        ):
            link = await reply_message.download()
            file = None

    if (
        not is_url(link)
        and not is_magnet(link)
        and not ospath.exists(link)
        and file is None
    ):
        await sendMessage(MIRROR_HELP_MESSAGE, message)
        return

    if (
        not is_mega_link(link)
        and not is_magnet(link)
        and not is_gdrive_link(link)
        and not link.endswith(".torrent")
        and file is None
    ):
        content_type = await get_content_type(link)
        if content_type is None or re_match(r"text/html|text/plain", content_type):
            try:
                link = await run_sync(direct_link_generator, link)
            except DirectDownloadLinkException as e:
                if str(e).startswith("ERROR:"):
                    await sendMessage(str(e), message)
                    return

    listener = TaskListener(
        message,
        tag,
        user_id,
        compress,
        extract,
        select,
        seed,
        isLeech,
        screenshots,
        sameDir,
    )

    if file is not None:
        if reply_message and not multi:
            buttons = ButtonMaker()
            name = file.file_name if hasattr(file, "file_name") else "None"
            msg = f"<b>Which name do you want to use?</b>\n\n"
            msg += f"<b>Name</b>: <code>{name}</code>\n\n"
            msg += f"<b>Size</b>: <code>{get_readable_size(file.file_size)}</code>"
            buttons.cb_buildbutton("📄 By default", f"mirrormenu^default")
            buttons.cb_buildbutton("📝 Rename", f"mirrormenu^rename")
            buttons.cb_buildbutton("✘ Close Menu", f"mirrormenu^close", "footer")
            listener_dict[message_id] = [listener, file, message, isLeech, user_id, ""]
            await sendMarkup(msg, message, reply_markup=buttons.build_menu(2))
        else:
            tgdown = TelegramDownloader(file, client, listener, f"{path}/", name)
            if PARALLEL_TASKS:
                await m_queue.put(tgdown)
                return
            await tgdown.download()
    elif is_gdrive_link(link):
        await add_gd_download(link, path, listener, name)
    elif is_mega_link(link):
        await add_mega_download(link, f"{path}/", listener, name)
    elif is_magnet(link) or ospath.exists(link):
        await add_qb_torrent(link, path, listener, ratio, seed_time)
    else:
        ussr = args.auth_user
        pssw = args.auth_pswd
        if ussr or pssw:
            auth = f"{ussr}:{pssw}"
            auth = "Basic " + b64encode(auth.encode()).decode("ascii")
        else:
            auth = ""
        await add_aria2c_download(link, path, listener, name, auth)


async def mirror_menu(client, query):
    cmd = query.data.split("^")
    query_message = query.message
    reply_message = query_message.reply_to_message
    user_id = query.from_user.id
    message_id = reply_message.id

    info = listener_dict[message_id]
    listener = info[0]
    file = info[1]
    message = info[2]
    is_Leech = info[3]

    if int(info[-2]) != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
        return
    elif cmd[1] == "default":
        await query_message.delete()
        if config_dict["REMOTE_SELECTION"] and not is_Leech:
            await list_remotes(message, menu_type=Menus.REMOTE_SELECT)
        else:
            tgdown = TelegramDownloader(
                file, client, listener, f"{DOWNLOAD_DIR}{listener.uid}/"
            )
            if PARALLEL_TASKS:
                await m_queue.put(tgdown)
                return
            await tgdown.download()
    elif cmd[1] == "rename":
        await query_message.delete()
        question = await client.send_message(
            message.chat.id, text="Send the new name with extension, /ignore to cancel"
        )
        try:
            response = await client.listen.Message(
                filters.text, id=filters.user(user_id), timeout=60
            )
            if response:
                if "/ignore" in response.text:
                    await client.listen.Cancel(filters.user(user_id))
                else:
                    new_name = response.text.strip()
                    if config_dict["REMOTE_SELECTION"] and not is_Leech:
                        listener_dict[message_id][5] = new_name
                        await list_remotes(message, menu_type=Menus.REMOTE_SELECT)
                    else:
                        tgdown = TelegramDownloader(
                            file,
                            client,
                            listener,
                            f"{DOWNLOAD_DIR}{listener.uid}/",
                            new_name,
                        )
                        if PARALLEL_TASKS:
                            await m_queue.put(tgdown)
                            return
                        await tgdown.download()
        except TimeoutError:
            await sendMessage("Too late 60s gone, try again!", message)
        finally:
            await question.delete()
    else:
        await query.answer()
        await query_message.delete()


async def mirror_select(client, callback_query):
    query = callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id = query.from_user.id
    message_id = int(cmd[-1])

    info = listener_dict[message_id]
    listener = info[0]
    file = info[1]
    new_name = info[5]

    if int(info[-2]) != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
        return
    elif cmd[1] == "remote":
        await query.answer()
        await deleteMessage(message)
        update_rclone_data("MIRROR_SELECT_BASE_DIR", "", user_id)
        update_rclone_data("MIRROR_SELECT_REMOTE", cmd[2], user_id)
        if user_id == OWNER_ID:
            config_dict.update({"DEFAULT_OWNER_REMOTE": cmd[2]})
        tgdown = TelegramDownloader(
            file, client, listener, f"{DOWNLOAD_DIR}{listener.uid}/", new_name
        )
        if PARALLEL_TASKS:
            await m_queue.put(tgdown)
            return
        await tgdown.download()
    elif cmd[1] == "close":
        await query.answer()
        await deleteMessage(message)
    del listener_dict[message_id]


async def handle_auto_mirror(client, message):
    user_id = message.from_user.id
    if await is_rclone_config(user_id, message) == False:
        return
    if await is_remote_selected(user_id, message) == False:
        return
    file = (
        message.document
        or message.video
        or message.audio
        or message.photo
        or message.voice
        or message.video_note
        or message.sticker
        or message.animation
        or None
    )
    if username := message.from_user.username:
        tag = f"@{username}"
    else:
        tag = message.from_user.mention
    if file is not None:
        if file.mime_type != "application/x-bittorrent":
            listener = TaskListener(message, tag, user_id)
            tgdown = TelegramDownloader(
                file, client, listener, f"{DOWNLOAD_DIR}{listener.uid}/"
            )
            if PARALLEL_TASKS:
                await m_queue.put(tgdown)
                return
            await tgdown.download()


parser = ArgumentParser(description="rcmltb args usage:", argument_default="")

parser.add_argument("link", nargs="*")
parser.add_argument("-s", action="store_true", default=False, dest="select")
parser.add_argument("-d", nargs="?", default=False, const=True, dest="seed")
parser.add_argument("-i", nargs="?", default=0, dest="multi", type=int)
parser.add_argument("-m", nargs="?", default="", dest="folderName")
parser.add_argument("-n", nargs="?", default="", dest="newName")
parser.add_argument("-au", nargs="?", default=None, dest="auth_user")
parser.add_argument("-ap", nargs="?", default=None, dest="auth_pswd")
parser.add_argument("-e", nargs="?", default=None, const="", dest="extractPswd")
parser.add_argument("-z", nargs="?", default=None, const="", dest="zipPswd")
parser.add_argument("-ss", nargs="?", default=None, dest="screenshots", type=int)


bot.add_handler(
    MessageHandler(
        handle_mirror,
        filters=filters.command(BotCommands.MirrorCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
bot.add_handler(CallbackQueryHandler(mirror_menu, filters=filters.regex("mirrormenu")))
bot.add_handler(
    CallbackQueryHandler(mirror_select, filters=filters.regex("remoteselectmenu"))
)

if config_dict["AUTO_MIRROR"]:
    bot.add_handler(
        MessageHandler(
            handle_auto_mirror,
            filters=filters.video | filters.document | filters.audio | filters.photo,
        )
    )
