from os import path as ospath
from aiofiles.os import path as aiopath
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from bot import bot, user_data
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage, sendFile
from bot.helper.ext_utils.media_utils import get_detailed_media_info, format_media_info


async def mediainfo_handler(client, message):
    """
    Handler for /mediainfo command.
    Usage: Reply to a media file or provide a local path.
    """
    user_id = message.from_user.id
    reply_message = message.reply_to_message

    if reply_message:
        # Get file from reply
        file = (
            reply_message.document
            or reply_message.video
            or reply_message.audio
            or reply_message.voice
            or reply_message.video_note
            or None
        )

        if file is None:
            await sendMessage(
                "❌ <b>Reply to a media file (document, video, or audio)</b>",
                message
            )
            return

        # Get file info without downloading
        file_name = file.file_name if hasattr(file, "file_name") else "media_file"

        # For Telegram files, we can't get detailed info without downloading
        # So we send basic info from Telegram
        from bot.helper.ext_utils.human_format import get_readable_file_size

        file_size = file.file_size
        mime_type = file.mime_type if hasattr(file, "mime_type") else "Unknown"

        msg = f"""📊 <b>MediaInfo (Telegram File)</b>

<b>File:</b> <code>{file_name}</code>
<b>Size:</b> {get_readable_file_size(file_size)}
<b>MIME Type:</b> {mime_type}

<i>Note: For detailed technical info (codec, resolution, etc.), the file needs to be downloaded first or provide a local path.</i>
"""

        if hasattr(file, "duration") and file.duration:
            minutes = file.duration // 60
            seconds = file.duration % 60
            msg += f"<b>Duration:</b> {minutes}:{seconds:02d}\n"

        if hasattr(file, "width") and file.width:
            msg += f"<b>Resolution:</b> {file.width}x{file.height}\n"

        await sendMessage(msg, message)

    else:
        # Check if user provided a local path
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await sendMessage(
                """📋 <b>MediaInfo Usage:</b>

1. Reply to a media file with <code>/mediainfo</code>
2. Or provide a local path: <code>/mediainfo /path/to/file.mkv</code>""",
                message
            )
            return

        file_path = args[1].strip()

        # Security check - only allow paths in download directory or user rclone
        from bot import DOWNLOAD_DIR
        safe_prefixes = [DOWNLOAD_DIR, f"rclone/{user_id}/"]

        is_safe = any(file_path.startswith(prefix) for prefix in safe_prefixes)
        if not is_safe:
            await sendMessage(
                "❌ <b>Invalid path. Only files in download directory or your rclone config are allowed.</b>",
                message
            )
            return

        if not await aiopath.exists(file_path):
            await sendMessage(
                f"❌ <b>File not found:</b> <code>{file_path}</code>",
                message
            )
            return

        # Get detailed media info using ffprobe
        processing_msg = await sendMessage(
            "⏳ <b>Analyzing media file...</b>",
            message
        )

        info = await get_detailed_media_info(file_path)

        await processing_msg.delete()

        if info is None:
            await sendMessage(
                "❌ <b>Failed to get media info. Make sure the file is a valid media file.</b>",
                message
            )
            return

        file_name = ospath.basename(file_path)
        formatted_info = format_media_info(info, file_name)

        # If message is too long, send as file
        if len(formatted_info) > 4000:
            txt_file = f"/tmp/mediainfo_{user_id}.txt"
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write(formatted_info.replace("<b>", "").replace("</b>", "")
                                          .replace("<code>", "").replace("</code>", "")
                                          .replace("📊 ", "").replace("🎬 ", "")
                                          .replace("🔊 ", "").replace("📝 ", ""))
            await sendFile(message, txt_file)
        else:
            await sendMessage(formatted_info, message)


bot.add_handler(
    MessageHandler(
        mediainfo_handler,
        filters=filters.command(BotCommands.MediaInfoCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
