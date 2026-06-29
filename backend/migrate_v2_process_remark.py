"""Add process_remark to process_sheet_item and yarn_plan_no to contract_item."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine, Base
from sqlalchemy import text

with engine.connect() as conn:
    # Check if column exists before adding
    result = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='process_sheet_item' AND COLUMN_NAME='process_remark'"
    ))
    if result.scalar() == 0:
        conn.execute(text(
            "ALTER TABLE process_sheet_item ADD COLUMN process_remark TEXT COMMENT '工艺备注（下推时填写）'"
        ))
        print("Added process_remark to process_sheet_item")
    else:
        print("process_remark already exists")

    result = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='contract_item' AND COLUMN_NAME='yarn_plan_no'"
    ))
    if result.scalar() == 0:
        conn.execute(text(
            "ALTER TABLE contract_item ADD COLUMN yarn_plan_no VARCHAR(100) COMMENT '坯布计划单号'"
        ))
        print("Added yarn_plan_no to contract_item")
    else:
        print("yarn_plan_no already exists")

    conn.commit()
print("Migration complete")
