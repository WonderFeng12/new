"""迁移脚本：pressed_image / pressed_image_name 从 VARCHAR 改为 JSON，支持多图

Usage: python migrate_20260701_pressed_images_json.py
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Read existing pressed_image values before altering
    rows = conn.execute(text(
        "SELECT id, pressed_image, pressed_image_name FROM process_sheet_item"
    )).fetchall()

    # Clear empty strings to NULL (invalid JSON)
    conn.execute(text(
        "UPDATE process_sheet_item SET pressed_image = NULL WHERE pressed_image = ''"
    ))
    conn.execute(text(
        "UPDATE process_sheet_item SET pressed_image_name = NULL WHERE pressed_image_name = ''"
    ))
    print("  ✓ Cleared empty strings to NULL")

    # Alter columns to JSON
    conn.execute(text(
        "ALTER TABLE process_sheet_item MODIFY pressed_image JSON NULL "
        "COMMENT '压花图片URL列表（多图）'"
    ))
    print("  ✓ Changed pressed_image to JSON")

    conn.execute(text(
        "ALTER TABLE process_sheet_item MODIFY pressed_image_name JSON NULL "
        "COMMENT '压花图片原始文件名列表'"
    ))
    print("  ✓ Changed pressed_image_name to JSON")

    # Convert existing single values to JSON arrays
    updated = 0
    for row in rows:
        pid, img, name = row
        new_img = None
        new_name = None
        if img:
            try:
                parsed = json.loads(img)
                if isinstance(parsed, list):
                    continue  # already JSON array
            except (json.JSONDecodeError, TypeError):
                pass
            new_img = json.dumps([img], ensure_ascii=False)
        if name:
            try:
                parsed = json.loads(name)
                if isinstance(parsed, list):
                    continue
            except (json.JSONDecodeError, TypeError):
                pass
            new_name = json.dumps([name], ensure_ascii=False)
        if new_img is not None or new_name is not None:
            conn.execute(
                text("UPDATE process_sheet_item SET pressed_image = :img, pressed_image_name = :nm WHERE id = :id"),
                {"img": new_img, "nm": new_name, "id": pid}
            )
            updated += 1

    conn.commit()
    print(f"  ✓ Converted {updated} rows to JSON arrays")
    print("  ✓ Migration complete")
