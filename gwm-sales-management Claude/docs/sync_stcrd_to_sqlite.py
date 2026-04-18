import sqlite3
from dbfread import DBF
import os

def sync_stcrd():
    dbf_file = "dbf/STCRD.DBF"
    sqlite_db = "car_management.db"
    
    if not os.path.exists(dbf_file):
        print(f"❌ Error: {dbf_file} not found.")
        return

    print(f"📖 Reading structure from {dbf_file}...")
    table = DBF(dbf_file, encoding='cp874')
    
    # 0. เตรียมคำสั่งสร้างตาราง stockcardxp4 ตามโครงสร้าง DBF
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
    
    create_sql = f"CREATE TABLE IF NOT EXISTS stockcardxp4 ({', '.join(fields)})"
    
    try:
        conn = sqlite3.connect(sqlite_db)
        cursor = conn.cursor()
        
        # สร้างตารางใหม่
        cursor.execute("DROP TABLE IF EXISTS stockcardxp4")
        cursor.execute(create_sql)
        print("✅ Table 'stockcardxp4' created successfully.")

        # 1. ดึงรายการ STKCOD ที่เราสนใจจาก stockxp4 มาพักไว้ในหน่วยความจำเพื่อใช้กรอง
        print("🔍 Fetching valid Product Codes from stockxp4...")
        cursor.execute("SELECT DISTINCT STKCOD FROM stockxp4")
        valid_stkcods = set(row[0] for row in cursor.fetchall())
        print(f"   - Found {len(valid_stkcods)} valid codes to track.")

        # 2. นำเข้าข้อมูลและกรอง STKCOD
        print(f"📥 Importing records from {dbf_file}...")
        
        insert_placeholders = ", ".join(["?"] * len(table.field_names))
        insert_sql = f"INSERT INTO stockcardxp4 ({', '.join(table.field_names)}) VALUES ({insert_placeholders})"
        
        count = 0
        skipped = 0
        records_to_insert = []

        for record in table:
            stkcod = record['STKCOD'].strip()
            
            # กรองเอาเฉพาะ STKCOD ที่มีในตารางหลักของเรา
            if stkcod not in valid_stkcods:
                skipped += 1
                continue
            
            row_data = []
            for field_name in table.field_names:
                val = record[field_name]
                if hasattr(val, 'isoformat'): # Handle Date
                    val = val.isoformat()
                row_data.append(val)
            
            records_to_insert.append(row_data)
            count += 1
            
            if len(records_to_insert) >= 500: # เพิ่มขนาด Batch เพื่อความเร็ว
                cursor.executemany(insert_sql, records_to_insert)
                records_to_insert = []

        if records_to_insert:
            cursor.executemany(insert_sql, records_to_insert)

        conn.commit()
        conn.close()
        
        print(f"🎉 Stock Card Import Complete!")
        print(f"   - Total records imported: {count}")
        print(f"   - Records skipped (Not in master): {skipped}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    sync_stcrd()
