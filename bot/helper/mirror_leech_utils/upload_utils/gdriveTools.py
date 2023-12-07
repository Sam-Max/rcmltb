from io import FileIO
from logging import getLogger, ERROR
from time import time
from pickle import load as pload
from re import search as re_search
from urllib.parse import parse_qs, urlparse
from os import makedirs, path as ospath, listdir
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from bot import GLOBAL_EXTENSION_FILTER, config_dict
from bot.helper.ext_utils.bot_utils import run_async, setInterval
from random import randrange
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
    RetryError,
)


LOGGER = getLogger(__name__)
getLogger("googleapiclient.discovery").setLevel(ERROR)


class GoogleDriveHelper:
    def __init__(self, name=None, path=None, listener=None):
        self.__OAUTH_SCOPE = ["https://www.googleapis.com/auth/drive"]
        self.__G_DRIVE_DIR_MIME_TYPE = "application/vnd.google-apps.folder"
        self.__G_DRIVE_BASE_DOWNLOAD_URL = (
            "https://drive.google.com/uc?id={}&export=download"
        )
        self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL = (
            "https://drive.google.com/drive/folders/{}"
        )
        self.__listener = listener
        self.__path = path
        self.__total_bytes = 0
        self.__total_files = 0
        self.__total_folders = 0
        self.__processed_bytes = 0
        self.__total_time = 0
        self.__start_time = 0
        self.__alt_auth = False
        self.__is_downloading = False
        self.__is_cloning = False
        self.__is_cancelled = False
        self.__status = None
        self.__updater = None
        self.__update_interval = 3
        self.__sa_index = 0
        self.__sa_count = 1
        self.__sa_number = 100
        self.__service = self.__authorize()
        self.__file_processed_bytes = 0
        self.__processed_bytes = 0
        self.name = name

    @property
    def speed(self):
        try:
            return self.processed_bytes / self.__total_time
        except:
            return 0

    @property
    def processed_bytes(self):
        return self.__processed_bytes

    def __authorize(self):
        credentials = None
        if config_dict["USE_SERVICE_ACCOUNTS"]:
            json_files = listdir("accounts")
            self.__sa_number = len(json_files)
            self.__sa_index = randrange(self.__sa_number)
            LOGGER.info(
                f"Authorizing with {json_files[self.__sa_index]} service account"
            )
            credentials = service_account.Credentials.from_service_account_file(
                f"accounts/{json_files[self.__sa_index]}", scopes=self.__OAUTH_SCOPE
            )
        elif ospath.exists("token.pickle"):
            LOGGER.info("Authorize with token.pickle")
            with open("token.pickle", "rb") as f:
                credentials = pload(f)
        else:
            LOGGER.error("token.pickle not found!")
        return build("drive", "v3", credentials=credentials, cache_discovery=False)

    def __alt_authorize(self):
        if not self.__alt_auth:
            self.__alt_auth = True
            if ospath.exists("token.pickle"):
                LOGGER.info("Authorize with token.pickle")
                with open("token.pickle", "rb") as f:
                    credentials = pload(f)
                return build(
                    "drive", "v3", credentials=credentials, cache_discovery=False
                )
            else:
                LOGGER.error("token.pickle not found!")
        return None

    @staticmethod
    def __getIdFromUrl(link: str):
        if "folders" in link or "file" in link:
            regex = r"https:\/\/drive\.google\.com\/(?:drive(.*?)\/folders\/|file(.*?)?\/d\/)([-\w]+)"
            res = re_search(regex, link)
            if res is None:
                raise IndexError("G-Drive ID not found.")
            return res.group(3)
        parsed = urlparse(link)
        return parse_qs(parsed.query)["id"][0]

    @retry(
        wait=wait_exponential(multiplier=2, min=3, max=6),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
    )
    def __set_permission(self, drive_id):
        permissions = {
            "role": "reader",
            "type": "anyone",
            "value": None,
            "withLink": True,
        }
        return (
            self.__service.permissions()
            .create(fileId=drive_id, body=permissions, supportsAllDrives=True)
            .execute()
        )

    @retry(
        wait=wait_exponential(multiplier=2, min=3, max=6),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
    )
    def __getFileMetadata(self, file_id):
        return (
            self.__service.files()
            .get(
                fileId=file_id,
                supportsAllDrives=True,
                fields="name, id, mimeType, size",
            )
            .execute()
        )

    @retry(
        wait=wait_exponential(multiplier=2, min=3, max=6),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
    )
    def __getFilesByFolderId(self, folder_id):
        page_token = None
        files = []
        while True:
            response = (
                self.__service.files()
                .list(
                    supportsAllDrives=True,
                    includeTeamDriveItems=True,
                    q=f"'{folder_id}' in parents and trashed = false",
                    spaces="drive",
                    pageSize=200,
                    fields="nextPageToken, files(id, name, mimeType, size, shortcutDetails)",
                    orderBy="folder, name",
                    pageToken=page_token,
                )
                .execute()
            )
            files.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if page_token is None:
                break
        return files

    async def _progress(self):
        if self.__status is not None:
            chunk_size = (
                self.__status.total_size * self.__status.progress()
                - self.__file_processed_bytes
            )
            self.__file_processed_bytes = (
                self.__status.total_size * self.__status.progress()
            )
            self.__processed_bytes += chunk_size
            self.__total_time += self.__update_interval

    @retry(
        wait=wait_exponential(multiplier=2, min=3, max=6),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
    )
    def __create_directory(self, directory_name, dest_id):
        file_metadata = {
            "name": directory_name,
            "description": "Uploaded by rcmltb",
            "mimeType": self.__G_DRIVE_DIR_MIME_TYPE,
        }
        if dest_id is not None:
            file_metadata["parents"] = [dest_id]
        file = (
            self.__service.files()
            .create(body=file_metadata, supportsAllDrives=True)
            .execute()
        )
        file_id = file.get("id")
        if not config_dict["IS_TEAM_DRIVE"]:
            self.__set_permission(file_id)
        if not config_dict["NO_TASKS_LOGS"]:
            LOGGER.info(
                "Created G-Drive Folder:\nName: {}\nID: {} ".format(
                    file.get("name"), file_id
                )
            )
        return file_id

    def clone(self, link):
        self.__is_cloning = True
        self.__start_time = time()
        self.__total_files = 0
        self.__total_folders = 0
        try:
            file_id = self.__getIdFromUrl(link)
        except (KeyError, IndexError):
            return "Google Drive ID could not be found in the provided link"
        msg = ""
        try:
            meta = self.__getFileMetadata(file_id)
            mime_type = meta.get("mimeType")
            if mime_type == self.__G_DRIVE_DIR_MIME_TYPE:
                dir_id = self.__create_directory(
                    meta.get("name"), config_dict["GDRIVE_FOLDER_ID"]
                )
                self.__cloneFolder(
                    meta.get("name"), meta.get("name"), meta.get("id"), dir_id
                )
                durl = self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL.format(dir_id)
                if self.__is_cancelled:
                    LOGGER.info("Deleting cloned data from Drive...")
                    self.deletefile(durl)
                    return None, None, None, None, None
                mime_type = "Folder"
                size = self.__processed_bytes
            else:
                file = self.__copyFile(meta.get("id"), config_dict["GDRIVE_FOLDER_ID"])
                msg += f'<b>Name: </b><code>{file.get("name")}</code>'
                durl = self.__G_DRIVE_BASE_DOWNLOAD_URL.format(file.get("id"))
                if mime_type is None:
                    mime_type = "File"
                size = int(meta.get("size", 0))
            return durl, size, mime_type, self.__total_files, self.__total_folders
        except Exception as err:
            if isinstance(err, RetryError):
                LOGGER.info(f"Total Attempts: {err.last_attempt.attempt_number}")
                err = err.last_attempt.exception()
            err = str(err).replace(">", "").replace("<", "")
            if "User rate limit exceeded" in err:
                msg = "User rate limit exceeded."
            elif "File not found" in err:
                if not self.__alt_auth:
                    token_service = self.__alt_authorize()
                    if token_service is not None:
                        LOGGER.error("File not found. Trying with token.pickle...")
                        self.__service = token_service
                        return self.clone(link)
                msg = "File not found."
            else:
                msg = f"Error.\n{err}"
            run_async(self.__listener.onUploadError, msg)
            return None, None, None, None, None

    def __cloneFolder(self, name, local_path, folder_id, dest_id):
        LOGGER.info(f"Syncing: {local_path}")
        files = self.__getFilesByFolderId(folder_id)
        if len(files) == 0:
            return dest_id
        for file in files:
            if file.get("mimeType") == self.__G_DRIVE_DIR_MIME_TYPE:
                self.__total_folders += 1
                file_path = ospath.join(local_path, file.get("name"))
                current_dir_id = self.__create_directory(file.get("name"), dest_id)
                self.__cloneFolder(
                    file.get("name"), file_path, file.get("id"), current_dir_id
                )
            elif not file.get("name").lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                self.__total_files += 1
                self.__copyFile(file.get("id"), dest_id)
                self.__processed_bytes += int(file.get("size", 0))
                self.__total_time = int(time() - self.__start_time)
            if self.__is_cancelled:
                break

    def count(self, link):
        try:
            file_id = self.__getIdFromUrl(link)
        except (KeyError, IndexError):
            return (
                "Google Drive ID could not be found in the provided link",
                None,
                None,
                None,
                None,
            )
        try:
            return self.__proceed_count(file_id)
        except Exception as err:
            if isinstance(err, RetryError):
                LOGGER.info(f"Total Attempts: {err.last_attempt.attempt_number}")
                err = err.last_attempt.exception()
            err = str(err).replace(">", "").replace("<", "")
            if "File not found" in err:
                if not self.__alt_auth:
                    token_service = self.__alt_authorize()
                    if token_service is not None:
                        LOGGER.error("File not found. Trying with token.pickle...")
                        self.__service = token_service
                        return self.count(link)
                msg = "File not found."
            else:
                msg = f"Error.\n{err}"
        return msg, None, None, None, None

    def __proceed_count(self, file_id):
        meta = self.__getFileMetadata(file_id)
        name = meta["name"]
        LOGGER.info(f"Counting: {name}")
        mime_type = meta.get("mimeType")
        if mime_type == self.__G_DRIVE_DIR_MIME_TYPE:
            self.__gDrive_directory(meta)
            mime_type = "Folder"
        else:
            if mime_type is None:
                mime_type = "File"
            self.__total_files += 1
            self.__gDrive_file(meta)
        return (
            name,
            mime_type,
            self.__total_bytes,
            self.__total_files,
            self.__total_folders,
        )

    @retry(
        wait=wait_exponential(multiplier=2, min=3, max=6),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
    )
    def __copyFile(self, file_id, dest_id):
        body = {"parents": [dest_id]}
        try:
            return (
                self.__service.files()
                .copy(fileId=file_id, body=body, supportsAllDrives=True)
                .execute()
            )
        except HttpError as err:
            if err.resp.get("content-type", "").startswith("application/json"):
                reason = eval(err.content).get("error").get("errors")[0].get("reason")
                if reason not in [
                    "userRateLimitExceeded",
                    "dailyLimitExceeded",
                    "cannotCopyFile",
                ]:
                    raise err
                if reason == "cannotCopyFile":
                    LOGGER.error(err)
                elif config_dict["USE_SERVICE_ACCOUNTS"]:
                    if self.__sa_count >= self.__sa_number:
                        LOGGER.info(
                            f"Reached maximum number of service accounts switching, which is {self.__sa_count}"
                        )
                        raise err
                    else:
                        if self.__is_cancelled:
                            return
                        self.__switchServiceAccount()
                        return self.__copyFile(file_id, dest_id)
                else:
                    LOGGER.error(f"Got: {reason}")
                    raise err

    async def __progress(self):
        if self.__status is not None:
            chunk_size = (
                self.__status.total_size * self.__status.progress()
                - self.__file_processed_bytes
            )
            self.__file_processed_bytes = (
                self.__status.total_size * self.__status.progress()
            )
            self.__processed_bytes += chunk_size
            self.__total_time += self.__update_interval

    def __switchServiceAccount(self):
        if self.__sa_index == self.__sa_number - 1:
            self.__sa_index = 0
        else:
            self.__sa_index += 1
        self.__sa_count += 1
        LOGGER.info(f"Switching to {self.__sa_index} index")
        self.__service = self.__authorize()

    def __gDrive_file(self, filee):
        size = int(filee.get("size", 0))
        self.__total_bytes += size

    def __gDrive_directory(self, drive_folder):
        files = self.__getFilesByFolderId(drive_folder["id"])
        if len(files) == 0:
            return
        for filee in files:
            shortcut_details = filee.get("shortcutDetails")
            if shortcut_details is not None:
                mime_type = shortcut_details["targetMimeType"]
                file_id = shortcut_details["targetId"]
                filee = self.__getFileMetadata(file_id)
            else:
                mime_type = filee.get("mimeType")
            if mime_type == self.__G_DRIVE_DIR_MIME_TYPE:
                self.__total_folders += 1
                self.__gDrive_directory(filee)
            else:
                self.__total_files += 1
                self.__gDrive_file(filee)

    def deletefile(self, link: str):
        try:
            file_id = self.__getIdFromUrl(link)
        except (KeyError, IndexError):
            return "Google Drive ID could not be found in the provided link"
        msg = ""
        try:
            self.__service.files().delete(
                fileId=file_id, supportsAllDrives=True
            ).execute()
            msg = "Successfully deleted"
            LOGGER.info(f"Delete Result: {msg}")
        except HttpError as err:
            if "File not found" in str(err) or "insufficientFilePermissions" in str(
                err
            ):
                token_service = self.__alt_authorize()
                if token_service is not None:
                    LOGGER.error("File not found. Trying with token.pickle...")
                    self.__service = token_service
                    return self.deletefile(link)
                err = "File not found or insufficientFilePermissions!"
            LOGGER.error(f"Delete Result: {err}")
            msg = str(err)
        return msg

    def download(self, link):
        self.__is_downloading = True
        file_id = self.__getIdFromUrl(link)
        self.__updater = setInterval(self.__update_interval, self.__progress)
        try:
            meta = self.__getFileMetadata(file_id)
            if meta.get("mimeType") == self.__G_DRIVE_DIR_MIME_TYPE:
                self.__download_folder(file_id, self.__path, self.name)
            else:
                makedirs(self.__path, exist_ok=True)
                self.__download_file(
                    file_id, self.__path, self.name, meta.get("mimeType")
                )
        except Exception as err:
            if isinstance(err, RetryError):
                LOGGER.info(f"Total Attempts: {err.last_attempt.attempt_number}")
                err = err.last_attempt.exception()
            err = str(err).replace(">", "").replace("<", "")
            if "downloadQuotaExceeded" in err:
                err = "Download Quota Exceeded."
            elif "File not found" in err:
                if not self.__alt_auth:
                    token_service = self.__alt_authorize()
                    if token_service is not None:
                        LOGGER.error("File not found. Trying with token.pickle...")
                        self.__service = token_service
                        self.__updater.cancel()
                        return self.download(link)
                err = "File not found!"
            run_async(self.__listener.onDownloadError, err)
            self.__is_cancelled = True
        finally:
            self.__updater.cancel()
            if self.__is_cancelled:
                return
            run_async(self.__listener.onDownloadComplete)

    def __download_folder(self, folder_id, path, folder_name):
        folder_name = folder_name.replace("/", "")
        if not ospath.exists(f"{path}/{folder_name}"):
            makedirs(f"{path}/{folder_name}")
        path += f"/{folder_name}"
        result = self.__getFilesByFolderId(folder_id)
        if len(result) == 0:
            return
        result = sorted(result, key=lambda k: k["name"])
        for item in result:
            file_id = item["id"]
            filename = item["name"]
            shortcut_details = item.get("shortcutDetails")
            if shortcut_details is not None:
                file_id = shortcut_details["targetId"]
                mime_type = shortcut_details["targetMimeType"]
            else:
                mime_type = item.get("mimeType")
            if mime_type == self.__G_DRIVE_DIR_MIME_TYPE:
                self.__download_folder(file_id, path, filename)
            elif not ospath.isfile(
                f"{path}{filename}"
            ) and not filename.lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                self.__download_file(file_id, path, filename, mime_type)
            if self.__is_cancelled:
                break

    @retry(
        wait=wait_exponential(multiplier=2, min=3, max=6),
        stop=stop_after_attempt(3),
        retry=(retry_if_exception_type(Exception)),
    )
    def __download_file(self, file_id, path, filename, mime_type):
        request = self.__service.files().get_media(
            fileId=file_id, supportsAllDrives=True
        )
        filename = filename.replace("/", "")
        if len(filename.encode()) > 255:
            ext = ospath.splitext(filename)[1]
            filename = f"{filename[:245]}{ext}"
            if self.name.endswith(ext):
                self.name = filename
        if self.__is_cancelled:
            return
        fh = FileIO(f"{path}/{filename}", "wb")
        downloader = MediaIoBaseDownload(fh, request, chunksize=100 * 1024 * 1024)
        done = False
        retries = 0
        while not done:
            if self.__is_cancelled:
                fh.close()
                break
            try:
                self.__status, done = downloader.next_chunk()
            except HttpError as err:
                if err.resp.status in [500, 502, 503, 504] and retries < 10:
                    retries += 1
                    continue
                if err.resp.get("content-type", "").startswith("application/json"):
                    reason = (
                        eval(err.content).get("error").get("errors")[0].get("reason")
                    )
                    if reason not in [
                        "downloadQuotaExceeded",
                        "dailyLimitExceeded",
                    ]:
                        raise err
                    if config_dict["USE_SERVICE_ACCOUNTS"]:
                        if self.__sa_count >= self.__sa_number:
                            LOGGER.info(
                                f"Reached maximum number of service accounts switching, which is {self.__sa_count}"
                            )
                            raise err
                        else:
                            if self.__is_cancelled:
                                return
                            self.__switchServiceAccount()
                            LOGGER.info(f"Got: {reason}, Trying Again...")
                            return self.__download_file(
                                file_id, path, filename, mime_type
                            )
                    else:
                        LOGGER.error(f"Got: {reason}")
                        raise err
        self.__file_processed_bytes = 0

    async def cancel_download(self):
        self.__is_cancelled = True
        if self.__is_downloading:
            if not config_dict["NO_TASKS_LOGS"]:
                LOGGER.info(f"Cancelling Download: {self.name}")
            await self.__listener.onDownloadError("Download stopped by user!")
        elif self.__is_cloning:
            if not config_dict["NO_TASKS_LOGS"]:
                LOGGER.info(f"Cancelling Clone: {self.name}")
            await self.__listener.onUploadError(
                "your clone has been stopped and cloned data has been deleted!"
            )
