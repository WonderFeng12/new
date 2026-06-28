"""Migration: create process_sheet_item table, add detail_data to process_sheet.

Usage: python migrate_20260628_process_sheet_item.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models import ProcessSheetItem  # noqa: ensure registered
from sqlalchemy import inspect, text


def run():
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    # Create process_sheet_item table if not exists
    if "process_sheet_item" not in tables:
        ProcessSheetItem.__table__.create(engine)
        print("Created table: process_sheet_item")
    else:
        print("Table process_sheet_item already exists")

    # Add detail_data column to process_sheet if not exists
    if "process_sheet" in tables:
        cols = [c["name"] for c in inspector.get_columns("process_sheet")]
        if "detail_data" not in cols:
            with engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE process_sheet ADD COLUMN detail_data JSON "
                    "COMMENT '生产详情: tech_notes, accessories, pack_notes, box_notes, binding, emboss etc.'"
                ))
                conn.commit()
            print("Added column: process_sheet.detail_data")
        else:
            print("Column process_sheet.detail_data already exists")
    else:
        print("Table process_sheet does not exist, skipping column add")

    print("Migration complete")


if __name__ == "__main__":
    run()
