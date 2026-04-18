import sqlite3
from dbfread import DBF
import os

def sync_apmas():
    dbf_file = "dbf/APMAS.DBF"
    sqlite_db = "car_management.db"
    table_name = "master_supplier"
    
    if not os.path.exists(dbf_file):
        print(f"❌ Error: {dbf_file} not found.")
        return

    print(f"📖 Reading structure from {dbf_file}...")
    table = DBF(dbf_file, encoding='cp874')
    
    # 0. เตรียมคำสั่งสร้างตาราง โดยกำหนด SUPCOD เป็น PRIMARY KEY
    fields = []
    for field in table.fields:
        name = field.name
        typ = field.type
        
        field_def = name
        if typ == 'N':
            field_def += " REAL"
        elif typ == 'L':
            field_def += " INTEGER"
        else:
            field_def += " TEXT"
            
        if name == 'SUPCOD':
            field_def += " PRIMARY KEY"
            
        fields.append(field_def)
    
    try:
        conn = sqlite3.connect(sqlite_db)
        cursor = conn.cursor()
        
        # สร้างตาราง
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(f"CREATE TABLE {table_name} ({', '.join(fields)})")
        print(f"✅ Table '{table_name}' created with SUPCOD as Primary Key.")

        # 1. นำเข้าข้อมูล
        print(f"📥 Importing data from {dbf_file}...")
        
        insert_placeholders = ", ".join(["?"] * len(table.field_names))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(table.field_names)}) VALUES ({insert_placeholders})"
        
        count = 0
        records_to_insert = []
        for record in table:
            row_data = []
            for field_name in table.field_names:
                val = record[field_name]
                if hasattr(val, 'isoformat'):
                    val = val.isoformat()
                row_data.append(val)
            
            records_to_insert.append(row_data)
            count += 1
            
            if len(records_to_insert) >= 100:
                cursor.executemany(insert_sql, records_to_insert)
                records_to_insert = []

        if records_to_insert:
            cursor.executemany(insert_sql, records_to_insert)

        conn.commit()
        conn.close()
        print(f"🎉 Success! Imported {count} suppliers into '{table_name}'.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    sync_apmas()
