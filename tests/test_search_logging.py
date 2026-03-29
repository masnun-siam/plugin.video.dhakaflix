import sys
import types
import unittest
from unittest import mock


xbmc_stub = types.SimpleNamespace(
    LOGINFO=1, LOGERROR=4, log=lambda *args, **kwargs: None
)
xbmcaddon_stub = types.SimpleNamespace(Addon=lambda: None)
sys.modules.setdefault("xbmc", xbmc_stub)
sys.modules.setdefault("xbmcaddon", xbmcaddon_stub)

from lib.search import search_single_server


class SearchLoggingTests(unittest.TestCase):
    def setUp(self):
        self.server = {
            "name": "English Movies",
            "url": "http://172.16.50.7/DHAKA-FLIX-7/English%20Movies/",
            "base_url": "http://172.16.50.7",
            "api_path": "/_h5ai/public/index.php",
        }

    def test_search_single_server_logs_only_when_setting_enabled(self):
        addon = mock.Mock()
        addon.getSettingBool.return_value = False

        with (
            mock.patch("lib.log_utils.xbmcaddon.Addon", return_value=addon),
            mock.patch(
                "lib.search.search_directory",
                return_value=[
                    {
                        "name": "Avatar",
                        "type": "folder",
                        "path": "/x/",
                        "url": "http://x",
                    }
                ],
            ),
            mock.patch("lib.log_utils.xbmc.log") as log_mock,
        ):
            results = search_single_server("avatar", self.server)

        self.assertEqual(results[0]["source_category"], "English Movies")
        log_mock.assert_not_called()

        addon.getSettingBool.return_value = True
        with (
            mock.patch("lib.log_utils.xbmcaddon.Addon", return_value=addon),
            mock.patch(
                "lib.search.search_directory",
                return_value=[
                    {
                        "name": "Avatar",
                        "type": "folder",
                        "path": "/x/",
                        "url": "http://x",
                    }
                ],
            ),
            mock.patch("lib.log_utils.xbmc.log") as log_mock,
        ):
            search_single_server("avatar", self.server)

        messages = [call.args[0] for call in log_mock.call_args_list]
        self.assertTrue(any("query='avatar'" in message for message in messages))
        self.assertTrue(any("English Movies" in message for message in messages))
        self.assertTrue(any("returned 1 results" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
