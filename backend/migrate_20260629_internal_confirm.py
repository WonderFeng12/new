"""Migration: Add customer_confirmed, internal_confirm_required, internal_confirmed_users to process_sheet."""
import pymysql
from app.config import settings
DATABASE_URL = settings.DATABASE_URL

# Parse DATABASE_URL: mysql+pymysql://user:pass@host:port/db
import re
m = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)', DATABASE_URL)
if not m:
    raise ValueError("Cannot parse DATABASE_URL")

user, password, host, port, dbname = m.groups()

conn = pymysql.connect(host=host, port=int(port), user=user, password=password, database=dbname, charset='utf8mb4')
cursor = conn.cursor()

try:
    # Check if columns already exist
    cursor.execute("SHOW COLUMNS FROM process_sheet LIKE 'customer_confirmed'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE process_sheet ADD COLUMN customer_confirmed TINYINT(1) DEFAULT 0 COMMENT '客户是否已确认'")
        print("Added column: customer_confirmed")
    else:
        print("Column customer_confirmed already exists, skipping")

    cursor.execute("SHOW COLUMNS FROM process_sheet LIKE 'internal_confirm_required'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE process_sheet ADD COLUMN internal_confirm_required INT DEFAULT 1 COMMENT '内部确认所需人数'")
        print("Added column: internal_confirm_required")
    else:
        print("Column internal_confirm_required already exists, skipping")

    cursor.execute("SHOW COLUMNS FROM process_sheet LIKE 'internal_confirmed_users'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE process_sheet ADD COLUMN internal_confirmed_users JSON DEFAULT (JSON_ARRAY()) COMMENT '已内部确认的用户ID列表'")
        print("Added column: internal_confirmed_users")
    else:
        print("Column internal_confirmed_users already exists, skipping")

    # Migrate existing records: status='已确认' → customer_confirmed=1, confirm_version_no=0.5
    cursor.execute("UPDATE process_sheet SET customer_confirmed=1, confirm_version_no=0.5 WHERE status='已确认' AND customer_confirmed=0")
    print(f"Migrated {cursor.rowcount} existing records from status='已确认'")

    conn.commit()
    print("Migration completed successfully")
except Exception as e:
    conn.rollback()
    print(f"Migration failed: {e}")
    raise
finally:
    cursor.close()
    conn.close()
