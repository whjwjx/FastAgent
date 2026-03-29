from sqlalchemy.orm import Session
from datetime import timezone
from models.models import User

# 导入拆分后的子模块
from services.tools.search_tools import tool_search_web, SEARCH_TOOLS_SCHEMA
from services.tools.schedule_tools import (
    tool_create_schedule, 
    tool_read_schedules, 
    tool_update_schedule, 
    tool_delete_schedule,
    SCHEDULE_TOOLS_SCHEMA
)
from services.tools.thought_tools import (
    tool_create_thought, 
    tool_read_thoughts, 
    tool_update_thought, 
    tool_delete_thought,
    THOUGHT_TOOLS_SCHEMA
)

# Tool Registry：集中注册所有子模块中的工具函数
TOOL_REGISTRY = {
    "search_web": tool_search_web,
    
    "create_thought": tool_create_thought,
    "read_thoughts": tool_read_thoughts,
    "update_thought": tool_update_thought,
    "delete_thought": tool_delete_thought,
    
    "create_schedule": tool_create_schedule,
    "read_schedules": tool_read_schedules,
    "update_schedule": tool_update_schedule,
    "delete_schedule": tool_delete_schedule
}

def execute_tool(tool_name: str, db: Session, current_user: User, user_tz=timezone.utc, **kwargs):
    if tool_name not in TOOL_REGISTRY:
        return {"status": "error", "message": f"未知工具: {tool_name}"}
    try:
        # 针对需要 timezone 的函数，自动注入 user_tz
        if tool_name in ["create_schedule", "read_schedules", "update_schedule"]:
            return TOOL_REGISTRY[tool_name](db, current_user, user_tz=user_tz, **kwargs)
        else:
            return TOOL_REGISTRY[tool_name](db, current_user, **kwargs)
    except Exception as e:
        return {"status": "error", "message": f"工具执行异常: {str(e)}"}

# 组装所有工具的 Schema 供大模型调用
TOOLS = []
TOOLS.extend(SEARCH_TOOLS_SCHEMA)
TOOLS.extend(THOUGHT_TOOLS_SCHEMA)
TOOLS.extend(SCHEDULE_TOOLS_SCHEMA)
