"""Permission service - reads role->permissions mapping from system_config."""
import json
import logging
from sqlalchemy.orm import Session
from app.models.system_config import SystemConfig

_CONFIG_KEY = "role_permissions"
_logger = logging.getLogger(__name__)

# Module-level cache: {role_name: [perm1, perm2, ...]}
_cache = None


def _load_permissions(db: Session) -> dict:
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == _CONFIG_KEY
    ).first()
    if not config or not config.config_value:
        return {}
    try:
        data = json.loads(config.config_value)
        return data.get("roles", {})
    except (json.JSONDecodeError, TypeError):
        _logger.error("Invalid role_permissions config value")
        return {}


def _ensure_cache(db: Session) -> dict:
    global _cache
    if _cache is None:
        _cache = _load_permissions(db)
    return _cache


def check_permission(db: Session, role: str, permission: str) -> bool:
    perm_map = _ensure_cache(db)
    role_perms = perm_map.get(role, [])
    return permission in role_perms


def invalidate_cache():
    global _cache
    _cache = None


def reload_cache(db: Session) -> dict:
    global _cache
    _cache = _load_permissions(db)
    return _cache


def get_all_permissions(db: Session) -> dict:
    return _ensure_cache(db)


def get_all_permission_definitions() -> list:
    return [
        {
            "module": "合同管理",
            "module_key": "contract",
            "permissions": [
                {"key": "contract:view", "label": "查看合同"},
                {"key": "contract:create", "label": "新建合同"},
                {"key": "contract:edit", "label": "编辑合同（草稿状态）"},
                {"key": "contract:delete", "label": "删除合同"},
                {"key": "contract:request_confirm", "label": "请求确认"},
                {"key": "contract:manual_confirm", "label": "手动确认"},
                {"key": "contract:reopen_edit", "label": "重新打开编辑"},
                {"key": "contract:generate_confirm_image", "label": "生成确认图"},
                {"key": "contract:view_versions", "label": "查看版本历史"},
                {"key": "contract:push_down", "label": "下推行项目到工艺单"},
            ]
        },
        {
            "module": "工艺单管理",
            "module_key": "sheet",
            "permissions": [
                {"key": "sheet:view", "label": "查看工艺单"},
                {"key": "sheet:create", "label": "新建/下推工艺单"},
                {"key": "sheet:edit", "label": "编辑工艺单"},
                {"key": "sheet:delete", "label": "删除工艺单"},
                {"key": "sheet:mark_version", "label": "客户沟通标记"},
                {"key": "sheet:internal_confirm", "label": "内部确认"},
                {"key": "sheet:force_confirm", "label": "强制通过"},
                {"key": "sheet:set_confirm_users", "label": "设置内部确认人"},
                {"key": "sheet:dispatch", "label": "下发工艺单"},
                {"key": "sheet:print", "label": "打印PDF"},
                {"key": "sheet:reopen_edit", "label": "重新打开编辑"},
                {"key": "sheet:generate_confirm_link", "label": "生成确认链接"},
            ]
        },
        {
            "module": "生产管理",
            "module_key": "production",
            "permissions": [
                {"key": "production:manage_steps", "label": "管理工序（CRUD）"},
                {"key": "production:advance", "label": "生产推进"},
                {"key": "production:rollback", "label": "回退"},
                {"key": "production:rework", "label": "返工"},
                {"key": "production:cancel", "label": "取消行项目"},
                {"key": "production:restore", "label": "恢复已取消行项目"},
                {"key": "production:yarn_plan", "label": "下达坯布计划"},
            ]
        },
        {
            "module": "基础数据",
            "module_key": "basic_data",
            "permissions": [
                {"key": "basic_data:view", "label": "查看基础数据"},
                {"key": "basic_data:manage", "label": "管理基础数据"},
                {"key": "customer:manage", "label": "管理客户"},
                {"key": "spec:manage", "label": "管理规格"},
            ]
        },
        {
            "module": "系统设置",
            "module_key": "settings",
            "permissions": [
                {"key": "settings:user:view", "label": "查看用户列表"},
                {"key": "settings:user:manage", "label": "管理用户"},
                {"key": "settings:webhook:view", "label": "查看Webhook"},
                {"key": "settings:webhook:manage", "label": "管理Webhook"},
                {"key": "settings:permissions:manage", "label": "管理角色权限"},
            ]
        },
    ]
