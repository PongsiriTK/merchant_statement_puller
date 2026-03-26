"""CLI application for Merchant Statement Puller."""

from __future__ import annotations

import csv
import logging
import time
from datetime import date
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console, Group
from rich.live import Live
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from src.__version__ import __version__, __app_name__, __app_name_th__
from src.cli.i18n import Locale, get_locale
from src.core.gmail_client import GmailClient
from src.core.merchant_config import load_merchant_config
from src.core.models import PlatformReport
from src.parsers.registry import ParserRegistry

console = Console()

PLATFORM_FORMATS = {
    "shopee": "Excel (.xlsx)",
    "grab": "PDF",
    "robinhood": "Excel (.xlsx)",
}

app = typer.Typer(
    name="merchant-puller",
    help="\u0e23\u0e30\u0e1a\u0e1a\u0e14\u0e36\u0e07\u0e23\u0e32\u0e22\u0e07\u0e32\u0e19\u0e23\u0e49\u0e32\u0e19\u0e04\u0e49\u0e32 \u2014 Merchant Statement Puller",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# Step Progress Log — terminal-like live display
# ---------------------------------------------------------------------------

class StepLog:
    """A live-updating step progress panel that looks like a terminal log."""

    _SPINNER = "\u280b\u2819\u2839\u2838\u283c\u2834\u2826\u2827\u2807\u280f"

    def __init__(self, title: str):
        self.title = title
        self._steps: list[tuple[str, str, str, float]] = []
        self._step_start: float = 0.0
        self._total_start: float = time.time()
        self._finished = False
        self._finish_label = ""

    def start(self, label: str) -> None:
        self._steps.append(("running", label, "", 0.0))
        self._step_start = time.time()

    def complete(self, detail: str = "") -> None:
        if not self._steps:
            return
        elapsed = time.time() - self._step_start
        _, label, _, _ = self._steps[-1]
        self._steps[-1] = ("done", label, detail, elapsed)

    def warn(self, detail: str = "") -> None:
        if not self._steps:
            return
        elapsed = time.time() - self._step_start
        _, label, _, _ = self._steps[-1]
        self._steps[-1] = ("warn", label, detail, elapsed)

    def fail(self, detail: str = "") -> None:
        if not self._steps:
            return
        elapsed = time.time() - self._step_start
        _, label, _, _ = self._steps[-1]
        self._steps[-1] = ("error", label, detail, elapsed)

    def finish(self, label: str) -> None:
        self._finished = True
        self._finish_label = label

    def _icon(self, status: str) -> tuple[str, str]:
        if status == "done":
            return ("\u2714", "green bold")
        if status == "error":
            return ("\u2718", "red bold")
        if status == "warn":
            return ("\u26a0", "yellow bold")
        frame = self._SPINNER[int(time.time() * 10) % len(self._SPINNER)]
        return (frame, "cyan bold")

    def __rich__(self) -> Panel:
        grid = Table.grid(padding=(0, 1))
        grid.add_column(width=3)
        grid.add_column(min_width=34)
        grid.add_column(min_width=20)
        grid.add_column(justify="right", width=8)

        for status, label, detail, elapsed in self._steps:
            icon_char, icon_style = self._icon(status)

            if status == "running":
                elapsed = time.time() - self._step_start
                label_style = "white"
                detail_style = "dim"
            elif status == "error":
                label_style = "red"
                detail_style = "red dim"
            elif status == "warn":
                label_style = "yellow"
                detail_style = "yellow"
            else:
                label_style = "white"
                detail_style = "cyan"

            grid.add_row(
                Text(icon_char, style=icon_style),
                Text(label, style=label_style),
                Text(f"\u2192 {detail}" if detail else "", style=detail_style),
                Text(f"{elapsed:.1f}s", style="dim"),
            )

        if self._finished:
            total = time.time() - self._total_start
            grid.add_row(Text(""), Text(""), Text(""), Text(""))
            grid.add_row(
                Text("\u2714", style="green bold"),
                Text(self._finish_label, style="green bold"),
                Text(""),
                Text(f"{total:.1f}s", style="green"),
            )

        return Panel(
            grid,
            title=f"[bold cyan]{self.title}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, show_time=False, show_path=False)],
    )


def _print_banner(lang: str = "th") -> None:
    t = get_locale(lang)

    logo = Text.from_markup(
        "[bold cyan]"
        "  __  __               _                 _     ____        _ _           \n"
        " |  \\/  | ___ _ __ ___| |__   __ _ _ __ | |_  |  _ \\ _   _| | | ___ _ __ \n"
        " | |\\/| |/ _ \\ '__/ __| '_ \\ / _` | '_ \\| __| | |_) | | | | | |/ _ \\ '__|\n"
        " | |  | |  __/ | | (__| | | | (_| | | | | |_  |  __/| |_| | | |  __/ |   \n"
        " |_|  |_|\\___|_|  \\___|_| |_|\\__,_|_| |_|\\__| |_|    \\__,_|_|_|\\___|_|   \n"
        "[/bold cyan]"
    )

    title_line = Text()
    title_line.append(f"  {t.app_title}", style="bold white")
    title_line.append(f"  v{__version__}", style="dim cyan")

    subtitle = Text(f"  {t.app_subtitle}", style="dim")

    content = Text()
    content.append_text(logo)
    content.append("\n")
    content.append_text(title_line)
    content.append("\n")
    content.append_text(subtitle)

    console.print(Panel(
        content,
        border_style="cyan",
        padding=(0, 1),
        subtitle="[dim]github.com/PongsiriTK/merchant-statement-puller[/dim]",
    ))
    console.print()


def _print_config_info(merchant_name: str, email: str, platform: str, year: int, t: Locale) -> None:
    info = Table.grid(padding=(0, 2))
    info.add_column(style="cyan", justify="right", min_width=14)
    info.add_column(style="white")

    info.add_row(f"  {t.status_merchant}", merchant_name)
    info.add_row(f"  {t.status_email}", email)
    info.add_row(f"  {t.status_platform}", platform)
    info.add_row(f"  {t.status_year}", str(year))

    console.print(Panel(info, border_style="dim", padding=(0, 1), title="[dim]Config[/dim]"))
    console.print()


def _print_summary_table(report: PlatformReport, t: Locale) -> None:
    table = Table(
        title=t.tbl_daily_title.format(platform=report.platform, year=report.year),
        box=box.HEAVY_HEAD,
        show_lines=False,
        title_style="bold white",
        header_style="bold cyan",
        row_styles=["", "dim"],
        padding=(0, 1),
    )
    table.add_column(t.tbl_col_num, justify="right", style="dim", width=5)
    table.add_column(t.tbl_col_date, justify="center", width=12)
    table.add_column(t.tbl_col_file, max_width=44, no_wrap=True, overflow="ellipsis")
    table.add_column(t.tbl_col_orders, justify="right", width=10)
    table.add_column(t.tbl_col_total, justify="right", style="green", width=16)
    table.add_column(t.tbl_col_commission, justify="right", style="yellow", width=16)
    table.add_column(t.tbl_col_vat, justify="right", style="yellow", width=14)
    table.add_column(t.tbl_col_net, justify="right", style="bold green", width=16)

    for idx, daily in enumerate(
        sorted(report.daily_reports, key=lambda d: d.report_date), start=1
    ):
        table.add_row(
            str(idx),
            daily.report_date.strftime("%Y-%m-%d"),
            daily.filename[:44],
            str(daily.order_count),
            f"{daily.total_sales:,.2f}",
            f"{daily.total_commission:,.2f}",
            f"{daily.total_vat:,.2f}",
            f"{daily.total_net_income:,.2f}",
        )

    table.add_section()
    table.add_row(
        "",
        f"[bold]{t.tbl_col_total_row}[/bold]",
        f"[dim]{t.tbl_col_reports.format(count=report.total_days)}[/dim]",
        f"[bold]{report.total_orders}[/bold]",
        f"[bold green]{report.grand_total:,.2f}[/bold green]",
        f"[bold yellow]{report.grand_commission:,.2f}[/bold yellow]",
        f"[bold yellow]{report.grand_vat:,.2f}[/bold yellow]",
        f"[bold green]{report.grand_net_income:,.2f}[/bold green]",
    )

    console.print(table)
    console.print()

    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="white", min_width=20)
    summary.add_column(style="white", justify="right", min_width=20)

    summary.add_row(t.sum_platform, report.platform)
    summary.add_row(t.sum_merchant, report.merchant_name)
    summary.add_row(t.sum_year, str(report.year))
    summary.add_row(t.sum_reports, str(report.total_days))
    summary.add_row(t.sum_orders, str(report.total_orders))
    summary.add_row("[dim]\u2500" * 40 + "[/dim]", "")
    summary.add_row(
        f"[green]{t.sum_gross}[/green]",
        f"[green]\u0e3f{report.grand_total:>14,.2f}[/green]",
    )
    summary.add_row(
        f"[yellow]{t.sum_commission}[/yellow]",
        f"[yellow]\u0e3f{report.grand_commission:>14,.2f}[/yellow]",
    )
    summary.add_row(
        f"[yellow]{t.sum_vat}[/yellow]",
        f"[yellow]\u0e3f{report.grand_vat:>14,.2f}[/yellow]",
    )
    summary.add_row(
        f"[bold green]{t.sum_net}[/bold green]",
        f"[bold green]\u0e3f{report.grand_net_income:>14,.2f}[/bold green]",
    )

    console.print(Panel(
        summary,
        title=f"[bold white]{t.sum_title}[/bold white]",
        border_style="green",
        padding=(1, 3),
    ))


