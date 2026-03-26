"""GrabFood daily business report parser (PDF).

Grab sends daily business reports (รายงานธุรกิจรายวัน) as PDF email
attachments — one per day.

Focus field: ยอดรายการ (item subtotal before VAT / promotions / commission)
             under the รายรับทั้งหมด (total revenue) section.

Summary table columns (under รายรับทั้งหมด):
    ยอดรายการ | VAT | ค่าบริการของร้าน | โปรโมชันร้าน |
    ค่าคอมมิชชันและภาษีทั้งหมด | ส่วนลดค่าจัดส่งโดยร้าน |
    รายรับทั้งหมด | ค้างชำระ Grab

Order table columns (under คำสั่งซื้อจากแอปฯ):
    เวลาที่จัดส่ง | รหัสคำสั่งซื้อ | (same financial columns) | รายรับทั้งหมด

Email subject pattern:
    "สรุปยอดขายสำหรับคำสั่งซื้อ ... GrabFood"

Attachment filename pattern:
    "3-CZCUE73FEZMUCT-20260321.pdf"
"""

from __future__ import annotations

import logging
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pdfplumber

from src.core.models import DailyReport, OrderRecord
from .base import BaseParser

logger = logging.getLogger(__name__)

THAI_MONTHS = {
    "มกราคม": 1, "กุมภาพันธ": 2, "มีนาคม": 3, "เมษายน": 4,
    "พฤษภาคม": 5, "มิถุนายน": 6, "กรกฎาคม": 7, "สิงหาคม": 8,
    "กันยายน": 9, "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12,
}

# Grab PDFs use Unicode Private Use Area chars in place of Thai diacritics
_PUA_RE = re.compile(r"[\uf700-\uf7ff]")


def _clean(text) -> str:
    """Strip PUA chars and whitespace from a cell value."""
    if text is None:
        return ""
    return _PUA_RE.sub("", str(text)).strip()


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    try:
        text = _clean(value).replace(",", "").replace("THB", "").strip()
        if not text or text == "-":
            return Decimal("0")
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _cell(row: list, col_map: dict[str, int], key: str) -> Decimal:
    """Safely extract a Decimal from a row using a column map."""
    idx = col_map.get(key)
    if idx is None or idx >= len(row):
        return Decimal("0")
    return _to_decimal(row[idx])


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def _parse_thai_date(text: str) -> date | None:
    """Parse a Thai date like '21 มีนาคม 2026'."""
    cleaned = _clean(text)
    for month_name, month_num in THAI_MONTHS.items():
        match = re.search(rf"(\d{{1,2}})\s*{month_name}\S*\s*(\d{{4}})", cleaned)
        if match:
            try:
                return date(int(match.group(2)), month_num, int(match.group(1)))
            except ValueError:
                continue
    return None


def _parse_date_from_filename(filename: str) -> date | None:
    """Parse YYYYMMDD from filename like '3-CZCUE73FEZMUCT-20260321.pdf'."""
    match = re.search(r"(\d{4})(\d{2})(\d{2})", filename)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            pass
    return None


# ---------------------------------------------------------------------------
# Table parsing helpers
# ---------------------------------------------------------------------------

def _build_col_map(header_row: list) -> dict[str, int]:
    """Map known column names to their indices in a header row."""
    col_map: dict[str, int] = {}
    for idx, raw_cell in enumerate(header_row):
        c = _clean(raw_cell)
        if not c:
            continue
        if c == "ยอดรายการ":
            col_map["item_amount"] = idx
        elif c == "VAT":
            col_map["vat"] = idx
        elif "คอมมิชชัน" in c:
            col_map["commission"] = idx
        elif "รายรับ" in c and "หมด" in c:
            col_map["total_revenue"] = idx
        elif "รหัส" in c:
            col_map["order_id"] = idx
    return col_map


class GrabParser(BaseParser):
    """Parser for GrabFood daily business report PDFs."""

    platform_name = "GrabFood"

    def build_search_subject(self, merchant_name: str) -> str:
        return "สรุปยอดขาย GrabFood"

    def attachment_filename_filter(self, merchant_name: str) -> str:
        return ".pdf"

    def parse_file(
        self,
        filepath: Path,
        email_subject: str = "",
        email_date: str = "",
        password: str = "",
    ) -> DailyReport:
        """Parse a GrabFood daily business report PDF.

        Focus: ยอดรายการ under รายรับทั้งหมด.
        """
        logger.info("Parsing GrabFood report: %s", filepath.name)

        text = ""
        all_rows: list[list] = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
                for table in (page.extract_tables() or []):
                    all_rows.extend(table)

        # --- Report date ---
        report_date = (
            _parse_thai_date(text)
            or _parse_thai_date(email_subject)
            or _parse_date_from_filename(filepath.name)
        )
        if report_date is None:
            logger.warning("Could not extract date from %s", filepath.name)
            report_date = date.today()

        # --- Walk rows: find header rows containing "ยอดรายการ" ---
        summary: dict | None = None
        orders: list[OrderRecord] = []

        i = 0
        while i < len(all_rows):
            cleaned_cells = [_clean(c) for c in all_rows[i]]

            if "ยอดรายการ" not in cleaned_cells:
                i += 1
                continue

            col_map = _build_col_map(all_rows[i])
            is_order_table = "order_id" in col_map
            i += 1  # move past header

            # Read data rows until a non-data row
            while i < len(all_rows):
                row = all_rows[i]
                first = _clean(row[0]) if row else ""

                # Stop if first cell is not numeric/time/empty (i.e. new section)
                if first and not re.match(r"[\d.,:+\-\s]+$", first):
                    break

                if is_order_table:
                    order = _parse_order_row(row, col_map, report_date)
                    if order:
                        orders.append(order)
                elif summary is None:
                    summary = {
                        "item_amount": _cell(row, col_map, "item_amount"),
                        "vat": _cell(row, col_map, "vat"),
                        "commission": _cell(row, col_map, "commission"),
                        "total_revenue": _cell(row, col_map, "total_revenue"),
                    }

                i += 1
            # don't increment i again — outer loop re-checks current row

        # --- Build report ---
        if not orders and summary:
            orders = [
                OrderRecord(
                    order_id=f"grab-{report_date.isoformat()}",
                    order_date=report_date,
                    order_amount=summary["item_amount"],
                    total=summary["item_amount"],
                    commission=summary["commission"],
                    vat_on_commission=summary["vat"],
                    net_income=summary["total_revenue"],
                    status="settled",
                )
            ]

        report = DailyReport(
            report_date=report_date,
            filename=filepath.name,
            orders=orders,
            email_subject=email_subject,
            email_date=email_date,
        )

        logger.info(
            "Parsed %d order(s), ยอดรายการ=%.2f, รายรับทั้งหมด=%.2f",
            report.order_count,
            report.total_sales,
            report.total_net_income,
        )

        return report


def _parse_order_row(
    row: list, col_map: dict[str, int], report_date: date
) -> OrderRecord | None:
    """Parse one order row. Returns None if the row has no order ID."""
    order_id = _clean(row[col_map["order_id"]]) if "order_id" in col_map else ""
    if not order_id:
        return None

    item_amount = _cell(row, col_map, "item_amount")
    return OrderRecord(
        order_id=order_id,
        order_date=report_date,
        order_amount=item_amount,
        total=item_amount,
        commission=_cell(row, col_map, "commission"),
        vat_on_commission=_cell(row, col_map, "vat"),
        net_income=_cell(row, col_map, "total_revenue"),
        status="settled",
    )
