#!/usr/bin/env python3
"""
ระบบดึงรายงานร้านค้า — Merchant Statement Puller v1.0.0

Pull and aggregate daily sales reports from food delivery platform emails
for annual tax filing. Supports Thai and English interface.

Usage:
    python main.py pull shopee -m merchant.md -y 2026
    python main.py pull grab -m merchant.md --lang en
    python main.py platforms
    python main.py --version
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.cli.app import main

if __name__ == "__main__":
    main()
