from bot import CMD_INDEX


class _BotCommands:
    def __init__(self):
        self.StartCommand = f"start{CMD_INDEX}"
        self.MirrorCommand = [f"mirror{CMD_INDEX}", f"m{CMD_INDEX}"]
        self.MirrorBatchCommand = [f"mirror_batch{CMD_INDEX}", f"mb{CMD_INDEX}"]
        self.MirrorSelectCommand = [f"mirror_select{CMD_INDEX}", f"ms{CMD_INDEX}"]
        self.LeechCommand = [f"leech{CMD_INDEX}", f"l{CMD_INDEX}"]
        self.LeechBatchCommand = [f"leech_batch{CMD_INDEX}", f"lb{CMD_INDEX}"]
        self.YtdlMirrorCommand = [f"ytdl{CMD_INDEX}", f"y{CMD_INDEX}"]
        self.YtdlLeechCommand = [f"ytdl_leech{CMD_INDEX}", f"yl{CMD_INDEX}"]
        self.BotFilesCommand = [f"files{CMD_INDEX}", f"bf{CMD_INDEX}"]
        self.CopyCommand = f"copy{CMD_INDEX}"
        self.CloneCommand = f"clone{CMD_INDEX}"
        self.CountCommand = f"count{CMD_INDEX}"
        self.TorrentSearchCommand = f"torrsch{CMD_INDEX}"
        self.StatusCommand = f"status{CMD_INDEX}"
        self.StatsCommand = f"stats{CMD_INDEX}"
        self.ShellCommand = f"shell{CMD_INDEX}"
        self.ExecCommand = f"exec{CMD_INDEX}"
        self.ServeCommand = f"serve{CMD_INDEX}"
        self.SyncCommand = f"sync{CMD_INDEX}"
        self.RcfmCommand = f"rcfm{CMD_INDEX}"
        self.StorageCommand = f"storage{CMD_INDEX}"
        self.CleanupCommand = f"cleanup{CMD_INDEX}"
        self.BiSyncCommand = f"bisync{CMD_INDEX}"
        self.UserSetCommand = f"user_setting{CMD_INDEX}"
        self.OwnerSetCommand = f"own_setting{CMD_INDEX}"
        self.CancelAllCommand = f"cancel_all{CMD_INDEX}"
        self.CancelCommand = f"cancel{CMD_INDEX}"
        self.RssCommand = f"rss{CMD_INDEX}"
        self.LogsCommand = f"log{CMD_INDEX}"
        self.RestartCommand = f"restart{CMD_INDEX}"
        self.PingCommand = f"ping{CMD_INDEX}"
        self.IpCommand = f"ip{CMD_INDEX}"
        self.TMDB = f"tmdb{CMD_INDEX}"
        self.Debrid = f"debrid{CMD_INDEX}"
        self.DebridInfo = f"info{CMD_INDEX}"


BotCommands = _BotCommands()
