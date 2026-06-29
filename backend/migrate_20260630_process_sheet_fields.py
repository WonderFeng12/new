"""迁移脚本：为 process_sheet 和 process_sheet_item 添加新字段

Usage: python migrate_20260630_process_sheet_fields.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Add confirm_user_ids to process_sheet
    try:
        conn.execute(text(
            "ALTER TABLE process_sheet ADD COLUMN confirm_user_ids JSON DEFAULT NULL "
            "COMMENT '工艺单指定的内部确认人用户ID列表'"
        ))
        print("  ✓ Added confirm_user_ids to process_sheet")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("  - confirm_user_ids already exists, skipping")
        else:
            print(f"  ✗ Error: {e}")

    # Add pressed_image_name to process_sheet_item
    try:
        conn.execute(text(
            "ALTER TABLE process_sheet_item ADD COLUMN pressed_image_name VARCHAR(200) DEFAULT NULL "
            "COMMENT '压花图片原始文件名'"
        ))
        print("  ✓ Added pressed_image_name to process_sheet_item")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("  - pressed_image_name already exists, skipping")
        else:
            print(f"  ✗ Error: {e}")

    conn.commit()
    print("\nDone! Fields added successfully.")
