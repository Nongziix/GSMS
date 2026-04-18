# GWM Sales Management System (GSMS)
ระบบบริหารจัดการงานขายและสต็อกรถยนต์ เชื่อมต่อข้อมูลจาก Express 4 DOS

## 📁 Project Structure
```text
gwm-sales-management/
├── docs/                # เอกสารประกอบโปรเจกต์ และกฎการพัฒนา (.md)
│   ├── sync_*.py         # Legacy scripts for reference logic
├── static/              # ไฟล์ Static (CSS, JS, Images, Chart.js)
├── templates/           # Jinja2 Templates (HTML files)
├── data/
│   ├── raw_express/     # ที่สำหรับวางไฟล์ .DBF (Source จาก Express)
│   └── database/        # ที่เก็บไฟล์ SQLite (app_data.db)
├── app/
│   ├── __init__.py      # Initial Flask App
│   ├── routes.py        # แผนผังเส้นทางของเว็บไซต์ (URL Routing)
│   ├── dbf_engine.py    # ส่วนประมวลผลการอ่านไฟล์ DBF เป็น Pandas
│   └── models.py        # โครงสร้างฐานข้อมูล SQLite
├── app.py               # จุดเริ่มต้นรันโปรแกรม (Main Entry)
└── requirements.txt     # รายการ Library ที่ต้องติดตั้ง (Flask, Pandas, dbfread)


# GWM Sales Management - Development Rules

## 1. Core Principles
- **Single Source of Truth:** ข้อมูลสต็อกและต้นทุนต้องอ้างอิงหลักการคำนวณจากไฟล์ .DBF ของ Express เป็นหลัก
- **Data Safety:** ห้ามเขียนทับ (Write) ลงในไฟล์ .DBF ต้นฉบับโดยตรง ให้ใช้วิธี Read-only แล้วมาจัดการใน SQLite แทน
- **Code Style:** เขียนโค้ด Python ตามมาตรฐาน PEP 8 และใช้ชื่อตัวแปรที่สื่อความหมาย (เช่น `car_stock_count`)

## 2. Tech Stack Requirements
- **Backend:** Flask (Python 3.x)
- **Data Engine:** Pandas (ใช้สำหรับเตรียมข้อมูลจาก DBF และ CSV)
- **Database:** SQLite (สำหรับเก็บข้อมูลเสริมที่ Express ไม่มี เช่น สถานะจองรถ)
- **Frontend:** Bootstrap 5 (Mobile Friendly)

## 3. DBF Handling Rules
- ใช้ Library `dbfread` หรือ `simpledbf` ในการอ่านข้อมูล
- เมื่ออ่านไฟล์ DBF มาแล้ว ให้แปลงเป็น Pandas DataFrame ทันทีเพื่อความรวดเร็วในการ Query
- การคำนวณต้นทุน (FIFO/Average) ต้องให้ตรงกับรายงานใน Express

## 4. UI/UX Rules
- Dashboard ต้องมี Chart.js แสดงผลสต็อกรถแยกตามรุ่น (TANK 300, ORA, etc.)
- สีหลักของเว็บแอปต้องอิงตาม Brand Identity ของ GWM ( #000000 โทนสีดำ #9F9FA0 เทา #D7000F แดง #FFFFF ขาว)