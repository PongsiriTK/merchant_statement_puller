"""Gmail IMAP client for fetching email attachments."""

from __future__ import annotations

import email
import imaplib
import logging
import tempfile
from dataclasses import dataclass, field
from email.header import decode_header
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

GMAIL_IMAP_HOST = "imap.gmail.com"
GMAIL_IMAP_PORT = 993


@dataclass
class EmailAttachment:
    """Represents a downloaded email attachment."""

    filename: str
    filepath: Path
    content_type: str
    email_subject: str
    email_date: str


@dataclass
class GmailClient:
    """IMAP client for Gmail with App Password authentication."""

    email_address: str
    app_password: str
    _connection: Optional[imaplib.IMAP4_SSL] = field(default=None, repr=False)

    def connect(self) -> None:
        """Establish IMAP connection to Gmail."""
        logger.info("Connecting to Gmail IMAP as %s", self.email_address)
        self._connection = imaplib.IMAP4_SSL(GMAIL_IMAP_HOST, GMAIL_IMAP_PORT)
        # Google App Passwords are displayed as "xxxx xxxx xxxx xxxx" for
        # readability, but IMAP LOGIN needs the raw 16-char string (no spaces)
        # to avoid splitting it into multiple IMAP tokens.
        password = self.app_password.replace(" ", "")
        self._connection.login(self.email_address, password)
        logger.info("Successfully authenticated")

    def disconnect(self) -> None:
        """Close IMAP connection."""
        if self._connection:
            try:
                self._connection.logout()
            except Exception:
                pass
            self._connection = None
            logger.info("Disconnected from Gmail")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()

    def _decode_header_value(self, raw: str) -> str:
        """Decode MIME-encoded email header into a readable string."""
        decoded_parts = decode_header(raw)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                result.append(part)
        return "".join(result)

    def _gmail_search(self, query: str, mailbox: str = "INBOX") -> list[str]:
        """Use Gmail's native X-GM-RAW search extension.

        Gmail IMAP supports the X-GM-RAW attribute which accepts the same
        query syntax as the Gmail web search bar, including full UTF-8.
        This avoids the ASCII-only limitation of standard IMAP SEARCH.

        Args:
            query: Gmail search query string (supports UTF-8, same as web UI).
            mailbox: IMAP mailbox to search (default: INBOX).

        Returns:
            List of email message IDs matching the query.
        """
        if not self._connection:
            raise RuntimeError("Not connected. Call connect() first.")

        self._connection.select(mailbox, readonly=True)

        logger.info("Gmail X-GM-RAW search: %s", query)

        # Non-ASCII queries (Thai, CJK, etc.) must be sent as an IMAP
        # literal with CHARSET UTF-8 so Gmail can interpret the encoding.
        # The client sends  SEARCH CHARSET UTF-8 X-GM-RAW {N}\r\n,
        # the server replies "+", then the raw UTF-8 bytes are sent.
        self._connection.literal = query.encode("utf-8")
        status, data = self._connection.search("UTF-8", "X-GM-RAW")

        if status != "OK":
            logger.warning("Gmail search failed: %s", status)
            return []

        message_ids = data[0].split() if data[0] else []
        logger.info("Found %d emails matching criteria", len(message_ids))
        return [mid.decode() for mid in message_ids]

    def search_emails(
        self,
        subject_contains: str,
        year: int,
        mailbox: str = "INBOX",
    ) -> list[str]:
        """Search for emails matching subject criteria within a year.

        Uses Gmail's X-GM-RAW extension for full UTF-8 subject search,
        which is essential for non-ASCII merchant names (Thai, CJK, etc.).

        Args:
            subject_contains: Substring to match in email subject.
            year: Filter emails from this year.
            mailbox: IMAP mailbox to search (default: INBOX).

        Returns:
            List of email message IDs matching the criteria.
        """
        # Build Gmail-style search query with date range + subject filter.
        # Avoid inner double-quotes around the subject phrase — use
        # subject:() grouping instead, since the whole query is already
        # wrapped in IMAP double-quotes by _gmail_search().
        query = (
            f"subject:({subject_contains}) "
            f"after:{year}/01/01 before:{year + 1}/01/01"
        )

        return self._gmail_search(query, mailbox)

    def fetch_attachments(
        self,
        message_ids: list[str],
        download_dir: Optional[Path] = None,
        filename_filter: Optional[str] = None,
    ) -> list[EmailAttachment]:
        """Download attachments from the specified email messages.

        Args:
            message_ids: List of email message IDs to process.
            download_dir: Directory to save attachments. Uses temp dir if None.
            filename_filter: Only download files whose name contains this string.

        Returns:
            List of EmailAttachment objects for each downloaded file.
        """
        if not self._connection:
            raise RuntimeError("Not connected. Call connect() first.")

        if download_dir is None:
            download_dir = Path(tempfile.mkdtemp(prefix="merchant_stmt_"))
        download_dir.mkdir(parents=True, exist_ok=True)

        attachments: list[EmailAttachment] = []

        for msg_id in message_ids:
            status, msg_data = self._connection.fetch(msg_id, "(RFC822)")
            if status != "OK":
                logger.warning("Failed to fetch message %s", msg_id)
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = self._decode_header_value(msg.get("Subject", ""))
            email_date = msg.get("Date", "")

            logger.debug("Processing email: %s", subject)

            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" not in content_disposition:
                    continue

                raw_filename = part.get_filename()
                if not raw_filename:
                    continue

                filename = self._decode_header_value(raw_filename)

                if filename_filter and filename_filter not in filename:
                    logger.debug("Skipping attachment: %s (filter mismatch)", filename)
                    continue

                # Save the attachment — skip if already downloaded
                # (platforms like Grab send duplicate emails with the
                # same report attached, so same filename = same report)
                filepath = download_dir / filename
                if filepath.exists():
                    logger.debug("Skipping duplicate attachment: %s", filename)
                    continue

                payload = part.get_payload(decode=True)
                if payload:
                    filepath.write_bytes(payload)
                    logger.info("Downloaded: %s (%d bytes)", filename, len(payload))

                    attachments.append(
                        EmailAttachment(
                            filename=filename,
                            filepath=filepath,
                            content_type=part.get_content_type(),
                            email_subject=subject,
                            email_date=email_date,
                        )
                    )

        return attachments
