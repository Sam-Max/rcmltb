from pyrogram.filters import create
from bot import OWNER_ID, user_data


class CustomFilters:
    async def custom_owner_filter(self, _, update):
        uid = update.from_user.id or update.sender_chat.id
        return uid == OWNER_ID

    owner_filter = create(custom_owner_filter)

    async def custom_chat_filter(self, _, update):
        chat_id = update.chat.id
        return chat_id in user_data and user_data[chat_id].get("is_auth", False)

    chat_filter = create(custom_chat_filter)

    async def custom_user_filter(self, _, update):
        uid = update.from_user.id or update.sender_chat.id
        return (
            uid == OWNER_ID
            or uid in user_data
            and (
                user_data[uid].get("is_auth", False)
                or user_data[uid].get("is_sudo", False)
            )
        )

    user_filter = create(custom_user_filter)

    async def custom_sudo_filter(self, _, update):
        uid = update.from_user.id or update.sender_chat.id
        return uid in user_data and user_data[uid].get("is_sudo")

    sudo_filter = create(custom_sudo_filter)

    @staticmethod
    def _owner_query(uid):
        return uid == OWNER_ID or uid in user_data and user_data[uid].get("is_sudo")
