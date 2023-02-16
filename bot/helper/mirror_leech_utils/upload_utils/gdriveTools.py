# Source: https://github.com/anasty17/mirror-leech-telegram-bot/blob/master/bot/helper/mirror_utils/upload_utils/gdriveTools.py
# Adapted for asyncio framework

from io import FileIO
from logging import getLogger, ERROR
from time import time
from pickle import load as pload, dump as pdump
from os import makedirs, path as ospath
from re import search as re_search
from urllib.parse import parse_qs, urlparse
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError, Error as GCError
from googleapiclient.http import MediaIoBaseDownload
from bot import GLOBAL_EXTENSION_FILTER, config_dict, botloop
from bot.helper.ext_utils.bot_utils import setInterval
from google.auth.transport.requests import Request
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.button_build import ButtonMaker
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, RetryError

LOGGER = getLogger(__name__)
getLogger('googleapiclient.discovery').setLevel(ERROR)



class GoogleDriveHelper:
    def __init__(self, name=None, path=None, listener= None):
        self.__G_DRIVE_TOKEN_FILE = "token.pickle"
        self.__G_DRIVE_DIR_MIME_TYPE = "application/vnd.google-apps.folder"
        self.__G_DRIVE_BASE_DOWNLOAD_URL = "https://drive.google.com/uc?id={}&export=download"
        self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL = "https://drive.google.com/drive/folders/{}"
        self.__total_bytes = 0
        self.__total_files = 0
        self.__total_folders = 0
        self.__start_time = 0
        self.__total_time = 0
        self.__alt_auth = False
        self.__listener = listener
        self.__path = path
        self.__is_cancelled = False
        self.__is_downloading = False
        self.__status = None
        self.__update_interval = 3
        self._file_processed_bytes = 0
        self.name = name
        self.processed_bytes = 0
        self.transferred_size = 0
        self.__service = self.__authorize()

    def speed(self):
        """
        It calculates the average upload speed and returns it in bytes/seconds unit
        :return: Upload speed in bytes/second
        """
        try:
            return self.processed_bytes / self.__total_time
        except:
            return 0

    def cspeed(self):
        try:
            return self.transferred_size / int(time() - self.__start_time)
        except:
            return 0

    def __authorize(self):
        # Get credentials
        credentials = None
        if ospath.exists(self.__G_DRIVE_TOKEN_FILE):
            LOGGER.info("Authorize with token.pickle")
            with open(self.__G_DRIVE_TOKEN_FILE, 'rb') as f:
                credentials = pload(f)
            if credentials and not credentials.valid and credentials.expired and credentials.refresh_token:
                LOGGER.warning('Your token is expired! Refreshing Token...')
                credentials.refresh(Request())
                with open(self.__G_DRIVE_TOKEN_FILE, 'wb') as token:
                    pdump(credentials, token)
        else:
            LOGGER.error('token.pickle not found!')
        return build('drive', 'v3', credentials=credentials, cache_discovery=False)

    def __alt_authorize(self):
        credentials = None
        if not self.__alt_auth:
            self.__alt_auth = True
            if ospath.exists(self.__G_DRIVE_TOKEN_FILE):
                LOGGER.info("Authorize with token.pickle")
                with open(self.__G_DRIVE_TOKEN_FILE, 'rb') as f:
                    credentials = pload(f)
                return build('drive', 'v3', credentials=credentials, cache_discovery=False)
        return None

    @staticmethod
    def __getIdFromUrl(link: str):
        if "folders" in link or "file" in link:
            regex = r"https:\/\/drive\.google\.com\/(?:drive(.*?)\/folders\/|file(.*?)?\/d\/)([-\w]+)"
            res = re_search(regex,link)
            if res is None:
                raise IndexError("G-Drive ID not found.")
            return res.group(3)
        parsed = urlparse(link)
        return parse_qs(parsed.query)['id'][0]

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3),
           retry=retry_if_exception_type(GCError))
    def __set_permission(self, drive_id):
        permissions = {
            'role': 'reader',
            'type': 'anyone',
            'value': None,
            'withLink': True
        }
        return self.__service.permissions().create(fileId=drive_id, body=permissions, supportsTeamDrives=True).execute()

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3),
           retry=retry_if_exception_type(GCError))
    def __getFileMetadata(self, file_id):
        return self.__service.files().get(fileId=file_id, supportsTeamDrives=True,
                                          fields='name, id, mimeType, size').execute() 

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3),
           retry=retry_if_exception_type(GCError))
    def __getFilesByFolderId(self, folder_id):
        page_token = None
        files = []
        while True:
            response = self.__service.files().list(supportsTeamDrives=True, includeTeamDriveItems=True,
                                                   q=f"'{folder_id}' in parents and trashed = false",
                                                   spaces='drive', pageSize=200,
                                                   fields='nextPageToken, files(id, name, mimeType, size, shortcutDetails)',
                                                   orderBy='folder, name', pageToken=page_token).execute()
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            if page_token is None:
                break
        return files

    async def _progress(self):
        if self.__status is not None:
            chunk_size = self.__status.total_size * self.__status.progress() - self._file_processed_bytes
            self._file_processed_bytes = self.__status.total_size * self.__status.progress()
            self.processed_bytes += chunk_size
            self.__total_time += self.__update_interval

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3),
           retry=retry_if_exception_type(GCError))
    def __create_directory(self, directory_name, dest_id):
        file_metadata = {
            "name": directory_name,
            "description": "Uploaded by Mirror-leech-telegram-bot",
            "mimeType": self.__G_DRIVE_DIR_MIME_TYPE
        }
        if dest_id is not None:
            file_metadata["parents"] = [dest_id]
        file = self.__service.files().create(body=file_metadata, supportsTeamDrives=True).execute()
        file_id = file.get("id")
        if not config_dict['IS_TEAM_DRIVE']:
            self.__set_permission(file_id)
        LOGGER.info("Created G-Drive Folder:\nName: {}\nID: {} ".format(file.get("name"), file_id))
        return file_id

    def clone(self, link):
        self.__start_time = time()
        self.__total_files = 0
        self.__total_folders = 0
        try:
            file_id = self.__getIdFromUrl(link)
        except (KeyError, IndexError):
            msg = "Google Drive ID could not be found in the provided link"
            return msg
        msg = ""
        LOGGER.info(f"File ID: {file_id}")
        try:
            meta = self.__getFileMetadata(file_id)
            mime_type = meta.get("mimeType")
            if mime_type == self.__G_DRIVE_DIR_MIME_TYPE:
                dir_id = self.__create_directory(meta.get('name'), config_dict['GDRIVE_FOLDER_ID'])
                self.__cloneFolder(meta.get('name'), meta.get('name'), meta.get('id'), dir_id)
                durl = self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL.format(dir_id)
                if self.__is_cancelled:
                    LOGGER.info("Deleting cloned data from Drive...")
                    self.deletefile(durl)
                    return "your clone has been stopped and cloned data has been deleted!", "cancelled"
                msg += f'<b>Name: </b><code>{meta.get("name")}</code>'
                msg += f'\n\n<b>Size: </b>{get_readable_file_size(self.transferred_size)}'
                msg += '\n\n<b>Type: </b>Folder'
                msg += f'\n<b>SubFolders: </b>{self.__total_folders}'
                msg += f'\n<b>Files: </b>{self.__total_files}'
                buttons = ButtonMaker()
                buttons.url_buildbutton("Cloud Link 🔗", durl)
            else:
                file = self.__copyFile(meta.get('id'), config_dict['GDRIVE_FOLDER_ID'])
                msg += f'<b>Name: </b><code>{file.get("name")}</code>'
                durl = self.__G_DRIVE_BASE_DOWNLOAD_URL.format(file.get("id"))
                buttons = ButtonMaker()
                buttons.url_buildbutton("Cloud Link 🔗", durl)
                if mime_type is None:
                    mime_type = 'File'
                msg += f'\n\n<b>Size: </b>{get_readable_file_size(int(meta.get("size", 0)))}'
                msg += f'\n\n<b>Type: </b>{mime_type}'
        except Exception as err:
            if isinstance(err, RetryError):
                LOGGER.info(f"Total Attempts: {err.last_attempt.attempt_number}")
                err = err.last_attempt.exception()
            err = str(err).replace('>', '').replace('<', '')
            if "User rate limit exceeded" in err:
                msg = "User rate limit exceeded."
            elif "File not found" in err:
                token_service = self.__alt_authorize()
                if token_service is not None:
                    self.__service = token_service
                    return self.clone(link)
                msg = "File not found."
            else:
                msg = f"Error.\n{err}"
            return msg, ""
        return msg, buttons.build_menu(2)

    def __cloneFolder(self, name, local_path, folder_id, dest_id):
        LOGGER.info(f"Syncing: {local_path}")
        files = self.__getFilesByFolderId(folder_id)
        if len(files) == 0:
            return dest_id
        for file in files:
            if file.get('mimeType') == self.__G_DRIVE_DIR_MIME_TYPE:
                self.__total_folders += 1
                file_path = ospath.join(local_path, file.get('name'))
                current_dir_id = self.__create_directory(file.get('name'), dest_id)
                self.__cloneFolder(file.get('name'), file_path, file.get('id'), current_dir_id)
            elif not file.get('name').lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                self.__total_files += 1
                self.transferred_size += int(file.get('size', 0))
                self.__copyFile(file.get('id'), dest_id)
            if self.__is_cancelled:
                break

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3),
           retry=retry_if_exception_type(GCError))
    def __copyFile(self, file_id, dest_id):
        body = {'parents': [dest_id]}
        try:
            return self.__service.files().copy(fileId=file_id, body=body, supportsTeamDrives=True).execute()
        except HttpError as err:
            if err.resp.get('content-type', '').startswith('application/json'):
                reason = eval(err.content).get('error').get('errors')[0].get('reason')
                if reason in ['userRateLimitExceeded', 'dailyLimitExceeded']:
                    self.__is_cancelled  = True
                    LOGGER.error(f"Got: {reason}")
                    raise err
                else:
                    raise err

    def __gDrive_file(self, filee):
        size = int(filee.get('size', 0))
        self.__total_bytes += size

    def __gDrive_directory(self, drive_folder):
        files = self.__getFilesByFolderId(drive_folder['id'])
        if len(files) == 0:
            return
        for filee in files:
            shortcut_details = filee.get('shortcutDetails')
            if shortcut_details is not None:
                mime_type = shortcut_details['targetMimeType']
                file_id = shortcut_details['targetId']
                filee = self.__getFileMetadata(file_id)
            else:
                mime_type = filee.get('mimeType')
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
            msg = "Google Drive ID could not be found in the provided link"
            return msg
        msg = ''
        try:
            self.__service.files().delete(fileId=file_id, supportsTeamDrives=True).execute()
            msg = "Successfully deleted"
            LOGGER.info(f"Delete Result: {msg}")
        except HttpError as err:
            if "File not found" in str(err):
                msg = "No such file exist"
            elif "insufficientFilePermissions" in str(err):
                msg = "Insufficient File Permissions"
                token_service = self.__alt_authorize()
                if token_service is not None:
                    self.__service = token_service
                    return self.deletefile(link)
            else:
                msg = err
            LOGGER.error(f"Delete Result: {msg}")
        finally:
            return msg

    async def download(self, link):
        self.__is_downloading = True
        file_id = self.__getIdFromUrl(link)
        self.__updater = setInterval(self.__update_interval, self._progress)
        try:
            meta = await botloop.run_in_executor(None, self.__getFileMetadata, file_id)
            if meta.get("mimeType") == self.__G_DRIVE_DIR_MIME_TYPE:
                await botloop.run_in_executor(None, self.__download_folder, file_id, self.__path, self.name)
            else:
                makedirs(self.__path, exist_ok=True)
                await botloop.run_in_executor(None, self.__download_file, file_id, self.__path, self.name, meta.get('mimeType'))
        except Exception as err:
            if isinstance(err, RetryError):
                LOGGER.info(f"Total Attempts: {err.last_attempt.attempt_number}")
                err = err.last_attempt.exception()
            err = str(err).replace('>', '').replace('<', '')
            if "downloadQuotaExceeded" in err:
                err = "Download Quota Exceeded."
            elif "File not found" in err:
                token_service = self.__alt_authorize()
                if token_service is not None:
                    self.__service = token_service
                    self.__updater.cancel()
                    return await self.download(link)
            await self.__listener.onDownloadError(err)
            self.__is_cancelled = True
        finally:
            self.__updater.cancel()
            if self.__is_cancelled:
                return
        await self.__listener.onDownloadComplete()

    def __download_folder(self, folder_id, path, folder_name):
        folder_name = folder_name.replace('/', '')
        if not ospath.exists(f"{path}/{folder_name}"):
            makedirs(f"{path}/{folder_name}")
        path += f"/{folder_name}"
        result = self.__getFilesByFolderId(folder_id)
        if len(result) == 0:
            return
        result = sorted(result, key=lambda k: k['name'])
        for item in result:
            file_id = item['id']
            filename = item['name']
            shortcut_details = item.get('shortcutDetails')
            if shortcut_details is not None:
                file_id = shortcut_details['targetId']
                mime_type = shortcut_details['targetMimeType']
            else:
                mime_type = item.get('mimeType')
            if mime_type == self.__G_DRIVE_DIR_MIME_TYPE:
                self.__download_folder(file_id, path, filename)
            elif not ospath.isfile(f"{path}{filename}") and not filename.lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                self.__download_file(file_id, path, filename, mime_type)
            if self.__is_cancelled:
                break    

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3),
           retry=(retry_if_exception_type(Exception)))
    def __download_file(self, file_id, path, filename, mime_type):
        request = self.__service.files().get_media(fileId=file_id, supportsAllDrives=True)
        filename = filename.replace('/', '')
        if len(filename.encode()) > 255:
            ext = ospath.splitext(filename)[1]
            filename = f"{filename[:245]}{ext}"
            if self.name.endswith(ext):
                self.name = filename
        if self.__is_cancelled:
            return
        fh = FileIO(f"{path}/{filename}", 'wb')
        downloader = MediaIoBaseDownload(fh, request, chunksize=50 * 1024 * 1024)
        done = False
        while not done:
            if self.__is_cancelled:
                fh.close()
                break
            try:
                self.__status, done = downloader.next_chunk()
            except HttpError as err:
                if err.resp.get('content-type', '').startswith('application/json'):
                    reason = eval(err.content).get('error').get('errors')[0].get('reason')
                    if reason not in [
                        'downloadQuotaExceeded',
                        'dailyLimitExceeded',
                    ]:
                        raise err
                    LOGGER.error(f"Got: {reason}")
                    raise err
        self._file_processed_bytes = 0            

    def helper(self, link):
        try:
            file_id = self.__getIdFromUrl(link)
        except (KeyError, IndexError):
            msg = "Google Drive ID could not be found in the provided link"
            return msg, "", "", ""
        LOGGER.info(f"File ID: {file_id}")
        try:
            meta = self.__getFileMetadata(file_id)
            name = meta['name']
            LOGGER.info(f"Checking size, this might take a minute: {name}")
            if meta.get('mimeType') == self.__G_DRIVE_DIR_MIME_TYPE:
                self.__gDrive_directory(meta)
            else:
                self.__total_files += 1
                self.__gDrive_file(meta)
            size = self.__total_bytes
            files = self.__total_files
        except Exception as err:
            if isinstance(err, RetryError):
                LOGGER.info(f"Total Attempts: {err.last_attempt.attempt_number}")
                err = err.last_attempt.exception()
            err = str(err).replace('>', '').replace('<', '')
            if "File not found" in err:
                token_service = self.__alt_authorize()
                if token_service is not None:
                    self.__service = token_service
                    return self.helper(link)
                msg = "File not found."
            else:
                msg = f"Error.\n{err}"
            return msg, "", "", ""
        return "", size, name, files

    async def cancel_download(self):
        self.__is_cancelled = True
        if self.__is_downloading:
            LOGGER.info(f"Cancelling Download: {self.name}")
            await self.__listener.onDownloadError('Download stopped by user!')
        else:
            LOGGER.info(f"Cancelling Clone: {self.name}")
