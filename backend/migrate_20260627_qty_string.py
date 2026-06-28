"""Migration: Change accessory_qty_2/3/4 from DECIMAL to VARCHAR"""
from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE contract MODIFY accessory_qty_2 VARCHAR(100) DEFAULT NULL"))
        print("Changed accessory_qty_2 to VARCHAR(100)")
    except Exception as e:
        print(f"accessory_qty_2: {e}")

    try:
        conn.execute(text("ALTER TABLE contract MODIFY accessory_qty_3 VARCHAR(100) DEFAULT NULL"))
        print("Changed accessory_qty_3 to VARCHAR(100)")
    except Exception as e:
        print(f"accessory_qty_3: {e}")

    try:
        conn.execute(text("ALTER TABLE contract MODIFY accessory_qty_4 VARCHAR(100) DEFAULT NULL"))
        print("Changed accessory_qty_4 to VARCHAR(100)")
    except Exception as e:
        print(f"accessory_qty_4: {e}")

    conn.commit()

print("Migration complete!")
