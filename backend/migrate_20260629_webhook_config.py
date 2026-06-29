"""迁移：创建 webhook_config 表"""
import sys
from sqlalchemy import create_engine, inspect, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)

if not inspector.has_table("webhook_config"):
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE webhook_config (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE COMMENT 'webhook名称',
                webhook_url TEXT NOT NULL COMMENT '企业微信群机器人URL',
                is_enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='企业微信webhook配置';
        """))
        conn.commit()
    print("✓ 已创建 webhook_config 表")
else:
    print("= webhook_config 表已存在")

# Migrate existing data from system_config if present
with engine.connect() as conn:
    result = conn.execute(text("SELECT config_value FROM system_config WHERE config_key = 'wecom_webhook_url'"))
    row = result.fetchone()
    if row and row[0]:
        result = conn.execute(text("SELECT COUNT(*) FROM webhook_config WHERE name = '合同通知'"))
        if result.scalar() == 0:
            conn.execute(text(
                "INSERT IGNORE INTO webhook_config (name, webhook_url, is_enabled) VALUES (:name, :url, :enabled)"
            ), {"name": "合同通知", "url": row[0], "enabled": True})
            conn.commit()
            print("✓ 已从 system_config 迁移合同通知 webhook 配置")

print("迁移完成")
