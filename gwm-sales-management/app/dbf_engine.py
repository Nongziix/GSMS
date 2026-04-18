import os
import sqlite3
from dbfread import DBF
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DBFSyncEngine:
    def __init__(self):
        self.db_path = os.getenv('DB_PATH', 'data/database/GSMS_data.db')
        self.dbf_root = os.getenv('EXPRESS_DBF_PATH', 'data/raw_express/')
        self.encoding = 'cp874'

    def _get_dbf_path(self, filename):
        """คืนค่า path เต็มของไฟล์ DBF"""
        return os.path.join(self.dbf_root, filename)

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _map_field_type(self, dbf_type):
        """Map DBF field types → SQLite types"""
        mapping = {
            'N': 'REAL',
            'L': 'INTEGER',
            'D': 'TEXT',
            'M': 'TEXT',
            'C': 'TEXT',
        }
        return mapping.get(dbf_type, 'TEXT')

    def _create_table_from_dbf(self, cursor, table_name, dbf_table, primary_key=None):
        """สร้างตาราง SQLite ตามโครงสร้างของไฟล์ DBF"""
        fields = []
        for field in dbf_table.fields:
            name = field.name
            typ = self._map_field_type(field.type)
            field_def = f"{name} {typ}"
            if primary_key and name == primary_key:
                field_def += " PRIMARY KEY"
            fields.append(field_def)

        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(f"CREATE TABLE {table_name} ({', '.join(fields)})")

    def _sync_table(self, dbf_filename, table_name, primary_key=None,
                    filter_fn=None, batch_size=500):
        """
        Helper กลางสำหรับ sync DBF → SQLite
        ลด code ซ้ำระหว่าง sync_stmas / sync_stcrd / sync_apmas / sync_aptrn

        Args:
            dbf_filename : ชื่อไฟล์ DBF เช่น 'STMAS.DBF'
            table_name   : ชื่อตาราง SQLite ปลายทาง
            primary_key  : ชื่อ field ที่เป็น PK (ถ้ามี)
            filter_fn    : ฟังก์ชัน (record) -> bool  False = ข้ามแถวนั้น
            batch_size   : จำนวนแถวต่อ batch insert
        Returns:
            จำนวนแถวที่ sync สำเร็จ
        """
        dbf_file = self._get_dbf_path(dbf_filename)
        if not os.path.exists(dbf_file):
            return 0

        table = DBF(dbf_file, encoding=self.encoding)
        conn = self._get_connection()
        cursor = conn.cursor()

        self._create_table_from_dbf(cursor, table_name, table, primary_key)

        placeholders = ", ".join(["?"] * len(table.field_names))
        insert_sql = (
            f"INSERT INTO {table_name} "
            f"({', '.join(table.field_names)}) "
            f"VALUES ({placeholders})"
        )

        batch = []
        count = 0

        for record in table:
            if filter_fn and not filter_fn(record):
                continue

            row = [
                v.isoformat() if hasattr(v, 'isoformat') else v
                for v in (record[fn] for fn in table.field_names)
            ]
            batch.append(row)
            count += 1

            if len(batch) >= batch_size:
                cursor.executemany(insert_sql, batch)
                batch = []

        if batch:
            cursor.executemany(insert_sql, batch)

        conn.commit()
        conn.close()
        return count

    # ------------------------------------------------------------------
    # Public sync methods
    # ------------------------------------------------------------------

    def sync_stmas(self):
        """Sync STMAS.DBF → stockxp4 (ตัดกลุ่ม คช/รด ออก)"""
        exclude = {'คช', 'รด', 'เธเธ', 'เนเธฃเธ"'}
        return self._sync_table(
            'STMAS.DBF',
            'stockxp4',
            filter_fn=lambda r: r['STKGRP'].strip() not in exclude,
        )

    def sync_stcrd(self):
        """Sync STCRD.DBF → stockcardxp4 (กรองเฉพาะ STKCOD ที่มีใน stockxp4)"""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT DISTINCT STKCOD FROM stockxp4").fetchall()
            valid_stkcods = {row[0].strip() for row in rows}
        except sqlite3.OperationalError:
            # stockxp4 ยังไม่มี — sync โดยไม่กรอง
            valid_stkcods = None
        finally:
            conn.close()

        filter_fn = (
            (lambda r: r['STKCOD'].strip() in valid_stkcods)
            if valid_stkcods is not None
            else None
        )
        return self._sync_table(
            'STCRD.DBF',
            'stockcardxp4',
            filter_fn=filter_fn,
            batch_size=1000,
        )

    def sync_apmas(self):
        """Sync APMAS.DBF → master_supplier"""
        return self._sync_table(
            'APMAS.DBF',
            'master_supplier',
            primary_key='SUPCOD',
        )

    def sync_aptrn(self):
        """Sync APTRN.DBF → master_aptrn"""
        return self._sync_table(
            'APTRN.DBF',
            'master_aptrn',
            primary_key='DOCNUM',
        )

    def sync_all(self):
        """Sync ทุกตาราง แล้วคืนผลลัพธ์จำนวนแถว"""
        return {
            'stmas': self.sync_stmas(),
            'stcrd': self.sync_stcrd(),
            'apmas': self.sync_apmas(),
            'aptrn': self.sync_aptrn(),
        }
