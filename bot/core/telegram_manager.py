from asyncio import Lock
from pyrogram import Client as tgClient, enums
from pyrogram.types import LinkPreviewOptions

from bot import LOGGER
from bot.core.config_manager import Config


class TgClient:
    bot: tgClient = None
    user: tgClient = None
    NAME: str = ""
    ID: int = 0
    IS_PREMIUM_USER: bool = False
    MAX_SPLIT_SIZE: int = 2097152000
    _lock = Lock()

    @classmethod
    async def start_bot(cls):
        LOGGER.info("Creating bot Pyrogram client")
        cls.bot = tgClient(
            "pyrogram",
            api_id=Config.TELEGRAM_API_ID,
            api_hash=Config.TELEGRAM_API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=1000,
            max_concurrent_transmissions=10,
            parse_mode=enums.ParseMode.HTML,
            max_message_cache_size=15000,
            max_topic_cache_size=15000,
            sleep_threshold=0,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        from bot.conv_pyrogram import Conversation
        Conversation(cls.bot)
        await cls.bot.start()
        cls.NAME = cls.bot.me.first_name
        cls.ID = cls.bot.me.id
        LOGGER.info(f"Bot started as {cls.NAME} (ID: {cls.ID})")
        # Flush any handler registrations that were buffered before bot was ready
        import bot as bot_module
        bot_module.bot._flush_pending_handlers()

    @classmethod
    async def start_user(cls):
        if not Config.USER_SESSION_STRING:
            return
        LOGGER.info("Creating user Pyrogram client from USER_SESSION_STRING")
        cls.user = tgClient(
            "pyrogram_session",
            api_id=Config.TELEGRAM_API_ID,
            api_hash=Config.TELEGRAM_API_HASH,
            session_string=Config.USER_SESSION_STRING,
            max_concurrent_transmissions=10,
            parse_mode=enums.ParseMode.HTML,
            max_message_cache_size=15000,
            max_topic_cache_size=15000,
            sleep_threshold=60,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        await cls.user.start()
        cls.IS_PREMIUM_USER = cls.user.me.is_premium
        cls.MAX_SPLIT_SIZE = (
            4194304000 if cls.IS_PREMIUM_USER else 2097152000
        )
        LOGGER.info(
            f"User client started (Premium: {cls.IS_PREMIUM_USER})"
        )

    @classmethod
    async def stop(cls):
        if cls.bot:
            await cls.bot.stop()
        if cls.user:
            await cls.user.stop()

    @classmethod
    async def reload(cls):
        await cls.stop()
        await cls.start_bot()
        await cls.start_user()
