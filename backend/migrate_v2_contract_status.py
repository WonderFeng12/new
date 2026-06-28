"""Migrate contract table for V2 workflow: status '保存' -> '确认', drop V1 fields"""
import pymysql

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="root",
    database="huazhi",
    charset="utf8mb4",
)
cur = conn.cursor()

# Step 1: Change status from ENUM to VARCHAR to avoid ENUM issues
cur.execute("ALTER TABLE contract MODIFY COLUMN status VARCHAR(20) NOT NULL DEFAULT '草稿'")

# Step 2: Rename '保存' to '确认'
cur.execute("UPDATE contract SET status = '确认' WHERE status = '保存'")

# Step 3: Drop V1-only fields
cur.execute("ALTER TABLE contract DROP COLUMN confirm_token")
cur.execute("ALTER TABLE contract DROP COLUMN customer_comment")
cur.execute("ALTER TABLE contract DROP COLUMN latest_confirm_version")

conn.commit()
cur.close()
conn.close()
print("Migration done: status '保存' -> '确认', dropped confirm_token, customer_comment, latest_confirm_version")
