"""Notification compatibility shim."""

from __future__ import annotations

import logging
from collections.abc import Iterable

LOGGER = logging.getLogger(__name__)


def sendmail(
    to: str,
    subject: str,
    body: str,
    attachments: Iterable[str] = (),
) -> dict[str, object]:
    """Log a notification payload; job notifications replace SMTP (D4-003)."""

    payload = {
        "to": to,
        "subject": subject,
        "body": body,
        "attachments": tuple(attachments),
    }
    LOGGER.info("sendmail stub: %s", payload)
    return payload
