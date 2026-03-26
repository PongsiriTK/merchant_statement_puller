"""Parser registry — maps platform names to their parser implementations."""

from __future__ import annotations

from .base import BaseParser
from .grab import GrabParser
from .robinhood import RobinhoodParser
from .shopee import ShopeeParser


class ParserRegistry:
    """Central registry for all platform parsers.

    Usage:
        parser = ParserRegistry.get("shopee")
        parser = ParserRegistry.get("robinhood")
    """

    _parsers: dict[str, BaseParser] = {
        "shopee": ShopeeParser(),
        "robinhood": RobinhoodParser(),
        "grab": GrabParser(),
    }

    @classmethod
    def get(cls, platform: str) -> BaseParser:
        """Get a parser by platform name (case-insensitive)."""
        key = platform.lower().strip()
        if key not in cls._parsers:
            available = ", ".join(sorted(cls._parsers.keys()))
            raise ValueError(
                f"Unknown platform: {platform!r}. Available: {available}"
            )
        return cls._parsers[key]

    @classmethod
    def list_platforms(cls) -> list[str]:
        """Return all registered platform names."""
        return sorted(cls._parsers.keys())

    @classmethod
    def register(cls, name: str, parser: BaseParser) -> None:
        """Register a new platform parser."""
        cls._parsers[name.lower().strip()] = parser
