from typing import Final

from ..schema.nexusphp import Visit
from ..utils import net_utils


class MainClass(Visit):
    URL: Final = 'https://zeus.hamsters.space/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [252, 567]
    }

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    # The seeding and leeching counts are only separated by the
                    # arrow images, so the markup has to be kept.
                    'do_not_strip': True,
                    'elements': {
                        'bar': '#header-userinfo',
                        'table': '#outer table'
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'id="uploaded">\s*([\d.]+ ?[ZEPTGMK]?i?B)'
                },
                'downloaded': {
                    'regex': r'下[载載]量.*?</span>\s*([\d.]+ ?[ZEPTGMK]?i?B)'
                },
                'share_ratio': {
                    'regex': r'分享率.*?</span>\s*(---|∞|无限|無限|[\d,.]+)'
                },
                'points': {
                    'regex': r'id="bonus">\s*([\d,.]+)'
                },
                'seeding': {
                    'regex': r'class="arrowup"[^>]*>\s*(\d+)'
                },
                'leeching': {
                    'regex': r'class="arrowdown"[^>]*>\s*(\d+)'
                },
                'join_date': {
                    'regex': r'加入日期</td>.*?(\d{4}-\d{2}-\d{2})'
                },
                'hr': None
            }
        })
        return selector
