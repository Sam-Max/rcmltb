from pyrogram.filters import command
from pyrogram.handlers import MessageHandler

from bot import bot
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMarkup


async def bot_help(_, message):
    buttons = ButtonMaker()
    buttons.cb_buildbutton("Mirror", "help back m")
    buttons.cb_buildbutton("YT-DLP", "help back y")
    buttons.cb_buildbutton("Leech", "help back l")
    buttons.cb_buildbutton("Batch", "help back b")

    help_text = (
        "📚 <b>RCMLTB Help</b>\n\n"
        "Use the buttons below for detailed command usage menus.\n\n"
        f"• <code>/{BotCommands.MirrorCommand[0]}</code> - Mirror to cloud\n"
        f"• <code>/{BotCommands.MirrorBatchCommand[0]}</code> - Mirror multiple links\n"
        f"• <code>/{BotCommands.MirrorSelectCommand[0]}</code> - Mirror with torrent file select\n"
        f"• <code>/{BotCommands.LeechCommand[0]}</code> - Leech to Telegram\n"
        f"• <code>/{BotCommands.LeechBatchCommand[0]}</code> - Leech multiple links\n"
        f"• <code>/{BotCommands.YtdlMirrorCommand[0]}</code> - Download with YT-DLP\n"
        f"• <code>/{BotCommands.YtdlLeechCommand[0]}</code> - YT-DLP leech\n"
        f"• <code>/{BotCommands.CloneCommand}</code> - Clone cloud links\n"
        f"• <code>/{BotCommands.CopyCommand}</code> - Copy between remotes\n"
        f"• <code>/{BotCommands.SyncCommand}</code> - Sync remotes\n"
        f"• <code>/{BotCommands.BiSyncCommand}</code> - Two-way remote sync\n"
        f"• <code>/{BotCommands.RcfmCommand}</code> - Remote file manager\n"
        f"• <code>/{BotCommands.StorageCommand}</code> - Show remote storage\n"
        f"• <code>/{BotCommands.CleanupCommand}</code> - Cleanup remote paths\n"
        f"• <code>/{BotCommands.ServeCommand}</code> - Serve files on web\n"
        f"• <code>/{BotCommands.CountCommand}</code> - Count Google Drive files\n"
        f"• <code>/{BotCommands.RssCommand}</code> - RSS manager\n"
        f"• <code>/{BotCommands.TorrentSearchCommand}</code> - Torrent search\n"
        f"• <code>/{BotCommands.TMDB}</code> - TMDB search\n"
        f"• <code>/{BotCommands.Debrid}</code> - Real-Debrid tools\n"
        f"• <code>/{BotCommands.DebridInfo}</code> - Debrid account info\n"
        f"• <code>/{BotCommands.StatusCommand}</code> - Task status\n"
        f"• <code>/{BotCommands.CancelCommand}</code> - Cancel task\n"
        f"• <code>/{BotCommands.CancelAllCommand}</code> - Cancel by status/all\n"
        f"• <code>/{BotCommands.ForceStartCommand[0]}</code> - Force start queued task\n"
        f"• <code>/{BotCommands.SelectCommand}</code> - Select torrent files by GID\n"
        f"• <code>/{BotCommands.UserSetCommand}</code> - User settings\n"
        f"• <code>/{BotCommands.OwnerSetCommand}</code> - Owner settings\n"
        f"• <code>/{BotCommands.StatsCommand}</code> - System stats\n"
        f"• <code>/{BotCommands.PingCommand}</code> - Bot latency"
    )
    await sendMarkup(help_text, message, buttons.build_menu(2))


bot.add_handler(
    MessageHandler(
        bot_help,
        filters=command(BotCommands.HelpCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
