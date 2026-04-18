import sqlite3
from dbfread import DBF
import os

def sync_stmas():
    dbf_file = "dbf/STMAS.DBF"
    sqlite_db = "car_management.db"
    
    if not os.path.exists(dbf_file):
        print(f"❌ Error: {dbf_file} not found.")
        return

    print(f"📖 Reading structure from {dbf_file}...")
    table = DBF(dbf_file, encoding='cp874')
    
    # 0. เตรียมคำสั่งสร้างตาราง stockxp4 ตามโครงสร้าง DBF
    # DBF Type Mapping: C->TEXT, N->REAL, D->TEXT, L->INTEGER, M->TEXT
    fields = []
    for field in table.fields:
        name = field.name
        typ = field.type
        if typ == 'N':
            fields.append(f"{name} REAL")
        elif typ == 'L':
            fields.append(f"{name} INTEGER")
        else:
            fields.append(f"{name} TEXT")
    
    create_sql = f"CREATE TABLE IF NOT EXISTS stockxp4 ({', '.join(fields)})"
    
    try:
        conn = sqlite3.connect(sqlite_db)
        cursor = conn.cursor()
        
        # สร้างตาราง
        cursor.execute("DROP TABLE IF EXISTS stockxp4")
        cursor.execute(create_sql)
        print("✅ Table 'stockxp4' created successfully.")

        # 1. นำเข้าข้อมูลและกรองหมวด คช, รด
        # คช (CP874) -> 'เธเธ' (UTF-8 representation of CP874 bytes in some environments) 
        # เพื่อความชัวร์ เราจะกรองทั้งตัวอักษรไทยปกติ และ byte pattern
        exclude_groups = ['คช', 'รด', 'เธเธ', 'เนเธฃเธ”']
        
        print("📥 Importing data from STMAS.DBF (Filtering out expenses and incomes)...")
        
        insert_placeholders = ", ".join(["?"] * len(table.field_names))
        insert_sql = f"INSERT INTO stockxp4 ({', '.join(table.field_names)}) VALUES ({insert_placeholders})"
        
        count = 0
        skipped = 0
        
        # เตรียมข้อมูลสำหรับการ insert (Batch insert เพื่อความเร็ว)
        records_to_insert = []
        for record in table:
            grp = record['STKGRP'].strip()
            if grp in exclude_groups:
                skipped += 1
                continue
            
            # แปลงค่าบางอย่างที่ SQLite ไม่รองรับโดยตรง (เช่น datetime.date)
            row_data = []
            for field_name in table.field_names:
                val = record[field_name]
                if hasattr(val, 'isoformat'): # Handle Date
                    val = val.isoformat()
                row_data.append(val)
            
            records_to_insert.append(row_data)
            count += 1
            
            # Insert ทุกๆ 100 รายการ
            if len(records_to_insert) >= 100:
                cursor.executemany(insert_sql, records_to_insert)
                records_to_insert = []

        # Insert ส่วนที่เหลือ
        if records_to_insert:
            cursor.executemany(insert_sql, records_to_insert)

        conn.commit()
        conn.close()
        
        print(f"🎉 Import Complete!")
        print(f"   - Total records imported: {count}")
        print(f"   - Records skipped (คช/รด): {skipped}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    sync_stmas()