def _export_csv(report: PlatformReport, csv_path: Path) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Date", "File", "Orders", "Total", "Commission", "VAT", "Net Income",
        ])
        for daily in sorted(report.daily_reports, key=lambda d: d.report_date):
            writer.writerow([
                daily.report_date.isoformat(),
                daily.filename,
                daily.order_count,
                f"{daily.total_sales:.2f}",
                f"{daily.total_commission:.2f}",
                f"{daily.total_vat:.2f}",
                f"{daily.total_net_income:.2f}",
            ])
        writer.writerow([
            "TOTAL", "", report.total_orders,
            f"{report.grand_total:.2f}",
            f"{report.grand_commission:.2f}",
            f"{report.grand_vat:.2f}",
            f"{report.grand_net_income:.2f}",
        ])


def _version_callback(value: bool) -> None:
    if value:
        console.print(
            f"[bold cyan]{__app_name_th__}[/bold cyan] "
            f"[dim]({__app_name__})[/dim] "
            f"v{__version__}"
        )
        raise typer.Exit()


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-V",
        help="\u0e41\u0e2a\u0e14\u0e07\u0e40\u0e27\u0e2d\u0e23\u0e4c\u0e0a\u0e31\u0e19 / Show version",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """\u0e23\u0e30\u0e1a\u0e1a\u0e14\u0e36\u0e07\u0e23\u0e32\u0e22\u0e07\u0e32\u0e19\u0e23\u0e49\u0e32\u0e19\u0e04\u0e49\u0e32 \u2014 Merchant Statement Puller"""


