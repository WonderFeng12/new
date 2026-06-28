"""企业微信通知服务"""
import json
import logging
import httpx
from sqlalchemy.orm import Session
from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)


def _get_webhook_url(db: Session) -> str | None:
    """Get the configured WeCom webhook URL."""
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == "wecom_webhook_url"
    ).first()
    return config.config_value if config else None


def _is_notify_enabled(db: Session) -> bool:
    """Check if production notifications are enabled."""
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == "production_notify_enabled"
    ).first()
    return config.config_value == "true" if config else False


def send_message(db: Session, content: str, mentioned_list: list[str] = None) -> bool:
    """Send a message to the WeCom group chat via webhook.

    Args:
        db: Database session
        content: Message text content
        mentioned_list: List of WeCom user IDs to @mention

    Returns:
        True if sent successfully, False otherwise
    """
    if not _is_notify_enabled(db):
        logger.info("Notifications disabled, skipping")
        return True

    webhook_url = _get_webhook_url(db)
    if not webhook_url:
        logger.warning("No WeCom webhook URL configured")
        return False

    payload = {
        "msgtype": "text",
        "text": {
            "content": content,
        }
    }
    if mentioned_list:
        payload["text"]["mentioned_list"] = mentioned_list

    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        if result.get("errcode") != 0:
            logger.error(f"WeCom API error: {result}")
            return False
        logger.info(f"WeCom notification sent: {content[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to send WeCom notification: {e}")
        return False


def notify_contract_ready_for_confirm(db: Session, contract_no: str, creator_name: str):
    """Notify sales manager that a contract needs confirmation."""
    content = (
        f"📋 合同确认请求\n"
        f"合同号：{contract_no}\n"
        f"创建人：{creator_name}\n"
        f"请尽快确认。"
    )
    send_message(db, content)


def notify_yarn_plan_released(db: Session, contract_no: str, spec_desc: str,
                               assignee_wecom_id: str = None):
    """Notify the external worker about yarn plan assignment."""
    content = (
        f"🧵 坯布计划已下达\n"
        f"合同：{contract_no} | {spec_desc}\n"
        f"请查看并安排织造。"
    )
    mentioned = [assignee_wecom_id] if assignee_wecom_id else None
    send_message(db, content, mentioned)


def notify_production_advance(db: Session, contract_no: str, spec_desc: str,
                               from_step: str, to_step: str, operator: str,
                               next_assignee_wecom_ids: list[str] = None):
    """Notify that production has advanced to the next step."""
    content = (
        f"📈 生产进度通知\n"
        f"合同：{contract_no} | {spec_desc}\n"
        f"工序：{from_step} → {to_step}\n"
        f"操作人：{operator}\n"
        f"下一道工序请安排。"
    )
    send_message(db, content, next_assignee_wecom_ids)


def notify_item_cancelled(db: Session, contract_no: str, spec_desc: str,
                           reason: str, operator: str):
    """Notify that a line item has been cancelled."""
    content = (
        f"❌ 行项目取消通知\n"
        f"合同：{contract_no} | {spec_desc}\n"
        f"原因：{reason}\n"
        f"操作人：{operator}"
    )
    send_message(db, content)


def notify_completed(db: Session, contract_no: str, spec_desc: str):
    """Notify that a line item has been completed."""
    content = (
        f"✅ 成品完成通知\n"
        f"合同：{contract_no} | {spec_desc}\n"
        f"该行项目已全部完成。"
    )
    send_message(db, content)
