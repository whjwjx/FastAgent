from sqlalchemy.orm import Session
from datetime import timezone
import logging
from models.models import User

logger = logging.getLogger(__name__)

# 导入拆分后的子模块
from services.tools.search_tools import tool_search_web, SEARCH_TOOLS_SCHEMA
from services.tools.schedule_tools import (
    tool_schedule_crud_create, 
    tool_schedule_crud_read, 
    tool_schedule_crud_update, 
    tool_schedule_crud_delete,
    SCHEDULE_TOOLS_SCHEMA
)
from services.tools.thought_tools import (
    tool_thought_crud_create, 
    tool_thought_crud_read, 
    tool_thought_crud_update, 
    tool_thought_crud_delete,
    THOUGHT_TOOLS_SCHEMA
)

# Tool Registry：集中注册所有子模块中的工具函数
TOOL_REGISTRY = {
    "search_web": tool_search_web,
    
    "thought:crud:create": tool_thought_crud_create,
    "thought:crud:read": tool_thought_crud_read,
    "thought:crud:update": tool_thought_crud_update,
    "thought:crud:delete": tool_thought_crud_delete,
    
    "schedule:crud:create": tool_schedule_crud_create,
    "schedule:crud:read": tool_schedule_crud_read,
    "schedule:crud:update": tool_schedule_crud_update,
    "schedule:crud:delete": tool_schedule_crud_delete
}

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

# 组装所有工具的 Schema 供大模型调用
TOOLS = []
TOOLS.extend(SEARCH_TOOLS_SCHEMA)
TOOLS.extend(THOUGHT_TOOLS_SCHEMA)
TOOLS.extend(SCHEDULE_TOOLS_SCHEMA)
