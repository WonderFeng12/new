"""Migration: Add spec_id, is_pressed, packaging_type to contract_item; make contract.spec_id nullable"""
from sqlalchemy import text
from app.database import engine, Base

with engine.connect() as conn:
    # Add spec_id to contract_item
    try:
        conn.execute(text("ALTER TABLE contract_item ADD COLUMN spec_id INT"))
        conn.execute(text("ALTER TABLE contract_item ADD FOREIGN KEY (spec_id) REFERENCES spec(id)"))
        print("Added spec_id to contract_item")
    except Exception as e:
        print(f"spec_id: {e}")

    # Add is_pressed to contract_item
    try:
        conn.execute(text("ALTER TABLE contract_item ADD COLUMN is_pressed TINYINT(1) DEFAULT 0"))
        print("Added is_pressed to contract_item")
    except Exception as e:
        print(f"is_pressed: {e}")

    # Add packaging_type to contract_item
    try:
        conn.execute(text("ALTER TABLE contract_item ADD COLUMN packaging_type VARCHAR(50)"))
        print("Added packaging_type to contract_item")
    except Exception as e:
        print(f"packaging_type: {e}")

    # Make contract.spec_id nullable
    try:
        conn.execute(text("ALTER TABLE contract MODIFY COLUMN spec_id INT NULL"))
        print("Made contract.spec_id nullable")
    except Exception as e:
        print(f"contract.spec_id: {e}")

    conn.commit()

print("Migration complete!")