@app.command()
def pull(
    platform: str = typer.Argument(
        help="\u0e41\u0e1e\u0e25\u0e15\u0e1f\u0e2d\u0e23\u0e4c\u0e21 \u0e40\u0e0a\u0e48\u0e19 shopee, grab, robinhood",
    ),
    merchant_config: str = typer.Option(
        ..., "--merchant", "-m",
        help="\u0e44\u0e1f\u0e25\u0e4c\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32\u0e23\u0e49\u0e32\u0e19\u0e04\u0e49\u0e32 (.md)",
    ),
    email_address: Optional[str] = typer.Option(
        None, "--email", "-e",
        help="\u0e2d\u0e35\u0e40\u0e21\u0e25 Gmail \u0e2a\u0e33\u0e2b\u0e23\u0e31\u0e1a\u0e40\u0e0a\u0e37\u0e48\u0e2d\u0e21\u0e15\u0e48\u0e2d",
    ),
    year: int = typer.Option(
        date.today().year, "--year", "-y",
        help="\u0e1b\u0e35\u0e20\u0e32\u0e29\u0e35 / Tax year",
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="\u0e42\u0e1f\u0e25\u0e40\u0e14\u0e2d\u0e23\u0e4c\u0e2a\u0e33\u0e2b\u0e23\u0e31\u0e1a\u0e1a\u0e31\u0e19\u0e17\u0e36\u0e01\u0e44\u0e1f\u0e25\u0e4c\u0e41\u0e19\u0e1a",
    ),
    export_csv: Optional[str] = typer.Option(
        None, "--csv",
        help="\u0e2a\u0e48\u0e07\u0e2d\u0e2d\u0e01 CSV / Export CSV path",
    ),
    lang: str = typer.Option(
        "th", "--lang", "-l",
        help="\u0e20\u0e32\u0e29\u0e32 th/en",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="\u0e41\u0e2a\u0e14\u0e07\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e14\u0e35\u0e1a\u0e31\u0e01",
    ),
) -> None:
    """\u0e14\u0e36\u0e07\u0e41\u0e25\u0e30\u0e23\u0e27\u0e21\u0e23\u0e32\u0e22\u0e07\u0e32\u0e19\u0e22\u0e2d\u0e14\u0e02\u0e32\u0e22\u0e23\u0e32\u0e22\u0e27\u0e31\u0e19\u0e08\u0e32\u0e01\u0e2d\u0e35\u0e40\u0e21\u0e25\u0e41\u0e1e\u0e25\u0e15\u0e1f\u0e2d\u0e23\u0e4c\u0e21\u0e2a\u0e48\u0e07\u0e2d\u0e32\u0e2b\u0e32\u0e23"""
    _setup_logging(verbose)
    t = get_locale(lang)
    _print_banner(lang)

    # ── Build the step log ──────────────────────────────────────────────
    steps = StepLog(title=t.step_title)

    with Live(steps, console=console, refresh_per_second=12) as live:

        # Step 1: Load config
        steps.start(t.step_load_config)
        try:
            merchant = load_merchant_config(merchant_config, email=email_address)
        except (FileNotFoundError, ValueError) as exc:
            steps.fail(str(exc))
            live.stop()
            console.print(f"\n[red bold] {t.err_config}[/red bold] {exc}")
            raise typer.Exit(1)

        if not merchant.email:
            steps.fail(t.err_no_email)
            live.stop()
            console.print(f"\n[red bold] {t.err_no_email}[/red bold]")
            console.print(f"  [dim]{t.err_no_email_hint}[/dim]")
            raise typer.Exit(1)

        steps.complete(merchant.name)

        # Step 2: Resolve parser
        steps.start(t.step_resolve_parser.format(platform=platform))
        try:
            parser = ParserRegistry.get(platform)
        except ValueError as exc:
            steps.fail(str(exc))
            live.stop()
            console.print(f"\n[red bold] {t.err_parser}[/red bold] {exc}")
            raise typer.Exit(1)

        search_subject = parser.build_search_subject(merchant.name)
        filename_filter = parser.attachment_filename_filter(merchant.name)
        download_path = Path(output_dir) if output_dir else None
        steps.complete(parser.platform_name)

        # Step 2b: File password (if needed)
        file_password = ""
        if parser.requires_file_password:
            steps.start(t.step_password_check)
            file_password = merchant.get_file_password(platform)
            if not file_password:
                steps.fail(t.err_need_password.format(platform=parser.platform_name))
                live.stop()
                console.print(
                    f"\n[red bold] {t.err_need_password.format(platform=parser.platform_name)}[/red bold]"
                )
                console.print(
                    f"  [dim]{t.err_need_password_hint.format(platform=platform.title(), config=merchant_config)}[/dim]"
                )
                raise typer.Exit(1)
            steps.complete()

        # Step 3: Connect to Gmail
        steps.start(t.step_connect)
        try:
            client = GmailClient(
                email_address=merchant.email,
                app_password=merchant.app_password,
            )
            client.connect()
        except Exception as exc:
            steps.fail(str(exc))
            live.stop()
            console.print(f"\n[red bold] {t.err_gmail_fail}[/red bold] {exc}")
            raise typer.Exit(1)
        steps.complete(merchant.email)

        # Step 4: Search emails
        steps.start(t.step_search.format(year=year))
        try:
            message_ids = client.search_emails(
                subject_contains=search_subject, year=year,
            )
        except Exception as exc:
            client.disconnect()
            steps.fail(str(exc))
            live.stop()
            console.print(f"\n[red bold] {t.err_search_fail}[/red bold] {exc}")
            raise typer.Exit(1)

        if not message_ids:
            client.disconnect()
            steps.warn(t.err_no_emails.format(query=search_subject, year=year))
            steps.finish(t.step_complete)
            live.update(steps)
            time.sleep(0.3)
            live.stop()
            console.print(
                f"\n[yellow] {t.err_no_emails.format(query=search_subject, year=year)}[/yellow]"
            )
            raise typer.Exit(0)

        steps.complete(t.step_found.format(count=len(message_ids)))

        # Step 5: Download attachments
        steps.start(t.step_download)
        try:
            attachments = client.fetch_attachments(
                message_ids=message_ids,
                download_dir=download_path,
                filename_filter=filename_filter,
            )
        except Exception as exc:
            client.disconnect()
            steps.fail(str(exc))
            live.stop()
            console.print(f"\n[red bold] {t.err_download_fail}[/red bold] {exc}")
            raise typer.Exit(1)

        client.disconnect()

        if not attachments:
            steps.warn(t.err_no_attachments)
            steps.finish(t.step_complete)
            live.update(steps)
            time.sleep(0.3)
            live.stop()
            console.print(f"\n[yellow] {t.err_no_attachments}[/yellow]")
            raise typer.Exit(0)

        steps.complete(t.step_files.format(count=len(attachments)))

        # Step 6: Parse reports
        steps.start(t.step_parse)
        report = PlatformReport(
            platform=parser.platform_name,
            merchant_name=merchant.name,
            year=year,
        )

        parse_errors = 0
        for att in attachments:
            try:
                daily = parser.parse_file(
                    filepath=att.filepath,
                    email_subject=att.email_subject,
                    email_date=att.email_date,
                    password=file_password,
                )
                report.daily_reports.append(daily)
            except Exception as exc:
                parse_errors += 1
                logging.getLogger(__name__).warning(
                    "Failed to parse %s: %s", att.filename, exc
                )

        detail_parts = [t.step_reports.format(count=len(report.daily_reports))]
        if parse_errors:
            detail_parts.append(f"({t.status_errors.format(count=parse_errors)})")
        steps.complete(" ".join(detail_parts))

        # Finish
        steps.finish(t.step_complete)
        live.update(steps)
        time.sleep(0.4)  # brief pause so user sees completed state

    # ── Results ─────────────────────────────────────────────────────────
    console.print()

    if report.daily_reports:
        _print_config_info(merchant.name, merchant.email, platform, year, t)
        _print_summary_table(report, t)

        if export_csv:
            csv_path = Path(export_csv)
            _export_csv(report, csv_path)
            console.print()
            console.print(
                f"[green bold]\u2714[/green bold] {t.status_exported_csv.format(path=csv_path)}"
            )
    else:
        console.print(f"[yellow]{t.no_data}[/yellow]")

    console.print()


