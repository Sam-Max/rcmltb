# -*- coding: utf-8 -*-

from telethon import TelegramClient


class RcloneTgClient(TelegramClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # for now only queue is required
        self.queue = None
        self.dl_passwords = {}
        self.pyro = None
