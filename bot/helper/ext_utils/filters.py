from pyrogram import filters
from bot import ALLOWED_CHATS, ALLOWED_USERS, OWNER_ID

class CustomFilters():
     async def custom_owner_filter(_, client, update):
          return update.from_user.id == OWNER_ID

     owner_filter = filters.create(custom_owner_filter)

     async def custom_chat_filter(_, client, update):
          return update.chat.id in ALLOWED_CHATS

     chat_filter = filters.create(custom_chat_filter)

     async def custom_user_filter(_, client, update):
          user_id= update.from_user.id
          return user_id in ALLOWED_USERS or user_id == OWNER_ID

     user_filter = filters.create(custom_user_filter)