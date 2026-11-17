import re
from typing import Final

from requests import Response

from ..base.entry import SignInEntry
from ..base.sign_in import SignState, check_final_state, check_sign_in_state
from ..base.work import Work
from ..schema.nexusphp import AttendanceHR
from ..utils import net_utils


class MainClass(AttendanceHR):
    URL: Final = 'https://www.htpt.cc/'
    USER_CLASSES: Final = {
        'downloaded': [805306368000, 3298534883328],
        'share_ratio': [3.05, 4.55],
        'days': [280, 700]
    }

    def sign_in_build_workflow(self, entry: SignInEntry, config: dict) -> list[Work]:
        succeed_regex = [r'今日已签到']
        return [
            Work(
                url='/attendance.php',
                method=self.sign_in_by_get,
                succeed_regex=succeed_regex,
                assert_state=(check_sign_in_state, SignState.NO_SIGN_IN),
                is_base_content=True,
            ),
            Work(
                url='/attendance.php',
                method=self.sign_in_by_post_and_refresh,
                data={'fixed': {'action': 'sign'}},
                succeed_regex=succeed_regex,
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True,
            ),
        ]


    def sign_in_by_post_and_refresh(
        self, entry: SignInEntry, config: dict, work: Work, last_content: str | None = None
    ) -> Response | None:
        response = self.sign_in_by_post(entry, config, work, last_content)
        if entry.failed or response is None:
            return response

        content = net_utils.decode(response)
        if content and re.search(
            r"""window\.location\.href\s*=\s*["'](?:\./|/)?attendance\.php\?msg=[^"']+["']""",
            content,
        ):
            # The site returns a JavaScript redirect after submitting the form.
            return self.sign_in_by_get(entry, config, work)
        return response
