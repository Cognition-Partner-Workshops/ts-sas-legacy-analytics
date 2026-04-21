"""
Tests for sas_utils.email.sendmail

Derived from Macro/sendmail.sas Usage block (lines 134-257).
Mock SMTP server tests.
"""

from unittest.mock import MagicMock, patch

import pytest

from sas_utils.email.sendmail import send_email


# ====================================================================
# Test: basic email sending (mocked)
# ====================================================================
class TestSendEmail:
    @patch("sas_utils.email.sendmail.smtplib.SMTP")
    def test_basic_send(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        send_email(
            to="user@example.com",
            subject="Test Subject",
            body="Test body",
            from_addr="sender@example.com",
        )

        mock_server.sendmail.assert_called_once()
        args = mock_server.sendmail.call_args
        assert args[0][0] == "sender@example.com"
        assert "user@example.com" in args[0][1]

    @patch("sas_utils.email.sendmail.smtplib.SMTP")
    def test_send_with_cc_bcc(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        send_email(
            to="user@example.com",
            subject="Test",
            cc="cc@example.com",
            bcc="bcc@example.com",
            from_addr="sender@example.com",
        )

        args = mock_server.sendmail.call_args
        recipients = args[0][1]
        assert "user@example.com" in recipients
        assert "cc@example.com" in recipients
        assert "bcc@example.com" in recipients

    @patch("sas_utils.email.sendmail.smtplib.SMTP")
    def test_send_multiple_to(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        send_email(
            to=["a@example.com", "b@example.com"],
            subject="Test",
            from_addr="sender@example.com",
        )

        args = mock_server.sendmail.call_args
        recipients = args[0][1]
        assert "a@example.com" in recipients
        assert "b@example.com" in recipients

    @patch("sas_utils.email.sendmail.smtplib.SMTP")
    def test_send_with_attachment(self, mock_smtp_cls, tmp_path):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        attachment = tmp_path / "test.txt"
        attachment.write_text("attachment content")

        send_email(
            to="user@example.com",
            subject="Test",
            body="See attached",
            attachments=[attachment],
            from_addr="sender@example.com",
        )

        mock_server.sendmail.assert_called_once()
