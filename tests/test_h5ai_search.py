import json
import sys
import types
import unittest
from unittest import mock


xbmc_stub = types.SimpleNamespace(
    LOGINFO=1, LOGERROR=4, log=lambda *args, **kwargs: None
)
xbmcaddon_stub = types.SimpleNamespace(Addon=lambda *args, **kwargs: None)
sys.modules.setdefault("xbmc", xbmc_stub)
sys.modules.setdefault("xbmcaddon", xbmcaddon_stub)

from lib.h5ai import search_directory


class _FakeResponse:
    def __init__(self, body: str):
        self._body = body.encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class SearchDirectoryTests(unittest.TestCase):
    def test_search_directory_uses_h5ai_search_params(self):
        def fake_urlopen(request, timeout=0):
            self.assertEqual(timeout, 15)
            payload = request.data.decode("utf-8")
            self.assertIn("action=get", payload)
            self.assertIn(
                "search%5Bhref%5D=%2FDHAKA-FLIX-7%2FEnglish%20Movies%2F", payload
            )
            self.assertIn("search%5Bpattern%5D=avatar", payload)
            self.assertIn("search%5Bignorecase%5D=1", payload)

            body = json.dumps(
                {
                    "search": [
                        {
                            "href": "/DHAKA-FLIX-7/English%20Movies/%282009%29/Avatar%20%282009%29/",
                            "size": None,
                        }
                    ]
                }
            )
            return _FakeResponse(body)

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            results = search_directory(
                pattern="avatar",
                href="/DHAKA-FLIX-7/English Movies/",
                base_url="http://172.16.50.7",
                api_path="/_h5ai/public/index.php",
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Avatar (2009)")
        self.assertEqual(results[0]["type"], "folder")


if __name__ == "__main__":
    unittest.main()
