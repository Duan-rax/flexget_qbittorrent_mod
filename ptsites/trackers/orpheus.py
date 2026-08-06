from typing import Final

from ..base.entry import SignInEntry
from ..base.request import check_network_state, NetworkState
from ..base.sign_in import check_final_state, SignState
from ..base.work import Work
from ..schema.gazelle import Gazelle
from ..utils import net_utils
from ..utils.net_utils import get_module_name


class MainClass(Gazelle):
    URL: Final = 'https://orpheus.network/'
    USER_CLASSES: Final = {
        'uploaded': [26843545600, 2199023255552],
        'share_ratio': [1.05, 1.05],
        'days': [14, 56]
    }

    @classmethod
    def sign_in_build_schema(cls) -> dict:
        return {
            get_module_name(cls): {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'},
                    'login': {
                        'type': 'object',
                        'properties': {
                            'username': {'type': 'string'},
                            'password': {'type': 'string'}
                        },
                        'additionalProperties': False
                    }
                },
                'additionalProperties': False
            }
        }

    def sign_in_build_login_data(self, login: dict, last_content: str) -> dict:
        return {
            'username': login['username'],
            'password': login['password'],
            'mfa': '',
            'keeplogged': 1,
            'login': 'Log in',
        }

    def sign_in_build_login_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/login.php',
                method=self.sign_in_by_login,
                assert_state=(check_network_state, NetworkState.SUCCEED),
                response_urls=['/index.php'],
            ),
        ]

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['<h1 class="site_name">Orpheus</h1>'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        net_utils.dict_merge(selector, {
            'detail_sources': {
                'default': {
                    'elements': {
                        # Seeding and leeching counts live in the Community box,
                        # not in the Statistics box the base class reads.
                        'community': 'div.box_userinfo_community > ul'
                    }
                }
            },
            'details': {
                # Anchor on the colon so "Seeding Size: 0 B" in the Statistics
                # box is not picked up instead of the actual torrent count.
                'seeding': {
                    'regex': r'Seeding:\s*([\d,]+)'
                },
                'leeching': {
                    'regex': r'Leeching:\s*([\d,]+)'
                }
            }
        })
        return selector
