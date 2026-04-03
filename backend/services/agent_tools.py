from sqlalchemy.orm import Session
from datetime import timezone
import logging
from models.models import User

logger = logging.getLogger(__name__)

# 导入拆分后的物理隔离 Skills
from skills import TOOLS, TOOL_REGISTRY

def execute_tool(tool_name: str, db: Session, current_user: User, user_tz=timezone.utc, **kwargs):
    logger.info(f"--- [Skill Call] User: {current_user.id} | Action: {tool_name} ---")
    if tool_name not in TOOL_REGISTRY:
        logger.warning(f"--- [Skill Error] Unknown Tool: {tool_name} ---")
        return {"status": "error", "message": f"未知工具: {tool_name}"}
    try:
        # 针对需要 timezone 的函数，自动注入 user_tz
        if "schedule" in tool_name:
            result = TOOL_REGISTRY[tool_name](db, current_user, user_tz=user_tz, **kwargs)
        else:
            result = TOOL_REGISTRY[tool_name](db, current_user, **kwargs)
        
        logger.info(f"--- [Skill Success] Action: {tool_name} | Result: {str(result)[:100]}... ---")
        return result
    except Exception as e:
        logger.error(f"--- [Skill Exception] Action: {tool_name} | Error: {str(e)} ---")
        return {"status": "error", "message": f"工具执行异常: {str(e)}"}

