"""Migration: Add delivery_date to contract_item"""
from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE contract_item ADD COLUMN delivery_date DATE"))
        print("Added delivery_date to contract_item")
    except Exception as e:
        print(f"delivery_date: {e}")

    conn.commit()

print("Migration complete!")
