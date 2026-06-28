"""V2 Migration: Add confirm fields to process_sheet, make production_log.operator_id nullable.

Usage: python migrate_v2_process_sheet.py
"""
from app.database import engine
from sqlalchemy import inspect, text


def run():
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if "process_sheet" in tables:
        cols = [c["name"] for c in inspector.get_columns("process_sheet")]

        # Step 1: Change status from ENUM to VARCHAR to accept new values
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE process_sheet MODIFY COLUMN status VARCHAR(20) NOT NULL DEFAULT '草稿'"
            ))
            conn.commit()
        print("Migrated: process_sheet.status -> VARCHAR(20)")

        # Step 2: Add confirm_token column
        if "confirm_token" not in cols:
            with engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE process_sheet ADD COLUMN confirm_token VARCHAR(36) UNIQUE"
                ))
                conn.commit()
            print("Added: process_sheet.confirm_token")
        else:
            print("Skipped: process_sheet.confirm_token already exists")

        # Step 3: Add customer_comment column
        if "customer_comment" not in cols:
            with engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE process_sheet ADD COLUMN customer_comment TEXT"
                ))
                conn.commit()
            print("Added: process_sheet.customer_comment")
        else:
            print("Skipped: process_sheet.customer_comment already exists")
    else:
        print("Table process_sheet does not exist, skipping")

    # Step 4: Make production_log.operator_id nullable
    if "production_log" in tables:
        from sqlalchemy import inspect as sa_inspect
        pl_cols = [c["name"] for c in inspector.get_columns("production_log")]
        if "operator_id" in pl_cols:
            with engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE production_log MODIFY COLUMN operator_id INT NULL"
                ))
                conn.commit()
            print("Migrated: production_log.operator_id -> nullable")
        else:
            print("Skipped: production_log.operator_id not found")
    else:
        print("Table production_log does not exist, skipping")

    print("Migration complete")


if __name__ == "__main__":
    run()
