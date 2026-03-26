"""Data models for merchant statement puller."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class OrderRecord:
    """Single order row from a daily sales report."""

    order_id: str
    order_date: date
    order_amount: Decimal
    total: Decimal
    net_income: Decimal
    commission: Decimal
    vat_on_commission: Decimal
    status: str
    store_name: str = ""

    @property
    def is_settled(self) -> bool:
        return self.status.lower() == "settled"


@dataclass
class DailyReport:
    """One daily sales report file (one email attachment)."""

    report_date: date
    filename: str
    orders: list[OrderRecord] = field(default_factory=list)
    email_subject: str = ""
    email_date: Optional[str] = None

    @property
    def total_sales(self) -> Decimal:
        return sum((o.total for o in self.orders), Decimal("0"))

    @property
    def total_net_income(self) -> Decimal:
        return sum((o.net_income for o in self.orders), Decimal("0"))

    @property
    def total_commission(self) -> Decimal:
        return sum((o.commission for o in self.orders), Decimal("0"))

    @property
    def total_vat(self) -> Decimal:
        return sum((o.vat_on_commission for o in self.orders), Decimal("0"))

    @property
    def order_count(self) -> int:
        return len(self.orders)


@dataclass
class PlatformReport:
    """Aggregated report for a single platform over a date range."""

    platform: str
    merchant_name: str
    year: int
    daily_reports: list[DailyReport] = field(default_factory=list)

    @property
    def grand_total(self) -> Decimal:
        return sum((r.total_sales for r in self.daily_reports), Decimal("0"))

    @property
    def grand_net_income(self) -> Decimal:
        return sum((r.total_net_income for r in self.daily_reports), Decimal("0"))

    @property
    def grand_commission(self) -> Decimal:
        return sum((r.total_commission for r in self.daily_reports), Decimal("0"))

    @property
    def grand_vat(self) -> Decimal:
        return sum((r.total_vat for r in self.daily_reports), Decimal("0"))

    @property
    def total_orders(self) -> int:
        return sum(r.order_count for r in self.daily_reports)

    @property
    def total_days(self) -> int:
        return len(self.daily_reports)
