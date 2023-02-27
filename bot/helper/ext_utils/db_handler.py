from os import path as ospath, makedirs
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
from bot import DATABASE_URL, user_data, rss_dict, LOGGER, bot_id, config_dict, aria2_options, qbit_options, botloop



class DbManager:
    def __init__(self):
        self.__err = False
        self.__db = None
        self.__conn = None
        self.__connect()

    def __connect(self):
        try:
            self.__conn = AsyncIOMotorClient(DATABASE_URL)
            self.__db = self.__conn.rcmltb
        except PyMongoError as e:
            LOGGER.error(f"Error in DB connection: {e}")
            self.__err = True

    async def db_load(self):
        if self.__err:
            return
        # Save bot settings
        await self.__db.settings.config.update_one({'_id': bot_id}, {'$set': config_dict}, upsert=True)
        # Save Aria2c options
        if await self.__db.settings.aria2c.find_one({'_id': bot_id}) is None:
            await self.__db.settings.aria2c.update_one({'_id': bot_id}, {'$set': aria2_options}, upsert=True)
        # Save qbittorrent options
        if await self.__db.settings.qbittorrent.find_one({'_id': bot_id}) is None:
            await self.__db.settings.qbittorrent.update_one({'_id': bot_id}, {'$set': qbit_options}, upsert=True)
        # User Data
        if await self.__db.users.find_one():
            rows = self.__db.users.find({})  # return a dict ==> {_id, is_sudo, is_auth, as_doc, thumb}
            async for row in rows:
                uid = row['_id']
                del row['_id']
                path = f"Thumbnails/{uid}.jpg"
                if row.get('thumb'):
                    if not ospath.exists('Thumbnails'):
                        makedirs('Thumbnails')
                    with open(path, 'wb+') as f:
                        f.write(row['thumb'])
                    row['thumb'] = path
                user_data[uid] = row
            LOGGER.info("Users data has been imported from Database")
        # Rss Data
        if await self.__db.rss[bot_id].find_one():
            rows = self.__db.rss[bot_id].find({})  # return a dict ==> {_id, link, last_feed, last_name, filters}
            async for row in rows:
                title = row['_id']
                del row['_id']
                rss_dict[title] = row
            LOGGER.info("Rss data has been imported from Database.")
        self.__conn.close()

    async def update_config(self, dict_):
        if self.__err:
            return
        await self.__db.settings.config.update_one({'_id': bot_id}, {'$set': dict_}, upsert=True)
        self.__conn.close()

    async def update_aria2(self, key, value):
        if self.__err:
            return
        await self.__db.settings.aria2c.update_one({'_id': bot_id}, {'$set': {key: value}}, upsert=True)
        self.__conn.close()

    async def update_qbittorrent(self, key, value):
        if self.__err:
            return
        await self.__db.settings.qbittorrent.update_one({'_id': bot_id}, {'$set': {key: value}}, upsert=True)
        self.__conn.close()

    async def update_private_file(self, path):
        if self.__err:
            return
        if ospath.exists(path):
            with open(path, 'rb+') as pf:
                pf_bin = pf.read()
        else:
            pf_bin = ''
        path = path.replace('.', '__')
        await self.__db.settings.files.update_one({'_id': bot_id}, {'$set': {path: pf_bin}}, upsert=True)
        self.__conn.close()

    async def update_user_data(self, user_id):
        if self.__err:
            return
        data = user_data[user_id]
        if data.get('thumb'):
            del data['thumb']
        await self.__db.users.update_one({'_id': user_id}, {'$set': data}, upsert=True)
        self.__conn.close()

    async def update_thumb(self, user_id, path=None):
        if self.__err:
            return
        if path is not None:
            with open(path, 'rb+') as image:
                image_bin = image.read()
        else:
            image_bin = ''
        await self.__db.users.update_one({'_id': user_id}, {'$set': {'thumb': image_bin}}, upsert=True)
        self.__conn.close()

    async def rss_update(self, title):
        if self.__err:
            return
        await self.__db.rss[bot_id].update_one({'_id': title}, {'$set': rss_dict[title]}, upsert=True)
        self.__conn.close()

    async def rss_delete(self, title):
        if self.__err:
            return
        await self.__db.rss[bot_id].delete_one({'_id': title})
        self.__conn.close()

    async def trunc_table(self, name):
        if self.__err:
            return
        await self.__db[name][bot_id].drop()
        self.__conn.close()

if DATABASE_URL:
    botloop.run_until_complete(DbManager().db_load())

