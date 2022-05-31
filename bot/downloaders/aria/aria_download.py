#Modified from: (c) YashDK [yash-dk@github]

import asyncio, aria2p, os
from asyncio import sleep
from bot import LOGGER
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from functools import partial
from bot.utils.human_format import human_readable_bytes


class AriaDownloader():
    def __init__(self, dl_link, user_message, new_file_name=None):
        super().__init__()
        self._aloop = asyncio.get_event_loop()
        self._client = None
        self._dl_link = dl_link
        self._new_file_name = new_file_name 
        self._gid = 0
        self._user_message= user_message
        self._update_info = None

    async def get_client(self):
        if self._client is not None:
            return self._client

        aria2_daemon_start_cmd = []
        aria2_daemon_start_cmd.append("aria2c")
        aria2_daemon_start_cmd.append("--daemon=true")
        aria2_daemon_start_cmd.append("--enable-rpc")
        aria2_daemon_start_cmd.append("--disk-cache=0")
        aria2_daemon_start_cmd.append("--follow-torrent=false")
        aria2_daemon_start_cmd.append("--max-connection-per-server=10")
        aria2_daemon_start_cmd.append("--min-split-size=10M")
        aria2_daemon_start_cmd.append("--rpc-listen-all=true")
        aria2_daemon_start_cmd.append(f"--rpc-listen-port=8100")
        aria2_daemon_start_cmd.append("--rpc-max-request-size=1024M")
        aria2_daemon_start_cmd.append("--seed-ratio=0.0")
        aria2_daemon_start_cmd.append("--seed-time=1")
        aria2_daemon_start_cmd.append("--split=10")
        aria2_daemon_start_cmd.append(f"--bt-stop-timeout=100")
        aria2_daemon_start_cmd.append(f"--max-tries=10")
        aria2_daemon_start_cmd.append(f"--retry-wait=2")

        process = await asyncio.create_subprocess_exec(
            *aria2_daemon_start_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        arcli = await self._aloop.run_in_executor(
            None, 
            partial(
                aria2p.Client, 
                host="http://localhost", 
                port=8100, 
                secret=""
                )
        )
        aria2 = await self._aloop.run_in_executor(None, aria2p.API, arcli)
        self._client = aria2
        return aria2

    async def add_magnet(self, aria_instance, magnetic_link):
        try:
            download = await self._aloop.run_in_executor(None, 
            aria_instance.add_magnet, magnetic_link)
        except Exception as e:
            return False, "**FAILED** \n" + str(e) + " \nPlease do not send slow links"
        else:
            return True, "" + download.gid + ""


    async def add_torrent(self, aria_instance, torrent_file_path):
        if torrent_file_path is None:
            return False, "**FAILED** \n\nsomething wrongings when trying to add <u>TORRENT</u> file"
        if os.path.exists(torrent_file_path):
            try:
                download = await self._aloop.run_in_executor(None, partial(aria_instance.add_torrent, torrent_file_path, uris=None, options=None, position=None))
            except Exception as e:
                return False, "**FAILED** \n" + str(e) + " \nPlease do not send slow links"
            else:
                return True, "" + download.gid + ""
        else:
            return False, "**FAILED** \n" + str(e) + " \nPlease try other sources to get workable link"

    async def add_url(self, aria_instance, text_url):
        uris = [text_url]
        try:
            download = await self._aloop.run_in_executor(None, aria_instance.add_uris, uris)
        except Exception as e:
            return False, "**FAILED** \n" + str(e) + " \nPlease do not send slow links."
        else:
            return True, "" + download.gid + ""

    async def check_metadata(self, aria2, gid):
        file = await self._aloop.run_in_executor(None, aria2.get_download, gid)
        if not file.followed_by_ids:
            return None
        new_gid = file.followed_by_ids[0]
        LOGGER.info("Changing GID " + gid + " to " + new_gid)
        return new_gid

    async def execute(self):
        aria_instance = await self.get_client()

        if self._dl_link.lower().startswith("magnet:"):
            sagtus, err_message = await self.add_magnet(aria_instance, self._dl_link) 
            if not sagtus:
                self._is_errored = True
                self._error_reason = err_message
                return False
            self._gid = err_message
            err_message = await self.check_metadata(aria_instance, err_message)
            await sleep(1)
            if err_message is not None:
                await self.aria_progress_update()
            else:
              LOGGER.error("Can't get metadata.\n")
              self._is_errored = True
              self._error_reason = "Can't get metadata.\n"
              return False
        elif self._dl_link.lower().endswith(".torrent"):
            LOGGER.info("Cant download this .torrent file")
            return False
        else:
            sagtus, err_message = await self.add_url(aria_instance, self._dl_link)
            if not sagtus:
                self._is_errored = True
                self._error_reason = err_message
                return False
            self._gid = err_message
            statusr= await self.aria_progress_update()
            if statusr:
                file = await self._aloop.run_in_executor(None, aria_instance.get_download,err_message)
                file_path = os.path.join(file.dir, file.name)
                return file_path

    async def aria_progress_update(self):
        aria2 = await self.get_client()
        gid = self._gid
        user_msg= self._user_message
        while True:
            try:
                file = await self._aloop.run_in_executor(None, aria2.get_download, gid)
                self._update_info = file
                complete = file.is_complete
                update_message1= ""
                sleeps= False
                if not complete:
                    if not file.error_message:
                        if file is None:
                            LOGGER.exception("Errored in fetching the direct DL.")
                            return False
                        else:
                            sleeps = True
                            update_message= await self.create_update_message()
                            if update_message1 != update_message:
                                try:
                                    data = "cancel_aria2_{}".format(gid)
                                    await user_msg.edit(text=update_message, reply_markup=(InlineKeyboardMarkup([
                                            [InlineKeyboardButton('Cancel', callback_data=data.encode("UTF-8"))]
                                            ])))
                                    update_message1 = update_message
                                except Exception as e:
                                    LOGGER.info("Not expected {}".format(e))
                                    pass

                            if sleeps:
                                if complete:
                                    await user_msg.edit("Completed")     
                                    break     
                                sleeps = False
                                await asyncio.sleep(2)
                    else:
                        msg = file.error_message
                        self._is_errored = True
                        self._error_reason = msg
                        await user_msg.edit(msg)
                        LOGGER.info(f"The aria download failed due to this reason:- {msg}")
                        return False
                else:
                    self._is_completed = True
                    self._is_done = True
                    self._error_reason = f"Download completed: `{file.name}` - (`{file.total_length_string()}`)"
                    await user_msg.edit(f"Download completed: `{file.name}` - (`{file.total_length_string()}`)")
                    return True
            except aria2p.client.ClientException as e:
                if " not found" in str(e) or "'file'" in str(e):
                    fname = "N/A"
                    try:
                        fname = file.name
                    except:pass
                    self._is_canceled = True
                    self._error_reason = f"The Download was canceled. {fname}"
                else:
                    LOGGER.warning("Errored due to ta client error.")
                pass
            except RecursionError:
                file.remove(force=True)
                self._is_errored = True
                self._error_reason = "The link is basically dead."
                return False
            except Exception as e:
                LOGGER.info(str(e))
                self._is_errored = True
                if " not found" in str(e) or "'file'" in str(e):
                    self._error_reason = "The Download was canceled."
                else:
                    LOGGER.warning(str(e))
                    self._error_reason =  f"Error: {str(e)}"

    async def create_update_message(self):
        LOGGER.info("create_update_message")
        file= self._update_info
        downloading_dir_name = "N/A"
        try:
            downloading_dir_name = str(file.name)
        except:
            pass
        msg = "Downloading:{}\n".format(downloading_dir_name)
        msg += "Down: {} Up: {}\n".format(file.download_speed_string(),file.upload_speed_string())
        msg += "Progress: {} - {}%\n".format(self.progress_bar(file.progress/100), round(file.progress, 2))
        msg += "Downloaded: {} of {}\n".format(human_readable_bytes(file.completed_length),human_readable_bytes(file.total_length))
        msg += "ETA: {} Mins\n".format(file.eta_string())
        msg += "Conns:{}\n".format(file.connections)
        msg += "Using engine: Aria2 For Direct Links"
        return msg
    
    def progress_bar(self, percentage):
        """Returns a progress bar for download
        """
        #percentage is on the scale of 0-1
        comp = "▰"
        ncomp = "▱"
        pr = ""

        for i in range(1,11):
            if i <= int(percentage*10):
                pr += comp
            else:
                pr += ncomp
        return pr

    async def remove_dl(self, gid):
        if gid is None:
            gid = self._gid
        aria2 = await self.get_client()
        try:
            downloads = await self._aloop.run_in_executor(None, aria2.get_download, gid)
            downloads.remove(force=True, files=True)
            #await self._user_message.edit("Download Removed")
            LOGGER.info("Download Removed")
        except Exception as e:
            LOGGER.exception(e)
            LOGGER.exception("Failed to Remove Download")
            pass

    def get_gid(self):
        return self._gid

    def cancel(self, is_admin=False):
        self._is_canceled = True
        if is_admin:
            self._canceled_by = self.ADMIN
        else: 
            self._canceled_by = self.USER
    
    async def get_update(self):
        return self._update_info

    def get_error_reason(self):
        return self._error_reason
    