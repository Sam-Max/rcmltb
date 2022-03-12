__version__ = "1.0"
__author__ = "Sam-Max"

import logging
from dotenv import load_dotenv

from bot.utils.load_rclone import load_rclone
from .core.var_holder import VarHolder
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("botlog.txt")]
)

uptime = time.time()

load_dotenv('config.env', override=True)
SessionVars = VarHolder()
load_rclone()
