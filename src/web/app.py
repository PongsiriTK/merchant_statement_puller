"""Streamlit web UI for Merchant Statement Puller.

A browser-based interface designed for non-technical Thai restaurant owners.
Wraps the same core logic as the CLI but presents it as a simple form.

Launch:
    streamlit run src/web/app.py
    # or
    merchant-puller-web
"""

from __future__ import annotations

import csv
import io
import logging
import tempfile
from datetime import date
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Ensure project root is importable
# ---------------------------------------------------------------------------
import sys

_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.__version__ import __version__
from src.core.gmail_client import GmailClient
from src.core.models import PlatformReport
from src.parsers.registry import ParserRegistry

# ---------------------------------------------------------------------------
# i18n — lightweight web-specific translations
# ---------------------------------------------------------------------------

_TH = {
    "page_title": "Merchant Puller — ระบบดึงรายงานร้านค้า",
    "header": "ระบบดึงรายงานร้านค้า",
    "subtitle": "ดึงรายงานยอดขายจากอีเมลแพลตฟอร์มส่งอาหาร สำหรับยื่นภาษีประจำปี",
    "lang_toggle": "English",
    "section_config": "1. ข้อมูลร้านค้า",
    "shop_name": "ชื่อร้านค้า (ภาษาไทย)",
    "shop_name_help": "ใช้ชื่อเดียวกับที่ลงทะเบียนกับแพลตฟอร์ม",
    "email": "อีเมล Gmail",
    "email_help": "อีเมลที่ได้รับรายงานจากแพลตฟอร์ม",
    "app_password": "Google App Password",
    "app_password_help": "รหัส 16 ตัวอักษรจาก Google (ไม่ใช่รหัสผ่าน Gmail ปกติ)",
    "app_password_link": "วิธีสร้าง App Password",
    "section_platform": "2. เลือกแพลตฟอร์ม",
    "select_platforms": "แพลตฟอร์มที่ต้องการดึงข้อมูล",
    "year": "ปีภาษี",
    "file_password": "รหัสเปิดไฟล์ {platform}",
    "file_password_help": "แพลตฟอร์มนี้ส่งไฟล์ที่มีรหัสผ่าน",
    "section_pull": "3. ดึงรายงาน",
    "btn_pull": "ดึงรายงาน",
    "btn_test": "ทดสอบการเชื่อมต่อ",
    "progress_connect": "กำลังเชื่อมต่อ Gmail...",
    "progress_search": "กำลังค้นหาอีเมล {platform} ปี {year}...",
    "progress_download": "กำลังดาวน์โหลดไฟล์แนบ...",
    "progress_parse": "กำลังอ่านรายงาน...",
    "progress_done": "เสร็จสิ้น!",
    "result_title": "ผลลัพธ์ — {platform}",
    "result_summary": "สรุปสำหรับยื่นภาษี",
    "col_num": "#",
    "col_date": "วันที่",
    "col_file": "ไฟล์",
    "col_orders": "ออเดอร์",
    "col_total": "ยอดขาย",
    "col_commission": "ค่าคอมมิชชัน",
    "col_vat": "VAT",
    "col_net": "รายได้สุทธิ",
    "sum_platform": "แพลตฟอร์ม",
    "sum_merchant": "ร้านค้า",
    "sum_year": "ปีภาษี",
    "sum_reports": "จำนวนรายงาน",
    "sum_orders": "จำนวนออเดอร์",
    "sum_gross": "ยอดขายรวม",
    "sum_commission": "ค่าคอมมิชชัน",
    "sum_vat": "VAT",
    "sum_net": "รายได้สุทธิ",
    "download_csv": "ดาวน์โหลด CSV",
    "no_emails": "ไม่พบอีเมลสำหรับ {platform} ปี {year}",
    "no_attachments": "พบอีเมลแต่ไม่มีไฟล์แนบ",
    "no_data": "ไม่สามารถอ่านข้อมูลจากไฟล์แนบได้",
    "err_connect": "เชื่อมต่อ Gmail ไม่สำเร็จ",
    "err_search": "ค้นหาอีเมลไม่สำเร็จ",
    "err_name_required": "กรุณาใส่ชื่อร้านค้า",
    "err_email_required": "กรุณาใส่อีเมล Gmail",
    "err_password_required": "กรุณาใส่ Google App Password",
    "err_platform_required": "กรุณาเลือกอย่างน้อย 1 แพลตฟอร์ม",
    "err_file_password_required": "กรุณาใส่รหัสเปิดไฟล์ {platform}",
    "test_ok": "เชื่อมต่อสำเร็จ!",
    "test_found": "พบ {count} อีเมลสำหรับ {platform} ปี {year}",
    "test_fail": "เชื่อมต่อไม่สำเร็จ: {error}",
    "save_config": "บันทึกการตั้งค่า",
    "save_config_help": "บันทึกข้อมูลร้านค้าเป็นไฟล์ เพื่อใช้งานครั้งต่อไปไม่ต้องกรอกใหม่",
    "load_config": "โหลดการตั้งค่า",
    "load_config_help": "เลือกไฟล์ตั้งค่าร้านค้าที่เคยบันทึกไว้ (.md)",
    "config_loaded": "โหลดการตั้งค่าสำเร็จ: {name}",
    "config_saved": "บันทึกการตั้งค่าเรียบร้อย: {path}",
    "parse_errors": "อ่านไม่สำเร็จ {count} ไฟล์",
    "guide_title": "คู่มือเริ่มต้นใช้งาน",
    "guide_steps": [
        "กรอกชื่อร้านค้า, อีเมล Gmail และ App Password",
        "เลือกแพลตฟอร์มที่ต้องการดึงข้อมูล",
        'กด "ดึงรายงาน" แล้วรอสักครู่',
        "ดูผลลัพธ์และดาวน์โหลด CSV ไปเปิดใน Excel",
    ],
    "footer": "Merchant Statement Puller v{version}",
    "currency": "฿",
}

