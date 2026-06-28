"""Migration: Add production workflow tables (process_step, assignee, log, config) + columns"""
from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    # ─── 1. process_step ────────────────────────────────────────────────────
    print("Creating process_step table...")
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS process_step (
            id INT AUTO_INCREMENT PRIMARY KEY,
            step_code VARCHAR(30) NOT NULL UNIQUE,
            step_name VARCHAR(50) NOT NULL,
            sort_order INT NOT NULL DEFAULT 0,
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))

    # Seed default data
    conn.execute(text("""
        INSERT IGNORE INTO process_step (step_code, step_name, sort_order)
        VALUES
            ('yarn_plan', '坯布计划', 1),
            ('weaving', '织造', 2),
            ('setting', '定型', 3),
            ('brushing', '刷毛烫光', 4),
            ('printing', '印花', 5),
            ('sewing', '成品缝制', 6),
            ('completed', '成品完成', 7)
    """))
    print("  Seeded 7 default process steps.")

    # ─── 2. process_step_assignee ───────────────────────────────────────────
    print("Creating process_step_assignee table...")
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS process_step_assignee (
            id INT AUTO_INCREMENT PRIMARY KEY,
            process_step_id INT NOT NULL,
            user_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_step_user (process_step_id, user_id),
            CONSTRAINT fk_assignee_step FOREIGN KEY (process_step_id)
                REFERENCES process_step(id) ON DELETE CASCADE,
            CONSTRAINT fk_assignee_user FOREIGN KEY (user_id)
                REFERENCES user(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))

    # ─── 3. production_log ──────────────────────────────────────────────────
    print("Creating production_log table...")
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS production_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            contract_id INT NOT NULL,
            contract_item_id INT NULL,
            from_status VARCHAR(30) DEFAULT NULL,
            to_status VARCHAR(30) NOT NULL,
            operation_type ENUM('推进','回退','返工','取消','确认','坯布下达') NOT NULL,
            operator_id INT NOT NULL,
            remark TEXT DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            notify_status VARCHAR(20) DEFAULT 'pending',
            INDEX idx_item_created (contract_item_id, created_at),
            INDEX idx_contract_created (contract_id, created_at),
            CONSTRAINT fk_log_contract FOREIGN KEY (contract_id)
                REFERENCES contract(id) ON DELETE CASCADE,
            CONSTRAINT fk_log_contract_item FOREIGN KEY (contract_item_id)
                REFERENCES contract_item(id) ON DELETE SET NULL,
            CONSTRAINT fk_log_operator FOREIGN KEY (operator_id)
                REFERENCES user(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))

    # ─── 4. system_config ───────────────────────────────────────────────────
    print("Creating system_config table...")
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS system_config (
            id INT AUTO_INCREMENT PRIMARY KEY,
            config_key VARCHAR(100) NOT NULL UNIQUE,
            config_value TEXT DEFAULT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))

    # ─── 5. ALTER contract_item ─────────────────────────────────────────────
    print("Altering contract_item table...")
    try:
        conn.execute(text("ALTER TABLE contract_item ADD COLUMN production_status VARCHAR(30) NULL"))
        print("  Added production_status")
    except Exception as e:
        print(f"  production_status: {e}")

    try:
        conn.execute(text("ALTER TABLE contract_item ADD COLUMN yarn_plan_user_id INT NULL"))
        print("  Added yarn_plan_user_id")
    except Exception as e:
        print(f"  yarn_plan_user_id: {e}")

    try:
        conn.execute(text("ALTER TABLE contract_item ADD COLUMN cancel_quantities JSON NULL"))
        print("  Added cancel_quantities")
    except Exception as e:
        print(f"  cancel_quantities: {e}")

    try:
        conn.execute(text("ALTER TABLE contract_item ADD COLUMN cancel_reason TEXT NULL"))
        print("  Added cancel_reason")
    except Exception as e:
        print(f"  cancel_reason: {e}")

    # ─── 6. ALTER user ──────────────────────────────────────────────────────
    print("Altering user table...")
    try:
        conn.execute(text("ALTER TABLE user ADD COLUMN wecom_userid VARCHAR(100) NULL"))
        print("  Added wecom_userid")
    except Exception as e:
        print(f"  wecom_userid: {e}")

    conn.commit()

print("\nMigration complete!")
