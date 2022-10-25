# Source: https://github.com/anasty17/mirror-leech-telegram-bot/blob/master/update.py

import logging
from os import path as ospath, environ
from subprocess import run as srun
from logging import FileHandler, StreamHandler, INFO, basicConfig
from os import path as ospath, environ
from subprocess import run as srun


if ospath.exists('botlog.txt'):
    with open('botlog.txt', 'r+') as f:
        f.truncate(0)

basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[FileHandler('log.txt'), StreamHandler()],
                    level=INFO)

UPSTREAM_REPO = environ.get('UPSTREAM_REPO', '')
if len(UPSTREAM_REPO) == 0:
    UPSTREAM_REPO = None

UPSTREAM_BRANCH = environ.get('UPSTREAM_BRANCH', '')
if len(UPSTREAM_BRANCH) == 0:
    UPSTREAM_BRANCH = 'master'

if UPSTREAM_REPO is not None:
    if ospath.exists('.git'):
        srun(["rm", "-rf", ".git"])

    update = srun([f"git init -q \
            && git config --global user.email sam.agd@outlook.com \
            && git config --global user.name rctb \
            && git add . \
            && git commit -sm update -q \
            && git remote add origin {UPSTREAM_REPO} \
            && git fetch origin -q \
            && git reset --hard origin/{UPSTREAM_BRANCH} -q"], shell=True)

    if update.returncode == 0:
        logging.info('Successfully updated from UPSTREAM_REPO')
    else:
        logging.error('Something went wrong while updating, check UPSTREAM_REPO if valid or not!')