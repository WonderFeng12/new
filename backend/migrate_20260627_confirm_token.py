"""Add confirm_token and customer_comment to contract table"""
import pymysql

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="root",
    database="huazhi",
    charset="utf8mb4",
)
cur = conn.cursor()

cur.execute("ALTER TABLE contract ADD COLUMN confirm_token VARCHAR(36) UNIQUE NULL AFTER latest_confirm_version")
cur.execute("ALTER TABLE contract ADD COLUMN customer_comment TEXT NULL AFTER confirm_token")
cur.execute("CREATE INDEX idx_confirm_token ON contract(confirm_token)")

conn.commit()
cur.close()
conn.close()
print("Migration done: added confirm_token and customer_comment")
