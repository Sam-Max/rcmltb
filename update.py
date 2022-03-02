#**************************************************
# Based on:
# Repository:  https://github.com/anasty17/mirror-leech-telegram-bot/
# Source: https://github.com/anasty17/mirror-leech-telegram-bot/blob/master/update.py
#**************************************************/

import logging
from os import path as ospath, environ
from subprocess import run as srun
from requests import get as rget

if ospath.exists('botlog.txt'):
    with open('botlog.txt', 'r+') as f:
        f.truncate(0)

CONFIG_FILE_URL = environ.get('CONFIG_FILE_URL')
logging.info("CONFIG_FILE_URL {}".format(CONFIG_FILE_URL))
try:
    if len(CONFIG_FILE_URL) == 0:
        logging.info("TypeError")
        raise TypeError
    try:
        res = rget(CONFIG_FILE_URL)
        if res.status_code == 200:
            with open('config.env', 'wb+') as f:
                f.write(res.content)
        else:
            logging.error(f"Failed to download config.env {res.status_code}")
    except Exception as e:
        logging.error(f"CONFIG_FILE_URL: {e}")
except TypeError:
    pass

UPSTREAM_REPO = environ.get('UPSTREAM_REPO')
UPSTREAM_BRANCH = environ.get('UPSTREAM_BRANCH')
try:
    if len(UPSTREAM_REPO) == 0:
       raise TypeError
except TypeError:
    UPSTREAM_REPO = None
try:
    if len(UPSTREAM_BRANCH) == 0:
       raise TypeError
except TypeError:
    UPSTREAM_BRANCH = 'master'

if UPSTREAM_REPO is not None:
    if ospath.exists('.git'):
        srun(["rm", "-rf", ".git"])

    srun([f"git init -q \
            && git config --global user.email sam.agd@outlook.com \
            && git config --global user.name rctb \
            && git add . \
            && git commit -sm update -q \
            && git remote add origin {UPSTREAM_REPO} \
            && git fetch origin -q \
            && git reset --hard origin/{UPSTREAM_BRANCH} -q"], shell=True)