_EN = {
    "page_title": "Merchant Puller — Merchant Statement Puller",
    "header": "Merchant Statement Puller",
    "subtitle": "Pull daily sales reports from food delivery platform emails for annual tax filing.",
    "lang_toggle": "ภาษาไทย",
    "section_config": "1. Merchant Information",
    "shop_name": "Shop Name (Thai)",
    "shop_name_help": "Use the same name registered with the platform",
    "email": "Gmail Address",
    "email_help": "The Gmail that receives platform reports",
    "app_password": "Google App Password",
    "app_password_help": "16-character code from Google (not your normal Gmail password)",
    "app_password_link": "How to create an App Password",
    "section_platform": "2. Select Platforms",
    "select_platforms": "Platforms to pull data from",
    "year": "Tax Year",
    "file_password": "{platform} File Password",
    "file_password_help": "This platform sends password-protected files",
    "section_pull": "3. Pull Reports",
    "btn_pull": "Pull Reports",
    "btn_test": "Test Connection",
    "progress_connect": "Connecting to Gmail...",
    "progress_search": "Searching {platform} emails for {year}...",
    "progress_download": "Downloading attachments...",
    "progress_parse": "Parsing reports...",
    "progress_done": "Done!",
    "result_title": "Results — {platform}",
    "result_summary": "Tax Filing Summary",
    "col_num": "#",
    "col_date": "Date",
    "col_file": "File",
    "col_orders": "Orders",
    "col_total": "Total Sales",
    "col_commission": "Commission",
    "col_vat": "VAT",
    "col_net": "Net Income",
    "sum_platform": "Platform",
    "sum_merchant": "Merchant",
    "sum_year": "Tax Year",
    "sum_reports": "Reports",
    "sum_orders": "Total Orders",
    "sum_gross": "Gross Sales",
    "sum_commission": "Commission",
    "sum_vat": "VAT",
    "sum_net": "Net Income",
    "download_csv": "Download CSV",
    "no_emails": "No emails found for {platform} in {year}",
    "no_attachments": "Emails found but no attachments",
    "no_data": "Could not parse any data from attachments",
    "err_connect": "Failed to connect to Gmail",
    "err_search": "Failed to search emails",
    "err_name_required": "Please enter shop name",
    "err_email_required": "Please enter Gmail address",
    "err_password_required": "Please enter Google App Password",
    "err_platform_required": "Please select at least 1 platform",
    "err_file_password_required": "Please enter file password for {platform}",
    "test_ok": "Connection successful!",
    "test_found": "Found {count} emails for {platform} in {year}",
    "test_fail": "Connection failed: {error}",
    "save_config": "Save Settings",
    "save_config_help": "Save merchant settings to a file for next time",
    "load_config": "Load Settings",
    "load_config_help": "Select a previously saved merchant config file (.md)",
    "config_loaded": "Settings loaded: {name}",
    "config_saved": "Settings saved: {path}",
    "parse_errors": "Failed to parse {count} files",
    "guide_title": "Getting Started",
    "guide_steps": [
        "Enter your shop name, Gmail address, and App Password",
        "Select the platforms you want to pull data from",
        'Click "Pull Reports" and wait',
        "View results and download CSV to open in Excel",
    ],
    "footer": "Merchant Statement Puller v{version}",
    "currency": "฿",
}


