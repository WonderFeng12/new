"""定时催办任务"""
import logging
from datetime import date, datetime
from app.database import SessionLocal
from app.services.contract import get_contracts_pending_confirm, mark_reminded
from app.services.notify import notify_contract_confirm_reminder
from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)


def check_contract_reminders():
    """每天早上8点执行：检查有未确认的合同并发送催办提醒。"""
    try:
        db = SessionLocal()
        try:
            pending = get_contracts_pending_confirm(db)
            if not pending:
                logger.info("无待催办的合同确认请求")
                return

            # Read system base URL for the reminder link
            config = db.query(SystemConfig).filter(
                SystemConfig.config_key == "system_base_url"
            ).first()
            base_url = config.config_value if config else ""

            logger.info(f"发现 {len(pending)} 个待确认合同，发送催办提醒")
            notify_contract_confirm_reminder(db, pending, base_url=base_url)

            # Mark all reminded contracts
            for c in pending:
                mark_reminded(db, c["contract_no"])

            logger.info(f"催办提醒已发送，共 {len(pending)} 个合同")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"催办任务执行失败: {e}")
