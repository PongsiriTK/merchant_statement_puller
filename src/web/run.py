"""Entry point to launch the Streamlit web UI."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    app_path = Path(__file__).resolve().parent / "app.py"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.headless=false"],
        check=False,
    )


if __name__ == "__main__":
    main()
