from os import makedirs, path as ospath

from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from bot import (
    DATABASE_URL,
    LOGGER,
    aria2_options,
    bot_id,
    config_dict,
    qbit_options,
    user_data,
)


class DbManager:
    def __init__(self):
        self.__err = False

    _conn = None
    _db = None

    async def connect(self):
        if not DATABASE_URL:
            self.__err = True
            return False
        if self.__class__._conn is not None and self.__class__._db is not None:
            self.__err = False
            return True
        try:
            self.__class__._conn = AsyncIOMotorClient(
                DATABASE_URL,
                connectTimeoutMS=60000,
                serverSelectionTimeoutMS=60000,
                socketTimeoutMS=60000,
            )
            self.__class__._db = self.__class__._conn.rcmltb
            await self.__class__._conn.admin.command("ping")
            LOGGER.info("[DB] MongoDB connected")
            self.__err = False
            return True
        except PyMongoError as e:
            LOGGER.error(f"[DB] Connection error: {e}")
            self.__err = True
            self.__class__._conn = None
            self.__class__._db = None
            return False

    async def disconnect(self):
        if self.__class__._conn is not None:
            self.__class__._conn.close()
            self.__class__._conn = None
            self.__class__._db = None
            LOGGER.info("[DB] MongoDB disconnected")

    async def _ensure_connected(self):
        if self.__err:
            return False
        if self.__class__._db is None:
            return await self.connect()
        return True

    @property
    def _db_ref(self):
        return self.__class__._db

    async def db_load(self):
        if not await self._ensure_connected():
            return
        # Save bot settings
        await self._db_ref.settings.config.update_one(
            {"_id": bot_id}, {"$set": config_dict}, upsert=True
        )
        # Save Aria2c options
        if await self._db_ref.settings.aria2c.find_one({"_id": bot_id}) is None:
            await self._db_ref.settings.aria2c.update_one(
                {"_id": bot_id}, {"$set": aria2_options}, upsert=True
            )
        # Save qbittorrent options
        if await self._db_ref.settings.qbittorrent.find_one({"_id": bot_id}) is None:
            await self._db_ref.settings.qbittorrent.update_one(
                {"_id": bot_id}, {"$set": qbit_options}, upsert=True
            )
        # User Data
        if await self._db_ref.users.find_one():
            rows = self._db_ref.users.find({})
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
    async def update_deploy_config(self):
        if not await self._ensure_connected():
            return
        current_config = dict(dotenv_values("config.env"))
        await self._db_ref.settings.deployConfig.replace_one(
            {"_id": bot_id}, current_config, upsert=True
        )

    async def update_config(self, dict_):
        if not await self._ensure_connected():
            return
        await self._db_ref.settings.config.update_one(
            {"_id": bot_id}, {"$set": dict_}, upsert=True
        )

    async def update_aria2(self, key, value):
        if not await self._ensure_connected():
            return
        await self._db_ref.settings.aria2c.update_one(
            {"_id": bot_id}, {"$set": {key: value}}, upsert=True
        )

    async def update_qbittorrent(self, key, value):
        if not await self._ensure_connected():
            return
        await self._db_ref.settings.qbittorrent.update_one(
            {"_id": bot_id}, {"$set": {key: value}}, upsert=True
        )

    async def update_private_file(self, path):
        if not await self._ensure_connected():
            return
        db_path = path.replace(".", "__")
        if ospath.exists(path):
            with open(path, "rb+") as pf:
                pf_bin = pf.read()
            await self._db_ref.settings.files.update_one(
                {"_id": bot_id}, {"$set": {db_path: pf_bin}}, upsert=True
            )
        else:
            await self._db_ref.settings.files.update_one(
                {"_id": bot_id}, {"$unset": {db_path: ""}}, upsert=True
            )
        if db_path == "config.env":
            await self.update_deploy_config()

    async def update_user_doc(self, user_id, key, path=""):
        if not await self._ensure_connected():
            return
        if path:
            with open(path, "rb+") as doc:
                doc_bin = doc.read()
            await self._db_ref.users.update_one(
                {"_id": user_id}, {"$set": {key: doc_bin}}, upsert=True
            )
        else:
            await self._db_ref.users.update_one(
                {"_id": user_id}, {"$unset": {key: ""}}, upsert=True
            )

    async def update_user_data(self, user_id):
        if not await self._ensure_connected():
            return
        data = user_data[user_id].copy()
        if data.get("thumb"):
            del data["thumb"]
        await self._db_ref.users.update_one({"_id": user_id}, {"$set": data}, upsert=True)

    async def update_thumb(self, user_id, path=None):
        if not await self._ensure_connected():
            return
        if path is not None:
            with open(path, "rb+") as image:
                image_bin = image.read()
            await self._db_ref.users.update_one(
                {"_id": user_id}, {"$set": {"thumb": image_bin}}, upsert=True
            )
        else:
            await self._db_ref.users.update_one(
                {"_id": user_id}, {"$unset": {"thumb": ""}}, upsert=True
            )

    async def trunc_table(self, name):
        if not await self._ensure_connected():
            return
        await self._db_ref[name][bot_id].drop()


database = DbManager()