@app.command()
def platforms(
    lang: str = typer.Option(
        "th", "--lang", "-l",
        help="\u0e20\u0e32\u0e29\u0e32 th/en",
    ),
) -> None:
    """\u0e41\u0e2a\u0e14\u0e07\u0e23\u0e32\u0e22\u0e0a\u0e37\u0e48\u0e2d\u0e41\u0e1e\u0e25\u0e15\u0e1f\u0e2d\u0e23\u0e4c\u0e21\u0e17\u0e35\u0e48\u0e23\u0e2d\u0e07\u0e23\u0e31\u0e1a"""
    t = get_locale(lang)
    _print_banner(lang)

    table = Table(
        title=t.plat_title,
        box=box.HEAVY_HEAD,
        header_style="bold cyan",
        padding=(0, 2),
    )
    table.add_column(t.plat_col_num, justify="right", width=5, style="dim")
    table.add_column(t.plat_col_name, width=20)
    table.add_column(t.plat_col_format, width=16, style="dim")
    table.add_column(t.plat_col_status, width=16)

    for idx, name in enumerate(ParserRegistry.list_platforms(), start=1):
        fmt = PLATFORM_FORMATS.get(name, "")
        parser = ParserRegistry.get(name)
        lock = " \U0001f512" if parser.requires_file_password else ""
        table.add_row(
            str(idx),
            f"[bold]{parser.platform_name}[/bold]{lock}",
            fmt,
            f"[green]\u2714 {t.plat_ready}[/green]",
        )

    console.print(table)
    console.print()
    console.print(f"[dim]  \U0001f512 = {t.plat_password_note}[/dim]")
    console.print()


