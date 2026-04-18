import sqlite3
from dbfread import DBF
import os

def sync_aptrn():
    dbf_file = "dbf/APTRN.DBF"
    sqlite_db = "car_management.db"
    table_name = "master_aptrn"
    
    if not os.path.exists(dbf_file):
        print(f"❌ Error: {dbf_file} not found.")
        return

    table = DBF(dbf_file, encoding='cp874')
    
    fields = []
    for field in table.fields:
        name = field.name
        typ = field.type
        field_def = name
        if typ == 'N': field_def += " REAL"
        elif typ == 'L': field_def += " INTEGER"
        else: field_def += " TEXT"
        if name == 'DOCNUM': field_def += " PRIMARY KEY"
        fields.append(field_def)
    
    try:
        conn = sqlite3.connect(sqlite_db)
        cursor = conn.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(f"CREATE TABLE {table_name} ({', '.join(fields)})")
        
        insert_placeholders = ", ".join(["?"] * len(table.field_names))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(table.field_names)}) VALUES ({insert_placeholders})"
        
        records = []
        for record in table:
            row = [record[fn].isoformat() if hasattr(record[fn], 'isoformat') else record[fn] for fn in table.field_names]
            records.append(row)
            if len(records) >= 500:
                cursor.executemany(insert_sql, records)
                records = []
        if records: cursor.executemany(insert_sql, records)
        
        conn.commit(); conn.close()
        print(f"✅ Table '{table_name}' ready with {len(table)} records.")
    except Exception as e: print(f"❌ Error: {e}")

if __name__ == "__main__":
    sync_aptrn()
