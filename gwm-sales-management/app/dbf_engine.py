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
        return os.path.join(self.dbf_root, filename)

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _map_field_type(self, dbf_type):
        """Map DBF types to SQLite types."""
        mapping = {
            'N': 'REAL',
            'L': 'INTEGER',
            'D': 'TEXT',
            'M': 'TEXT',
            'C': 'TEXT'
        }
        return mapping.get(dbf_type, 'TEXT')

    def _create_table_from_dbf(self, cursor, table_name, dbf_table, primary_key=None):
        """Creates a table based on DBF structure."""
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

    def sync_stmas(self):
        """Sync STMAS.DBF to stockxp4 table with filtering."""
        dbf_file = self._get_get_dbf_path("STMAS.DBF")
        if not os.path.exists(dbf_file):
            return 0

        table = DBF(dbf_file, encoding=self.encoding)
        conn = self._get_connection()
        cursor = conn.cursor()

        self._create_table_from_dbf(cursor, "stockxp4", table)
        
        # Filtering logic: exclude expenses/incomes
        exclude_groups = ['คช', 'รด', 'เธเธ', 'เนเธฃเธ”']
        
        insert_placeholders = ", ".join(["?"] * len(table.field_names))
        insert_sql = f"INSERT INTO stockxp4 ({', '.join(table.field_names)}) VALUES ({insert_placeholders})"
        
        records_to_insert = []
        count = 0

        for record in table:
            grp = record['STKGRP'].strip()
            if grp in exclude_groups:
                continue
            
            row = [record[fn].isoformat() if hasattr(record[fn], 'isoformat') else record[fn] for fn in table.field_names]
            records_to_insert.append(row)
            count += 1

            if len(records_to_insert) >= 500:
                cursor.executemany(insert_sql, records_to_insert)
                records_to_insert = []

        if records_to_insert:
            cursor.executemany(insert_sql, records_to_insert)

        conn.commit()
        conn.close()
        return count

    def sync_stcrd(self):
        """Sync STCRD.DBF to stockcardxp4 with STKCOD filtering."""
        dbf_file = self._get_get_dbf_path("STCRD.DBF")
        if not os.path.exists(dbf_file):
            return 0

        conn = self._get_connection()
        cursor = conn.cursor()

        # Get valid STKCODs from stockxp4 first
        try:
            cursor.execute("SELECT DISTINCT STKCOD FROM stockxp4")
            valid_stkcods = set(row[0].strip() for row in cursor.fetchall())
        except sqlite3.OperationalError:
            # If stockxp4 doesn't exist, we can't filter
            valid_stkcods = None

        table = DBF(dbf_file, encoding=self.encoding)
        self._create_table_from_dbf(cursor, "stockcardxp4", table)

        insert_placeholders = ", ".join(["?"] * len(table.field_names))
        insert_sql = f"INSERT INTO stockcardxp4 ({', '.join(table.field_names)}) VALUES ({insert_placeholders})"
        
        records_to_insert = []
        count = 0

        for record in table:
            stkcod = record['STKCOD'].strip()
            if valid_stkcods is not None and stkcod not in valid_stkcods:
                continue

            row = [record[fn].isoformat() if hasattr(record[fn], 'isoformat') else record[fn] for fn in table.field_names]
            records_to_insert.append(row)
            count += 1

            if len(records_to_insert) >= 1000:
                cursor.executemany(insert_sql, records_to_insert)
                records_to_insert = []

        if records_to_insert:
            cursor.executemany(insert_sql, records_to_insert)

        conn.commit()
        conn.close()
        return count

    def sync_apmas(self):
        """Sync APMAS.DBF to master_supplier."""
        dbf_file = self._get_get_dbf_path("APMAS.DBF")
        if not os.path.exists(dbf_file):
            return 0

        table = DBF(dbf_file, encoding=self.encoding)
        conn = self._get_connection()
        cursor = conn.cursor()

        self._create_table_from_dbf(cursor, "master_supplier", table, primary_key='SUPCOD')

        insert_placeholders = ", ".join(["?"] * len(table.field_names))
        insert_sql = f"INSERT INTO master_supplier ({', '.join(table.field_names)}) VALUES ({insert_placeholders})"
        
        records_to_insert = []
        count = 0

        for record in table:
            row = [record[fn].isoformat() if hasattr(record[fn], 'isoformat') else record[fn] for fn in table.field_names]
            records_to_insert.append(row)
            count += 1

            if len(records_to_insert) >= 500:
                cursor.executemany(insert_sql, records_to_insert)
                records_to_insert = []

        if records_to_insert:
            cursor.executemany(insert_sql, records_to_insert)

        conn.commit()
        conn.close()
        return count

    def sync_aptrn(self):
        """Sync APTRN.DBF to master_aptrn."""
        dbf_file = self._get_get_dbf_path("APTRN.DBF")
        if not os.path.exists(dbf_file):
            return 0

        table = DBF(dbf_file, encoding=self.encoding)
        conn = self._get_connection()
        cursor = conn.cursor()

        self._create_table_from_dbf(cursor, "master_aptrn", table, primary_key='DOCNUM')

        insert_placeholders = ", ".join(["?"] * len(table.field_names))
        insert_sql = f"INSERT INTO master_aptrn ({', '.join(table.field_names)}) VALUES ({insert_placeholders})"
        
        records_to_insert = []
        count = 0

        for record in table:
            row = [record[fn].isoformat() if hasattr(record[fn], 'isoformat') else record[fn] for fn in table.field_names]
            records_to_insert.append(row)
            count += 1

            if len(records_to_insert) >= 500:
                cursor.executemany(insert_sql, records_to_insert)
                records_to_insert = []

        if records_to_insert:
            cursor.executemany(insert_sql, records_to_insert)

        conn.commit()
        conn.close()
        return count

    def sync_all(self):
        """Sync all DBF tables and return results."""
        results = {
            'stmas': self.sync_stmas(),
            'stcrd': self.sync_stcrd(),
            'apmas': self.sync_apmas(),
            'aptrn': self.sync_aptrn()
        }
        return results

    def _get_get_dbf_path(self, filename): # Small fix for method name typo
        return os.path.join(self.dbf_root, filename)
