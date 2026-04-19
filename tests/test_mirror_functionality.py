import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


os.environ.setdefault("BOT_TOKEN", "123456:TESTTOKEN")
os.environ.setdefault("OWNER_ID", "6319125974")
os.environ.setdefault("TELEGRAM_API_ID", "12345")
os.environ.setdefault("TELEGRAM_API_HASH", "testhash")


from bot.helper.ext_utils import rclone_utils
from bot.modules import botfiles, mirror_leech


class _PromptMessage:
    async def delete(self):
        return None


class _FakeListen:
    def __init__(self, response):
        self._response = response

    async def Message(self, *args, **kwargs):
        return self._response

    async def Cancel(self, *args, **kwargs):
        return None


class _FakeClient:
    def __init__(self, response, payload=b"[remote]\ntype = drive\n"):
        self.listen = _FakeListen(response)
        self._payload = payload

    async def send_message(self, *args, **kwargs):
        return _PromptMessage()

    async def download_media(self, _response, file_name):
        folder = os.path.dirname(file_name)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(file_name, "wb") as stream:
            stream.write(self._payload)
        return file_name


def _make_message(user_id=1000, text="/mirror"):
    return SimpleNamespace(
        from_user=SimpleNamespace(id=user_id, username="tester", mention="tester"),
        sender_chat=None,
        id=777,
        text=text,
        chat=SimpleNamespace(id=-100123456),
        reply_to_message=None,
    )


class MirrorFunctionalityTests(unittest.IsolatedAsyncioTestCase):
    async def test_mirror_stops_when_rclone_config_missing(self):
        message = _make_message()

        with patch.object(
            mirror_leech, "is_rclone_config", AsyncMock(return_value=False)
        ) as config_mock, patch.object(
            mirror_leech, "is_remote_selected", AsyncMock(return_value=True)
        ) as remote_mock:
            await mirror_leech.mirror_leech(SimpleNamespace(), message)

        config_mock.assert_awaited_once()
        remote_mock.assert_not_called()

    async def test_mirror_stops_when_remote_not_selected(self):
        message = _make_message()

        with patch.object(
            mirror_leech, "is_rclone_config", AsyncMock(return_value=True)
        ) as config_mock, patch.object(
            mirror_leech, "is_remote_selected", AsyncMock(return_value=False)
        ) as remote_mock:
            await mirror_leech.mirror_leech(SimpleNamespace(), message)

        config_mock.assert_awaited_once()
        remote_mock.assert_awaited_once()

    async def test_rclone_upload_saves_config_for_target_user(self):
        user_id = 6319125974
        message = _make_message(user_id=user_id)
        query = SimpleNamespace(from_user=SimpleNamespace(id=user_id))
        response = SimpleNamespace(text=None, document=SimpleNamespace(file_name="my.conf"))
        client = _FakeClient(response)

        old_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                with patch.object(botfiles, "sendMessage", AsyncMock()), patch.object(
                    botfiles, "DATABASE_URL", ""
                ):
                    await botfiles.set_config_listener(
                        client,
                        query,
                        message,
                        forced_section="rclone",
                        target_user_id=user_id,
                    )

                saved_path = os.path.join("rclone", str(user_id), "rclone.conf")
                self.assertTrue(os.path.exists(saved_path))
            finally:
                os.chdir(old_cwd)

    async def test_is_rclone_config_shows_upload_prompt_when_enabled(self):
        user_id = 6319125974
        message = _make_message(user_id=user_id)

        old_multi = rclone_utils.config_dict.get("MULTI_RCLONE_CONFIG")
        old_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                rclone_utils.config_dict["MULTI_RCLONE_CONFIG"] = True
                with patch.object(
                    rclone_utils, "send_rclone_config_upload_prompt", AsyncMock()
                ) as prompt_mock:
                    result = await rclone_utils.is_rclone_config(
                        user_id,
                        message,
                        show_prompt=True,
                    )

                self.assertFalse(result)
                prompt_mock.assert_awaited_once()
            finally:
                rclone_utils.config_dict["MULTI_RCLONE_CONFIG"] = old_multi
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
