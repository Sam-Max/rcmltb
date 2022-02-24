from telethon import TelegramClient


class RcloneTgClient(TelegramClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pyro = None
