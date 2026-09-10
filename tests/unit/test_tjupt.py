from __future__ import annotations

import pytest
from PIL import Image
from requests import Response

from ptsites.base.entry import SignInEntry
from ptsites.trackers.tjupt import MainClass, compareHash, toHash


def test_to_hash_uses_grayscale_average_threshold() -> None:
    image = Image.new('L', (10, 10))
    image.putdata([0] * 50 + [255] * 50)

    assert toHash(image) == '0' * 50 + '1' * 50


def test_compare_hash_returns_matching_pixel_ratio() -> None:
    assert compareHash('0' * 50 + '1' * 50, '0' * 75 + '1' * 25) == 0.75


@pytest.mark.parametrize(('counts', 'seeding', 'leeching'), [
    ('种子数合计 123 / 4', '123', '4'),
    ('种子数合计 0 / 0', '0', '0'),
    ('当前做种 [显示/隐藏] 加载中... 当前下载 [显示/隐藏] 加载中...', '*', '*'),
])
def test_details_support_legacy_and_async_counts(monkeypatch, counts, seeding, leeching) -> None:
    tracker = MainClass()
    entry = SignInEntry()
    entry.update({
        'site_name': 'tjupt',
        'site_config': 'test-cookie',
        'url': tracker.URL,
        'base_content': '<a href="userdetails.php?id=123">User</a>',
    })
    response = Response()
    response.status_code = 200
    response.url = tracker.URL + 'userdetails.php?id=123'
    response._content = f'''
        <table id="info_block"><tbody><tr><td>个人主页设定</td></tr></tbody></table>
        <div id="outer"><table class="main"><tr><td>
        加入日期2021-03-17 01:59:41
        上传量5.244 TiB
        H&amp;R积分100
        魔力值1398841.9
        {counts}
        完成种子 加载中... 未完成种子 加载中...
        </td></tr></table></div>
    '''.encode('utf-8')
    monkeypatch.setattr(tracker, 'request', lambda *args, **kwargs: response)

    tracker.get_details(entry, {})

    assert not entry.failed
    assert entry['details'] == {
        'uploaded': '5.244 TiB', 'downloaded': '*', 'share_ratio': '*',
        'points': '1398841.9', 'join_date': '2021-03-17',
        'seeding': seeding, 'leeching': leeching, 'hr': '0',
    }


def test_missing_required_detail_still_fails_to_parse() -> None:
    tracker = MainClass()
    assert tracker.get_detail_value('加载中...', tracker.details_selector['details']['uploaded']) is None
    assert tracker.get_detail_value('', None) == '*'
