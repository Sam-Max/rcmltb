from os import path as ospath, makedirs
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
from dotenv import dotenv_values
from bot import (
    DATABASE_URL,
    user_data,
    rss_dict,
    LOGGER,
    bot_id,
    config_dict,
    aria2_options,
    qbit_options,
    botloop,
)


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
        await self.__db.settings.config.update_one(
            {"_id": bot_id}, {"$set": config_dict}, upsert=True
        )
        # Save Aria2c options
        if await self.__db.settings.aria2c.find_one({"_id": bot_id}) is None:
            await self.__db.settings.aria2c.update_one(
                {"_id": bot_id}, {"$set": aria2_options}, upsert=True
            )
        # Save qbittorrent options
        if await self.__db.settings.qbittorrent.find_one({"_id": bot_id}) is None:
            await self.__db.settings.qbittorrent.update_one(
                {"_id": bot_id}, {"$set": qbit_options}, upsert=True
            )
        # User Data
        if await self.__db.users.find_one():
            rows = self.__db.users.find({})
            # user - return a dict ==> {_id, is_sudo, is_auth, as_doc, thumb, yt_opt, equal_splits, split_size, rclone}
            # owner - return a dict ==> {_id, is_sudo, is_auth, as_doc, thumb, yt_opt, equal_splits, split_size, rclone, rclone_global}
            async for row in rows:
                uid = row["_id"]
                del row["_id"]
                thumb_path = f"Thumbnails/{uid}.jpg"
                rclone_user = f"rclone/{uid}/rclone.conf"
                rclone_global = f"rclone/rclone_global/rclone.conf"
                if row.get("thumb"):
                    if not ospath.exists("Thumbnails"):
                        makedirs("Thumbnails")
                    with open(thumb_path, "wb+") as f:
                        f.write(row["thumb"])
                    row["thumb"] = thumb_path
                if row.get("rclone"):
                    if not ospath.exists(f"rclone/{uid}"):
                        makedirs(f"rclone/{uid}")
                    with open(rclone_user, "wb+") as f:
                        f.write(row["rclone"])
                if row.get("rclone_global"):
                    if not ospath.exists("rclone/rclone_global"):
                        makedirs("rclone/rclone_global")
                    with open(rclone_global, "wb+") as f:
                        f.write(row["rclone_global"])
            LOGGER.info("Users data has been imported from Database")
        # Rss Data
        if await self.__db.rss[bot_id].find_one():
            rows = self.__db.rss[bot_id].find(
                {}
            )  # return a dict ==> {_id, link, last_feed, last_name, filters}
            async for row in rows:
                title = row["_id"]
                del row["_id"]
                rss_dict[title] = row
            LOGGER.info("Rss data has been imported from Database.")
        self.__conn.close()

    async def update_deploy_config(self):
        if self.__err:
            return
        current_config = dict(dotenv_values("config.env"))
        await self.__db.settings.deployConfig.replace_one(
            {"_id": bot_id}, current_config, upsert=True
        )
        self.__conn.close

    async def update_config(self, dict_):
        if self.__err:
            return
        await self.__db.settings.config.update_one(
            {"_id": bot_id}, {"$set": dict_}, upsert=True
        )
        self.__conn.close

    async def update_aria2(self, key, value):
        if self.__err:
            return
        await self.__db.settings.aria2c.update_one(
            {"_id": bot_id}, {"$set": {key: value}}, upsert=True
        )
        self.__conn.close

    async def update_qbittorrent(self, key, value):
        if self.__err:
            return
        await self.__db.settings.qbittorrent.update_one(
            {"_id": bot_id}, {"$set": {key: value}}, upsert=True
        )
        self.__conn.close

    async def update_private_file(self, path):
        if self.__err:
            return
        if ospath.exists(path):
            with open(path, "rb+") as pf:
                pf_bin = pf.read()
        else:
            pf_bin = ""
        path = path.replace(".", "__")
        await self.__db.settings.files.update_one(
            {"_id": bot_id}, {"$set": {path: pf_bin}}, upsert=True
        )
        if path == "config.env":
            await self.update_deploy_config()
        self.__conn.close

    async def update_user_doc(self, user_id, key, path=""):
        if self.__err:
            return
        if path:
            with open(path, "rb+") as doc:
                doc_bin = doc.read()
        else:
            doc_bin = ""
        await self.__db.users.update_one(
            {"_id": user_id}, {"$set": {key: doc_bin}}, upsert=True
        )
        self.__conn.close

    async def update_user_data(self, user_id):
        if self.__err:
            return
        data = user_data[user_id]
        if data.get("thumb"):
            del data["thumb"]
        await self.__db.users.update_one({"_id": user_id}, {"$set": data}, upsert=True)
        self.__conn.close

    async def update_thumb(self, user_id, path=None):
        if self.__err:
            return
        if path is not None:
            with open(path, "rb+") as image:
                image_bin = image.read()
        else:
            image_bin = ""
        await self.__db.users.update_one(
            {"_id": user_id}, {"$set": {"thumb": image_bin}}, upsert=True
        )
        self.__conn.close

    async def rss_update(self, user_id):
        if self.__err:
            return
        await self.__db.rss[bot_id].replace_one(
            {"_id": user_id}, rss_dict[user_id], upsert=True
        )
        self.__conn.close

    async def rss_update_all(self):
        if self.__err:
            return
        for user_id in list(rss_dict.keys()):
            await self.__db.rss[bot_id].replace_one(
                {"_id": user_id}, rss_dict[user_id], upsert=True
            )
        self.__conn.close

    async def rss_delete(self, user_id):
        if self.__err:
            return
        await self.__db.rss[bot_id].delete_one({"_id": user_id})
        self.__conn.close

    async def trunc_table(self, name):
        if self.__err:
            return
        await self.__db[name][bot_id].drop()
        self.__conn.close


if DATABASE_URL:
    botloop.run_until_complete(DbManager().db_load())
