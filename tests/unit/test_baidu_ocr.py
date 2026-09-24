from __future__ import annotations

from PIL import Image

from ptsites.base.entry import SignInEntry
from ptsites.utils import baidu_ocr


def test_get_client_reuses_sdk_client(monkeypatch) -> None:
    clients = []

    class FakeAipOcr:
        def __init__(self, app_id, api_key, secret_key):
            clients.append((app_id, api_key, secret_key))

    monkeypatch.setattr(baidu_ocr, 'AipOcr', FakeAipOcr)
    baidu_ocr._get_cached_client.cache_clear()
    entry = SignInEntry()
    config = {
        'aipocr': {
            'app_id': 'app-id',
            'api_key': 'api-key',
            'secret_key': 'secret-key',
        }
    }

    assert baidu_ocr.get_client(entry, config) is baidu_ocr.get_client(entry, config)
    assert clients == [('app-id', 'api-key', 'secret-key')]
    baidu_ocr._get_cached_client.cache_clear()


def test_japanese_ocr_network_error_is_recoverable(monkeypatch) -> None:
    class FailingClient:
        def basicAccurate(self, *args, **kwargs):
            raise ConnectionError('https://example.test/token?client_secret=must-not-be-logged')

    monkeypatch.setattr(baidu_ocr, 'get_client', lambda *args: FailingClient())
    entry = SignInEntry()

    assert baidu_ocr.get_jap_ocr(Image.new('RGB', (10, 10)), entry, {}) is None
    assert not entry.failed
