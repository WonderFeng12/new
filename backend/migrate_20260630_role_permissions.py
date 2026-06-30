"""Seed the role_permissions config with default values matching current hardcoded behavior."""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from app.database import SessionLocal
from app.models.system_config import SystemConfig

DEFAULT_ROLES = {
    "业务员": [
        "contract:view", "contract:create", "contract:edit",
        "contract:delete", "contract:request_confirm",
        "contract:generate_confirm_image", "contract:view_versions",
        "sheet:view", "sheet:mark_version",
        "sheet:generate_confirm_link",
        "production:cancel",
        "basic_data:view", "customer:manage", "spec:manage",
    ],
    "销售经理": [
        "contract:view", "contract:create", "contract:edit",
        "contract:delete", "contract:request_confirm",
        "contract:manual_confirm", "contract:reopen_edit",
        "contract:generate_confirm_image", "contract:view_versions",
        "contract:push_down",
        "sheet:view", "sheet:create", "sheet:edit",
        "sheet:delete", "sheet:mark_version",
        "sheet:internal_confirm", "sheet:force_confirm",
        "sheet:set_confirm_users", "sheet:dispatch", "sheet:print",
        "sheet:reopen_edit", "sheet:generate_confirm_link",
        "production:manage_steps", "production:advance",
        "production:rollback", "production:rework",
        "production:cancel", "production:restore",
        "production:yarn_plan",
        "basic_data:view", "basic_data:manage",
        "customer:manage", "spec:manage",
        "settings:user:view", "settings:user:manage",
        "settings:webhook:view", "settings:webhook:manage",
        "settings:permissions:manage",
    ],
    "生产专员": [
        "contract:push_down",
        "sheet:view", "sheet:create", "sheet:edit",
        "sheet:delete", "sheet:mark_version",
        "sheet:internal_confirm", "sheet:dispatch", "sheet:print",
        "sheet:reopen_edit", "sheet:generate_confirm_link",
        "production:manage_steps", "production:advance",
        "production:rollback", "production:rework",
        "production:cancel", "production:restore",
        "production:yarn_plan",
        "basic_data:view", "basic_data:manage",
        "settings:user:view",
    ],
    "外协人员": [
        "sheet:view",
        "production:advance",
    ],
    "管理员": [
        "contract:view", "contract:create", "contract:edit",
        "contract:delete", "contract:request_confirm",
        "contract:manual_confirm", "contract:reopen_edit",
        "contract:generate_confirm_image", "contract:view_versions",
        "contract:push_down",
        "sheet:view", "sheet:create", "sheet:edit",
        "sheet:delete", "sheet:mark_version",
        "sheet:internal_confirm", "sheet:force_confirm",
        "sheet:set_confirm_users", "sheet:dispatch", "sheet:print",
        "sheet:reopen_edit", "sheet:generate_confirm_link",
        "production:manage_steps", "production:advance",
        "production:rollback", "production:rework",
        "production:cancel", "production:restore",
        "production:yarn_plan",
        "basic_data:view", "basic_data:manage",
        "customer:manage", "spec:manage",
        "settings:user:view", "settings:user:manage",
        "settings:webhook:view", "settings:webhook:manage",
        "settings:permissions:manage",
    ],
}

db = SessionLocal()
try:
    existing = db.query(SystemConfig).filter(
        SystemConfig.config_key == "role_permissions"
    ).first()
    if existing:
        print("role_permissions already exists, updating...")
    else:
        existing = SystemConfig(config_key="role_permissions", config_value="")
        db.add(existing)

    existing.config_value = json.dumps({"roles": DEFAULT_ROLES}, ensure_ascii=False)
    db.commit()
    print("role_permissions seeded successfully")
    print(f"  业务员: {len(DEFAULT_ROLES['业务员'])} permissions")
    print(f"  销售经理: {len(DEFAULT_ROLES['销售经理'])} permissions")
    print(f"  生产专员: {len(DEFAULT_ROLES['生产专员'])} permissions")
    print(f"  外协人员: {len(DEFAULT_ROLES['外协人员'])} permissions")
    print(f"  管理员: {len(DEFAULT_ROLES['管理员'])} permissions")
finally:
    db.close()
