"""
Email sending utility.

Migrated from: Macro/sendmail.sas
Original author: Scott Bass (01AUG2016)

Sends email via SMTP, with optional attachments and CC/BCC support.
"""

from __future__ import annotations

import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional, Sequence, Union


def send_email(
    to: Union[str, Sequence[str]],
    subject: str,
    body: Optional[str] = None,
    cc: Optional[Union[str, Sequence[str]]] = None,
    bcc: Optional[Union[str, Sequence[str]]] = None,
    from_addr: Optional[str] = None,
    attachments: Optional[Sequence[Union[str, Path]]] = None,
    smtp_host: str = "localhost",
    smtp_port: int = 25,
    content_type: str = "plain",
) -> None:
    """
    Send an email via SMTP.

    Parameters
    ----------
    to : str or list of str
        Recipient email address(es).
    subject : str
        Email subject line.
    body : str, optional
        Email body text.
    cc : str or list of str, optional
        CC recipient(s).
    bcc : str or list of str, optional
        BCC recipient(s).
    from_addr : str, optional
        Sender address. Defaults to ``USER@HOSTNAME``.
    attachments : list of str or Path, optional
        File paths to attach.
    smtp_host : str
        SMTP server hostname. Default ``"localhost"``.
    smtp_port : int
        SMTP server port. Default ``25``.
    content_type : str
        Body content type: ``"plain"`` or ``"html"``. Default ``"plain"``.
    """
    if isinstance(to, str):
        to = [to]
    if isinstance(cc, str):
        cc = [cc]
    if isinstance(bcc, str):
        bcc = [bcc]

    if from_addr is None:
        user = os.environ.get("USER", "unknown")
        import socket
        hostname = socket.gethostname()
        from_addr = f"{user}@{hostname}"

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject

    if cc:
        msg["Cc"] = ", ".join(cc)

    if body:
        msg.attach(MIMEText(body, content_type))

    if attachments:
        for filepath in attachments:
            filepath = Path(filepath)
            if not filepath.exists():
                continue
            with open(filepath, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={filepath.name}",
                )
                msg.attach(part)

    # Build full recipient list
    all_recipients = list(to)
    if cc:
        all_recipients.extend(cc)
    if bcc:
        all_recipients.extend(bcc)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.sendmail(from_addr, all_recipients, msg.as_string())
