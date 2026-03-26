"""Base parser interface for delivery platform statement files."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.core.models import DailyReport


class BaseParser(ABC):
    """Abstract base class for platform-specific statement parsers.

    Each delivery platform (Shopee, Grab, Robinhood, etc.) sends statements
    in different formats. Subclasses implement the parsing logic for each.
    """

    platform_name: str = "unknown"

    # --- Email matching ---

    @abstractmethod
    def build_search_subject(self, merchant_name: str) -> str:
        """Return the IMAP SUBJECT search string for this platform's emails."""
        ...

    @abstractmethod
    def attachment_filename_filter(self, merchant_name: str) -> str:
        """Return a substring to filter relevant attachments by filename."""
        ...

    # --- File parsing ---

    @property
    def requires_file_password(self) -> bool:
        """Whether this parser needs a file decryption password."""
        return False

    @abstractmethod
    def parse_file(
        self,
        filepath: Path,
        email_subject: str = "",
        email_date: str = "",
        password: str = "",
    ) -> DailyReport:
        """Parse a single downloaded attachment into a DailyReport.

        Args:
            filepath: Path to the downloaded attachment.
            email_subject: Original email subject line.
            email_date: Original email Date header.
            password: File decryption password (for encrypted files).
        """
        ...
