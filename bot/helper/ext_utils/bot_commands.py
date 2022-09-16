from bot import CMD_INDEX


class _BotCommands:
    def __init__(self):
        self.StartCommand = f'start{CMD_INDEX}'
        self.MirrorCommand = f'mirror{CMD_INDEX}'
        self.UnzipMirrorCommand = f'unzipmirror{CMD_INDEX}'
        self.ZipMirrorCommand = f'zipmirror{CMD_INDEX}'
        self.MirrorSetCommand = f'mirrorset{CMD_INDEX}'
        self.MirrorBatchCommand = f'mirrorbatch{CMD_INDEX}'
        self.LeechCommand = f'leech{CMD_INDEX}'
        self.UnzipLeechCommand = f'unzipleech{CMD_INDEX}'
        self.ZipLeechCommand = f'zipleech{CMD_INDEX}'
        self.LeechSetCommand = f'leechset{CMD_INDEX}'
        self.LeechBatchCommand = f'leechbatch{CMD_INDEX}'
        self.ConfigCommand = f'config{CMD_INDEX}'
        self.CopyCommand = f'copy{CMD_INDEX}'
        self.GcloneCommand = f'clone{CMD_INDEX}'
        self.MyFilesCommand = f'myfiles{CMD_INDEX}'
        self.StorageCommand = f'storage{CMD_INDEX}'
        self.CleanupCommand = f'cleanup{CMD_INDEX}'
        self.SearchCommand = f'search{CMD_INDEX}'
        self.StatusCommand = f'status{CMD_INDEX}'
        self.ExecCommand = f'exec{CMD_INDEX}'
        self.LogsCommand = f'log{CMD_INDEX}'
        self.ServerCommand = f'server{CMD_INDEX}'
        self.SpeedtestCommand = f'speedtest{CMD_INDEX}'
        self.RestartCommand = f'restart{CMD_INDEX}'
        self.PingCommand = f'ping{CMD_INDEX}'

BotCommands = _BotCommands()



   