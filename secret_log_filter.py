from __future__ import annotations

import logging
import re

from flexget.log import add_filter


SECRET_PATTERNS = (
    re.compile(
        r'(?P<prefix>(?:https?://)?api\.telegram\.org/bot)'
        r'\d{5,20}:[A-Za-z0-9_-]{20,}',
        flags=re.IGNORECASE,
    ),
    re.compile(
        r'(?P<prefix>(?:access_token|token|api(?:_|-)?key|passkey|password|psd|client_secret)=)'
        r'[^&\s"<>]+',
        flags=re.IGNORECASE,
    ),
    re.compile(
        r'(?P<prefix>Passkey.{0,3000}?<code>)[^<]+',
        flags=re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r'(?P<prefix>data-copy=["\'])[^"\']+',
        flags=re.IGNORECASE,
    ),
)


def redact_secrets(message: str) -> str:
    for pattern in SECRET_PATTERNS:
        message = pattern.sub(r'\g<prefix>[REDACTED]', message)
    return message


class SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted_message = redact_secrets(message)
        if redacted_message != message:
            record.msg = redacted_message
            record.args = ()
        return True


def redact_loguru_record(record: dict) -> bool:
    record['message'] = redact_secrets(record['message'])
    return True


logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

secret_redaction_filter = SecretRedactionFilter()
for handler in logging.getLogger().handlers:
    handler.addFilter(secret_redaction_filter)

add_filter(redact_loguru_record)
