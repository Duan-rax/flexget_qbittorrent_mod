from __future__ import annotations

from requests import Response

from ptsites.base.entry import SignInEntry
from ptsites.base.work import Work
from ptsites.trackers import dmhy


def test_anime_answer_is_submitted_from_showup_page(monkeypatch) -> None:
    tracker = dmhy.MainClass()
    entry = SignInEntry()
    entry.update({
        'site_config': {'username': 'tester'},
        'url': tracker.URL,
    })
    work = Work(
        url=tracker.URL + 'showup.php?action=show',
        method=tracker.sign_in_by_anime,
        data={},
    )
    answer = {
        'captcha_token': 'answer',
        'req': 'request-token',
        'hash': 'image-hash',
        'form': 'form-token',
    }
    submitted = {}
    response = Response()
    response.status_code = 200

    monkeypatch.setattr(dmhy, 'fuzz', object())
    monkeypatch.setattr(dmhy, 'process', object())
    monkeypatch.setattr(tracker, 'build_data', lambda *args: answer)

    def fake_request(entry_arg, method, url, **kwargs):
        submitted.update(method=method, url=url, **kwargs)
        return response

    monkeypatch.setattr(tracker, 'request', fake_request)

    assert tracker.sign_in_by_anime(entry, {}, work, '<html>') is response
    assert submitted == {
        'method': 'post',
        'url': tracker.URL + 'showup.php?action=show',
        'data': answer,
        'headers': {
            'origin': 'https://u2.dmhy.org',
            'referer': tracker.URL + 'showup.php?action=show',
        },
    }
