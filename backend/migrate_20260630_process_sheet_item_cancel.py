"""迁移脚本：为 process_sheet_item 添加取消相关字段

Usage: python migrate_20260630_process_sheet_item_cancel.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Add cancel_reason to process_sheet_item
    try:
        conn.execute(text(
            "ALTER TABLE process_sheet_item ADD COLUMN cancel_reason TEXT NULL "
            "COMMENT '取消原因'"
        ))
        print("  ✓ Added cancel_reason to process_sheet_item")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("  - cancel_reason already exists, skipping")
        else:
            print(f"  ✗ Error: {e}")

    # Add cancel_quantities to process_sheet_item
    try:
        conn.execute(text(
            "ALTER TABLE process_sheet_item ADD COLUMN cancel_quantities JSON DEFAULT NULL "
            "COMMENT '取消快照(含 cancelled_timestamp, restored 等)'"
        ))
        print("  ✓ Added cancel_quantities to process_sheet_item")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("  - cancel_quantities already exists, skipping")
        else:
            print(f"  ✗ Error: {e}")

    conn.commit()
    print("  ✓ Migration complete")
