from ast import literal_eval
from os import getenv

from bot import LOGGER


class Config:
    AS_DOCUMENT = False
    ALLOWED_CHATS = ""
    AUTO_DELETE_MESSAGE_DURATION = 30
    AUTO_MIRROR = False
    BOT_TOKEN = ""
    BOT_PM = False
    CMD_INDEX = ""
    DATABASE_URL = ""
    DEFAULT_OWNER_REMOTE = ""
    DEFAULT_GLOBAL_REMOTE = ""
    DOWNLOAD_DIR = "/usr/src/app/downloads/"
    EQUAL_SPLITS = False
    EXTENSION_FILTER = ""
    GDRIVE_FOLDER_ID = ""
    GD_INDEX_URL = ""
    IS_TEAM_DRIVE = False
    LEECH_LOG = ""
    LEECH_SPLIT_SIZE = 2097152000
    LOCAL_MIRROR = False
    MEGA_EMAIL = ""
    MEGA_PASSWORD = ""
    MULTI_RCLONE_CONFIG = False
    MULTI_REMOTE_UP = False
    NO_TASKS_LOGS = False
    OWNER_ID = 0
    PARALLEL_TASKS = 0
    QB_BASE_URL = ""
    QB_SERVER_PORT = 80
    RC_INDEX_PASS = "admin"
    RC_INDEX_PORT = 8080
    RC_INDEX_URL = ""
    RC_INDEX_USER = "admin"
    RCLONE_COPY_FLAGS = ""
    RCLONE_DOWNLOAD_FLAGS = ""
    RCLONE_UPLOAD_FLAGS = ""
    REMOTE_SELECTION = False
    RSS_CHAT_ID = 0
    RSS_DELAY = 900
    SEARCH_API_LINK = ""
    SEARCH_LIMIT = 0
    SEARCH_PLUGINS = []
    SERVER_SIDE = False
    SERVICE_ACCOUNTS_REMOTE = ""
    STATUS_LIMIT = 10
    STATUS_UPDATE_INTERVAL = 10
    SUDO_USERS = ""
    TELEGRAM_API_HASH = ""
    TELEGRAM_API_ID = 0
    TMDB_API_KEY = ""
    TMDB_LANGUAGE = "en"
    TORRENT_TIMEOUT = 0
    UPSTREAM_BRANCH = "master"
    UPSTREAM_REPO = ""
    USE_SERVICE_ACCOUNTS = False
    USER_SESSION_STRING = ""
    VIEW_LINK = False
    WEB_PINCODE = False
    YT_DLP_OPTIONS = {}
    JD_EMAIL = ""
    JD_PASSWORD = ""
    QUEUE_ALL = 0
    QUEUE_DOWNLOAD = 0
    QUEUE_UPLOAD = 0
    NAME_SUBSTITUTE = ""

    @classmethod
    def _convert(cls, key: str, value):
        if not hasattr(cls, key):
            raise KeyError(f"{key} is not a valid configuration key.")

        expected_type = type(getattr(cls, key))

        if value is None:
            return None

        if isinstance(value, expected_type):
            return value

        if expected_type is bool:
            if isinstance(value, str):
                return value.strip().lower() in {"true", "1", "yes"}
            return bool(value)

        if expected_type is int:
            if isinstance(value, str) and value.strip() == "":
                return 0
            return int(value)

        if expected_type is str:
            return str(value) if value is not None else ""

        if expected_type in (list, dict):
            if not isinstance(value, str):
                raise TypeError(
                    f"Invalid type for {key}: expected {expected_type} (as string), got {type(value)}"
                )
            if not value:
                return expected_type()
            evaluated = literal_eval(value)
            if not isinstance(evaluated, expected_type):
                raise TypeError(
                    f"Invalid type for {key}: expected {expected_type}, got {type(evaluated)}"
                )
            return evaluated

        try:
            return expected_type(value)
        except (ValueError, TypeError) as exc:
            raise TypeError(
                f"Invalid type for {key}: expected {expected_type}, got {type(value)}"
            ) from exc

    @classmethod
    def get(cls, key: str, default=None):
        return getattr(cls, key, default)

    @classmethod
    def set(cls, key: str, value) -> None:
        if not hasattr(cls, key):
            raise KeyError(f"{key} is not a valid configuration key.")
        processed_value = cls._process_config_value(key, value)
        if processed_value is not None:
            setattr(cls, key, processed_value)
        else:
            converted_value = cls._convert(key, value)
            setattr(cls, key, converted_value)

    @classmethod
    def get_all(cls):
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith("_")
            and not callable(getattr(cls, key))
            and key
            not in {
                "_convert",
                "get",
                "set",
                "get_all",
                "load",
                "load_dict",
                "_is_valid_config_attr",
                "_process_config_value",
                "_validate_required_config",
                "_load_from_module",
            }
        }

    @classmethod
    def _is_valid_config_attr(cls, attr: str) -> bool:
        if attr.startswith("_") or callable(getattr(cls, attr, None)):
            return False
        return hasattr(cls, attr)

    @classmethod
    def _process_config_value(cls, attr: str, value):
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None

        converted_value = cls._convert(attr, value)

        if isinstance(converted_value, str):
            converted_value = converted_value.strip()

        if attr == "SEARCH_API_LINK":
            return converted_value.rstrip("/") if converted_value else ""

        if attr == "GD_INDEX_URL":
            return converted_value.rstrip("/") if converted_value else ""

        if attr == "QB_BASE_URL":
            return converted_value.rstrip("/") if converted_value else ""

        if attr == "DOWNLOAD_DIR":
            if not converted_value.endswith("/"):
                return f"{converted_value}/"
            return converted_value

        return converted_value

    @classmethod
    def _validate_required_config(cls):
        if not cls.BOT_TOKEN:
            LOGGER.error("BOT_TOKEN variable is missing! Exiting now")
            from sys import exit
            exit(1)
        if cls.OWNER_ID == 0:
            LOGGER.error("OWNER_ID variable is missing! Exiting now")
            from sys import exit
            exit(1)
        if cls.TELEGRAM_API_ID == 0:
            LOGGER.error("TELEGRAM_API_ID variable is missing! Exiting now")
            from sys import exit
            exit(1)
        if not cls.TELEGRAM_API_HASH:
            LOGGER.error("TELEGRAM_API_HASH variable is missing! Exiting now")
            from sys import exit
            exit(1)

    @classmethod
    def load_from_env(cls):
        for attr in dir(cls):
            if not cls._is_valid_config_attr(attr):
                continue

            env_value = getenv(attr)
            if env_value is None:
                continue

            processed_value = cls._process_config_value(attr, env_value)
            if processed_value is not None:
                setattr(cls, attr, processed_value)

    @classmethod
    def load_dict(cls, dict_: dict):
        for key, value in dict_.items():
            if not hasattr(cls, key):
                continue
            if value is None:
                continue
            processed = cls._process_config_value(key, value)
            if processed is not None:
                setattr(cls, key, processed)

    @classmethod
    def _load_from_module(cls):
        try:
            from importlib import import_module
            settings = import_module("config")
            for attr in dir(settings):
                if attr.startswith("_") or callable(getattr(settings, attr)):
                    continue
                if not hasattr(cls, attr):
                    continue
                raw_value = getattr(settings, attr)
                processed = cls._process_config_value(attr, raw_value)
                if processed is not None:
                    setattr(cls, attr, processed)
                elif raw_value is not None:
                    setattr(cls, attr, cls._convert(attr, raw_value))
            return True
        except ModuleNotFoundError:
            return False

    @classmethod
    def load(cls):
        if not cls._load_from_module():
            cls.load_from_env()
        cls._validate_required_config()
