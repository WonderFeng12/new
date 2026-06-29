"""企业微信通知服务"""
import json
import logging
from datetime import date, datetime
import httpx
from sqlalchemy.orm import Session
from app.models.webhook_config import WebhookConfig
from app.models.user import User

logger = logging.getLogger(__name__)


def _get_webhook_info(db: Session, webhook_type: str = "合同通知") -> tuple[str | None, bool]:
    """Get webhook URL and enabled status by type name."""
    wh = db.query(WebhookConfig).filter(
        WebhookConfig.name == webhook_type
    ).first()
    if wh and wh.is_enabled and wh.webhook_url:
        return wh.webhook_url, True
    return None, False


def _get_sales_manager_wecom_ids(db: Session) -> list[str]:
    """Get WeCom user IDs of all sales managers for @mention."""
    users = db.query(User).filter(
        User.role == "销售经理",
        User.wecom_userid.isnot(None),
        User.wecom_userid != "",
        User.is_active == True,
    ).all()
    return [u.wecom_userid for u in users]


def send_message(db: Session, content: str, mentioned_list: list[str] = None,
                 webhook_type: str = "合同通知") -> bool:
    """Send a message to the WeCom group chat via webhook.

    Args:
        db: Database session
        content: Message text content
        mentioned_list: List of WeCom user IDs to @mention
        webhook_type: Webhook config name (合同通知/工艺单通知)

    Returns:
        True if sent successfully, False otherwise
    """
    webhook_url, enabled = _get_webhook_info(db, webhook_type)
    if not enabled:
        logger.info(f"Webhook [{webhook_type}] not configured or disabled, skipping")
        return True
    if not webhook_url:
        logger.warning(f"No webhook URL configured for [{webhook_type}]")
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
        logger.info(f"WeCom [{webhook_type}] notification sent: {content[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to send WeCom [{webhook_type}] notification: {e}")
        return False


def notify_contract_ready_for_confirm(db: Session, contract_no: str, creator_name: str,
                                       base_url: str = "", contract_id: int = None):
    """Notify sales manager that a contract needs confirmation. @mentions all sales managers."""
    managers = _get_sales_manager_wecom_ids(db)
    link = ""
    if base_url and contract_id:
        link = f"\n查看地址：{base_url}/contracts/{contract_id}"
    content = (
        f"📋 合同确认请求\n"
        f"合同号：{contract_no}\n"
        f"创建人：{creator_name}{link}\n"
        f"请尽快确认。"
    )
    send_message(db, content, managers if managers else None, webhook_type="合同通知")


def notify_contract_confirm_reminder(db: Session, contracts: list[dict],
                                      base_url: str = ""):
    """Send a batch reminder about contracts pending confirmation."""
    if not contracts:
        return

    managers = _get_sales_manager_wecom_ids(db)
    general_link = f"\n系统地址：{base_url}" if base_url else ""
    lines = [f"⏰ 合同确认催办提醒 ({date.today().isoformat()}){general_link}"]
    for c in contracts:
        req_time = c.get("requested_at", "")
        lines.append(f"• {c['contract_no']}（请求时间：{req_time}）")
    lines.append("请及时处理。")

    content = "\n".join(lines)
    send_message(db, content, managers if managers else None, webhook_type="合同通知")


def notify_yarn_plan_released(db: Session, contract_no: str, spec_desc: str,
                               assignee_wecom_id: str = None):
    """Notify the external worker about yarn plan assignment."""
    content = (
        f"🧵 坯布计划已下达\n"
        f"合同：{contract_no} | {spec_desc}\n"
        f"请查看并安排织造。"
    )
    mentioned = [assignee_wecom_id] if assignee_wecom_id else None
    send_message(db, content, mentioned, webhook_type="工艺单通知")


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
    send_message(db, content, next_assignee_wecom_ids, webhook_type="工艺单通知")


def notify_item_cancelled(db: Session, contract_no: str, spec_desc: str,
                           reason: str, operator: str):
    """Notify that a line item has been cancelled."""
    content = (
        f"❌ 行项目取消通知\n"
        f"合同：{contract_no} | {spec_desc}\n"
        f"原因：{reason}\n"
        f"操作人：{operator}"
    )
    send_message(db, content, webhook_type="工艺单通知")


def notify_completed(db: Session, contract_no: str, spec_desc: str):
    """Notify that a line item has been completed."""
    content = (
        f"✅ 成品完成通知\n"
        f"合同：{contract_no} | {spec_desc}\n"
        f"该行项目已全部完成。"
    )
    send_message(db, content, webhook_type="工艺单通知")
