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
        self.LeechBatchCommand = f'leechbatch{CMD_INDEX}'
        self.ConfigCommand = f'config{CMD_INDEX}'
        self.UserSetCommand = f'usetting{CMD_INDEX}'
        self.OwnerSetCommand = f'ownsetting{CMD_INDEX}'
        self.CopyCommand = f'copy{CMD_INDEX}'
        self.CloneCommand = f'clone{CMD_INDEX}'
        self.MyFilesCommand = f'myfiles{CMD_INDEX}'
        self.StorageCommand = f'storage{CMD_INDEX}'
        self.CleanupCommand = f'cleanup{CMD_INDEX}'
        self.YtdlMirrorCommand = f'ytdlmirror{CMD_INDEX}'
        self.YtdlLeechCommand = f'ytdlleech{CMD_INDEX}'
        self.YtdlZipMirrorCommand = (f'ytdlzipmirror{CMD_INDEX}')
        self.YtdlZipLeechCommand = (f'ytdlzipleech{CMD_INDEX}')
        self.SearchCommand = f'search{CMD_INDEX}'
        self.StatusCommand = f'status{CMD_INDEX}'
        self.StatsCommand = f'stats{CMD_INDEX}'
        self.ShellCommand = f'shell{CMD_INDEX}'
        self.ServeCommand = f'serve{CMD_INDEX}'
        self.CancelAllCommand= f'cancelall{CMD_INDEX}'
        self.CancelCommand= f'cancel{CMD_INDEX}'
        self.RssListCommand = f'rsslist{CMD_INDEX}'
        self.RssGetCommand = f'rssget{CMD_INDEX}'
        self.RssSubCommand = f'rsssub{CMD_INDEX}'
        self.RssUnSubCommand = f'rssunsub{CMD_INDEX}'
        self.RssSettingsCommand = f'rssset{CMD_INDEX}'
        self.LogsCommand = f'log{CMD_INDEX}'
        self.RestartCommand = f'restart{CMD_INDEX}'
        self.PingCommand = f'ping{CMD_INDEX}'

BotCommands = _BotCommands()



   