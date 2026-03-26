"""Merchant configuration loader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class MerchantConfig:
    """Configuration for a merchant pulled from a .md config file."""

    name: str
    app_password: str
    email: str
    config_path: str
    file_passwords: dict = None  # platform → file decryption password

    def __post_init__(self):
        if self.file_passwords is None:
            self.file_passwords = {}

    def get_file_password(self, platform: str) -> str:
        """Get the file decryption password for a specific platform.

        Returns empty string if no password is configured.
        """
        return self.file_passwords.get(platform.lower(), "")

    def __repr__(self) -> str:
        masked = self.app_password[:4] + " **** **** ****"
        return f"MerchantConfig(name={self.name!r}, email={self.email!r}, app_password={masked!r})"


def load_merchant_config(
    config_path: str, email: Optional[str] = None
) -> MerchantConfig:
    """Load merchant config from a markdown file.

    Expected format:
        Google App Password = xxxx xxxx xxxx xxxx
        TH Name = "ร้านค้า"
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Merchant config not found: {config_path}")

    text = path.read_text(encoding="utf-8").strip()
    config: dict[str, str] = {}

    for line in text.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        config[key] = value

    app_password = config.get("Google App Password", "")
    th_name = config.get("TH Name", "")
    merchant_email = config.get("Email", "")

    if not app_password:
        raise ValueError(f"Missing 'Google App Password' in {config_path}")
    if not th_name:
        raise ValueError(f"Missing 'TH Name' in {config_path}")

    # Collect per-platform file passwords (e.g. "Robinhood File Password = 123456")
    file_passwords: dict[str, str] = {}
    for key, value in config.items():
        if key.endswith("File Password"):
            platform = key.replace("File Password", "").strip().lower()
            file_passwords[platform] = value

    return MerchantConfig(
        name=th_name,
        app_password=app_password,
        email=email or merchant_email,
        config_path=str(path.resolve()),
        file_passwords=file_passwords,
    )