def _t(key: str) -> str | list:
    """Get translation for current language."""
    lang = st.session_state.get("lang", "th")
    strings = _TH if lang == "th" else _EN
    return strings.get(key, key)


# ---------------------------------------------------------------------------
# Platform display names
# ---------------------------------------------------------------------------

_PLATFORM_DISPLAY = {
    "shopee": "ShopeeFood",
    "grab": "GrabFood",
    "robinhood": "Robinhood",
}

_PLATFORM_FORMATS = {
    "shopee": "Excel (.xlsx)",
    "grab": "PDF",
    "robinhood": "Excel (.xlsx)",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_csv(report: PlatformReport) -> str:
    """Build CSV string from a PlatformReport."""
    buf = io.StringIO()
    writer = csv.writer(buf)
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
    return buf.getvalue()


def _save_config_file(
    shop_name: str,
    email_addr: str,
    app_password: str,
    file_passwords: dict[str, str],
) -> str:
    """Generate merchant config file content."""
    lines = [
        f"Google App Password = {app_password}",
        f"TH Name = {shop_name}",
        f"Email = {email_addr}",
    ]
    for platform_key, pw in file_passwords.items():
        display = _PLATFORM_DISPLAY.get(platform_key, platform_key.title())
        lines.append(f"{display} File Password = {pw}")
    return "\n".join(lines) + "\n"


def _parse_config_text(text: str) -> dict:
    """Parse merchant config text into a dict."""
    config: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        config[key.strip()] = value.strip().strip('"').strip("'")
    return config


def _pull_platform(
    shop_name: str,
    email_addr: str,
    app_password: str,
    platform: str,
    year: int,
    file_password: str = "",
) -> tuple[PlatformReport | None, str]:
    """Pull reports for a single platform. Returns (report, error_message)."""
    parser = ParserRegistry.get(platform)

    # Connect
    try:
        client = GmailClient(email_address=email_addr, app_password=app_password)
        client.connect()
    except Exception as exc:
        return None, f"{_t('err_connect')}: {exc}"

    # Search
    try:
        search_subject = parser.build_search_subject(shop_name)
        message_ids = client.search_emails(subject_contains=search_subject, year=year)
    except Exception as exc:
        client.disconnect()
        return None, f"{_t('err_search')}: {exc}"

    if not message_ids:
        client.disconnect()
        return None, _t("no_emails").format(platform=parser.platform_name, year=year)

    # Download
    try:
        filename_filter = parser.attachment_filename_filter(shop_name)
        attachments = client.fetch_attachments(
            message_ids=message_ids,
            filename_filter=filename_filter,
        )
    except Exception as exc:
        client.disconnect()
        return None, str(exc)

    client.disconnect()

    if not attachments:
        return None, _t("no_attachments")

    # Parse
    report = PlatformReport(
        platform=parser.platform_name,
        merchant_name=shop_name,
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
        except Exception:
            parse_errors += 1

    if not report.daily_reports:
        return None, _t("no_data")

    error_note = ""
    if parse_errors:
        error_note = _t("parse_errors").format(count=parse_errors)

    return report, error_note


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Merchant Puller",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

if "lang" not in st.session_state:
    st.session_state.lang = "th"
if "reports" not in st.session_state:
    st.session_state.reports = {}


# ---------------------------------------------------------------------------
# Custom CSS for a clean, friendly look
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    /* Main header */
    .main-header {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    .main-header h1 {
        font-size: 2rem;
        margin-bottom: 0.25rem;
    }
    .main-header p {
        color: #888;
        font-size: 1rem;
    }

    /* Summary cards */
    .summary-card {
        background: #f0f2f6;
        border-radius: 0.75rem;
        padding: 1rem 1.25rem;
        text-align: center;
    }
    .summary-card .label {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 0.25rem;
    }
    .summary-card .value {
        font-size: 1.5rem;
        font-weight: 700;
    }
    .summary-card .value.green { color: #28a745; }
    .summary-card .value.yellow { color: #e6a800; }

    /* Guide box */
    .guide-box {
        background: #e8f4f8;
        border-left: 4px solid #1f77b4;
        border-radius: 0 0.5rem 0.5rem 0;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
    }
    .guide-box h4 { margin: 0 0 0.5rem 0; color: #1f77b4; }
    .guide-box ol { margin: 0; padding-left: 1.25rem; }
    .guide-box li { margin-bottom: 0.35rem; }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Tighter sidebar */
    section[data-testid="stSidebar"] > div { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar — config & settings
# ---------------------------------------------------------------------------

with st.sidebar:
    # Language toggle
    if st.button(_t("lang_toggle"), use_container_width=True):
        st.session_state.lang = "en" if st.session_state.lang == "th" else "th"
        st.rerun()

    st.markdown("---")

    # Load existing config
    st.markdown(f"**{_t('load_config')}**")
    uploaded = st.file_uploader(
        _t("load_config_help"),
        type=["md", "txt"],
        label_visibility="collapsed",
    )
    if uploaded is not None:
        config_text = uploaded.read().decode("utf-8")
        parsed = _parse_config_text(config_text)
        if parsed.get("TH Name"):
            st.session_state["cfg_name"] = parsed.get("TH Name", "")
            st.session_state["cfg_email"] = parsed.get("Email", "")
            st.session_state["cfg_app_pw"] = parsed.get("Google App Password", "")
            # Collect file passwords
            for key, val in parsed.items():
                if key.endswith("File Password"):
                    plat = key.replace("File Password", "").strip().lower()
                    st.session_state[f"cfg_filepw_{plat}"] = val
            st.success(_t("config_loaded").format(name=parsed["TH Name"]))

    st.markdown("---")

    # Guide
    guide_html = f"<div class='guide-box'><h4>{_t('guide_title')}</h4><ol>"
    for step in _t("guide_steps"):
        guide_html += f"<li>{step}</li>"
    guide_html += "</ol></div>"
    st.markdown(guide_html, unsafe_allow_html=True)

    st.markdown("---")
    st.caption(_t("footer").format(version=__version__))


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.markdown(
    f"<div class='main-header'>"
    f"<h1>{_t('header')}</h1>"
    f"<p>{_t('subtitle')}</p>"
    f"</div>",
    unsafe_allow_html=True,
)

# ── Section 1: Merchant info ──────────────────────────────────────────────

st.subheader(_t("section_config"))

col_name, col_email = st.columns(2)
with col_name:
    shop_name = st.text_input(
        _t("shop_name"),
        value=st.session_state.get("cfg_name", ""),
        help=_t("shop_name_help"),
        placeholder="ร้านลงดี" if st.session_state.lang == "th" else "My Restaurant",
    )
with col_email:
    email_addr = st.text_input(
        _t("email"),
        value=st.session_state.get("cfg_email", ""),
        help=_t("email_help"),
        placeholder="myshop@gmail.com",
    )

col_pw, col_link = st.columns([3, 1])
with col_pw:
    app_password = st.text_input(
        _t("app_password"),
        value=st.session_state.get("cfg_app_pw", ""),
        type="password",
        help=_t("app_password_help"),
        placeholder="xxxx xxxx xxxx xxxx",
    )
with col_link:
    st.markdown("<br>", unsafe_allow_html=True)
    st.link_button(
        _t("app_password_link"),
        url="https://myaccount.google.com/apppasswords",
        use_container_width=True,
    )

st.markdown("")

# ── Section 2: Platforms ──────────────────────────────────────────────────

st.subheader(_t("section_platform"))

available_platforms = ParserRegistry.list_platforms()
platform_options = {
    p: f"{_PLATFORM_DISPLAY.get(p, p)}  ({_PLATFORM_FORMATS.get(p, '')})"
    for p in available_platforms
}

selected_platforms = st.multiselect(
    _t("select_platforms"),
    options=available_platforms,
    default=available_platforms,
    format_func=lambda p: platform_options[p],
)

col_year, col_space = st.columns([1, 3])
with col_year:
    year = st.number_input(
        _t("year"),
        min_value=2020,
        max_value=date.today().year,
        value=date.today().year,
    )

# File passwords for platforms that need them
file_passwords: dict[str, str] = {}
needs_pw = [p for p in selected_platforms if ParserRegistry.get(p).requires_file_password]
if needs_pw:
    for p in needs_pw:
        display = _PLATFORM_DISPLAY.get(p, p.title())
        pw = st.text_input(
            _t("file_password").format(platform=display),
            value=st.session_state.get(f"cfg_filepw_{p}", ""),
            type="password",
            help=_t("file_password_help"),
        )
        if pw:
            file_passwords[p] = pw

st.markdown("")

# ── Section 3: Actions ────────────────────────────────────────────────────

st.subheader(_t("section_pull"))

col_pull, col_test, col_save = st.columns([2, 1, 1])

with col_pull:
    do_pull = st.button(_t("btn_pull"), type="primary", use_container_width=True)
with col_test:
    do_test = st.button(_t("btn_test"), use_container_width=True)
with col_save:
    do_save = st.button(_t("save_config"), use_container_width=True)


# ── Validate inputs ───────────────────────────────────────────────────────

def _validate() -> list[str]:
    errors = []
    if not shop_name.strip():
        errors.append(_t("err_name_required"))
    if not email_addr.strip() or "@" not in email_addr:
        errors.append(_t("err_email_required"))
    if not app_password.strip():
        errors.append(_t("err_password_required"))
    if not selected_platforms:
        errors.append(_t("err_platform_required"))
    for p in needs_pw:
        if p not in file_passwords or not file_passwords[p]:
            display = _PLATFORM_DISPLAY.get(p, p.title())
            errors.append(_t("err_file_password_required").format(platform=display))
    return errors


# ── Test connection ───────────────────────────────────────────────────────

if do_test:
    errors = _validate()
    if errors:
        for e in errors:
            st.error(e)
    else:
        with st.spinner(_t("progress_connect")):
            try:
                client = GmailClient(
                    email_address=email_addr.strip(),
                    app_password=app_password.strip(),
                )
                client.connect()
                st.success(_t("test_ok"))

                for p in selected_platforms:
                    parser = ParserRegistry.get(p)
                    subject = parser.build_search_subject(shop_name.strip())
                    ids = client.search_emails(subject_contains=subject, year=int(year))
                    st.info(_t("test_found").format(
                        count=len(ids),
                        platform=parser.platform_name,
                        year=int(year),
                    ))

                client.disconnect()
            except Exception as exc:
                st.error(_t("test_fail").format(error=str(exc)))


# ── Save config ───────────────────────────────────────────────────────────

if do_save:
    errors = _validate()
    if errors:
        for e in errors:
            st.error(e)
    else:
        config_content = _save_config_file(
            shop_name.strip(),
            email_addr.strip(),
            app_password.strip(),
            file_passwords,
        )
        safe_name = shop_name.strip().replace(" ", "_")[:20]
        filename = f"{safe_name}_merchant.md"
        st.download_button(
            label=_t("save_config"),
            data=config_content.encode("utf-8"),
            file_name=filename,
            mime="text/markdown",
        )


# ── Pull reports ──────────────────────────────────────────────────────────

if do_pull:
    errors = _validate()
    if errors:
        for e in errors:
            st.error(e)
    else:
        st.session_state.reports = {}
        progress_bar = st.progress(0)
        status_text = st.empty()
        total_steps = len(selected_platforms) * 4  # connect, search, download, parse per platform
        current_step = 0

        for p in selected_platforms:
            parser = ParserRegistry.get(p)
            platform_name = parser.platform_name
            fp = file_passwords.get(p, "")

            # Connect
            status_text.text(_t("progress_connect"))
            current_step += 1
            progress_bar.progress(current_step / total_steps)

            # Search
            status_text.text(_t("progress_search").format(platform=platform_name, year=int(year)))
            current_step += 1
            progress_bar.progress(current_step / total_steps)

            # Download + Parse
            status_text.text(_t("progress_download"))
            current_step += 1
            progress_bar.progress(current_step / total_steps)

            report, error_msg = _pull_platform(
                shop_name=shop_name.strip(),
                email_addr=email_addr.strip(),
                app_password=app_password.strip(),
                platform=p,
                year=int(year),
                file_password=fp,
            )

            status_text.text(_t("progress_parse"))
            current_step += 1
            progress_bar.progress(current_step / total_steps)

            if report:
                st.session_state.reports[p] = report
            if error_msg:
                if report:
                    st.warning(f"{platform_name}: {error_msg}")
                else:
                    st.error(f"{platform_name}: {error_msg}")

        progress_bar.progress(1.0)
        status_text.text(_t("progress_done"))


# ── Display results ───────────────────────────────────────────────────────

if st.session_state.reports:
    st.markdown("---")

    for platform_key, report in st.session_state.reports.items():
        st.subheader(_t("result_title").format(platform=report.platform))

        # Summary cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f"<div class='summary-card'>"
                f"<div class='label'>{_t('sum_reports')}</div>"
                f"<div class='value'>{report.total_days}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"<div class='summary-card'>"
                f"<div class='label'>{_t('sum_orders')}</div>"
                f"<div class='value'>{report.total_orders:,}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"<div class='summary-card'>"
                f"<div class='label'>{_t('sum_gross')}</div>"
                f"<div class='value green'>{_t('currency')}{report.grand_total:,.2f}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f"<div class='summary-card'>"
                f"<div class='label'>{_t('sum_net')}</div>"
                f"<div class='value green'>{_t('currency')}{report.grand_net_income:,.2f}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("")

        # Detailed summary
        with st.expander(_t("result_summary"), expanded=True):
            s1, s2 = st.columns(2)
            with s1:
                st.markdown(f"**{_t('sum_platform')}:** {report.platform}")
                st.markdown(f"**{_t('sum_merchant')}:** {report.merchant_name}")
                st.markdown(f"**{_t('sum_year')}:** {report.year}")
            with s2:
                st.markdown(f"**{_t('sum_gross')}:** {_t('currency')}{report.grand_total:,.2f}")
                st.markdown(f"**{_t('sum_commission')}:** {_t('currency')}{report.grand_commission:,.2f}")
                st.markdown(f"**{_t('sum_vat')}:** {_t('currency')}{report.grand_vat:,.2f}")
                st.markdown(f"**{_t('sum_net')}:** **{_t('currency')}{report.grand_net_income:,.2f}**")

        # Daily report table
        table_data = []
        for idx, daily in enumerate(
            sorted(report.daily_reports, key=lambda d: d.report_date), start=1
        ):
            table_data.append({
                _t("col_num"): idx,
                _t("col_date"): daily.report_date.strftime("%Y-%m-%d"),
                _t("col_file"): daily.filename[:40],
                _t("col_orders"): daily.order_count,
                _t("col_total"): f"{daily.total_sales:,.2f}",
                _t("col_commission"): f"{daily.total_commission:,.2f}",
                _t("col_vat"): f"{daily.total_vat:,.2f}",
                _t("col_net"): f"{daily.total_net_income:,.2f}",
            })

        if table_data:
            st.dataframe(table_data, use_container_width=True, hide_index=True)

        # CSV download
        csv_data = _build_csv(report)
        safe_name = report.merchant_name.replace(" ", "_")[:20]
        csv_filename = f"{safe_name}_{report.platform}_{report.year}.csv"

        st.download_button(
            label=f"{_t('download_csv')} — {report.platform}",
            data=csv_data.encode("utf-8-sig"),
            file_name=csv_filename,
            mime="text/csv",
            key=f"csv_{platform_key}",
        )

        st.markdown("")
