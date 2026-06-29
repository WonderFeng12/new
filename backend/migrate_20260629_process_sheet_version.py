"""
Migration: Change process_sheet.confirm_version_no from INT to DECIMAL(10,2).
Add version_marked and version_note columns.
"""
import pymysql

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="root",
    database="huazhi",
    charset="utf8mb4",
)

with conn.cursor() as cur:
    # Change column type to DECIMAL, default 0
    cur.execute("ALTER TABLE process_sheet MODIFY COLUMN confirm_version_no DECIMAL(10,2) NOT NULL DEFAULT 0")

    # Reset existing 草稿 records to 0 (no version in draft)
    cur.execute("UPDATE process_sheet SET confirm_version_no = 0 WHERE status = '草稿'")

    # Add version_marked column
    try:
        cur.execute("ALTER TABLE process_sheet ADD COLUMN version_marked TINYINT(1) DEFAULT 0 COMMENT '是否已标记版本用于客户沟通'")
    except pymysql.err.OperationalError as e:
        if "Duplicate column" not in str(e):
            raise

    # Add version_note column
    try:
        cur.execute("ALTER TABLE process_sheet ADD COLUMN version_note TEXT NULL COMMENT '版本标记说明（更改原因）'")
    except pymysql.err.OperationalError as e:
        if "Duplicate column" not in str(e):
            raise

conn.commit()
conn.close()
print("Migration complete: confirm_version_no DECIMAL, version_marked, version_note added")
