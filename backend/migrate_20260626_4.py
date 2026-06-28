"""Migration: Create basic_data table"""
from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    try:
        conn.execute(text("""
            CREATE TABLE basic_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(50) NOT NULL,
                code VARCHAR(100) NOT NULL,
                value VARCHAR(200),
                sort_order INT DEFAULT 0,
                created_at DATETIME,
                updated_at DATETIME
            )
        """))
        print("Created basic_data table")

        conn.execute(text("""
            INSERT INTO basic_data (category, code, value, sort_order)
            VALUES
            ('packaging_type', '纸箱', '纸箱', 1),
            ('packaging_type', '抽真空', '抽真空', 2),
            ('packaging_type', '压缩包', '压缩包', 3),
            ('packaging_type', '打卷面料', '打卷面料', 4)
        """))
        print("Seeded packaging types")
    except Exception as e:
        print(f"basic_data: {e}")

    conn.commit()

print("Migration complete!")