@app.command()
def setup(
    lang: str = typer.Option(
        "th", "--lang", "-l",
        help="\u0e20\u0e32\u0e29\u0e32 th/en",
    ),
) -> None:
    """\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32\u0e23\u0e49\u0e32\u0e19\u0e04\u0e49\u0e32\u0e43\u0e2b\u0e21\u0e48 \u2014 \u0e2a\u0e23\u0e49\u0e32\u0e07\u0e44\u0e1f\u0e25\u0e4c\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32\u0e41\u0e1a\u0e1a\u0e42\u0e15\u0e49\u0e15\u0e2d\u0e1a"""
    from datetime import date as _date
    from rich.prompt import Prompt, Confirm

    t = get_locale(lang)
    _print_banner(lang)

    console.print(Panel(
        f"[white]{t.setup_welcome}[/white]",
        title=f"[bold cyan]{t.setup_title}[/bold cyan]",
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()

    total_steps = 5

    # ── Step 1: Shop info ───────────────────────────────────────────────
    console.print(f"[bold cyan]{t.setup_step.format(step=1, total=total_steps)}:[/bold cyan] [bold]{t.setup_step_info}[/bold]")
    console.print()

    # Shop name
    while True:
        shop_name = Prompt.ask(f"  [cyan]{t.setup_shop_name}[/cyan]\n  [dim]{t.setup_shop_name_hint}[/dim]\n ")
        if shop_name.strip():
            shop_name = shop_name.strip()
            break
        console.print("  [red]  \u0e01\u0e23\u0e38\u0e13\u0e32\u0e43\u0e2a\u0e48\u0e0a\u0e37\u0e48\u0e2d\u0e23\u0e49\u0e32\u0e19\u0e04\u0e49\u0e32[/red]")

    # Email
    while True:
        email = Prompt.ask(f"\n  [cyan]{t.setup_email}[/cyan]\n  [dim]{t.setup_email_hint}[/dim]\n ")
        email = email.strip()
        if "@" in email and "." in email:
            break
        console.print(f"  [red]  {t.setup_invalid_email}[/red]")

    # App Password
    while True:
        app_password = Prompt.ask(f"\n  [cyan]{t.setup_app_password}[/cyan]\n  [dim]{t.setup_app_password_hint}[/dim]\n ")
        clean_pw = app_password.strip().replace(" ", "")
        if len(clean_pw) == 16:
            app_password = app_password.strip()
            break
        console.print(f"  [red]  {t.setup_invalid_password}[/red]")

    console.print()
    console.print(f"  [green]\u2714[/green] {t.setup_shop_name}: [bold]{shop_name}[/bold]")
    console.print(f"  [green]\u2714[/green] {t.setup_email}: [bold]{email}[/bold]")
    console.print(f"  [green]\u2714[/green] {t.setup_app_password}: [bold]{app_password[:4]} **** **** ****[/bold]")
    console.print()

    # ── Step 2: Select platforms ────────────────────────────────────────
    console.print(f"[bold cyan]{t.setup_step.format(step=2, total=total_steps)}:[/bold cyan] [bold]{t.setup_step_platform}[/bold]")
    console.print()

    platform_list = ParserRegistry.list_platforms()
    for idx, name in enumerate(platform_list, start=1):
        parser = ParserRegistry.get(name)
        lock = " \U0001f512" if parser.requires_file_password else ""
        fmt = PLATFORM_FORMATS.get(name, "")
        console.print(f"  [cyan]{idx}.[/cyan] {parser.platform_name}{lock}  [dim]({fmt})[/dim]")

    console.print()
    while True:
        selection = Prompt.ask(
            f"  [cyan]{t.setup_select_platforms}[/cyan]\n  [dim]{t.setup_select_platforms_hint}[/dim]\n ",
            default=",".join(str(i + 1) for i in range(len(platform_list))),
        )
        try:
            indices = [int(x.strip()) for x in selection.split(",") if x.strip()]
            selected_platforms = [platform_list[i - 1] for i in indices if 1 <= i <= len(platform_list)]
            if selected_platforms:
                break
        except (ValueError, IndexError):
            pass
        console.print("  [red]  \u0e01\u0e23\u0e38\u0e13\u0e32\u0e40\u0e25\u0e37\u0e2d\u0e01\u0e2d\u0e22\u0e48\u0e32\u0e07\u0e19\u0e49\u0e2d\u0e22 1 \u0e41\u0e1e\u0e25\u0e15\u0e1f\u0e2d\u0e23\u0e4c\u0e21[/red]")

    console.print()
    for p in selected_platforms:
        parser = ParserRegistry.get(p)
        console.print(f"  [green]\u2714[/green] {parser.platform_name}")
    console.print()

    # ── Step 3: File passwords ──────────────────────────────────────────
    file_passwords: dict[str, str] = {}
    needs_password = [p for p in selected_platforms if ParserRegistry.get(p).requires_file_password]

    if needs_password:
        console.print(f"[bold cyan]{t.setup_step.format(step=3, total=total_steps)}:[/bold cyan] [bold]{t.setup_step_password}[/bold]")
        console.print()
        for p in needs_password:
            parser = ParserRegistry.get(p)
            pw = Prompt.ask(f"  [cyan]{t.setup_file_password.format(platform=parser.platform_name)}[/cyan]\n ")
            if pw.strip():
                file_passwords[p] = pw.strip()
                console.print(f"  [green]\u2714[/green] {parser.platform_name}: [bold]{'*' * len(pw.strip())}[/bold]")
        console.print()
    else:
        console.print(f"[bold cyan]{t.setup_step.format(step=3, total=total_steps)}:[/bold cyan] [bold]{t.setup_step_password}[/bold]  [dim](\u0e02\u0e49\u0e32\u0e21 \u2014 \u0e44\u0e21\u0e48\u0e21\u0e35\u0e41\u0e1e\u0e25\u0e15\u0e1f\u0e2d\u0e23\u0e4c\u0e21\u0e17\u0e35\u0e48\u0e15\u0e49\u0e2d\u0e07\u0e43\u0e0a\u0e49\u0e23\u0e2b\u0e31\u0e2a\u0e1c\u0e48\u0e32\u0e19)[/dim]" if lang == "th" else
                       f"[bold cyan]{t.setup_step.format(step=3, total=total_steps)}:[/bold cyan] [bold]{t.setup_step_password}[/bold]  [dim](skip \u2014 no platforms need a password)[/dim]")
        console.print()

    # ── Step 4: Test connection ─────────────────────────────────────────
    console.print(f"[bold cyan]{t.setup_step.format(step=4, total=total_steps)}:[/bold cyan] [bold]{t.setup_step_test}[/bold]")
    console.print()
    do_test = Confirm.ask(f"  [cyan]{t.setup_test_ask}[/cyan]", default=True)
    console.print()

    if do_test:
        steps = StepLog(title=t.setup_testing)
        with Live(steps, console=console, refresh_per_second=12) as live:
            steps.start(t.setup_test_connect)
            try:
                client = GmailClient(email_address=email, app_password=app_password)
                client.connect()
                steps.complete(t.setup_test_ok)
            except Exception as exc:
                steps.fail(str(exc)[:60])
                steps.finish(t.setup_test_fail)
                live.update(steps)
                time.sleep(0.5)
                live.stop()
                console.print(f"\n  [yellow]\u26a0 {t.setup_test_fail}[/yellow]")
                console.print(f"  [dim]{exc}[/dim]")
                console.print()
                # Don't exit — still save the config, user can fix later
                do_test = False

            if do_test:
                current_year = _date.today().year
                for p in selected_platforms:
                    parser = ParserRegistry.get(p)
                    steps.start(t.setup_test_search.format(platform=parser.platform_name))
                    try:
                        subject = parser.build_search_subject(shop_name)
                        ids = client.search_emails(subject_contains=subject, year=current_year)
                        steps.complete(t.setup_test_found.format(count=len(ids), year=current_year))
                    except Exception:
                        steps.warn("0")

                client.disconnect()
                steps.finish(t.setup_test_ok)
                live.update(steps)
                time.sleep(0.5)
        console.print()
    else:
        console.print(f"  [dim]{t.setup_test_skip}[/dim]")
        console.print()

    # ── Step 5: Save config ─────────────────────────────────────────────
    console.print(f"[bold cyan]{t.setup_step.format(step=5, total=total_steps)}:[/bold cyan] [bold]{t.setup_step_save}[/bold]")
    console.print()

    # Generate default filename from shop name
    safe_name = shop_name.replace(" ", "_")[:20]
    default_filename = f"{safe_name}_merchant.md"

    filename = Prompt.ask(
        f"  [cyan]{t.setup_filename}[/cyan]",
        default=default_filename,
    )
    filepath = Path(filename)

    if filepath.exists():
        overwrite = Confirm.ask(
            f"  [yellow]{t.setup_overwrite.format(path=filepath)}[/yellow]",
            default=False,
        )
        if not overwrite:
            console.print("  [dim]Cancelled.[/dim]")
            raise typer.Exit(0)

    # Build config content
    lines = [
        f'Google App Password = {app_password}',
        f'TH Name = {shop_name}',
        f'Email = {email}',
    ]
    for platform_key, pw in file_passwords.items():
        parser = ParserRegistry.get(platform_key)
        lines.append(f'{parser.platform_name} File Password = {pw}')

    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")

    console.print()
    console.print(f"  [green bold]\u2714 {t.setup_saved}:[/green bold] [bold]{filepath}[/bold]")
    console.print()

    # Usage hints
    usage_grid = Table.grid(padding=(0, 1))
    usage_grid.add_column(style="dim", width=4)
    usage_grid.add_column()
    for p in selected_platforms:
        parser = ParserRegistry.get(p)
        cmd = t.setup_usage_cmd.format(platform=p, config=filepath)
        usage_grid.add_row("  $", f"[white]{cmd}[/white]")

    console.print(Panel(
        usage_grid,
        title=f"[bold cyan]{t.setup_usage_title}[/bold cyan]",
        border_style="green",
        padding=(1, 2),
    ))
    console.print()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
