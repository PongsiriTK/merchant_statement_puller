# Merchant Statement Puller

<div align="center">

```
  __  __               _                 _     ____        _ _
 |  \/  | ___ _ __ ___| |__   __ _ _ __ | |_  |  _ \ _   _| | | ___ _ __
 | |\/| |/ _ \ '__/ __| '_ \ / _` | '_ \| __| | |_) | | | | | |/ _ \ '__|
 | |  | |  __/ | | (__| | | | (_| | | | | |_  |  __/| |_| | | |  __/ |
 |_|  |_|\___|_|  \___|_| |_|\__,_|_| |_|\__| |_|    \__,_|_|_|\___|_|
```

**ดึงรายงานยอดขายจากอีเมลแพลตฟอร์มส่งอาหาร สรุปให้พร้อมยื่นภาษี**

`v1.0.0` &nbsp;&middot;&nbsp; Python 3.10+ &nbsp;&middot;&nbsp; &#x0e44;&#x0e17;&#x0e22; / English &nbsp;&middot;&nbsp; GrabFood &middot; ShopeeFood &middot; Robinhood

</div>

---

## ทำไมถึงสร้างตัวนี้ขึ้นมา?

ผมเป็นคนทำร้านอาหารเอง และเจอปัญหาเดียวกับร้านค้าหลายๆ ร้าน — **ทุกปีต้องนั่งเปิดอีเมลทีละฉบับ เปิดไฟล์ทีละไฟล์ แล้วมานั่งรวมยอดเอง** เพื่อเตรียมตัวเลขสำหรับยื่นภาษี

Grab ส่ง PDF มา, ShopeeFood ส่ง Excel มา, Robinhood ส่ง Excel ที่ล็อกรหัสมา — แต่ละเจ้าคนละรูปแบบ ปีนึงมีรายงาน 300-365 ฉบับ ทำมือไม่ไหว

เลยเขียนเครื่องมือนี้ขึ้นมาเพื่อ **ดึงรายงานจาก Gmail อัตโนมัติ อ่านไฟล์ทุกรูปแบบ แล้วสรุปยอดให้เลย** — ใช้คำสั่งเดียวจบ ได้ตัวเลขพร้อมยื่นภาษี

ถ้าคุณเป็นเจ้าของร้านอาหารที่ขายผ่านแอปส่งอาหาร เครื่องมือนี้ช่วยคุณได้

---

## ทำอะไรได้บ้าง?

- **ดึงรายงานจาก Gmail อัตโนมัติ** — เชื่อมต่อ Gmail แล้วหาอีเมลรายงานยอดขายให้เอง ดาวน์โหลดไฟล์แนบให้ทั้งหมด
- **รองรับ 3 แพลตฟอร์ม** — GrabFood (PDF), ShopeeFood (Excel), Robinhood (Excel เข้ารหัส)
- **อ่านได้ทั้งภาษาไทย** — ค้นหาอีเมลชื่อร้านภาษาไทยได้ แสดงผลภาษาไทยทั้งหมด
- **สรุปยอดพร้อมยื่นภาษี** — รวมยอดขาย ค่าคอมมิชชัน VAT รายได้สุทธิ ทั้งรายวันและรายปี
- **ส่งออก CSV** — เอาไปเปิดใน Excel หรือส่งต่อให้สำนักงานบัญชีได้เลย
- **ตั้งค่าง่าย** — มี Setup Wizard ถามข้อมูลทีละขั้น ไม่ต้องแก้ไฟล์เอง

---

## แพลตฟอร์มที่รองรับ

| แพลตฟอร์ม | รูปแบบไฟล์ | ต้องรหัสผ่าน | หมายเหตุ |
|-----------|-----------|:-----------:|---------|
| **GrabFood** | PDF | — | รายงานธุรกิจรายวัน |
| **ShopeeFood** | Excel (.xlsx) | — | รายงานยอดขายประจำวัน |
| **Robinhood** | Excel (.xlsx) | &#x1f512; | ไฟล์เข้ารหัส ต้องใช้รหัสผ่าน |

> อยากให้รองรับ LINE MAN, Foodpanda หรือแพลตฟอร์มอื่น? [เปิด Issue](https://github.com/PongsiriTK/merchant-statement-puller/issues) บอกได้เลย

---

## สิ่งที่ต้องเตรียม

- **Python 3.10** ขึ้นไป
- **บัญชี Gmail** ที่รับอีเมลรายงาน (เปิด 2-Step Verification แล้ว)
- **Google App Password** — รหัสผ่านเฉพาะแอป สร้างได้ที่ [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

> **ยังไม่เคยสร้าง App Password?** ไม่ต้องกังวล ตอนรัน `merchant-puller setup` ระบบจะมีคำแนะนำให้ทุกขั้นตอน

---

## การติดตั้ง

```bash
git clone https://github.com/PongsiriTK/merchant-statement-puller.git
cd merchant-statement-puller

python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

pip install -e .
```

ลองเช็คว่าติดตั้งสำเร็จ:

```bash
merchant-puller --version
```

---

## เริ่มต้นใช้งาน

### 1. ตั้งค่าร้านค้า (ครั้งแรกครั้งเดียว)

```bash
merchant-puller setup
```

ระบบจะถามข้อมูลทีละขั้น — ชื่อร้าน, อีเมล, App Password, เลือกแพลตฟอร์ม แล้วทดสอบเชื่อมต่อ Gmail ให้ด้วย พอเสร็จจะได้ไฟล์ตั้งค่าพร้อมใช้:

```
╭─ ขั้นตอนการทำงาน ─────────────────────────────────────────────╮
│                                                                │
│  ✔ โหลดไฟล์ตั้งค่าร้านค้า          → ร้านของฉัน          0.1s  │
│  ✔ ตรวจสอบ Parser (grab)          → GrabFood           0.0s  │
│  ✔ เชื่อมต่อ Gmail IMAP            → สำเร็จ              1.2s  │
│  ✔ ค้นหาอีเมล GrabFood           → พบ 365 ฉบับ         2.1s  │
│                                                                │
│  ✔ เสร็จสิ้น                                            3.4s  │
│                                                                │
╰────────────────────────────────────────────────────────────────╯
```

> **หรือจะสร้างไฟล์ตั้งค่าเอง** ก็ได้ — ดูหัวข้อ [ไฟล์ตั้งค่าร้านค้า](#ไฟล์ตั้งค่าร้านค้า)

### 2. ดึงรายงาน

```bash
# ดึงรายงาน GrabFood ปี 2025
merchant-puller pull grab -m my_shop.md -y 2025

# ดึงรายงาน ShopeeFood ปีปัจจุบัน
merchant-puller pull shopee -m my_shop.md

# ดึงรายงาน Robinhood
merchant-puller pull robinhood -m my_shop.md -y 2025
```

### 3. ดูผลลัพธ์

ระบบจะแสดงตารางสรุปยอดขายรายวัน และแผงสรุปรวมสำหรับยื่นภาษี:

```
╭─ สรุปสำหรับยื่นภาษี ──────────────────────────────────╮
│                                                        │
│  แพลตฟอร์ม        GrabFood                             │
│  ร้านค้า           ร้านของฉัน                              │
│  ปี               2025                                 │
│  จำนวนรายงาน      350                                  │
│  จำนวนคำสั่งซื้อ    4,200                                │
│  ─────────────────────────────────────                 │
│  ยอดขายรวม        ฿  1,234,567.00                      │
│  ค่าคอมมิชชัน      ฿    185,185.05                      │
│  VAT             ฿     12,962.95                      │
│  รายได้สุทธิ        ฿    985,432.00                      │
│                                                        │
╰────────────────────────────────────────────────────────╯
```

---

## คำสั่งทั้งหมด

| คำสั่ง | ทำอะไร |
|-------|-------|
| `merchant-puller setup` | ตั้งค่าร้านค้าใหม่แบบโต้ตอบ |
| `merchant-puller pull <platform> -m <config>` | ดึงและสรุปรายงานยอดขาย |
| `merchant-puller platforms` | แสดงแพลตฟอร์มที่รองรับ |
| `merchant-puller --version` | แสดงเวอร์ชัน |

### ตัวเลือกสำหรับ `pull`

| ตัวเลือก | ย่อ | คำอธิบาย |
|----------|-----|---------|
| `--merchant` | `-m` | ไฟล์ตั้งค่าร้านค้า **(ต้องระบุ)** |
| `--year` | `-y` | ปีที่ต้องการ (ค่าเริ่มต้น: ปีปัจจุบัน) |
| `--csv` | | ส่งออกเป็นไฟล์ CSV |
| `--output` | `-o` | โฟลเดอร์เก็บไฟล์ที่ดาวน์โหลด |
| `--lang` | `-l` | เปลี่ยนภาษา: `th` หรือ `en` |
| `--email` | `-e` | ใช้อีเมลอื่นแทนค่าในไฟล์ตั้งค่า |
| `--verbose` | `-v` | แสดง debug log |

**ตัวอย่าง:**

```bash
# ดึง + ส่งออก CSV + เก็บไฟล์
merchant-puller pull grab -m my_shop.md -y 2025 --csv report.csv -o ./downloads

# ใช้ภาษาอังกฤษ
merchant-puller pull shopee -m my_shop.md --lang en
```

---

## ไฟล์ตั้งค่าร้านค้า

ถ้าไม่ใช้ `setup` จะสร้างไฟล์เองก็ได้ — เป็นไฟล์ `.md` ง่ายๆ แบบนี้:

```
Google App Password = abcd efgh ijkl mnop
TH Name = ชื่อร้านภาษาไทย
Email = your.shop@gmail.com
Robinhood File Password = 123456
```

| ฟิลด์ | ต้องระบุ | คำอธิบาย |
|------|:-------:|---------|
| `Google App Password` | &#x2714; | รหัส 16 ตัวจาก Google (ใส่เว้นวรรคได้) |
| `TH Name` | &#x2714; | ชื่อร้านภาษาไทยตามที่ปรากฏในอีเมลรายงาน |
| `Email` | | อีเมล Gmail ที่รับรายงาน |
| `<Platform> File Password` | | รหัสผ่านไฟล์ เช่น `Robinhood File Password` |

> **เรื่องความปลอดภัย:** ไฟล์นี้มี App Password อยู่ — อย่าแชร์หรือ commit ขึ้น git นะ ไฟล์ `*merchant*.md` ถูก gitignore ไว้ให้แล้ว

---

## ส่งออก CSV

```bash
merchant-puller pull grab -m my_shop.md -y 2025 --csv grab_2025.csv
```

ได้ไฟล์ CSV (เปิดใน Excel ได้เลย ไม่มีปัญหาภาษาไทย) มีคอลัมน์: Date, File, Orders, Total, Commission, VAT, Net Income พร้อมแถวรวมยอดท้ายสุด

---

## คำถามที่พบบ่อย

<details>
<summary><strong>Google App Password คืออะไร? สร้างยังไง?</strong></summary>

Gmail ไม่ให้ล็อกอินด้วยรหัสผ่านปกติผ่าน IMAP แล้ว ต้องใช้ App Password ซึ่งเป็นรหัส 16 ตัวที่สร้างจาก Google:

1. ไปที่ [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. ล็อกอิน (ต้องเปิด 2FA ก่อน)
3. ตั้งชื่อ เช่น `merchant-puller` แล้วกด Create
4. ได้รหัส 16 ตัว เอาไปใส่ในไฟล์ตั้งค่า

</details>

<details>
<summary><strong>มีหลายร้าน ใช้ได้ไหม?</strong></summary>

ได้ สร้างไฟล์ตั้งค่าแยกแต่ละร้าน แล้วรันแยกกัน:

```bash
merchant-puller pull grab -m shop_a.md -y 2025
merchant-puller pull grab -m shop_b.md -y 2025
```

</details>

<details>
<summary><strong>เจอ error AUTHENTICATIONFAILED</strong></summary>

- ตรวจสอบ App Password ว่าถูกต้อง (16 ตัวอักษร)
- ตรวจสอบว่าเปิด IMAP ใน Gmail Settings > Forwarding and POP/IMAP
- ตรวจสอบว่าอีเมลสะกดถูก

</details>

<details>
<summary><strong>ใช้บน Windows ได้ไหม?</strong></summary>

ได้ ใช้ Python 3.10+ บน Windows, macOS, หรือ Linux ได้เหมือนกัน

</details>

---

## โครงสร้างโปรเจกต์

```
merchant-statement-puller/
├── main.py                    # Entry point
├── pyproject.toml             # Package config
├── requirements.txt           # Dependencies
├── LICENSE                    # สัญญาอนุญาต
└── src/
    ├── __version__.py         # เวอร์ชัน
    ├── cli/
    │   ├── app.py             # CLI (Typer + Rich)
    │   └── i18n.py            # ภาษาไทย/อังกฤษ
    ├── core/
    │   ├── gmail_client.py    # Gmail IMAP (UTF-8)
    │   ├── merchant_config.py # โหลดไฟล์ตั้งค่า
    │   └── models.py          # Data models
    └── parsers/
        ├── base.py            # Parser interface
        ├── registry.py        # Parser factory
        ├── grab.py            # GrabFood PDF
        ├── shopee.py          # ShopeeFood Excel
        └── robinhood.py       # Robinhood Excel (เข้ารหัส)
```

---

## มีไอเดียดีๆ เพิ่มเติม? 

โปรเจกต์นี้เปิดรับ Pull Request และ Issue ทุกรูปแบบ ไม่ว่าจะเป็น:

- **เพิ่มแพลตฟอร์มใหม่** — LINE MAN, Foodpanda, หรือเจ้าอื่นๆ
- **แก้ Parser** — ถ้าแพลตฟอร์มเปลี่ยนรูปแบบรายงาน
- **ปรับปรุงภาษา** — แก้คำแปลหรือเพิ่มภาษาใหม่
- **รายงาน Bug** — เจอปัญหาอะไรเปิด Issue ได้เลย

### อยากเพิ่มแพลตฟอร์มใหม่?

สร้างไฟล์ Parser ใหม่ แล้วลงทะเบียนในระบบ — ดูตัวอย่างจาก `src/parsers/grab.py` ได้เลย:

```python
from src.parsers.base import BaseParser
from src.core.models import DailyReport

class YourPlatformParser(BaseParser):
    platform_name = "YourPlatform"

    def build_search_subject(self, merchant_name: str) -> str:
        return "หัวเรื่องอีเมลรายงาน"

    def attachment_filename_filter(self, merchant_name: str) -> str:
        return ".xlsx"

    def parse_file(self, filepath, email_subject="", email_date="", password="") -> DailyReport:
        # ... อ่านไฟล์แล้วสร้าง DailyReport ...
        pass
```

---

## สิทธิ์การใช้งาน

เครื่องมือนี้เปิด source ให้ใช้ฟรี สำหรับ **ใช้งานส่วนตัวและไม่แสวงหากำไร**

| การใช้งาน | |
|----------|:---:|
| ใช้กับร้านตัวเอง | &#x2714; ใช้ได้เลย |
| ใช้เพื่อการศึกษา | &#x2714; ใช้ได้เลย |
| องค์กรไม่แสวงหากำไร | &#x2714; ใช้ได้เลย |
| โปรเจกต์ Open Source | &#x2714; ใช้ได้เลย |
| ใช้เชิงพาณิชย์ / Enterprise | &#x2709; ติดต่อก่อน |

### สนใจนำไปใช้เชิงพาณิชย์?

POS, สร้างเป็น SaaS, หรือใช้ในองค์กร — ติดต่อมาคุยกันได้:

> **GitHub:** [@PongsiriTK](https://github.com/PongsiriTK)
>
> **Email:** pongsiritonsuk@gmail.com — ใส่ subject `[Commercial License] Merchant Statement Puller`

รายละเอียดเต็มอยู่ในไฟล์ [LICENSE](LICENSE)

---

<div align="center">

สร้างด้วย &#x2764;&#xfe0f; โดย [Pongsiri Tonsuk](https://github.com/PongsiriTK) — เพื่อร้านค้าไทย

</div>
