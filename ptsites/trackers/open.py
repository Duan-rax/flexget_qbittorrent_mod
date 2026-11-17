from __future__ import annotations

from io import BytesIO
from typing import Final
from urllib.parse import urljoin

from flexget.utils.soup import get_soup
from requests import Response

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.reseed import ReseedPasskey
from ..base.sign_in import check_final_state, SignState, check_sign_in_state
from ..base.work import Work
from ..schema.nexusphp import NexusPHP
from ..utils import baidu_ocr
from ..utils import net_utils

try:
    from PIL import Image
except ImportError:
    Image = None


class MainClass(NexusPHP, ReseedPasskey):
    URL: Final = 'https://open.cd/'
    IGNORE_TITLE = '種子被刪除'
    USER_CLASSES: Final = {
        'downloaded': [644245094400, 3298534883328],
        'share_ratio': [3.5, 5],
        'days': [175, 210]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['查看簽到記錄'],
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True,
            ),
            Work(
                url='/plugin_sign-in.php',
                method=self.sign_in_by_ocr,
                succeed_regex=['{"state":"success","signindays":"\\d+","integral":"\\d+"}'],
                fail_regex='验证码错误',
                response_urls=['/plugin_sign-in.php', '/plugin_sign-in.php?cmd=signin'],
                assert_state=(check_final_state, SignState.SUCCEED),
            ),
        ]

    def sign_in_by_ocr(self, entry: SignInEntry, config: dict, work: Work, last_content: str) -> Response | None:
        image_hash_response = self.request(entry, 'get', work.url)
        image_hash_network_state = check_network_state(entry, work, image_hash_response)
        if image_hash_network_state != NetworkState.SUCCEED:
            entry.fail_with_prefix('Get image hash failed.')
            return None
        form = get_soup(net_utils.decode(image_hash_response)).select_one(
            'form:has(input[name="imagehash"]):has(input[name="imagestring"])'
        )
        if form is None:
            entry.fail_with_prefix('Cannot find the sign-in form.')
            return None

        fields = {}
        for name in ('imagehash', 'csrf_token'):
            field = form.select_one(f'input[name="{name}"][value]')
            if field is None or not field['value']:
                entry.fail_with_prefix(f'Cannot find key: {name}')
                return None
            fields[name] = (None, field['value'])

        image = form.select_one('img[src*="imagehash="]')
        if image is None:
            entry.fail_with_prefix('Cannot find the sign-in image.')
            return None

        headers = {'Referer': image_hash_response.url}
        img_url = urljoin(image_hash_response.url, image['src'])
        img_response = self.request(entry, 'get', img_url, headers=headers)
        if check_network_state(entry, img_url, img_response) != NetworkState.SUCCEED:
            entry.fail_with_prefix('Get image failed.')
            return None

        with Image.open(BytesIO(img_response.content)) as img:
            code, _ = baidu_ocr.get_ocr_code(img, entry, config)
        if not entry.failed and code and len(code) == 6:
            fields['imagestring'] = (None, code)
            return self.request(
                entry, 'post', work.url, files=fields, params={'cmd': 'signin'}, headers=headers
            )
        return None

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#info_block > tbody > tr > td > table > tbody > tr > td:nth-child(2)'
                    }
                }
            }
        })
        return selector

    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        self.get_nexusphp_messages(entry, config, ignore_title=self.IGNORE_TITLE)
