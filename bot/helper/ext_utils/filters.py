from pyrogram import filters
from bot import ALLOWED_CHATS, OWNER_ID, SUDO_USERS

class CustomFilters():
     async def custom_owner_filter(_, client, update):
          return update.from_user.id == OWNER_ID

     owner_filter = filters.create(custom_owner_filter)

     async def custom_chat_filter(_, client, update):
          return update.chat.id in ALLOWED_CHATS

     chat_filter = filters.create(custom_chat_filter)

     async def custom_user_filter(_, client, update):
          user_id= update.from_user.id
          return user_id in ALLOWED_CHATS or user_id in SUDO_USERS or user_id == OWNER_ID

     user_filter = filters.create(custom_user_filter)

     async def custom_sudo_filter(_, client, update):
          return update.from_user.id in SUDO_USERS 

     sudo_filter = filters.create(custom_sudo_filter)

     @staticmethod
     def _owner_query(user_id):
        return user_id == OWNER_ID or user_id in SUDO_USERS