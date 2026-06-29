"""
Migration: Add confirm_requested_at and last_reminded_at to contract table.
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
    try:
        cur.execute("ALTER TABLE contract ADD COLUMN confirm_requested_at DATETIME NULL COMMENT '最近一次请求确认的时间'")
    except pymysql.err.OperationalError as e:
        if "Duplicate column" not in str(e):
            raise

    try:
        cur.execute("ALTER TABLE contract ADD COLUMN last_reminded_at DATETIME NULL COMMENT '最近一次发送催办提醒的时间'")
    except pymysql.err.OperationalError as e:
        if "Duplicate column" not in str(e):
            raise

conn.commit()
conn.close()
print("Migration complete: added confirm_requested_at, last_reminded_at")
