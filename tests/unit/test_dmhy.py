from __future__ import annotations

import re
from types import SimpleNamespace

from PIL import Image
from requests import Response

from ptsites.base.entry import SignInEntry
from ptsites.base.work import Work
from ptsites.trackers import dmhy


def test_captcha_image_request_keeps_image_hash() -> None:
    tracker = dmhy.MainClass()
    entry = SignInEntry()
    entry['site_config'] = {'username': 'tester'}
    work = tracker.sign_in_build_workflow(entry, {})[1]
    image_url = 'image.php?action=adbc2&req=v2.signed-request&imagehash=c23fc31a6e29bccc'
    html = f'<img src="{image_url}" />'

    assert re.search(work.img_regex, html).group() == image_url


def test_build_data_uses_dynamic_images_then_registers_image_hash(monkeypatch) -> None:
    tracker = dmhy.MainClass()
    entry = SignInEntry()
    entry.update({
        'site_config': {'username': 'tester', 'comment': 'Hello World'},
        'url': tracker.URL,
    })
    work = tracker.sign_in_build_workflow(entry, {})[1]
    full_image_url = 'image.php?action=adbc2&req=v2.signed-request&imagehash=c23fc31a6e29bccc'
    html = f'''
        <img src="{full_image_url}" />
        <input type="submit" name="captcha_token" value="Salaryman Kintarou / 上班族金太郎" />
        <input type="hidden" name="req" value="v2.signed-request" />
        <input type="hidden" name="hash" value="c23fc31a6e29bccc" />
        <input type="hidden" name="form" value="form-token" />
    '''
    image = Image.new('RGB', (10, 10))
    analyzed_urls = []
    requested = []

    monkeypatch.setattr(
        tracker,
        'get_image',
        lambda entry_arg, config, url, char_count: analyzed_urls.append(url) or (image, image),
    )
    monkeypatch.setattr(dmhy.baidu_ocr, 'get_jap_ocr', lambda *args: '上班族金太郎')
    monkeypatch.setattr(
        dmhy,
        'process',
        SimpleNamespace(extractOne=lambda *args, **kwargs: ('上班族金太郎', 100)),
    )
    monkeypatch.setattr(dmhy, 'fuzz', SimpleNamespace(partial_ratio=object()))

    def fake_request(entry_arg, method, url, **kwargs):
        requested.append((method, url, kwargs))
        response = Response()
        response.status_code = 200
        response.url = url
        return response

    monkeypatch.setattr(tracker, 'request', fake_request)

    assert tracker.build_data(entry, {}, work, html, {'retry': 20, 'char_count': 4, 'score': 40}) == {
        'captcha_token': 'Salaryman Kintarou / 上班族金太郎',
        'req': 'v2.signed-request',
        'hash': 'c23fc31a6e29bccc',
        'form': 'form-token',
        'message': 'Hello World',
    }
    assert analyzed_urls == ['image.php?action=adbc2&req=v2.signed-request']
    assert requested == [(
        'get',
        tracker.URL + full_image_url,
        {'headers': {'referer': tracker.URL + 'showup.php?action=show'}},
    )]


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
