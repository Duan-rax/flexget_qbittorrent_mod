from __future__ import annotations

from typing import Final

from ..base.sign_in import check_final_state, SignState, Work
from ..schema.private_torrent import PrivateTorrent
from ..utils.value_handler import handle_infinite


class MainClass(PrivateTorrent):
    URL: Final = 'https://www.myanonamouse.net/'
    # The API session cannot reach HTML pages, so the join date is
    # unavailable and the 'days' requirement cannot be evaluated.
    USER_CLASSES: Final = {
        'uploaded': [26843545600],
        'share_ratio': [2.0],
    }

    # Config format (the mam_id= prefix is required):
    #   sign_in:
    #     sites:
    #       myanonamouse: 'mam_id=xxxxxxxx...'
    #
    # Create a session at Preferences -> Security (IP or ASN locked).
    # Password login via takelogin.php is deliberately avoided: the site
    # counts failed login attempts and locks the account out.

    def sign_in_build_workflow(self, entry, config: dict) -> list[Work]:
        return [
            Work(
                url='/jsonLoad.php?snatch_summary',
                method=self.sign_in_by_get,
                succeed_regex=[r'"uid":\s*\d+'],
                response_urls=['/jsonLoad.php?snatch_summary'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
            )
        ]

    @property
    def details_selector(self) -> dict:
        return {
            'user_id': r'"uid":\s*(\d+)',
            'detail_sources': {
                'default': {
                    'link': '/jsonLoad.php?snatch_summary',
                    'elements': None,
                }
            },
            'details': {
                'uploaded': {
                    'regex': r'"uploaded":\s*"([\d.,]+ [ZEPTGMK]i?B)"'
                },
                'downloaded': {
                    'regex': r'"downloaded":\s*"([\d.,]+ [ZEPTGMK]i?B)"'
                },
                'share_ratio': {
                    'regex': r'"ratio":\s*([\d.]+)',
                    'handle': handle_infinite
                },
                'points': {
                    'regex': r'"seedbonus":\s*([\d.]+)'
                },
                'seeding': {
                    'regex': r'"seedUnsat":\s*\{\s*"count":\s*(\d+)'
                },
                'leeching': {
                    'regex': r'"leeching":\s*\{\s*"count":\s*(\d+)'
                },
                'join_date': None,
                'hr': None,
            }
        }
