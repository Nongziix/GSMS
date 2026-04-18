# GWM Sales Management System (GSMS)
ระบบบริหารจัดการงานขายและสต็อกรถยนต์ เชื่อมต่อข้อมูลจาก Express 4 DOS

## 📁 Project Structure
```text
gwm-sales-management/
├── docs/                  # เอกสารประกอบโปรเจกต์
├── static/
│   └── css/
│       └── gsms.css       # ★ Main stylesheet (Luxury Dark Theme)
├── templates/             # Jinja2 Templates
│   ├── base.html          # Layout หลัก + Navbar
│   ├── index.html         # Dashboard
│   ├── stock.html         # รายการสต็อก
│   ├── stockcard.html     # Stock Card
│   ├── purchase_receive.html
│   ├── master_data.html   # CRUD Brand/Model/Variant/Color
│   └── settings.html
├── data/
│   ├── raw_express/       # ไฟล์ .DBF จาก Express
│   └── database/          # SQLite (GSMS_data.db)
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── dbf_engine.py      # DBF Sync Engine
│   └── models.py
├── app.py
└── requirements.txt
```

---

## 1. Core Principles
- **Single Source of Truth:** ข้อมูลสต็อกและต้นทุนอ้างอิงจาก Express DBF เป็นหลัก
- **Data Safety:** ห้ามเขียนทับ (Write) ลงในไฟล์ .DBF ต้นฉบับ ใช้วิธี Read-only แล้วจัดการใน SQLite
- **Code Style:** Python PEP 8, ชื่อตัวแปรสื่อความหมาย

## 2. Tech Stack
- **Backend:** Flask (Python 3.x) + Flask-SQLAlchemy
- **Data Engine:** Pandas + dbfread
- **Database:** SQLite
- **Frontend:** Bootstrap 5 + Custom CSS (`gsms.css`)

## 3. DBF Handling Rules
- ใช้ `dbfread` อ่านไฟล์ encoding `cp874`
- แปลงเป็น DataFrame / Insert ลง SQLite ทันที
- ห้าม Write กลับไปที่ DBF

---

## 4. 🎨 CSS / Styling Rules (สำคัญมาก)

### ไฟล์หลัก
```
static/css/gsms.css
```
ไฟล์นี้คือ **Single Source of Truth** ของ styling ทั้งระบบ  
**ห้ามเขียน inline style หรือ `<style>` tag ใน template** ยกเว้นกรณีจำเป็นจริงๆ เช่น dynamic color จาก Python

### Theme: "GWM Obsidian" — Luxury Dark
```css
--gwm-red:      #D7000F;   /* accent หลัก */
--bg-base:      #0a0a0a;   /* พื้นหลังสุด */
--bg-surface:   #111111;   /* Card/Navbar */
--bg-elevated:  #1a1a1a;   /* Card header, input */
--text-primary: #f0f0f0;
--text-secondary:#9F9FA0;
--font-display: 'Barlow Condensed'; /* heading, badge, button */
--font-body:    'DM Sans';          /* body text */
```

### กฎการเพิ่ม/แก้ไข Style
1. **เพิ่ม CSS ใหม่ใน `gsms.css` เสมอ** — ไม่เขียนใน template
2. **ใช้ CSS Variables** ห้าม hardcode สีโดยตรง เช่น `color: #D7000F` → ใช้ `color: var(--gwm-red)`
3. **ตั้งชื่อ section ให้ชัดเจน** โดยใช้ comment block:
   ```css
   /* --------------------------------------------------------------------------
      [ชื่อหน้า/component] Specific
      -------------------------------------------------------------------------- */
   ```
4. **Bootstrap class ยังใช้ได้** แต่ถ้า override ให้เขียนใน `gsms.css` ไม่ใช่ `!important` มั่วๆ
5. **อัปเดต README นี้** ทุกครั้งที่เพิ่ม section ใหม่ใน CSS

### Section ที่มีใน gsms.css (ปัจจุบัน)
| Section | เนื้อหา |
|---------|---------|
| 1 | Google Fonts Import |
| 2 | CSS Variables |
| 3 | Base Reset & Body |
| 4 | Typography |
| 5 | Navbar |
| 6 | Page Layout & Animations |
| 7 | Cards (รวม Stat Cards) |
| 8 | Tables + DataTables overrides |
| 9 | Forms & Inputs |
| 10 | Buttons |
| 11 | Badges |
| 12 | Alerts |
| 13 | Modals |
| 14 | Tabs |
| 15 | Breadcrumb |
| 16 | List Group |
| 17 | Text utilities override |
| 18 | Dashboard Specific |
| 19 | Stock Table |
| 20 | Purchase Form |
| 21 | Settings Page |
| 22 | Animations |
| 23 | Responsive |

---

## 5. UI/UX Rules
- **สีหลัก:** ดำ `#0a0a0a`, เทา `#9F9FA0`, แดง `#D7000F`, ขาว `#f0f0f0`
- Dashboard ต้องมี Chart.js แสดงสต็อกแยกรุ่น
- Mobile friendly (Bootstrap grid)
- ทุกปุ่ม Delete ต้องมี confirm modal ก่อนดำเนินการ

## 6. Route Structure
| URL | Function | หมายเหตุ |
|-----|----------|---------|
| `/` | dashboard | |
| `/stock` | stock list | จาก Express DBF |
| `/stockcard/<stkcod>` | stock card | |
| `/purchase/receive-car` | รับรถ | บันทึกลง SQLite |
| `/master-data` | CRUD master | Brand/Model/Variant/Color |
| `/settings` | sync DBF | |
| `/api/models/<brand_id>` | API | dropdown |
| `/api/variants/<model_id>` | API | dropdown |
| `/api/express-bills` | API | modal บิล |
