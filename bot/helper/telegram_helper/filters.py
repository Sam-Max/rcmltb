from pyrogram import filters
from bot import OWNER_ID, user_data

class CustomFilters():
     async def custom_owner_filter(self, client, update):
          return update.from_user.id == OWNER_ID

     owner_filter = filters.create(custom_owner_filter)

     async def custom_chat_filter(self, client, update):
          uid= update.chat.id
          return uid in user_data and user_data[uid].get('is_auth')

     chat_filter = filters.create(custom_chat_filter)

     async def custom_user_filter(self, client, update):
          uid= update.from_user.id
          return uid == OWNER_ID or uid in user_data and (user_data[uid].get('is_auth') or user_data[uid].get('is_sudo'))

     user_filter = filters.create(custom_user_filter)

     async def custom_sudo_filter(self, client, update):
          uid= update.from_user.id
          return uid in user_data and user_data[uid].get('is_sudo')

     sudo_filter = filters.create(custom_sudo_filter)

     @staticmethod
     def _owner_query(uid):
        return uid == OWNER_ID or uid in user_data and user_data[uid].get('is_sudo')