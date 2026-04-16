from asyncio import create_subprocess_exec
from os import environ, getcwd, path as ospath, remove as osremove
from subprocess import Popen, run as srun

from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient

from bot import (
    LOGGER,
    config_dict,
    user_data,
    leech_log,
    aria2_options,
    qbit_options,
    GLOBAL_EXTENSION_FILTER,
)
from bot.core.config_manager import Config


async def load_settings():
    global aria2_options, qbit_options

    from bot import bot_id

    DATABASE_URL = Config.DATABASE_URL or ""
    if not DATABASE_URL:
        return

    conn = AsyncIOMotorClient(DATABASE_URL)
    db = conn.rcmltb
    current_config = dict(dotenv_values("config.env"))
    old_config = await db.settings.deployConfig.find_one({"_id": bot_id})
    if old_config is None:
        await db.settings.deployConfig.replace_one(
            {"_id": bot_id}, current_config, upsert=True
        )
    else:
        del old_config["_id"]
    if old_config and old_config != current_config:
        await db.settings.deployConfig.replace_one(
            {"_id": bot_id}, current_config, upsert=True
        )
    elif saved_config := await db.settings.config.find_one({"_id": bot_id}):
        del saved_config["_id"]
        Config.load_dict(saved_config)
        for key, value in saved_config.items():
            environ[key] = str(value)
    if pf_dict := await db.settings.files.find_one({"_id": bot_id}):
        del pf_dict["_id"]
        for key, value in pf_dict.items():
            if value:
                file_ = key.replace("__", ".")
                with open(file_, "wb+") as f:
                    f.write(value)
    if a2c_options := await db.settings.aria2c.find_one({"_id": bot_id}):
        del a2c_options["_id"]
        aria2_options = a2c_options
    if qbit_opt := await db.settings.qbittorrent.find_one({"_id": bot_id}):
        del qbit_opt["_id"]
        qbit_options = qbit_opt
    conn.close()


async def load_configurations():
    if Config.QB_BASE_URL:
        Popen(
            f"gunicorn qbitweb.wserver:app --bind 0.0.0.0:{Config.QB_SERVER_PORT} --worker-class gevent",
            shell=True,
        )

    # Check if qBittorrent is already running before starting
    qb_check = srun(["pgrep", "-x", "qbittorrent-nox"], capture_output=True)
    if qb_check.returncode != 0:
        srun(["qbittorrent-nox", "-d", f"--profile={getcwd()}"])

    if not ospath.exists(".netrc"):
        with open(".netrc", "w"):
            pass
    srun(["chmod", "600", ".netrc"])
    # Only copy to /root/.netrc if running as root
    if environ.get("HOME") == "/root":
        srun(["cp", ".netrc", "/root/.netrc"])
    srun(["chmod", "+x", "aria.sh"])
    srun("./aria.sh", shell=True)
    if ospath.exists("accounts.zip"):
        if ospath.exists("accounts"):
            srun(["rm", "-rf", "accounts"])
        srun(["7z", "x", "-o.", "-aoa", "accounts.zip", "accounts/*.json"])
        srun(["chmod", "-R", "777", "accounts"])
        osremove("accounts.zip")
    if not ospath.exists("accounts"):
        Config.USE_SERVICE_ACCOUNTS = False
        config_dict["USE_SERVICE_ACCOUNTS"] = False


async def save_settings():
    from bot import bot_id, DATABASE_URL

    if not DATABASE_URL:
        return
    try:
        conn = AsyncIOMotorClient(DATABASE_URL)
        db = conn.rcmltb
        await db.settings.config.update_one(
            {"_id": bot_id}, {"$set": config_dict}, upsert=True
        )
        if await db.settings.aria2c.find_one({"_id": bot_id}) is None:
            await db.settings.aria2c.update_one(
                {"_id": bot_id}, {"$set": aria2_options}, upsert=True
            )
        if await db.settings.qbittorrent.find_one({"_id": bot_id}) is None:
            await db.settings.qbittorrent.update_one(
                {"_id": bot_id}, {"$set": qbit_options}, upsert=True
            )
        conn.close()
    except Exception as e:
        LOGGER.error(f"Error saving settings: {e}")


async def update_variables():
    if Config.ALLOWED_CHATS:
        for id_ in Config.ALLOWED_CHATS.split():
            user_data[int(id_.strip())] = {"is_auth": True}

    if Config.SUDO_USERS:
        for id_ in Config.SUDO_USERS.split():
            user_data[int(id_.strip())] = {"is_sudo": True}

    if Config.EXTENSION_FILTER:
        for x in Config.EXTENSION_FILTER.split():
            GLOBAL_EXTENSION_FILTER.append(x.lstrip(".").strip().lower())

    if Config.LEECH_LOG:
        leech_log.clear()
        for id_ in Config.LEECH_LOG.split():
            leech_log.append(int(id_.strip()))


async def update_aria2_options():
    from bot.core.torrent_manager import TorrentManager, aria2c_global

    global aria2_options

    if not aria2_options:
        aria2_options = await TorrentManager.get_aria2_options()
    else:
        a2c_glo = {}
        for op in aria2c_global:
            if op in aria2_options:
                a2c_glo[op] = aria2_options[op]
        await TorrentManager.set_aria2_options(a2c_glo)


async def update_qbit_options():
    global qbit_options

    from bot.core.torrent_manager import TorrentManager

    if not qbit_options:
        qbit_options = await TorrentManager.get_qbit_preferences()
        if "listen_port" in qbit_options:
            del qbit_options["listen_port"]
        for k in list(qbit_options.keys()):
            if k.startswith("rss"):
                del qbit_options[k]
    else:
        qb_opt = {**qbit_options}
        for k, v in list(qb_opt.items()):
            if v in ["", "*"]:
                del qb_opt[k]
        await TorrentManager.set_qbit_preferences(qb_opt)
