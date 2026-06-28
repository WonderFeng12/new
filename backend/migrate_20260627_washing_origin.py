"""Migration: Add washing_labels and origin_labels JSON columns to contract"""
from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    try:
        conn.execute(text("""
            ALTER TABLE contract
            ADD COLUMN washing_labels JSON DEFAULT NULL AFTER accessory_qty_6,
            ADD COLUMN origin_labels JSON DEFAULT NULL AFTER washing_labels
        """))
        print("Added washing_labels and origin_labels columns")
    except Exception as e:
        print(f"migration warning: {e}")

    conn.commit()

print("Migration complete!")
