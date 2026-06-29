"""
Migration: Add process_sheet_id to production_log, add '修改' to operation_type enum.
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
    # Add process_sheet_id column
    try:
        cur.execute("ALTER TABLE production_log ADD COLUMN process_sheet_id INT NULL COMMENT '关联工艺单ID'")
    except pymysql.err.OperationalError as e:
        if "Duplicate column" not in str(e):
            raise

    # Add index for process_sheet_id
    try:
        cur.execute("ALTER TABLE production_log ADD INDEX idx_process_sheet_log (process_sheet_id, created_at)")
    except pymysql.err.OperationalError as e:
        if "Duplicate key name" not in str(e):
            raise

    # Update ENUM to include '修改'
    cur.execute("ALTER TABLE production_log MODIFY COLUMN operation_type ENUM('推进','回退','返工','取消','确认','坯布下达','重新编辑','修改') NOT NULL")

conn.commit()
conn.close()
print("Migration complete: added process_sheet_id and '修改' to operation_type")
