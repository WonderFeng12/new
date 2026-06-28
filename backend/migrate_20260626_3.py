"""Migration: Add pattern_count and pattern_data to contract_item"""
from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE contract_item ADD COLUMN pattern_count INT DEFAULT 0"))
        print("Added pattern_count to contract_item")
    except Exception as e:
        print(f"pattern_count: {e}")

    try:
        conn.execute(text("ALTER TABLE contract_item ADD COLUMN pattern_data JSON"))
        print("Added pattern_data to contract_item")
    except Exception as e:
        print(f"pattern_data: {e}")

    conn.commit()

print("Migration complete!")
