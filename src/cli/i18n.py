"""Internationalization — Thai and English translations for the CLI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Locale:
    """All user-facing strings for a single language."""

    # Banner / branding
    app_title: str
    app_subtitle: str

    # Commands
    cmd_pull_help: str
    cmd_platforms_help: str

    # Pull command arguments
    arg_platform: str
    opt_merchant: str
    opt_email: str
    opt_year: str
    opt_output: str
    opt_verbose: str
    opt_lang: str
    opt_version: str
    opt_export_csv: str

    # Step progress panel
    step_title: str
    step_load_config: str
    step_resolve_parser: str
    step_connect: str
    step_search: str
    step_download: str
    step_parse: str
    step_complete: str
    step_found: str
    step_files: str
    step_reports: str
    step_total_time: str
    step_password_check: str

    # Status messages
    status_merchant: str
    status_email: str
    status_platform: str
    status_year: str
    status_processed: str
    status_errors: str
    status_exported_csv: str

    # Errors
    err_config: str
    err_no_email: str
    err_no_email_hint: str
    err_parser: str
    err_gmail_fail: str
    err_search_fail: str
    err_download_fail: str
    err_no_emails: str
    err_no_attachments: str
    err_need_password: str
    err_need_password_hint: str

    # Table headers
    tbl_daily_title: str
    tbl_col_num: str
    tbl_col_date: str
    tbl_col_file: str
    tbl_col_orders: str
    tbl_col_total: str
    tbl_col_commission: str
    tbl_col_vat: str
    tbl_col_net: str
    tbl_col_total_row: str
    tbl_col_reports: str

    # Summary panel
    sum_title: str
    sum_platform: str
    sum_merchant: str
    sum_year: str
    sum_reports: str
    sum_orders: str
    sum_gross: str
    sum_commission: str
    sum_vat: str
    sum_net: str

    # Platforms list
    plat_title: str
    plat_col_num: str
    plat_col_name: str
    plat_col_format: str
    plat_col_status: str
    plat_ready: str
    plat_password_note: str

    # No data
    no_data: str

    # Setup wizard
    setup_title: str
    setup_welcome: str
    setup_step: str
    setup_shop_name: str
    setup_shop_name_hint: str
    setup_email: str
    setup_email_hint: str
    setup_app_password: str
    setup_app_password_hint: str
    setup_select_platforms: str
    setup_select_platforms_hint: str
    setup_file_password: str
    setup_test_ask: str
    setup_testing: str
    setup_test_connect: str
    setup_test_search: str
    setup_test_found: str
    setup_test_ok: str
    setup_test_fail: str
    setup_test_skip: str
    setup_filename: str
    setup_filename_default: str
    setup_saved: str
    setup_overwrite: str
    setup_usage_title: str
    setup_usage_cmd: str
    setup_invalid_email: str
    setup_invalid_password: str
    setup_step_info: str
    setup_step_platform: str
    setup_step_password: str
    setup_step_test: str
    setup_step_save: str


TH = Locale(
    app_title="ระบบดึงรายงานร้านค้า",
    app_subtitle="รวบรวมยอดขายจากอีเมลแพลตฟอร์มส่งอาหาร สำหรับยื่นภาษี",

    cmd_pull_help="ดึงและรวมรายงานยอดขายรายวันจากอีเมลแพลตฟอร์มส่งอาหาร",
    cmd_platforms_help="แสดงรายชื่อแพลตฟอร์มที่รองรับ",

    arg_platform="แพลตฟอร์ม เช่น shopee, grab, robinhood",
    opt_merchant="ไฟล์ตั้งค่าร้านค้า (.md)",
    opt_email="อีเมล Gmail สำหรับเชื่อมต่อ",
    opt_year="ปีภาษีที่ต้องการดึงรายงาน",
    opt_output="โฟลเดอร์สำหรับบันทึกไฟล์แนบ",
    opt_verbose="แสดงข้อมูลดีบัก",
    opt_lang="ภาษา (th/en)",
    opt_version="แสดงเวอร์ชัน",
    opt_export_csv="ส่งออกเป็นไฟล์ CSV",

    step_title="ขั้นตอนการทำงาน",
    step_load_config="โหลดไฟล์ตั้งค่าร้านค้า",
    step_resolve_parser="ตรวจสอบ Parser ({platform})",
    step_connect="เชื่อมต่อ Gmail IMAP",
    step_search="ค้นหาอีเมลปี {year}",
    step_download="ดาวน์โหลดไฟล์แนบ",
    step_parse="ประมวลผลรายงาน",
    step_complete="เสร็จสิ้น",
    step_found="พบ {count} ฉบับ",
    step_files="{count} ไฟล์",
    step_reports="{count} รายงาน",
    step_total_time="รวมเวลา {time:.1f} วินาที",
    step_password_check="ตรวจสอบรหัสผ่านไฟล์",

    status_merchant="ร้านค้า",
    status_email="อีเมล",
    status_platform="แพลตฟอร์ม",
    status_year="ปี",
    status_processed="ประมวลผลแล้ว {count} ไฟล์",
    status_errors="{count} ข้อผิดพลาด",
    status_exported_csv="ส่งออก CSV แล้ว: {path}",

    err_config="ข้อผิดพลาดไฟล์ตั้งค่า:",
    err_no_email="ไม่พบอีเมล",
    err_no_email_hint="ใช้ --email หรือเพิ่ม 'Email = ...' ในไฟล์ตั้งค่าร้านค้า",
    err_parser="ข้อผิดพลาด Parser:",
    err_gmail_fail="เชื่อมต่อ Gmail ไม่สำเร็จ",
    err_search_fail="ค้นหาไม่สำเร็จ",
    err_download_fail="ดาวน์โหลดไม่สำเร็จ",
    err_no_emails="ไม่พบอีเมลสำหรับ '{query}' ในปี {year}",
    err_no_attachments="พบอีเมลแต่ไม่มีไฟล์แนบที่ตรงเงื่อนไข",
    err_need_password="{platform} ต้องการรหัสผ่านไฟล์แต่ไม่พบในไฟล์ตั้งค่า",
    err_need_password_hint="เพิ่ม '{platform} File Password = <รหัสผ่าน>' ในไฟล์ {config}",

    tbl_daily_title="รายงานยอดขายรายวัน — {platform} ({year})",
    tbl_col_num="#",
    tbl_col_date="วันที่",
    tbl_col_file="ไฟล์",
    tbl_col_orders="คำสั่งซื้อ",
    tbl_col_total="ยอดรวม (\u0e3f)",
    tbl_col_commission="ค่าคอมมิชชัน (\u0e3f)",
    tbl_col_vat="VAT (\u0e3f)",
    tbl_col_net="รายได้สุทธิ (\u0e3f)",
    tbl_col_total_row="รวมทั้งหมด",
    tbl_col_reports="{count} รายงาน",

    sum_title="สรุปสำหรับยื่นภาษี",
    sum_platform="แพลตฟอร์ม",
    sum_merchant="ร้านค้า",
    sum_year="ปี",
    sum_reports="จำนวนรายงาน",
    sum_orders="จำนวนคำสั่งซื้อ",
    sum_gross="ยอดขายรวม",
    sum_commission="ค่าคอมมิชชัน",
    sum_vat="VAT",
    sum_net="รายได้สุทธิ",

    plat_title="แพลตฟอร์มที่รองรับ",
    plat_col_num="#",
    plat_col_name="ชื่อ",
    plat_col_format="รูปแบบไฟล์",
    plat_col_status="สถานะ",
    plat_ready="พร้อมใช้งาน",
    plat_password_note="ต้องใช้รหัสผ่านไฟล์",

    no_data="ไม่มีข้อมูลแสดงผล",

    setup_title="ตั้งค่าร้านค้าใหม่",
    setup_welcome="สร้างไฟล์ตั้งค่าร้านค้าสำหรับดึงรายงานยอดขาย",
    setup_step="ขั้นตอนที่ {step}/{total}",
    setup_shop_name="ชื่อร้านค้า (ภาษาไทย)",
    setup_shop_name_hint="ต้องตรงกับชื่อที่ปรากฏในอีเมลรายงาน",
    setup_email="อีเมล Gmail",
    setup_email_hint="บัญชี Gmail ที่ได้รับอีเมลรายงานยอดขาย",
    setup_app_password="Google App Password",
    setup_app_password_hint="สร้างได้ที่ myaccount.google.com/apppasswords (ต้องเปิด 2FA ก่อน)",
    setup_select_platforms="เลือกแพลตฟอร์ม",
    setup_select_platforms_hint="ใส่ตัวเลขคั่นด้วย , เช่น 1,3",
    setup_file_password="รหัสผ่านไฟล์ {platform}",
    setup_test_ask="ต้องการทดสอบเชื่อมต่อ Gmail หรือไม่?",
    setup_testing="ทดสอบการเชื่อมต่อ",
    setup_test_connect="เชื่อมต่อ Gmail",
    setup_test_search="ค้นหาอีเมล {platform}",
    setup_test_found="พบ {count} อีเมลในปี {year}",
    setup_test_ok="เชื่อมต่อสำเร็จ",
    setup_test_fail="เชื่อมต่อไม่สำเร็จ — ตรวจสอบอีเมลและ App Password",
    setup_test_skip="ข้ามการทดสอบ",
    setup_filename="ชื่อไฟล์ตั้งค่า",
    setup_filename_default="my_shop.md",
    setup_saved="บันทึกไฟล์ตั้งค่าแล้ว",
    setup_overwrite="ไฟล์ {path} มีอยู่แล้ว — ต้องการเขียนทับ?",
    setup_usage_title="วิธีใช้งาน",
    setup_usage_cmd="merchant-puller pull {platform} -m {config}",
    setup_invalid_email="รูปแบบอีเมลไม่ถูกต้อง กรุณาใส่อีเมล Gmail",
    setup_invalid_password="App Password ต้องมี 16 ตัวอักษร (ไม่นับเว้นวรรค)",
    setup_step_info="ข้อมูลร้านค้า",
    setup_step_platform="เลือกแพลตฟอร์ม",
    setup_step_password="รหัสผ่านไฟล์",
    setup_step_test="ทดสอบการเชื่อมต่อ",
    setup_step_save="บันทึกไฟล์",
)


EN = Locale(
    app_title="Merchant Statement Puller",
    app_subtitle="Tax-ready sales aggregation from food delivery platform emails",

    cmd_pull_help="Pull and aggregate daily sales reports from food delivery platform emails",
    cmd_platforms_help="List all supported delivery platforms",

    arg_platform="Delivery platform (e.g., shopee, grab, robinhood)",
    opt_merchant="Path to merchant config .md file",
    opt_email="Gmail address to connect to",
    opt_year="Tax year to pull statements for",
    opt_output="Directory to save downloaded attachments",
    opt_verbose="Enable verbose/debug logging",
    opt_lang="Language (th/en)",
    opt_version="Show version",
    opt_export_csv="Export results to CSV file",

    step_title="Progress",
    step_load_config="Load merchant config",
    step_resolve_parser="Resolve parser ({platform})",
    step_connect="Connect to Gmail IMAP",
    step_search="Search emails for {year}",
    step_download="Download attachments",
    step_parse="Parse reports",
    step_complete="Complete",
    step_found="{count} emails found",
    step_files="{count} files",
    step_reports="{count} reports",
    step_total_time="Total time {time:.1f}s",
    step_password_check="Verify file password",

    status_merchant="Merchant",
    status_email="Email",
    status_platform="Platform",
    status_year="Year",
    status_processed="Processed {count} file(s)",
    status_errors="{count} error(s)",
    status_exported_csv="CSV exported: {path}",

    err_config="Config error:",
    err_no_email="No email address provided.",
    err_no_email_hint="Use --email or add 'Email = ...' to your merchant config file.",
    err_parser="Parser error:",
    err_gmail_fail="Gmail connection failed",
    err_search_fail="Search failed",
    err_download_fail="Download failed",
    err_no_emails="No emails found for '{query}' in {year}",
    err_no_attachments="Emails found but no matching attachments downloaded.",
    err_need_password="{platform} requires a file password but none found in config.",
    err_need_password_hint="Add '{platform} File Password = <password>' to {config}",

    tbl_daily_title="Daily Sales Report \u2014 {platform} ({year})",
    tbl_col_num="#",
    tbl_col_date="Date",
    tbl_col_file="File",
    tbl_col_orders="Orders",
    tbl_col_total="Total (\u0e3f)",
    tbl_col_commission="Commission (\u0e3f)",
    tbl_col_vat="VAT (\u0e3f)",
    tbl_col_net="Net Income (\u0e3f)",
    tbl_col_total_row="TOTAL",
    tbl_col_reports="{count} report(s)",

    sum_title="Tax Filing Summary",
    sum_platform="Platform",
    sum_merchant="Merchant",
    sum_year="Year",
    sum_reports="Total Reports",
    sum_orders="Total Orders",
    sum_gross="Gross Sales",
    sum_commission="Commission",
    sum_vat="VAT",
    sum_net="Net Income",

    plat_title="Supported Platforms",
    plat_col_num="#",
    plat_col_name="Platform",
    plat_col_format="File Format",
    plat_col_status="Status",
    plat_ready="Ready",
    plat_password_note="Requires file password",

    no_data="No data to display.",

    setup_title="New Merchant Setup",
    setup_welcome="Create a merchant config file for pulling sales reports",
    setup_step="Step {step}/{total}",
    setup_shop_name="Shop name (Thai)",
    setup_shop_name_hint="Must match the name in report emails",
    setup_email="Gmail address",
    setup_email_hint="Gmail account that receives sales report emails",
    setup_app_password="Google App Password",
    setup_app_password_hint="Create at myaccount.google.com/apppasswords (requires 2FA)",
    setup_select_platforms="Select platforms",
    setup_select_platforms_hint="Enter numbers separated by commas, e.g. 1,3",
    setup_file_password="{platform} file password",
    setup_test_ask="Test Gmail connection?",
    setup_testing="Testing connection",
    setup_test_connect="Connect to Gmail",
    setup_test_search="Search {platform} emails",
    setup_test_found="{count} emails found in {year}",
    setup_test_ok="Connection successful",
    setup_test_fail="Connection failed \u2014 check email and App Password",
    setup_test_skip="Skipping test",
    setup_filename="Config filename",
    setup_filename_default="my_shop.md",
    setup_saved="Config file saved",
    setup_overwrite="File {path} exists \u2014 overwrite?",
    setup_usage_title="Usage",
    setup_usage_cmd="merchant-puller pull {platform} -m {config}",
    setup_invalid_email="Invalid email format. Enter a Gmail address.",
    setup_invalid_password="App Password must be 16 characters (excluding spaces)",
    setup_step_info="Shop information",
    setup_step_platform="Select platforms",
    setup_step_password="File passwords",
    setup_step_test="Test connection",
    setup_step_save="Save config",
)


LOCALES: dict[str, Locale] = {"th": TH, "en": EN}


def get_locale(lang: str = "th") -> Locale:
    """Return the locale for the given language code."""
    return LOCALES.get(lang.lower(), TH)
