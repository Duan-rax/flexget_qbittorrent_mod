from __future__ import annotations

from types import SimpleNamespace

from requests import Response

from ptsites.base.entry import SignInEntry
from ptsites.trackers import ptsbao


def test_workflow_uses_captcha_post() -> None:
    tracker = ptsbao.MainClass()
    entry = SignInEntry()

    workflow = tracker.sign_in_build_workflow(entry, {})

    assert [work.url for work in workflow] == ['/attendance.php', '/attendance.php']
    assert workflow[1].method == tracker.sign_in_by_ocr


def test_ocr_uses_full_captcha_url_and_submits_code(monkeypatch) -> None:
    tracker = ptsbao.MainClass()
    entry = SignInEntry()
    entry.update({'url': tracker.URL, 'site_name': 'ptsbao', 'site_config': 'test-cookie'})
    work = tracker.sign_in_build_workflow(entry, {})[1]
    content = '''
        <form action="attendance.php" method="post">
            <img src="image.php?action=regimage&amp;imagehash=hash-token&amp;secret=secret-token" />
            <input type="hidden" name="imagehash" value="hash-token" />
        </form>
    '''
    requested = []

    def fake_request(entry_arg, method, url, **kwargs):
        requested.append((method, url, kwargs))
        response = Response()
        response.status_code = 200
        response.url = url
        response._content = b'image'
        return response

    monkeypatch.setattr(tracker, 'request', fake_request)
    monkeypatch.setattr(ptsbao, 'Image', SimpleNamespace(open=lambda *_: object()))
    monkeypatch.setattr(ptsbao.baidu_ocr, 'get_ocr_code', lambda *args: ('ABC123', b''))

    assert tracker.sign_in_by_ocr(entry, {}, work, content) is not None
    assert requested == [
        (
            'get',
            tracker.URL + 'image.php?action=regimage&imagehash=hash-token&secret=secret-token',
            {},
        ),
        (
            'post',
            '/attendance.php',
            {'data': {'imagehash': 'hash-token', 'imagestring': 'ABC123'}},
        ),
    ]
